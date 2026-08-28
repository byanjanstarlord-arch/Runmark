"""Integration tests for 'runmark share' CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from runmark.cli.app import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_cli_share_stdout_markdown():
    res = runner.invoke(app, ["share", "--path", str(FIXTURES_DIR / "python_project"), "--stdout"])
    assert res.exit_code == 0
    assert "# Runmark Diagnostic Report" in res.stdout
    assert "## Project & System" in res.stdout
    assert "## Diagnostics" in res.stdout
    # Purity check: no Rich formatting wrappers or log decorations
    assert "[bold" not in res.stdout


def test_cli_share_stdout_json():
    res = runner.invoke(
        app, ["share", "--path", str(FIXTURES_DIR / "python_project"), "--json", "--stdout"]
    )
    assert res.exit_code == 0
    assert '"environment_fingerprint"' in res.stdout
    assert '"report_id"' in res.stdout
    assert '"project"' in res.stdout


def test_cli_share_to_output_file(tmp_path):
    report_file = tmp_path / "custom_report.md"
    res = runner.invoke(
        app,
        ["share", "--path", str(FIXTURES_DIR / "python_project"), "--output", str(report_file)],
    )
    assert res.exit_code == 0
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "# Runmark Diagnostic Report" in content


def test_cli_share_refuse_overwrite_without_force(tmp_path):
    report_file = tmp_path / "report.md"
    report_file.write_text("Do not overwrite me!", encoding="utf-8")

    # 1. Without --force -> exit 2
    res = runner.invoke(
        app,
        ["share", "--path", str(FIXTURES_DIR / "python_project"), "--output", str(report_file)],
    )
    assert res.exit_code == 2
    assert report_file.read_text(encoding="utf-8") == "Do not overwrite me!"

    # 2. With --force -> exit 0 and overwrite
    res_force = runner.invoke(
        app,
        [
            "share",
            "--path",
            str(FIXTURES_DIR / "python_project"),
            "--output",
            str(report_file),
            "--force",
        ],
    )
    assert res_force.exit_code == 0
    assert "# Runmark Diagnostic Report" in report_file.read_text(encoding="utf-8")


def test_cli_share_default_file_generation(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "default-share-app"\n', encoding="utf-8"
    )
    res = runner.invoke(app, ["share", "--path", str(tmp_path)])
    assert res.exit_code == 0
    default_report = tmp_path / "runmark-report.md"
    assert default_report.exists()
    assert "# Runmark Diagnostic Report" in default_report.read_text(encoding="utf-8")


def test_cli_share_json_default_file_generation(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "default-json-app"\n', encoding="utf-8"
    )
    res = runner.invoke(app, ["share", "--path", str(tmp_path), "--json"])
    assert res.exit_code == 0
    default_json = tmp_path / "runmark-report.json"
    assert default_json.exists()
    assert '"environment_fingerprint"' in default_json.read_text(encoding="utf-8")


def test_cli_share_non_existent_path(tmp_path):
    non_existent = tmp_path / "missing_dir_xyz_123"
    res = runner.invoke(app, ["share", "--path", str(non_existent)])
    assert res.exit_code == 2
    assert "not found" in res.output.lower()
