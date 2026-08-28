"""Hardened tests for Runmark Doctor evidence/inference distinction and read-only behavior."""

from runmark.core.diff import DiffEngine
from runmark.core.doctor import Doctor
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


def _make_doctor_test_state():
    return RunmarkState(
        runmark=RunmarkMetadata(
            id="snap_doc_test",
            created_at="2026-01-01T00:00:00Z",
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="abc123456789",
        ),
        project=ProjectState(
            name="app",
            root="app",
            languages=["python", "javascript"],
            frameworks=["fastapi"],
            package_managers=["pip", "npm"],
            containerization=["docker"],
        ),
        git=GitState(is_repository=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version="3.12.4", status=DetectionStatus.DETECTED
            ),
            "node": RuntimeState(
                name="node", installed=False, version=None, status=DetectionStatus.NOT_FOUND
            ),
            "docker": RuntimeState(
                name="docker", installed=False, version=None, status=DetectionStatus.NOT_FOUND
            ),
        },
        dependencies=[
            DependencyState(
                name="fastapi",
                manager="pip",
                declared=">=0.110.0",
                resolved="0.110.1",
                kind=DependencyKind.DIRECT,
            ),
        ],
        services=[
            ServiceState(
                name="postgres",
                installed=False,
                running=False,
                detected_version=None,
                expected_version="16",
                status=DetectionStatus.NOT_FOUND,
                port=5432,
            ),
        ],
        environment=EnvironmentState(
            variables={
                "SECRET_KEY": EnvironmentVariableState(
                    name="SECRET_KEY",
                    required=True,
                    present=False,
                    secret=True,
                    source=".env.example",
                ),
            }
        ),
        network=[
            PortState(port=5432, service="postgres", expected=True, occupied=False, status="free")
        ],
        containers=[],
    )


def test_doctor_issue_structure_and_evidence_separation():
    state = _make_doctor_test_state()
    report = Doctor.diagnose_state(state)

    assert report.is_healthy is False
    assert report.has_critical is True
    assert len(report.issues) >= 3

    # Check missing env var issue structure
    env_issue = next(i for i in report.issues if i.code == "ENV_MISSING_REQUIRED")
    assert env_issue.evidence["variable"] == "SECRET_KEY"
    assert env_issue.evidence["actual"] == "missing"
    assert "explanation" in env_issue.__dict__
    assert "suggested_action" in env_issue.__dict__

    # Check Node missing runtime
    node_issue = next(i for i in report.issues if i.code == "RUNTIME_NODE_MISSING")
    assert node_issue.evidence["runtime"] == "node"
    assert node_issue.evidence["status"] == "not_found"

    # Check Postgres service stopped
    pg_issue = next(i for i in report.issues if i.code == "SERVICE_POSTGRES_STOPPED")
    assert pg_issue.evidence["service"] == "postgres"
    assert pg_issue.evidence["running"] is False


def test_doctor_diff_diagnosis():
    base = _make_doctor_test_state()
    curr = _make_doctor_test_state()
    curr.runtimes["python"].version = "3.10.0"

    diff = DiffEngine.compare(base, curr)
    report = Doctor.diagnose_diff(diff)

    assert report.is_healthy is False
    py_issue = next(i for i in report.issues if "RUNTIME" in i.code)
    assert py_issue.evidence["runtime"] == "python"
    assert "3.12.4" in py_issue.evidence["expected"]
    assert "3.10.0" in py_issue.evidence["actual"]
