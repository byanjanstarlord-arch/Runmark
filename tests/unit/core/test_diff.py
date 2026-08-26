"""Unit tests for semantic diff engine."""

from runmark.core.diff import DiffClassification, DiffEngine, DiffSeverity
from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.system import SystemState


def _build_base():
    return RunmarkState(
        runmark=RunmarkMetadata(id="snap_base", tool_version="0.1.0", schema_version="1.0"),
        project=ProjectState(name="app", root="app"),
        git=GitState(is_repository=True, branch="main", commit="1111111", dirty=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version="3.12.4", status=DetectionStatus.DETECTED
            ),
            "node": RuntimeState(
                name="node", installed=True, version="22.5.1", status=DetectionStatus.DETECTED
            ),
        },
        dependencies=[
            DependencyState(
                name="django",
                manager="pip",
                declared=">=5.0",
                resolved="5.0.6",
                kind=DependencyKind.DIRECT,
            ),
            DependencyState(
                name="requests",
                manager="pip",
                declared="==2.31.0",
                resolved="2.31.0",
                kind=DependencyKind.DIRECT,
            ),
        ],
        services=[],
        environment=EnvironmentState(
            variables={
                "STRIPE_SECRET_KEY": EnvironmentVariableState(
                    name="STRIPE_SECRET_KEY",
                    required=True,
                    present=True,
                    secret=True,
                    source=".env.example",
                ),
                "DEBUG": EnvironmentVariableState(
                    name="DEBUG", required=False, present=True, secret=False, source="process"
                ),
            }
        ),
        network=[],
        containers=[],
    )


def test_added_dependency_detected():
    base = _build_base()
    curr = _build_base()
    curr.dependencies.append(
        DependencyState(
            name="celery",
            manager="pip",
            declared=">=5.3",
            resolved="5.3.6",
            kind=DependencyKind.DIRECT,
        )
    )

    diff = DiffEngine.compare(base, curr)
    assert not diff.is_identical
    added = next((i for i in diff.items if i.item_name == "celery"), None)
    assert added is not None
    assert added.classification == DiffClassification.ADDED
    assert added.severity == DiffSeverity.INFO


def test_removed_dependency_detected():
    base = _build_base()
    curr = _build_base()
    curr.dependencies = [d for d in curr.dependencies if d.name != "requests"]

    diff = DiffEngine.compare(base, curr)
    assert not diff.is_identical
    removed = next((i for i in diff.items if i.item_name == "requests"), None)
    assert removed is not None
    assert removed.classification == DiffClassification.REMOVED


def test_runtime_version_change_detected():
    base = _build_base()
    curr = _build_base()
    curr.runtimes["node"] = RuntimeState(
        name="node", installed=True, version="23.0.0", status=DetectionStatus.DETECTED
    )

    diff = DiffEngine.compare(base, curr)
    node_diff = next((i for i in diff.items if i.item_name == "node"), None)
    assert node_diff is not None
    assert node_diff.classification == DiffClassification.CHANGED
    assert node_diff.severity == DiffSeverity.CRITICAL  # Major version bump 22 -> 23


def test_missing_required_environment_variable_detected():
    base = _build_base()
    curr = _build_base()
    curr.environment.variables["STRIPE_SECRET_KEY"] = EnvironmentVariableState(
        name="STRIPE_SECRET_KEY", required=True, present=False, secret=True, source=".env.example"
    )

    diff = DiffEngine.compare(base, curr)
    env_diff = next((i for i in diff.items if i.item_name == "STRIPE_SECRET_KEY"), None)
    assert env_diff is not None
    assert env_diff.classification == DiffClassification.CHANGED
    assert env_diff.severity == DiffSeverity.CRITICAL
