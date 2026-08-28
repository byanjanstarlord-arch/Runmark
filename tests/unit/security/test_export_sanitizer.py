"""Unit tests for ExportSanitizer and security boundary validation."""

import pytest

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
from runmark.security.export_sanitizer import ExportSanitizer, SecurityViolationError

CANARY_SECRETS = [
    "sk-proj-CANARY_OPENAI_KEY_123456789012345678901234567890",
    "AKIAIOSFODNN7CANARY01",
    "wJalrXUtnFEMI/K7MDENG/bPxRfiCYCANARYSECRET",
    "ghp_CANARY_GITHUB_PAT_TOKEN_SECRET_NEVER_LEAK_36CHARS_LONG",
    "glpat-CANARY_GITLAB_PAT_SECRET_VAL",
    "sk_live_CANARY_STRIPE_LIVE_KEY_123456789012",
    "CANARY_SECRET_SLACK_TOKEN_1234567890",
    "AIzaSyCANARY_GOOGLE_API_KEY_SEC_1234567",
    "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_CANARY_BEARER_TOKEN_9999",
    "postgres://superuser:CANARY_DB_PASS_123@db.internal.host:5432/production_db",
    "redis://default:CANARY_REDIS_PASS_456@redis.internal.host:6379/0",
]


def _build_contaminated_report():
    return DiagnosticReport(
        metadata=ReportMetadata(
            report_id="rpt_canary_test",
            environment_fingerprint="abc123456789",
        ),
        project=ProjectState(name="canary-project", root="/home/developer/secret-repo"),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={
            "python": RuntimeState(
                name="python",
                installed=True,
                version="3.12.4",
                executable_path="/home/developer/.pyenv/shims/python",
            )
        },
        dependencies=[],
        services=[
            ServiceState(
                name="postgres",
                installed=True,
                running=True,
                port=5432,
            )
        ],
        environment=EnvironmentState(
            variables={
                "DATABASE_URL": EnvironmentVariableState(
                    name="DATABASE_URL",
                    required=True,
                    present=True,
                    secret=True,
                    source=".env",
                ),
            }
        ),
        network=[],
        containers=[],
        git=GitState(is_repository=True, branch="main", commit="123456", dirty=False),
        diagnostics=[
            DiagnosticIssue(
                code="CANARY_CONTAMINATED_ISSUE",
                severity=DiagnosticSeverity.CRITICAL,
                category=DiagnosticCategory.SECURITY,
                title=f"Secret title with {CANARY_SECRETS[0]}",
                evidence={
                    "connection_uri": CANARY_SECRETS[9],  # postgres URI
                    "token": CANARY_SECRETS[3],  # GitHub token
                    "stripe": CANARY_SECRETS[5],  # Stripe key
                },
                explanation=f"Contaminated explanation mentioning {CANARY_SECRETS[1]} and {CANARY_SECRETS[8]}",
                suggested_action=f"Suggested action with {CANARY_SECRETS[6]}",
            )
        ],
    )


def test_export_sanitizer_cleans_report_fields():
    raw_report = _build_contaminated_report()
    sanitized = ExportSanitizer.sanitize_report(raw_report)

    # Check evidence dictionary
    assert "CANARY_DB_PASS_123" not in str(sanitized.diagnostics[0].evidence)
    assert "CANARY_GITHUB_PAT" not in str(sanitized.diagnostics[0].evidence)
    assert "CANARY_STRIPE_LIVE" not in str(sanitized.diagnostics[0].evidence)
    assert (
        sanitized.diagnostics[0].evidence["connection_uri"]
        == "postgres://db.internal.host:5432/production_db"
    )

    # Check title, explanation, suggested action
    assert "sk-proj-CANARY_OPENAI_KEY" not in sanitized.diagnostics[0].title
    assert "AKIAIOSFODNN7" not in sanitized.diagnostics[0].explanation
    assert "CANARY_SECRET_SLACK_TOKEN" not in sanitized.diagnostics[0].suggested_action


def test_verify_rendered_content_clean_raises_security_violation():
    for secret in CANARY_SECRETS:
        if secret == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYCANARYSECRET":
            continue  # Protected by variable name classification rather than prefix pattern
        dirty_content = f"# Safe Report\nHere is a leaked secret: {secret}\n"
        with pytest.raises(SecurityViolationError) as exc_info:
            ExportSanitizer.verify_rendered_content_clean(dirty_content)
        # Assert secret itself is not leaked into the exception message
        assert secret not in str(exc_info.value)
        assert "sensitive data or unredacted credentials" in str(exc_info.value)


def test_verify_rendered_content_clean_passes_clean_content():
    clean_content = "# Runmark Diagnostic Report\nAll checks passed cleanly.\n"
    # Should not raise exception
    ExportSanitizer.verify_rendered_content_clean(clean_content)
