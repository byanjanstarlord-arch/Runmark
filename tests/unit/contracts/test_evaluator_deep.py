"""Deep unit tests for ContractEvaluator covering containers, dependencies, network, and edge cases."""

from datetime import datetime, timezone

from runmark.contracts.evaluator import ContractEvaluator
from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.contract import RunmarkContract
from runmark.models.contract_result import ContractCheckStatus
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.network import PortState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState


def create_deep_state(
    os_name: str = "Linux",
    arch: str = "x86_64",
    runtimes: dict[str, RuntimeState] | None = None,
    dependencies: list[DependencyState] | None = None,
    services: list[ServiceState] | None = None,
    ports: list[PortState] | None = None,
    containerization: list[str] | None = None,
) -> RunmarkState:
    """Mock state with full custom subcomponents."""
    return RunmarkState(
        runmark=RunmarkMetadata(
            id="deep-snap",
            created_at=datetime.now(timezone.utc).isoformat(),
            tool_version="0.2.0",
            schema_version="1.0",
            environment_fingerprint="deep-fp",
        ),
        project=ProjectState(
            name="deep-project",
            root="/app",
            languages=["python", "node"],
            frameworks=[],
            package_managers=["pip", "npm"],
            containerization=containerization or [],
        ),
        git=GitState(is_repository=False, dirty=False),
        system=SystemState(
            os_name=os_name,
            os_version="6.1.0",
            architecture=arch,
        ),
        runtimes=runtimes or {},
        dependencies=dependencies or [],
        services=services or [],
        environment=EnvironmentState(variables={}),
        network=ports or [],
        containers=[],
    )


class TestContractEvaluatorDeep:
    """Deep coverage of evaluator edge cases."""

    def test_architecture_mismatch_and_alias(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "platform": {"architecture": ["arm64"]}}
        )
        # x86_64 should fail when only arm64 is accepted
        state_x86 = create_deep_state(arch="x86_64")
        res_x86 = ContractEvaluator.evaluate(contract, state_x86)
        assert res_x86.is_failed

        # aarch64 should match arm64 alias
        state_arm = create_deep_state(arch="aarch64")
        res_arm = ContractEvaluator.evaluate(contract, state_arm)
        assert res_arm.is_passed

    def test_container_docker_missing_fails(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "containers": {"docker": {"required": True}}}
        )
        state = create_deep_state(runtimes={})
        res = ContractEvaluator.evaluate(contract, state)
        assert res.is_failed
        docker_check = next(c for c in res.checks if c.id == "container.docker")
        assert docker_check.status == ContractCheckStatus.FAIL

    def test_container_compose_missing_fails(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "containers": {"compose": {"required": True}}}
        )
        state = create_deep_state(runtimes={}, containerization=[])
        res = ContractEvaluator.evaluate(contract, state)
        assert res.is_failed
        compose_check = next(c for c in res.checks if c.id == "container.compose")
        assert compose_check.status == ContractCheckStatus.FAIL

    def test_dependencies_evaluation(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "dependencies": {
                    "python": {"fastapi": ">=0.100.0", "flask": "3.x", "missing_pkg": "1.0.0"},
                },
            }
        )
        deps = [
            DependencyState(
                name="fastapi",
                manager="pip",
                declared=">=0.100.0",
                resolved="0.109.0",
                kind=DependencyKind.DIRECT,
            ),
            DependencyState(
                name="flask",
                manager="pip",
                declared="^2.0.0",
                resolved="2.3.2",
                kind=DependencyKind.DIRECT,
            ),
        ]
        state = create_deep_state(dependencies=deps)
        res = ContractEvaluator.evaluate(contract, state)
        assert res.is_failed

        fastapi_check = next(c for c in res.checks if c.id == "dependency.python.fastapi")
        assert fastapi_check.status == ContractCheckStatus.PASS

        flask_check = next(c for c in res.checks if c.id == "dependency.python.flask")
        assert flask_check.status == ContractCheckStatus.FAIL

        missing_check = next(c for c in res.checks if c.id == "dependency.python.missing_pkg")
        assert missing_check.status == ContractCheckStatus.UNKNOWN

    def test_service_running_version_mismatch(self) -> None:
        contract = RunmarkContract.model_validate({"version": 1, "services": {"redis": ">=7.0"}})
        redis_svc = ServiceState(
            name="redis",
            status=DetectionStatus.DETECTED,
            installed=True,
            running=True,
            detected_version="6.2.6",
        )
        state = create_deep_state(services=[redis_svc])
        res = ContractEvaluator.evaluate(contract, state)
        assert res.is_failed
        redis_check = next(c for c in res.checks if c.id == "service.redis")
        assert redis_check.status == ContractCheckStatus.FAIL

    def test_service_running_version_unknown(self) -> None:
        contract = RunmarkContract.model_validate({"version": 1, "services": {"redis": ">=7.0"}})
        redis_svc = ServiceState(
            name="redis",
            status=DetectionStatus.DETECTED,
            installed=True,
            running=True,
            detected_version=None,
        )
        state = create_deep_state(services=[redis_svc])
        res = ContractEvaluator.evaluate(contract, state)
        assert res.status == ContractCheckStatus.UNKNOWN
        redis_check = next(c for c in res.checks if c.id == "service.redis")
        assert redis_check.status == ContractCheckStatus.UNKNOWN
