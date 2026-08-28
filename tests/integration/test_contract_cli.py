"""Integration tests for 'runmark contract' CLI subcommands."""

import json
from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app

runner = CliRunner()


class TestContractValidateCLI:
    """Tests for runmark contract validate."""

    def test_validate_valid_contract(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text(
            '{"version": 1, "runtime": {"python": "3.12.x"}}', encoding="utf-8"
        )
        res = runner.invoke(app, ["contract", "validate", "--path", str(tmp_path)])
        assert res.exit_code == 0
        assert "valid" in res.stdout.lower()

    def test_validate_valid_contract_json(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text(
            '{"version": 1, "project": {"name": "p"}}', encoding="utf-8"
        )
        res = runner.invoke(app, ["contract", "validate", "--path", str(tmp_path), "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "valid"
        assert data["version"] == 1

    def test_validate_missing_contract_exit_2(self, tmp_path: Path) -> None:
        res = runner.invoke(app, ["contract", "validate", "--path", str(tmp_path)])
        assert res.exit_code == 2

    def test_validate_invalid_syntax_exit_2(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text('{"version": 2}', encoding="utf-8")
        res = runner.invoke(app, ["contract", "validate", "--path", str(tmp_path)])
        assert res.exit_code == 2

    def test_validate_secret_violation_exit_4(self, tmp_path: Path) -> None:
        malicious = {
            "version": 1,
            "runtime": {"python": "sk-proj-123456789012345678901234567890123456789012345678"},
        }
        (tmp_path / "runmark.json").write_text(json.dumps(malicious), encoding="utf-8")
        res = runner.invoke(app, ["contract", "validate", "--path", str(tmp_path)])
        assert res.exit_code == 4


class TestContractShowCLI:
    """Tests for runmark contract show."""

    def test_show_human(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text(
            json.dumps(
                {"version": 1, "project": {"name": "show-demo"}, "runtime": {"python": "3.12.x"}}
            ),
            encoding="utf-8",
        )
        res = runner.invoke(app, ["contract", "show", "--path", str(tmp_path)])
        assert res.exit_code == 0
        assert "show-demo" in res.stdout
        assert "3.12.x" in res.stdout

    def test_show_json(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text(
            json.dumps({"version": 1, "project": {"name": "show-demo"}}),
            encoding="utf-8",
        )
        res = runner.invoke(app, ["contract", "show", "--path", str(tmp_path), "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "contract" in data
        assert "fingerprint" in data
        assert len(data["fingerprint"]) == 64
