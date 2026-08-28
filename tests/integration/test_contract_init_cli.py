"""Integration tests for runmark contract init CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app
from runmark.contracts.parser import ContractParser

runner = CliRunner()


class TestContractInitCLI:
    """Integration test suite for `runmark contract init`."""

    def test_contract_init_dry_run(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test-init"\nrequires-python = ">=3.12"\n', encoding="utf-8"
        )

        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path), "--dry-run"])
        assert res.exit_code == 0
        assert "Dry-run mode enabled. No files were modified." in res.stdout
        assert not (tmp_path / "runmark.json").exists()

    def test_contract_init_yes_creates_file(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test-init"\nrequires-python = ">=3.12"\n', encoding="utf-8"
        )
        (tmp_path / ".env.example").write_text("DATABASE_URL=\nAPI_KEY=\n", encoding="utf-8")

        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path), "--yes"])
        assert res.exit_code == 0
        assert "created successfully" in res.stdout

        target_file = tmp_path / "runmark.json"
        assert target_file.exists()

        # Parse and verify
        contract = ContractParser.parse_file(target_file)
        assert contract.project.name == "test-init"
        assert contract.runtime.get("python") == ">=3.12"
        assert "DATABASE_URL" in contract.environment.required
        assert "API_KEY" in contract.environment.required

    def test_contract_init_existing_file_without_force_fails(self, tmp_path: Path) -> None:
        contract_file = tmp_path / "runmark.json"
        contract_file.write_text(
            '{"version": 1, "project": {"name": "original"}}', encoding="utf-8"
        )

        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path), "--yes"])
        assert res.exit_code == 2
        assert "already exists" in (res.stdout + res.stderr)

        # Ensure original file was NOT modified
        assert '"original"' in contract_file.read_text(encoding="utf-8")

    def test_contract_init_existing_file_with_force_succeeds(self, tmp_path: Path) -> None:
        contract_file = tmp_path / "runmark.json"
        contract_file.write_text(
            '{"version": 1, "project": {"name": "original"}}', encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "overwritten-app"\n', encoding="utf-8"
        )

        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path), "--yes", "--force"])
        assert res.exit_code == 0
        assert "created successfully" in res.stdout

        # Verify replacement
        contract = ContractParser.parse_file(contract_file)
        assert contract.project.name == "overwritten-app"

    def test_contract_init_interactive_abort(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test-init"\n', encoding="utf-8"
        )

        # Simulate user typing "n"
        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path)], input="n\n")
        assert res.exit_code == 0
        assert "Aborted. No files were modified." in res.stdout
        assert not (tmp_path / "runmark.json").exists()

    def test_contract_init_interactive_confirm(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "interactive-app"\n', encoding="utf-8"
        )

        # Simulate user typing "y"
        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path)], input="y\n")
        assert res.exit_code == 0
        assert "created successfully" in res.stdout
        assert (tmp_path / "runmark.json").exists()

    def test_contract_init_non_existent_directory(self, tmp_path: Path) -> None:
        missing_dir = tmp_path / "does_not_exist"
        res = runner.invoke(app, ["contract", "init", "--path", str(missing_dir), "--yes"])
        assert res.exit_code == 2
        assert "directory does not exist" in (res.stdout + res.stderr).lower()

    def test_contract_init_secret_fails_with_code_4(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "secret-app"\n', encoding="utf-8"
        )
        # Put secret inside .env.example
        (tmp_path / ".env.example").write_text(
            "DATABASE_URL=postgres://user:super_secret_pw@localhost:5432/db\n",
            encoding="utf-8",
        )
        res = runner.invoke(app, ["contract", "init", "--path", str(tmp_path), "--yes"])
        # Code should succeed because .env.example only extracts variable name DATABASE_URL (no secret leaked)
        assert res.exit_code == 0
        contract = ContractParser.parse_file(tmp_path / "runmark.json")
        assert "DATABASE_URL" in contract.environment.required
        # Zero secret in contract json
        assert "super_secret_pw" not in (tmp_path / "runmark.json").read_text(encoding="utf-8")
