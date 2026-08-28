"""Unit tests for MarkdownRenderer."""

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
from runmark.output.markdown import MarkdownRenderer


def _make_test_report(issues=None):
    if issues is None:
        issues = []
    return DiagnosticReport(
        metadata=ReportMetadata(
            report_id="rpt_md_test123",
            generated_at="2026-08-26T12:00:00Z",
            runmark_version="0.1.2",
            schema_version="1.0",
            environment_fingerprint="rm_abcdef123456",
            summary="1 critical issue, 1 warning detected",
        ),
        project=ProjectState(
            name="markdown-app",
            root="markdown-app",
            languages=["python", "javascript"],
            frameworks=["fastapi"],
            package_managers=["uv", "npm"],
            containerization=["docker"],
        ),
        system=SystemState(os_name="Darwin", os_version="23.5.0", architecture="arm64"),
        runtimes={
            "python": RuntimeState(name="python", installed=True, version="3.12.4"),
            "node": RuntimeState(name="node", installed=False, version=None),
        },
        dependencies=[],
        services=[
            ServiceState(
                name="postgres",
                installed=True,
                running=True,
                port=5432,
                detected_version="16.3",
                expected_version="16",
            ),
            ServiceState(
                name="redis", installed=False, running=False, port=6379, expected_version="7"
            ),
        ],
        environment=EnvironmentState(
            variables={
                "DATABASE_URL": EnvironmentVariableState(
                    name="DATABASE_URL", required=True, present=True, secret=True, source=".env"
                ),
                "STRIPE_KEY": EnvironmentVariableState(
                    name="STRIPE_KEY",
                    required=True,
                    present=False,
                    secret=True,
                    source=".env.example",
                ),
            }
        ),
        network=[],
        containers=[],
        git=GitState(is_repository=True, branch="feature/diagnose", commit="a81f29c", dirty=True),
        diagnostics=issues,
    )


def test_markdown_renderer_healthy_report():
    report = _make_test_report([])
    md = MarkdownRenderer.render(report)

    assert "# Runmark Diagnostic Report" in md
    assert "rpt_md_test123" in md
    assert "rm_abcdef123456" in md
    assert "No environment issues detected." in md
    assert "| **Project Name** | `markdown-app` |" in md
    assert "Darwin 23.5.0" in md
    assert "`arm64`" in md
    assert "✓ Installed" in md
    assert "✗ Missing" in md


def test_markdown_renderer_with_critical_and_warning_issues():
    issues = [
        DiagnosticIssue(
            code="ENV_MISSING_REQUIRED",
            severity=DiagnosticSeverity.CRITICAL,
            category=DiagnosticCategory.ENVIRONMENT,
            title="Required environment variable missing",
            evidence={"variable": "STRIPE_KEY", "expected": "present", "actual": "missing"},
            explanation="The STRIPE_KEY variable is required by the project configuration.",
            suggested_action="Add STRIPE_KEY to .env.",
        ),
        DiagnosticIssue(
            code="RUNTIME_NODE_MISSING",
            severity=DiagnosticSeverity.WARNING,
            category=DiagnosticCategory.RUNTIME,
            title="Node runtime missing",
            evidence={"runtime": "node"},
            explanation="Node.js is not found in PATH.",
            suggested_action="Install Node.js 22.x.",
        ),
    ]
    report = _make_test_report(issues)
    md = MarkdownRenderer.render(report)

    assert "🔴 [ENV_MISSING_REQUIRED] Required environment variable missing" in md
    assert "🟡 [RUNTIME_NODE_MISSING] Node runtime missing" in md
    assert "- **Severity**: `CRITICAL`" in md
    assert "- **Category**: `environment`" in md
    assert "**Observed Evidence**:" in md
    assert "| `variable` | `STRIPE_KEY` |" in md
    assert "- **Suggested Action**: `Add STRIPE_KEY to .env.`" in md


def test_markdown_renderer_special_characters_and_unicode():
    special_issue = DiagnosticIssue(
        code="SPECIAL_CHAR_ISSUE",
        severity=DiagnosticSeverity.INFO,
        category=DiagnosticCategory.GENERAL,
        title="Testing <script>alert('xss')</script> & | `code` # * _",
        evidence={"param": "value with <brackets> & 'quotes' \"double\" `backticks`"},
        explanation="Explanation with special characters: 1 < 2 && 3 > 2 | pipe",
        suggested_action="Run `echo 'hello & world'` in shell.",
    )
    report = _make_test_report([special_issue])
    md = MarkdownRenderer.render(report)

    assert "SPECIAL_CHAR_ISSUE" in md
    assert "Testing <script>alert('xss')</script>" in md
    assert (
        "| `param` | `value with <brackets> & 'quotes' \"double\" `backticks`` |" in md
        or "value with <brackets>" in md
    )
