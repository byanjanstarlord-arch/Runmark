"""Integration tests for runmark contract diff CLI command."""

import json
from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app
from runmark.utils.commands import safe_run

runner = CliRunner()


class TestContractDiffCLI:
    """Integration test suite for `runmark contract diff`."""

    def test_contract_diff_against_git_baseline(self, tmp_path: Path) -> None:
        # Initialize a temporary git repository
        safe_run(["git", "init"], cwd=tmp_path)
        safe_run(["git", "config", "user.name", "Runmark Test"], cwd=tmp_path)
        safe_run(["git", "config", "user.email", "test@runmark.dev"], cwd=tmp_path)

        # Baseline contract in HEAD
        c_baseline = {
            "version": 1,
            "project": {"name": "diff-app"},
            "runtime": {"python": ">=3.11"},
            "services": {"postgresql": {"version": ">=15", "required": True}},
        }
        (tmp_path / "runmark.json").write_text(json.dumps(c_baseline), encoding="utf-8")
        safe_run(["git", "add", "runmark.json"], cwd=tmp_path)
        safe_run(["git", "commit", "-m", "Baseline contract"], cwd=tmp_path)

        # Update working tree contract (upgrade python and add redis)
        c_updated = {
            "version": 1,
            "project": {"name": "diff-app"},
            "runtime": {"python": ">=3.12"},
            "services": {
                "postgresql": {"version": ">=15", "required": True},
                "redis": {"version": ">=7", "required": True},
            },
        }
        (tmp_path / "runmark.json").write_text(json.dumps(c_updated), encoding="utf-8")

        # Run contract diff in human mode
        res_human = runner.invoke(app, ["contract", "diff", "--path", str(tmp_path)])
        assert res_human.exit_code == 0
        assert "Runmark Contract Diff" in res_human.stdout
        assert "CHANGED" in res_human.stdout

        # Run contract diff in JSON mode
        res_json = runner.invoke(app, ["contract", "diff", "--path", str(tmp_path), "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.stdout)
        assert data["status"] == "CHANGED"
        assert data["summary"]["added"] == 1  # redis
        assert data["summary"]["changed"] == 1  # python runtime
        assert data["summary"]["removed"] == 0

    def test_contract_diff_no_baseline_error(self, tmp_path: Path) -> None:
        (tmp_path / "runmark.json").write_text('{"version": 1}', encoding="utf-8")
        res = runner.invoke(app, ["contract", "diff", "--path", str(tmp_path)])
        assert res.exit_code == 2
        assert "No baseline contract found" in (res.stdout + res.stderr)

    def test_contract_diff_unchanged(self, tmp_path: Path) -> None:
        safe_run(["git", "init"], cwd=tmp_path)
        safe_run(["git", "config", "user.name", "Runmark Test"], cwd=tmp_path)
        safe_run(["git", "config", "user.email", "test@runmark.dev"], cwd=tmp_path)

        c_data = {
            "version": 1,
            "project": {"name": "identical-app"},
            "runtime": {"python": ">=3.12"},
        }
        (tmp_path / "runmark.json").write_text(json.dumps(c_data), encoding="utf-8")
        safe_run(["git", "add", "runmark.json"], cwd=tmp_path)
        safe_run(["git", "commit", "-m", "Identical"], cwd=tmp_path)

        res = runner.invoke(app, ["contract", "diff", "--path", str(tmp_path)])
        assert res.exit_code == 0
        assert "No differences detected" in res.stdout
