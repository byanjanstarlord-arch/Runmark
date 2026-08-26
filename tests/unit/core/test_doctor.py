"""Unit tests for doctor diagnostics engine."""

from runmark.core.diff import DiffEngine
from runmark.core.doctor import Doctor
from runmark.models.common import DetectionStatus
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.system import SystemState


def test_doctor_diagnoses_missing_required_env_var():
    state = RunmarkState(
        runmark=RunmarkMetadata(id="snap_doc", tool_version="0.1.0", schema_version="1.0"),
        project=ProjectState(name="app", root="app", languages=["python"]),
        git=GitState(is_repository=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version="3.12.4", status=DetectionStatus.DETECTED
            )
        },
        dependencies=[],
        services=[],
        environment=EnvironmentState(
            variables={
                "STRIPE_SECRET_KEY": EnvironmentVariableState(
                    name="STRIPE_SECRET_KEY",
                    required=True,
                    present=False,
                    secret=True,
                    source=".env.example",
                )
            }
        ),
        network=[],
        containers=[],
    )

    report = Doctor.diagnose_state(state)
    assert not report.is_healthy
    assert report.has_critical is True
    assert len(report.issues) == 1

    issue = report.issues[0]
    assert issue.code == "ENV_MISSING_REQUIRED"
    assert "STRIPE_SECRET_KEY" in issue.evidence["variable"]
    assert "Add 'STRIPE_SECRET_KEY'" in issue.suggested_action


def test_doctor_diagnoses_diff():
    base = RunmarkState(
        runmark=RunmarkMetadata(id="snap_base", tool_version="0.1.0", schema_version="1.0"),
        project=ProjectState(name="app", root="app", languages=["javascript"]),
        git=GitState(is_repository=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "node": RuntimeState(
                name="node", installed=True, version="22.5.1", status=DetectionStatus.DETECTED
            )
        },
        dependencies=[],
        services=[],
        environment=EnvironmentState(),
        network=[],
        containers=[],
    )

    curr = RunmarkState(
        runmark=RunmarkMetadata(id="snap_curr", tool_version="0.1.0", schema_version="1.0"),
        project=ProjectState(name="app", root="app", languages=["javascript"]),
        git=GitState(is_repository=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "node": RuntimeState(
                name="node", installed=True, version="20.18.0", status=DetectionStatus.DETECTED
            )
        },
        dependencies=[],
        services=[],
        environment=EnvironmentState(),
        network=[],
        containers=[],
    )

    diff = DiffEngine.compare(base, curr)
    report = Doctor.diagnose_diff(diff)
    assert not report.is_healthy
    assert len(report.issues) >= 1
    assert any(i.code == "DIFF_RUNTIME_CRITICAL" for i in report.issues)
