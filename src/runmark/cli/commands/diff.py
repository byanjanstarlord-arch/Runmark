"""CLI command: runmark diff."""

from pathlib import Path

import typer

from runmark.core.diff import DiffEngine
from runmark.core.scanner import Scanner
from runmark.core.snapshot import SnapshotManager
from runmark.models.runmark import RunmarkState
from runmark.output.tables import render_diff
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def diff_command(
    from_snapshot: str | None = typer.Option(
        None,
        "--from",
        help="Baseline snapshot ID (defaults to current active snapshot)",
    ),
    to_snapshot: str | None = typer.Option(
        None,
        "--to",
        help="Target snapshot ID (defaults to active live scan of current environment)",
    ),
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Compare environment state between snapshots or against current live environment."""
    root = find_project_root(path)
    mgr = SnapshotManager(root)

    # 1. Load baseline state
    base_state: RunmarkState
    if from_snapshot:
        try:
            base_state = mgr.get_snapshot(from_snapshot)
        except FileNotFoundError:
            term.print_error(f"Snapshot '{from_snapshot}' not found.")
            raise typer.Exit(code=2) from None
    else:
        loaded_base = mgr.get_current()
        if not loaded_base:
            term.print_error(
                "No baseline snapshot found. Run 'runmark snapshot' first to create a baseline."
            )
            raise typer.Exit(code=2)
        base_state = loaded_base

    # 2. Load target state
    target_state: RunmarkState
    if to_snapshot:
        try:
            target_state = mgr.get_snapshot(to_snapshot)
        except FileNotFoundError:
            term.print_error(f"Snapshot '{to_snapshot}' not found.")
            raise typer.Exit(code=2) from None
    else:
        scanner = Scanner(root)
        target_state = scanner.scan()

    # 3. Compute semantic diff
    diff = DiffEngine.compare(base_state, target_state)

    if json_output:
        term.print_json(
            {
                "from_id": diff.from_id,
                "to_id": diff.to_id,
                "from_fingerprint": diff.from_fingerprint,
                "to_fingerprint": diff.to_fingerprint,
                "is_identical": diff.is_identical,
                "items": [
                    {
                        "category": item.category,
                        "item_name": item.item_name,
                        "classification": item.classification.value,
                        "severity": item.severity.value,
                        "old_value": item.old_value,
                        "new_value": item.new_value,
                        "description": item.description,
                        "is_source_revision": item.is_source_revision,
                    }
                    for item in diff.items
                ],
            }
        )
    else:
        render_diff(diff, term.console)
