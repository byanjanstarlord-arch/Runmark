"""CLI command: runmark history."""

from pathlib import Path

import typer

from runmark.core.snapshot import SnapshotManager
from runmark.output.tables import render_history
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def history_command(
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Display chronological history of captured environment snapshots."""
    root = find_project_root(path)
    mgr = SnapshotManager(root)
    snapshots = mgr.list_history()

    if json_output:
        term.print_json([s.model_dump(mode="json") for s in snapshots])
    else:
        render_history(snapshots, term.console)
