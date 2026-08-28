"""Adversarial security integration tests for 'runmark share' pipeline."""

from unittest.mock import patch

from typer.testing import CliRunner

from runmark.cli.app import app
from runmark.models.diagnostic import DiagnosticReport, ReportMetadata
from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.system import SystemState

runner = CliRunner()

CANARY_SECRETS = {
    "OPENAI_KEY": "sk-proj-CANARY_SECRET_OPENAI_9999999999999999999999999999",
    "AWS_KEY_ID": "AKIAIOSFODNN7CANARY01",
    "AWS_SECRET": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYCANARYSECRET",
    "AWS_TOKEN": "AQoDYXdzEJr1CANARY_SESSION_TOKEN_MUST_NEVER_ESCAPE_TEST_1234567890",
    "GITHUB_TOKEN": "ghp_CANARY_GITHUB_PAT_TOKEN_SECRET_NEVER_LEAK_36CHARS_LONG",
    "GITLAB_TOKEN": "glpat-CANARY_GITLAB_PAT_SECRET_VAL",
    "STRIPE_KEY": "sk_live_CANARY_STRIPE_LIVE_KEY_123456789012",
    "JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvbmRvZSIsImlhdCI6MTUxNjIzOTAyMn0.CANARY_JWT_SIGNATURE_MUST_NEVER_ESCAPE_ANYWHERE",
    "DATABASE_URI": "postgres://superuser:CANARY_DB_PASS_123@db.internal.host:5432/production_db",
}


def test_share_adversarial_canary_zero_leakage(tmp_path):
    """Verify that when canary secrets are in .env, manifests, or environment, 'runmark share' leaves zero secret traces in stdout or output files."""
    # Write .env with canary credentials
    env_content = "\n".join(f"{name}={val}" for name, val in CANARY_SECRETS.items())
    (tmp_path / ".env").write_text(env_content, encoding="utf-8")
    (tmp_path / ".env.example").write_text(env_content, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "canary-share-app"\n', encoding="utf-8"
    )

    out_file = tmp_path / "report.md"
    out_json = tmp_path / "report.json"

    # 1. Generate Markdown report file
    res_md = runner.invoke(
        app, ["share", "--path", str(tmp_path), "--output", str(out_file)], env=dict(CANARY_SECRETS)
    )
    assert res_md.exit_code == 0
    md_content = out_file.read_text(encoding="utf-8")

    # 2. Generate JSON report file
    res_json = runner.invoke(
        app,
        ["share", "--path", str(tmp_path), "--output", str(out_json), "--json"],
        env=dict(CANARY_SECRETS),
    )
    assert res_json.exit_code == 0
    json_content = out_json.read_text(encoding="utf-8")

    # 3. Stream to stdout
    res_stdout = runner.invoke(
        app, ["share", "--path", str(tmp_path), "--stdout"], env=dict(CANARY_SECRETS)
    )
    assert res_stdout.exit_code == 0

    all_emitted_text = md_content + "\n" + json_content + "\n" + res_stdout.stdout

    # Assert zero canary occurrences
    for secret_name, secret_val in CANARY_SECRETS.items():
        assert secret_val not in all_emitted_text, (
            f"Canary secret {secret_name} escaped in 'runmark share' output!"
        )


def test_share_aborts_with_exit_code_4_on_security_violation(tmp_path):
    """Verify that if an unredacted secret reaches the final export boundary, report export aborts with exit code 4 and deletes temporary files."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "violation-app"\n', encoding="utf-8"
    )
    out_file = tmp_path / "clean_destination.md"

    # Mock Reporter.generate_report to simulate an unredacted secret leaking into report summary
    dirty_report = DiagnosticReport(
        metadata=ReportMetadata(
            report_id="rpt_dirty",
            environment_fingerprint="rm_123",
            summary=f"Leaked secret: {CANARY_SECRETS['OPENAI_KEY']}",
        ),
        project=ProjectState(name="dirty-app", root=str(tmp_path)),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={},
        dependencies=[],
        services=[],
        environment=EnvironmentState(),
        network=[],
        containers=[],
        git=GitState(is_repository=False),
        diagnostics=[],
    )

    with patch("runmark.cli.commands.share.Reporter.generate_report", return_value=dirty_report):
        res = runner.invoke(app, ["share", "--path", str(tmp_path), "--output", str(out_file)])
        assert res.exit_code == 4
        assert (
            not out_file.exists()
        )  # Destination must NEVER be written on security boundary violation!
        assert "sensitive data or unredacted credentials" in res.output
