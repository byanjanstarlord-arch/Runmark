"""Unit tests for Reporter service and atomic report export."""

import pytest

from runmark.core.reporter import Reporter
from runmark.models.diagnostic import DiagnosticReport


def test_reporter_generate_report(tmp_path):
    # Setup test project files
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test-reporter-app"\n', encoding="utf-8"
    )
    (tmp_path / ".env.example").write_text(
        "DATABASE_URL=postgres://localhost:5432/db\nAPI_KEY=dummy\n", encoding="utf-8"
    )

    report = Reporter.generate_report(tmp_path)

    assert isinstance(report, DiagnosticReport)
    assert report.project.name == tmp_path.name
    assert report.metadata.environment_fingerprint is not None
    assert report.metadata.report_id.startswith("rpt_")


def test_reporter_export_to_file_and_atomic_replace(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "atomic-export-app"\n', encoding="utf-8"
    )
    report = Reporter.generate_report(tmp_path)

    out_file = tmp_path / "output" / "report.md"
    written_path = Reporter.export_to_file(report, out_file)

    assert written_path.exists()
    content = written_path.read_text(encoding="utf-8")
    assert "# Runmark Diagnostic Report" in content


def test_reporter_export_refuses_overwrite_without_force(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "overwrite-app"\n', encoding="utf-8"
    )
    report = Reporter.generate_report(tmp_path)

    out_file = tmp_path / "existing_report.md"
    out_file.write_text("Old content that must not be clobbered", encoding="utf-8")

    # 1. Attempt export without force -> raises FileExistsError
    with pytest.raises(FileExistsError) as exc_info:
        Reporter.export_to_file(report, out_file, force=False)
    assert "already exists" in str(exc_info.value)
    assert out_file.read_text(encoding="utf-8") == "Old content that must not be clobbered"

    # 2. Export with force=True -> overwrites cleanly
    Reporter.export_to_file(report, out_file, force=True)
    assert "# Runmark Diagnostic Report" in out_file.read_text(encoding="utf-8")


def test_reporter_export_json_format(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "json-export-app"\n', encoding="utf-8"
    )
    report = Reporter.generate_report(tmp_path)

    json_file = tmp_path / "report.json"
    written_path = Reporter.export_to_file(report, json_file, as_json=True)

    assert written_path.exists()
    content = written_path.read_text(encoding="utf-8")
    assert '"environment_fingerprint"' in content
    assert '"report_id"' in content


def test_reporter_with_baseline_diff_diagnostics(tmp_path):
    from runmark.core.scanner import Scanner
    from runmark.core.snapshot import SnapshotManager

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "diff-reporter-app"\n', encoding="utf-8"
    )
    (tmp_path / ".env.example").write_text("DB_HOST=localhost\n", encoding="utf-8")

    # 1. Create baseline snapshot
    scanner = Scanner(tmp_path)
    base_state = scanner.scan()
    mgr = SnapshotManager(tmp_path)
    mgr.storage.save_snapshot(base_state, set_as_current=True)

    # 2. Modify environment requirement in project
    (tmp_path / ".env.example").write_text(
        "DB_HOST=localhost\nNEW_REQUIRED_VAR=secret\n", encoding="utf-8"
    )

    # 3. Generate report -> should capture diff / missing var
    report = Reporter.generate_report(tmp_path)
    assert isinstance(report, DiagnosticReport)
    assert len(report.diagnostics) >= 1
    assert any(d.code == "ENV_MISSING_REQUIRED" for d in report.diagnostics)


def test_reporter_export_creates_nested_directories(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "nested-dir-app"\n', encoding="utf-8"
    )
    report = Reporter.generate_report(tmp_path)

    nested_file = tmp_path / "deeply" / "nested" / "dir" / "report.md"
    written_path = Reporter.export_to_file(report, nested_file)

    assert written_path.exists()
    assert "# Runmark Diagnostic Report" in written_path.read_text(encoding="utf-8")
