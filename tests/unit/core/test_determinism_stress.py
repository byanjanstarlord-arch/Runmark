"""Stress testing and invariant validation for deterministic SHA-256 fingerprinting."""

from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.network import PortState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState
from runmark.utils.hashing import calculate_environment_fingerprint


def _build_test_state(
    py_version="3.12.4",
    node_version="20.14.0",
    deps=None,
    env_vars=None,
    git_commit="abcdef123456",
    timestamp="2026-01-01T00:00:00Z",
    snapshot_id="snap_1234",
):
    if deps is None:
        deps = [
            DependencyState(
                name="fastapi",
                manager="pip",
                declared=">=0.110.0",
                resolved="0.110.1",
                kind=DependencyKind.DIRECT,
            ),
            DependencyState(
                name="pydantic",
                manager="pip",
                declared=">=2.0.0",
                resolved="2.7.4",
                kind=DependencyKind.DIRECT,
            ),
            DependencyState(
                name="pytest",
                manager="pip",
                declared=">=8.0.0",
                resolved="8.2.0",
                kind=DependencyKind.DEV,
            ),
        ]
    if env_vars is None:
        env_vars = {
            "API_KEY": EnvironmentVariableState(
                name="API_KEY", required=True, present=True, secret=True, source=".env"
            ),
            "PORT": EnvironmentVariableState(
                name="PORT", required=False, present=True, secret=False, source="environment"
            ),
            "DB_HOST": EnvironmentVariableState(
                name="DB_HOST", required=True, present=True, secret=False, source=".env.example"
            ),
        }

    return RunmarkState(
        runmark=RunmarkMetadata(
            id=snapshot_id,
            created_at=timestamp,
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="placeholder",
            message="Test state",
        ),
        project=ProjectState(
            name="test-app",
            root="test-app",
            languages=["python", "javascript"],
            frameworks=["fastapi"],
            package_managers=["pip", "npm"],
            containerization=["docker"],
        ),
        git=GitState(is_repository=True, branch="main", commit=git_commit, dirty=False),
        system=SystemState(os_name="Linux", os_version="6.1.0", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version=py_version, status=DetectionStatus.DETECTED
            ),
            "node": RuntimeState(
                name="node", installed=True, version=node_version, status=DetectionStatus.DETECTED
            ),
        },
        dependencies=deps,
        services=[
            ServiceState(
                name="postgres",
                installed=True,
                running=True,
                detected_version="16.2",
                expected_version="16",
                status=DetectionStatus.DETECTED,
                port=5432,
            ),
        ],
        environment=EnvironmentState(variables=env_vars),
        network=[
            PortState(port=5432, service="postgres", expected=True, occupied=True, status="in_use")
        ],
        containers=[],
    )


def test_repeated_hashing_determinism():
    """Verify that hashing the identical state across 50 iterations produces the exact same SHA-256 fingerprint."""
    state = _build_test_state()
    initial_fp = calculate_environment_fingerprint(state)

    for _ in range(50):
        fp = calculate_environment_fingerprint(state)
        assert fp == initial_fp


def test_order_invariance_dependencies_and_env():
    """Verify that changing the order of dependencies or environment variables does NOT alter the fingerprint."""
    state_a = _build_test_state()

    # Create reversed dependencies list
    state_b = _build_test_state(deps=list(reversed(state_a.dependencies)))

    fp_a = calculate_environment_fingerprint(state_a)
    fp_b = calculate_environment_fingerprint(state_b)
    assert fp_a == fp_b


def test_volatile_field_invariance():
    """Verify that timestamps, snapshot IDs, and commit messages do NOT alter the environment fingerprint."""
    state_1 = _build_test_state(
        timestamp="2026-01-01T12:00:00Z",
        snapshot_id="snap_111111111111",
    )
    state_2 = _build_test_state(
        timestamp="2026-08-26T23:59:59Z",
        snapshot_id="snap_999999999999",
    )

    fp_1 = calculate_environment_fingerprint(state_1)
    fp_2 = calculate_environment_fingerprint(state_2)
    assert fp_1 == fp_2


def test_git_commit_decoupling_from_environment_fingerprint():
    """Verify that Git commit changes do not alter the environment fingerprint (source revision != env state)."""
    state_commit_1 = _build_test_state(git_commit="1111111111111111111111111111111111111111")
    state_commit_2 = _build_test_state(git_commit="9999999999999999999999999999999999999999")

    fp_1 = calculate_environment_fingerprint(state_commit_1)
    fp_2 = calculate_environment_fingerprint(state_commit_2)
    assert fp_1 == fp_2


def test_fingerprint_mutation_sensitivity():
    """Verify that meaningful environment changes DO produce a different fingerprint."""
    base_state = _build_test_state(py_version="3.12.4")
    base_fp = calculate_environment_fingerprint(base_state)

    # 1. Modify Python runtime version
    diff_rt_state = _build_test_state(py_version="3.12.5")
    assert calculate_environment_fingerprint(diff_rt_state) != base_fp

    # 2. Modify Node runtime version
    diff_node_state = _build_test_state(node_version="22.0.0")
    assert calculate_environment_fingerprint(diff_node_state) != base_fp

    # 3. Modify dependency version
    diff_deps = [
        DependencyState(
            name="fastapi",
            manager="pip",
            declared=">=0.110.0",
            resolved="0.111.0",
            kind=DependencyKind.DIRECT,
        ),
    ]
    diff_dep_state = _build_test_state(deps=diff_deps)
    assert calculate_environment_fingerprint(diff_dep_state) != base_fp

    # 4. Modify required environment variable presence
    diff_env_vars = {
        "API_KEY": EnvironmentVariableState(
            name="API_KEY", required=True, present=False, secret=True, source=".env"
        ),
    }
    diff_env_state = _build_test_state(env_vars=diff_env_vars)
    assert calculate_environment_fingerprint(diff_env_state) != base_fp
