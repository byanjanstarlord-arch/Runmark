"""Unit tests for Rich table rendering functions."""

from rich.console import Console

from runmark.core.diff import DiffEngine
from runmark.core.doctor import Doctor
from runmark.core.verifier import Verifier
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
from runmark.output.tables import (
    render_diff,
    render_doctor,
    render_history,
    render_scan,
    render_verify,
)


def _make_comprehensive_state():
    return RunmarkState(
        runmark=RunmarkMetadata(
            id="snap_full_test",
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="abcdef0123456789",
            message="Full render test snapshot",
        ),
        project=ProjectState(
            name="demo-app",
            root="demo-app",
            languages=["python", "javascript"],
            frameworks=["django", "react"],
            package_managers=["pip", "npm"],
            containerization=["docker", "docker-compose"],
        ),
        git=GitState(is_repository=True, branch="feature/test", commit="a81f29c0f", dirty=True),
        system=SystemState(os_name="Linux", os_version="6.1.0", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version="3.12.4", status=DetectionStatus.DETECTED
            ),
            "node": RuntimeState(
                name="node", installed=False, version=None, status=DetectionStatus.NOT_FOUND
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
        ],
        services=[
            ServiceState(
                name="postgresql",
                installed=True,
                running=True,
                detected_version="16.3",
                expected_version="16",
                status=DetectionStatus.DETECTED,
                port=5432,
            ),
            ServiceState(
                name="redis",
                installed=True,
                running=False,
                detected_version="7.2",
                expected_version="7",
                status=DetectionStatus.DETECTED,
                port=6379,
            ),
        ],
        environment=EnvironmentState(
            variables={
                "API_KEY": EnvironmentVariableState(
                    name="API_KEY", required=True, present=True, secret=True, source=".env.example"
                ),
                "OPTIONAL_VAR": EnvironmentVariableState(
                    name="OPTIONAL_VAR",
                    required=False,
                    present=False,
                    secret=False,
                    source="process",
                ),
                "MISSING_REQ": EnvironmentVariableState(
                    name="MISSING_REQ",
                    required=True,
                    present=False,
                    secret=False,
                    source=".env.example",
                ),
            }
        ),
        network=[
            PortState(
                port=5432, service="postgresql", expected=True, occupied=True, status="in_use"
            )
        ],
        containers=[],
    )


def test_render_scan():
    console = Console(record=True, width=120)
    state = _make_comprehensive_state()
    render_scan(state, console)
    output = console.export_text()
    assert "RUNMARK ENVIRONMENT SCAN" in output
    assert "demo-app" in output
    assert "django" in output
    assert "Postgresql" in output


def test_render_diff():
    console = Console(record=True, width=120)
    base = _make_comprehensive_state()
    curr = _make_comprehensive_state()
    curr.runtimes["python"].version = "3.11.9"

    diff = DiffEngine.compare(base, curr)
    render_diff(diff, console)
    output = console.export_text()
    assert "ENVIRONMENT DRIFT DETECTED" in output
    assert "python" in output


def test_render_verify_pass_and_fail():
    console = Console(record=True, width=120)
    base = _make_comprehensive_state()
    curr = _make_comprehensive_state()

    verifier = Verifier()
    res_pass = verifier.verify(base, curr)
    render_verify(res_pass, console)
    assert "VERIFICATION PASSED" in console.export_text()

    # Make critical drift
    curr.environment.variables["API_KEY"].present = False
    res_fail = verifier.verify(base, curr)
    render_verify(res_fail, console)
    assert "VERIFICATION FAILED" in console.export_text()


def test_render_doctor():
    console = Console(record=True, width=120)
    state = _make_comprehensive_state()
    report = Doctor.diagnose_state(state)
    render_doctor(report, console)
    output = console.export_text()
    assert "RUNMARK DOCTOR DIAGNOSTIC REPORT" in output
    assert "MISSING_REQ" in output


def test_render_history():
    console = Console(record=True, width=120)
    snapshots = [_make_comprehensive_state()]
    render_history(snapshots, console)
    output = console.export_text()
    assert "RUNMARK SNAPSHOT HISTORY" in output
    assert "snap_full_test" in output
