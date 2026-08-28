"""Integration tests for Typer CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from runmark import __version__
from runmark.cli.app import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Runmark" in result.output


def test_cli_version_json():
    result = runner.invoke(app, ["version", "--json"])
    assert result.exit_code == 0
    assert f'"tool_version": "{__version__}"' in result.output


def test_cli_scan_json():
    result = runner.invoke(app, ["scan", "--path", str(FIXTURES_DIR / "python_project"), "--json"])
    assert result.exit_code == 0
    assert '"project"' in result.output
    assert '"environment_fingerprint"' in result.output


def test_cli_init_and_snapshot_workflow(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "cli-test"\n', encoding="utf-8")

    # 1. init
    res_init = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert res_init.exit_code == 0

    # 1b. init already initialized
    res_init_again = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert res_init_again.exit_code == 0
    assert "already initialized" in res_init_again.output

    # 1c. init with --json
    res_init_json = runner.invoke(app, ["init", "--path", str(tmp_path), "--force", "--json"])
    assert res_init_json.exit_code == 0
    assert '"status": "initialized"' in res_init_json.output

    # 2. snapshot
    res_snap = runner.invoke(app, ["snapshot", "--path", str(tmp_path), "-m", "CLI snapshot test"])
    assert res_snap.exit_code == 0
    assert "Snapshot Captured" in res_snap.output

    # 2b. snapshot --json
    res_snap_json = runner.invoke(app, ["snapshot", "--path", str(tmp_path), "--json"])
    assert res_snap_json.exit_code == 0
    assert '"tool_version"' in res_snap_json.output

    # 3. diff
    res_diff = runner.invoke(app, ["diff", "--path", str(tmp_path)])
    assert res_diff.exit_code == 0
    assert "ZERO ENVIRONMENT DRIFT" in res_diff.output

    # 3b. diff with --json
    res_diff_json = runner.invoke(app, ["diff", "--path", str(tmp_path), "--json"])
    assert res_diff_json.exit_code == 0
    assert '"is_identical": true' in res_diff_json.output

    # 4. verify
    res_verify = runner.invoke(app, ["verify", "--path", str(tmp_path)])
    assert res_verify.exit_code == 0
    assert "VERIFICATION PASSED" in res_verify.output

    # 4b. verify with --json
    res_verify_json = runner.invoke(app, ["verify", "--path", str(tmp_path), "--json"])
    assert res_verify_json.exit_code == 0
    assert '"status": "PASS"' in res_verify_json.output

    # 5. doctor
    res_doc = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert res_doc.exit_code == 0

    # 5b. doctor with --json
    res_doc_json = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    assert res_doc_json.exit_code == 0
    assert '"is_healthy"' in res_doc_json.output

    # 6. history
    res_hist = runner.invoke(app, ["history", "--path", str(tmp_path)])
    assert res_hist.exit_code == 0
    assert "SNAPSHOT HISTORY" in res_hist.output

    # 6b. history with --json
    res_hist_json = runner.invoke(app, ["history", "--path", str(tmp_path), "--json"])
    assert res_hist_json.exit_code == 0


def test_cli_error_handling(tmp_path):
    # Non-existent snapshot ID
    res_diff_err = runner.invoke(
        app, ["diff", "--from", "snap_nonexistent_9999", "--path", str(tmp_path)]
    )
    assert res_diff_err.exit_code == 2

    res_verify_err = runner.invoke(
        app, ["verify", "--snapshot", "snap_nonexistent_9999", "--path", str(tmp_path)]
    )
    assert res_verify_err.exit_code == 2

    res_doc_err = runner.invoke(
        app, ["doctor", "--snapshot", "snap_nonexistent_9999", "--path", str(tmp_path)]
    )
    assert res_doc_err.exit_code == 2
