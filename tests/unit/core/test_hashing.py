"""Unit tests for deterministic canonicalization and fingerprinting."""

from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.system import SystemState
from runmark.utils.hashing import calculate_environment_fingerprint


def _make_sample_state(
    py_version: str = "3.12.4",
    deps: list = None,
    created_at: str = "2026-01-01T00:00:00Z",
    git_commit: str = "abc1234",
) -> RunmarkState:
    dependencies = deps or [
        DependencyState(
            name="django",
            manager="pip",
            declared=">=5.0",
            resolved="5.0.6",
            kind=DependencyKind.DIRECT,
        ),
        DependencyState(
            name="redis",
            manager="pip",
            declared=">=5.0",
            resolved="5.0.4",
            kind=DependencyKind.DIRECT,
        ),
    ]

    return RunmarkState(
        runmark=RunmarkMetadata(
            id="snap_123",
            created_at=created_at,
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="",
        ),
        project=ProjectState(
            name="test-project",
            root="test-project",
            languages=["python"],
            frameworks=["django"],
            package_managers=["pip"],
            containerization=[],
        ),
        git=GitState(
            is_repository=True,
            branch="main",
            commit=git_commit,
            dirty=False,
        ),
        system=SystemState(
            os_name="Linux",
            os_version="6.1.0",
            architecture="x86_64",
        ),
        runtimes={
            "python": RuntimeState(
                name="python",
                installed=True,
                version=py_version,
                status=DetectionStatus.DETECTED,
            )
        },
        dependencies=dependencies,
        services=[],
        environment=EnvironmentState(
            variables={
                "DEBUG": EnvironmentVariableState(
                    name="DEBUG",
                    required=False,
                    present=True,
                    secret=False,
                    source="process",
                )
            }
        ),
        network=[],
        containers=[],
    )


def test_same_logical_state_produces_same_canonical_hash():
    s1 = _make_sample_state()
    s2 = _make_sample_state()

    fp1 = calculate_environment_fingerprint(s1)
    fp2 = calculate_environment_fingerprint(s2)

    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex length


def test_different_python_version_produces_different_fingerprint():
    s1 = _make_sample_state(py_version="3.12.4")
    s2 = _make_sample_state(py_version="3.11.9")

    fp1 = calculate_environment_fingerprint(s1)
    fp2 = calculate_environment_fingerprint(s2)

    assert fp1 != fp2


def test_dependency_ordering_does_not_change_fingerprint():
    dep_a = DependencyState(
        name="django", manager="pip", declared=">=5.0", resolved="5.0.6", kind=DependencyKind.DIRECT
    )
    dep_b = DependencyState(
        name="redis", manager="pip", declared=">=5.0", resolved="5.0.4", kind=DependencyKind.DIRECT
    )

    s1 = _make_sample_state(deps=[dep_a, dep_b])
    s2 = _make_sample_state(deps=[dep_b, dep_a])  # reversed order

    fp1 = calculate_environment_fingerprint(s1)
    fp2 = calculate_environment_fingerprint(s2)

    assert fp1 == fp2


def test_timestamp_and_git_commit_do_not_change_environment_fingerprint():
    s1 = _make_sample_state(created_at="2026-01-01T00:00:00Z", git_commit="commit_1111")
    s2 = _make_sample_state(created_at="2026-12-31T23:59:59Z", git_commit="commit_9999")

    fp1 = calculate_environment_fingerprint(s1)
    fp2 = calculate_environment_fingerprint(s2)

    assert fp1 == fp2
