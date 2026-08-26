"""CLI command: runmark snapshot."""

from pathlib import Path

import typer
from rich.panel import Panel

from runmark.core.snapshot import SnapshotManager
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def snapshot_command(
    message: str | None = typer.Option(
        None, "--message", "-m", help="Optional description of the snapshot"
    ),
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Capture and persist the current environment state into an immutable baseline snapshot."""
    root = find_project_root(path)
    mgr = SnapshotManager(root)
    state = mgr.create_snapshot(message=message)

    if json_output:
        term.print_json(state)
    else:
        term.print(
            Panel(
                f"[bold green]✓ Snapshot Captured & Saved[/bold green]\n\n"
                f"• Snapshot ID:  [bold cyan]{state.runmark.id}[/bold cyan]\n"
                f"• Fingerprint:  [bold green]{state.runmark.environment_fingerprint}[/bold green]\n"
                f"• Tool Version: [dim]{state.runmark.tool_version}[/dim]\n"
                f"• Project:      [bold]{state.project.name}[/bold]\n"
                f"• Git Commit:   [dim]{state.git.commit or 'none'}[/dim]\n"
                f"{f'• Note:         [italic]{state.runmark.message}[/italic]' if state.runmark.message else ''}",
                border_style="green",
            )
        )
