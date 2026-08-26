"""CLI command: runmark doctor."""

from pathlib import Path

import typer

from runmark.core.diff import DiffEngine
from runmark.core.doctor import Doctor
from runmark.core.scanner import Scanner
from runmark.core.snapshot import SnapshotManager
from runmark.output.tables import render_doctor
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def doctor_command(
    snapshot: str | None = typer.Option(
        None,
        "--snapshot",
        "-s",
        help="Compare current machine against a baseline snapshot",
    ),
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Diagnose development environment issues, missing dependencies, or baseline drift."""
    root = find_project_root(path)
    scanner = Scanner(root)
    current_state = scanner.scan()

    if snapshot:
        mgr = SnapshotManager(root)
        try:
            expected_state = mgr.get_snapshot(snapshot)
            diff = DiffEngine.compare(expected_state, current_state)
            report = Doctor.diagnose_diff(diff)
        except FileNotFoundError:
            term.print_error(f"Snapshot '{snapshot}' not found.")
            raise typer.Exit(code=2) from None
    else:
        # Check against baseline snapshot if exists, or diagnose current scan directly
        mgr = SnapshotManager(root)
        baseline = mgr.get_current()
        if baseline:
            diff = DiffEngine.compare(baseline, current_state)
            report = Doctor.diagnose_diff(diff)
            # If diff is clean, also do standalone check for missing required env vars in current state
            if report.is_healthy:
                report = Doctor.diagnose_state(current_state)
        else:
            report = Doctor.diagnose_state(current_state)

    if json_output:
        term.print_json(
            {
                "project_name": report.project_name,
                "fingerprint": report.fingerprint,
                "is_healthy": report.is_healthy,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity.value,
                        "title": issue.title,
                        "evidence": issue.evidence,
                        "explanation": issue.explanation,
                        "suggested_action": issue.suggested_action,
                    }
                    for issue in report.issues
                ],
            }
        )
    else:
        render_doctor(report, term.console)
