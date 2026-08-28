"""Integration tests for 'runmark check' CLI command."""

import json
from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app

runner = CliRunner()


def test_check_cli_success(tmp_path: Path) -> None:
    # Contract requiring Python >= 3
    contract_data = {
        "version": 1,
        "project": {"name": "test-cli-check"},
        "runtime": {"python": ">=3.8"},
    }
    (tmp_path / "runmark.json").write_text(json.dumps(contract_data), encoding="utf-8")

    res = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert res.exit_code == 0
    assert "PASSED" in res.stdout


def test_check_cli_failure_exit_code_1(tmp_path: Path) -> None:
    # Contract requiring an impossible runtime or missing required env var
    contract_data = {
        "version": 1,
        "environment": {"required": ["COMPLETELY_NONEXISTENT_ENV_VAR_12345"]},
    }
    (tmp_path / "runmark.json").write_text(json.dumps(contract_data), encoding="utf-8")

    res = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert res.exit_code == 1
    assert "FAILED" in res.stdout
    assert "REQUIRED_ENV_MISSING" in res.stdout


def test_check_cli_missing_contract_exit_code_2(tmp_path: Path) -> None:
    res = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert res.exit_code == 2
    output = res.stdout + (res.stderr if hasattr(res, "stderr") and res.stderr else "")
    assert "not found" in output.lower()


def test_check_cli_invalid_contract_exit_code_2(tmp_path: Path) -> None:
    (tmp_path / "runmark.json").write_text('{"version": 99}', encoding="utf-8")
    res = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert res.exit_code == 2


def test_check_cli_secret_violation_exit_code_4(tmp_path: Path) -> None:
    malicious = {
        "version": 1,
        "environment": {"required": ["postgres://user:super_secret_pw@localhost/db"]},
    }
    (tmp_path / "runmark.json").write_text(json.dumps(malicious), encoding="utf-8")

    res = runner.invoke(app, ["check", "--path", str(tmp_path)])
    assert res.exit_code == 4
    output = res.stdout + (res.stderr if hasattr(res, "stderr") and res.stderr else "")
    assert "security violation" in output.lower()


def test_check_cli_json_mode(tmp_path: Path) -> None:
    contract_data = {
        "version": 1,
        "project": {"name": "json-test"},
        "runtime": {"python": ">=3.8"},
    }
    (tmp_path / "runmark.json").write_text(json.dumps(contract_data), encoding="utf-8")

    res = runner.invoke(app, ["check", "--path", str(tmp_path), "--json"])
    assert res.exit_code == 0
    parsed = json.loads(res.stdout)
    assert parsed["status"] == "PASS"
    assert parsed["contract_version"] == 1
    assert "checks" in parsed
    assert "summary" in parsed


def test_check_cli_explain_mode(tmp_path: Path) -> None:
    contract_data = {
        "version": 1,
        "environment": {"required": ["MISSING_EXPLAIN_VAR"]},
    }
    (tmp_path / "runmark.json").write_text(json.dumps(contract_data), encoding="utf-8")

    res = runner.invoke(app, ["check", "--path", str(tmp_path), "--explain"])
    assert res.exit_code == 1
    assert "Detailed Diagnostic Explanations (--explain):" in res.stdout
    assert "Required:" in res.stdout
    assert "Detected:" in res.stdout
    assert "Why:" in res.stdout
    assert "Suggested Action:" in res.stdout
