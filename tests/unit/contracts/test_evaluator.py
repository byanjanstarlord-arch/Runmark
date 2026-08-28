"""Unit tests for ContractEvaluator."""

from datetime import datetime, timezone

from runmark.contracts.evaluator import ContractEvaluator
from runmark.models.common import DetectionStatus
from runmark.models.contract import RunmarkContract
from runmark.models.contract_result import ContractCheckStatus
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState


def create_dummy_state(
    os_name: str = "Windows",
    arch: str = "AMD64",
    python_version: str | None = "3.12.4",
    python_installed: bool = True,
    node_version: str | None = "20.11.0",
    node_installed: bool = True,
    env_vars: dict[str, bool] | None = None,
    services: list[ServiceState] | None = None,
    docker_installed: bool = True,
) -> RunmarkState:
    """Helper to generate a mock RunmarkState for deterministic evaluator testing."""
    runtimes = {}
    if python_installed or python_version:
        runtimes["python"] = RuntimeState(
            name="python",
            installed=python_installed,
            version=python_version,
            status=DetectionStatus.DETECTED if python_installed else DetectionStatus.NOT_FOUND,
            executable_path="python",
        )
    if node_installed or node_version:
        runtimes["node"] = RuntimeState(
            name="node",
            installed=node_installed,
            version=node_version,
            status=DetectionStatus.DETECTED if node_installed else DetectionStatus.NOT_FOUND,
            executable_path="node",
        )
    if docker_installed:
        runtimes["docker"] = RuntimeState(
            name="docker",
            installed=True,
            version="26.1.1",
            status=DetectionStatus.DETECTED,
            executable_path="docker",
        )

    variables = {}
    if env_vars:
        for name, present in env_vars.items():
            variables[name] = EnvironmentVariableState(
                name=name,
                required=False,
                present=present,
                secret=False,
                source="test",
            )

    return RunmarkState(
        runmark=RunmarkMetadata(
            id="test-state-id",
            created_at=datetime.now(timezone.utc).isoformat(),
            tool_version="0.2.0",
            schema_version="1.0",
            environment_fingerprint="test-fp",
        ),
        project=ProjectState(
            name="test-project",
            root="C:\\test-project",
            languages=["python"],
            frameworks=[],
            package_managers=["pip"],
            containerization=[],
        ),
        git=GitState(is_repository=False, dirty=False),
        system=SystemState(
            os_name=os_name,
            os_version="10.0.22631",
            architecture=arch,
        ),
        runtimes=runtimes,
        dependencies=[],
        services=services or [],
        environment=EnvironmentState(variables=variables),
        network=[],
        containers=[],
    )


class TestContractEvaluator:
    """Tests for ContractEvaluator logic across domains."""

    def test_evaluate_platform_pass(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "platform": {"os": ["windows", "linux"], "architecture": ["amd64", "arm64"]},
            }
        )
        state = create_dummy_state(os_name="Windows", arch="AMD64")
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_passed
        assert result.status == ContractCheckStatus.PASS

    def test_evaluate_platform_os_fail(self) -> None:
        contract = RunmarkContract.model_validate({"version": 1, "platform": {"os": ["linux"]}})
        state = create_dummy_state(os_name="Windows")
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_failed
        assert any(
            c.id == "platform.os" and c.status == ContractCheckStatus.FAIL for c in result.checks
        )

    def test_evaluate_runtime_pass_and_fail(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "runtime": {"python": ">=3.12", "node": "<18"}}
        )
        state = create_dummy_state(python_version="3.12.4", node_version="20.11.0")
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_failed
        # Python passed
        py_check = next(c for c in result.checks if c.id == "runtime.python")
        assert py_check.status == ContractCheckStatus.PASS
        # Node failed (20.11.0 is not <18)
        node_check = next(c for c in result.checks if c.id == "runtime.node")
        assert node_check.status == ContractCheckStatus.FAIL

    def test_evaluate_runtime_unknown_version(self) -> None:
        contract = RunmarkContract.model_validate({"version": 1, "runtime": {"python": ">=3.12"}})
        state = create_dummy_state(python_version=None, python_installed=True)
        result = ContractEvaluator.evaluate(contract, state)
        assert result.status == ContractCheckStatus.UNKNOWN
        py_check = next(c for c in result.checks if c.id == "runtime.python")
        assert py_check.status == ContractCheckStatus.UNKNOWN

    def test_evaluate_services_required_vs_optional(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "services": {
                    "postgresql": {"version": ">=14", "required": True},
                    "redis": {"version": ">=6", "required": False},
                },
            }
        )
        # Machine with no services running
        state = create_dummy_state(services=[])
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_failed
        pg_check = next(c for c in result.checks if c.id == "service.postgresql")
        assert pg_check.status == ContractCheckStatus.FAIL
        redis_check = next(c for c in result.checks if c.id == "service.redis")
        assert redis_check.status == ContractCheckStatus.SKIPPED

    def test_evaluate_services_running_and_satisfied(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "services": {"postgresql": ">=14"}}
        )
        pg_svc = ServiceState(
            name="postgresql",
            status=DetectionStatus.DETECTED,
            installed=True,
            running=True,
            port=5432,
            detected_version="15.2",
        )
        state = create_dummy_state(services=[pg_svc])
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_passed

    def test_evaluate_environment_variables(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "environment": {
                    "required": ["DATABASE_URL", "SECRET_KEY"],
                    "optional": ["DEBUG"],
                },
            }
        )
        state = create_dummy_state(
            env_vars={"DATABASE_URL": True, "SECRET_KEY": False, "DEBUG": False}
        )
        result = ContractEvaluator.evaluate(contract, state)
        assert result.is_failed
        db_check = next(c for c in result.checks if c.id == "environment.DATABASE_URL")
        assert db_check.status == ContractCheckStatus.PASS
        sec_check = next(c for c in result.checks if c.id == "environment.SECRET_KEY")
        assert sec_check.status == ContractCheckStatus.FAIL
        dbg_check = next(c for c in result.checks if c.id == "environment.DEBUG")
        assert dbg_check.status == ContractCheckStatus.SKIPPED
