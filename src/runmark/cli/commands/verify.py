"""CLI command: runmark verify."""

from pathlib import Path

import typer

from runmark.core.scanner import Scanner
from runmark.core.snapshot import SnapshotManager
from runmark.core.verifier import Verifier
from runmark.models.runmark import RunmarkState
from runmark.output.tables import render_verify
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def verify_command(
    snapshot: str | None = typer.Option(
        None,
        "--snapshot",
        "-s",
        help="Target baseline snapshot ID (defaults to current active snapshot)",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as verification failures",
    ),
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Verify that current environment matches expected baseline snapshot."""
    root = find_project_root(path)
    mgr = SnapshotManager(root)

    expected_state: RunmarkState
    if snapshot:
        try:
            expected_state = mgr.get_snapshot(snapshot)
        except FileNotFoundError:
            term.print_error(f"Snapshot '{snapshot}' not found.")
            raise typer.Exit(code=Verifier.EXIT_CODE_INVALID_USAGE) from None
    else:
        loaded_exp = mgr.get_current()
        if not loaded_exp:
            term.print_error(
                "No baseline snapshot found. Create one with 'runmark snapshot' or specify --snapshot."
            )
            raise typer.Exit(code=Verifier.EXIT_CODE_INVALID_USAGE)
        expected_state = loaded_exp

    try:
        scanner = Scanner(root)
        current_state = scanner.scan()
    except Exception as exc:
        term.print_error(f"Scanning failed during verification: {exc}")
        raise typer.Exit(code=Verifier.EXIT_CODE_INTERNAL_ERROR) from exc

    verifier = Verifier(strict=strict)
    result = verifier.verify(expected_state, current_state)

    if json_output:
        term.print_json(
            {
                "status": result.status.value,
                "exit_code": result.exit_code,
                "expected_fingerprint": expected_state.runmark.environment_fingerprint,
                "current_fingerprint": current_state.runmark.environment_fingerprint,
                "reasons": result.reasons,
                "diff_items_count": len(result.diff.environment_items),
            }
        )
    else:
        render_verify(result, term.console)

    raise typer.Exit(code=result.exit_code)
