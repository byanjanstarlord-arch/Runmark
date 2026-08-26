"""Unit tests for verification engine and exit codes."""

from runmark.core.verifier import VerificationStatus, Verifier
from runmark.models.common import DetectionStatus
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.system import SystemState


def _make_state(py_ver="3.12.4", missing_env=False):
    return RunmarkState(
        runmark=RunmarkMetadata(id="snap_1", tool_version="0.1.0", schema_version="1.0"),
        project=ProjectState(name="app", root="app"),
        git=GitState(is_repository=True, branch="main", commit="111", dirty=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python", installed=True, version=py_ver, status=DetectionStatus.DETECTED
            )
        },
        dependencies=[],
        services=[],
        environment=EnvironmentState(
            variables={
                "SECRET_KEY": EnvironmentVariableState(
                    name="SECRET_KEY",
                    required=True,
                    present=not missing_env,
                    secret=True,
                    source=".env.example",
                )
            }
        ),
        network=[],
        containers=[],
    )


def test_matching_environment_returns_exit_code_0():
    expected = _make_state()
    current = _make_state()

    verifier = Verifier()
    result = verifier.verify(expected, current)

    assert result.status == VerificationStatus.PASS
    assert result.exit_code == 0
    assert result.passed is True


def test_critical_drift_returns_exit_code_1():
    expected = _make_state(missing_env=False)
    current = _make_state(missing_env=True)

    verifier = Verifier()
    result = verifier.verify(expected, current)

    assert result.status == VerificationStatus.FAIL
    assert result.exit_code == 1
    assert result.passed is False
    assert len(result.reasons) > 0


def test_strict_mode_escalates_warning_to_failure():
    expected = _make_state(py_ver="3.12.4")
    current = _make_state(py_ver="3.13.0")  # minor version difference -> WARNING

    verifier_lenient = Verifier(strict=False)
    res_lenient = verifier_lenient.verify(expected, current)
    assert res_lenient.exit_code == 0
    assert res_lenient.status == VerificationStatus.WARN

    verifier_strict = Verifier(strict=True)
    res_strict = verifier_strict.verify(expected, current)
    assert res_strict.exit_code == 1
    assert res_strict.status == VerificationStatus.FAIL
