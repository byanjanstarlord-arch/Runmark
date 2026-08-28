"""Unit tests for JSONRenderer."""

import json

from runmark.models.diagnostic import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    DiagnosticSeverity,
    ReportMetadata,
)
from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.system import SystemState
from runmark.output.json import JSONRenderer


def test_json_renderer_valid_and_roundtrip():
    issue = DiagnosticIssue(
        code="ENV_MISSING",
        severity=DiagnosticSeverity.CRITICAL,
        category=DiagnosticCategory.ENVIRONMENT,
        title="Missing Var",
        evidence={"var": "SECRET_KEY"},
        explanation="Secret key is missing.",
        suggested_action="Set SECRET_KEY.",
    )
    report = DiagnosticReport(
        metadata=ReportMetadata(
            report_id="rpt_json_test123",
            environment_fingerprint="rm_123456",
            summary="1 issue detected",
        ),
        project=ProjectState(name="json-app", root="json-app"),
        system=SystemState(os_name="Windows", os_version="11", architecture="AMD64"),
        runtimes={},
        dependencies=[],
        services=[],
        environment=EnvironmentState(),
        network=[],
        containers=[],
        git=GitState(is_repository=False),
        diagnostics=[issue],
    )

    rendered_json = JSONRenderer.render(report)

    # 1. Assert valid JSON parsing
    parsed = json.loads(rendered_json)
    assert parsed["metadata"]["report_id"] == "rpt_json_test123"
    assert parsed["metadata"]["environment_fingerprint"] == "rm_123456"
    assert len(parsed["diagnostics"]) == 1
    assert parsed["diagnostics"][0]["code"] == "ENV_MISSING"
    assert parsed["diagnostics"][0]["severity"] == "CRITICAL"

    # 2. Assert roundtrip validation back to Pydantic model
    validated = DiagnosticReport.model_validate(parsed)
    assert validated.metadata.report_id == report.metadata.report_id
    assert validated.project.name == report.project.name
    assert validated.diagnostics[0].code == issue.code
