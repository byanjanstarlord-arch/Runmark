"""Unit tests for Diagnostic domain models."""

import pydantic
import pytest

from runmark import __version__
from runmark.models.diagnostic import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    DiagnosticSeverity,
    ReportMetadata,
)
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState


def _make_sample_report(issues=None):
    if issues is None:
        issues = []
    return DiagnosticReport(
        metadata=ReportMetadata(
            report_id="rpt_test123456",
            generated_at="2026-08-26T12:00:00Z",
            runmark_version=__version__,
            schema_version="1.0",
            report_format_version=1,
            environment_fingerprint="abc123def456",
            summary="Test summary",
        ),
        project=ProjectState(
            name="test-project",
            root="test-project",
            languages=["python"],
            frameworks=["fastapi"],
            package_managers=["pip"],
            containerization=[],
        ),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={"python": RuntimeState(name="python", installed=True, version="3.12.4")},
        dependencies=[],
        services=[ServiceState(name="postgres", installed=True, running=True, port=5432)],
        environment=EnvironmentState(
            variables={
                "PORT": EnvironmentVariableState(
                    name="PORT", required=False, present=True, secret=False
                ),
            }
        ),
        network=[],
        containers=[],
        git=GitState(is_repository=True, branch="main", commit="1234567890ab", dirty=False),
        diagnostics=issues,
    )


def test_diagnostic_issue_creation():
    issue = DiagnosticIssue(
        code="RUNTIME_PYTHON_MISSING",
        severity=DiagnosticSeverity.CRITICAL,
        category=DiagnosticCategory.RUNTIME,
        title="Python runtime missing",
        evidence={"runtime": "python", "status": "not_found"},
        explanation="Python is required but not installed.",
        suggested_action="Install Python >= 3.10.",
    )
    assert issue.code == "RUNTIME_PYTHON_MISSING"
    assert issue.severity == DiagnosticSeverity.CRITICAL
    assert issue.category == DiagnosticCategory.RUNTIME
    assert issue.evidence["runtime"] == "python"


def test_diagnostic_report_health_properties():
    # 1. Healthy report
    healthy = _make_sample_report([])
    assert healthy.is_healthy is True
    assert healthy.has_critical is False
    assert healthy.has_warnings is False

    # 2. Warning report
    warn_issue = DiagnosticIssue(
        code="DIFF_RUNTIME_WARNING",
        severity=DiagnosticSeverity.WARNING,
        category=DiagnosticCategory.RUNTIME,
        title="Python version mismatch",
        evidence={"runtime": "python", "expected": "3.12", "actual": "3.11"},
        explanation="Version does not match baseline.",
        suggested_action="Use Python 3.12.",
    )
    warn_report = _make_sample_report([warn_issue])
    assert warn_report.is_healthy is False
    assert warn_report.has_warnings is True
    assert warn_report.has_critical is False

    # 3. Critical report
    crit_issue = DiagnosticIssue(
        code="ENV_MISSING_REQUIRED",
        severity=DiagnosticSeverity.CRITICAL,
        category=DiagnosticCategory.ENVIRONMENT,
        title="Missing required env var",
        evidence={"variable": "API_KEY"},
        explanation="API_KEY is missing.",
        suggested_action="Add API_KEY.",
    )
    crit_report = _make_sample_report([crit_issue])
    assert crit_report.is_healthy is False
    assert crit_report.has_critical is True


def test_diagnostic_report_json_roundtrip():
    issue = DiagnosticIssue(
        code="ENV_MISSING_REQUIRED",
        severity=DiagnosticSeverity.CRITICAL,
        category=DiagnosticCategory.ENVIRONMENT,
        title="Required environment variable missing",
        evidence={"variable": "SECRET_KEY", "source": ".env.example"},
        explanation="SECRET_KEY is required.",
        suggested_action="Add SECRET_KEY to .env.",
    )
    report = _make_sample_report([issue])

    json_str = report.model_dump_json()
    reconstructed = DiagnosticReport.model_validate_json(json_str)

    assert reconstructed.metadata.report_id == report.metadata.report_id
    assert reconstructed.project.name == report.project.name
    assert len(reconstructed.diagnostics) == 1
    assert reconstructed.diagnostics[0].code == "ENV_MISSING_REQUIRED"
    assert reconstructed.diagnostics[0].severity == DiagnosticSeverity.CRITICAL


def test_diagnostic_models_extra_forbid():
    valid_data = {
        "code": "TEST_CODE",
        "severity": "INFO",
        "category": "general",
        "title": "Test Title",
        "evidence": {},
        "explanation": "Test explanation",
        "suggested_action": "Test action",
        "unknown_extra_field": "disallowed",
    }
    with pytest.raises(pydantic.ValidationError):
        DiagnosticIssue.model_validate(valid_data)


def test_report_metadata_defaults():
    meta = ReportMetadata(environment_fingerprint="rm_123456789")
    assert meta.report_id.startswith("rpt_")
    assert meta.schema_version == "1.0"
    assert meta.report_format_version == 1
    assert "T" in meta.generated_at  # ISO 8601


def test_diagnostic_category_and_severity_enums():
    for cat in [
        DiagnosticCategory.RUNTIME,
        DiagnosticCategory.DEPENDENCY,
        DiagnosticCategory.SERVICE,
        DiagnosticCategory.ENVIRONMENT,
        DiagnosticCategory.NETWORK,
        DiagnosticCategory.CONTAINER,
        DiagnosticCategory.SYSTEM,
        DiagnosticCategory.GIT,
        DiagnosticCategory.SECURITY,
        DiagnosticCategory.GENERAL,
    ]:
        assert isinstance(cat.value, str)

    assert DiagnosticSeverity.INFO.value == "INFO"
    assert DiagnosticSeverity.WARNING.value == "WARNING"
    assert DiagnosticSeverity.CRITICAL.value == "CRITICAL"
