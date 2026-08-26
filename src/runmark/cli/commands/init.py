"""CLI command: runmark init."""

from pathlib import Path

import typer
from rich.panel import Panel

from runmark.output.terminal import term
from runmark.storage.filesystem import FilesystemStorage
from runmark.storage.paths import find_project_root


def init_command(
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Initialize Runmark configuration in the current project."""
    root = find_project_root(path)
    storage = FilesystemStorage(root)

    already_initialized = storage.paths.is_initialized()
    if already_initialized and not force:
        if json_output:
            term.print_json(
                {
                    "status": "already_initialized",
                    "project_root": str(root),
                    "runmark_dir": str(storage.paths.runmark_dir),
                }
            )
        else:
            term.print(
                Panel(
                    f"[yellow]Runmark is already initialized in:[/yellow] [bold]{root}[/bold]\n"
                    f"Configuration: [dim]{storage.paths.config_file}[/dim]\n"
                    f"Use [cyan]--force[/cyan] to re-initialize.",
                    border_style="yellow",
                )
            )
        return

    storage.initialize(force=force)

    if json_output:
        term.print_json(
            {
                "status": "initialized",
                "project_root": str(root),
                "runmark_dir": str(storage.paths.runmark_dir),
                "config_file": str(storage.paths.config_file),
            }
        )
    else:
        term.print(
            Panel(
                f"[bold green]✓ Initialized Runmark in:[/bold green] [bold]{root}[/bold]\n\n"
                f"• Created configuration: [dim]{storage.paths.config_file}[/dim]\n"
                f"• Created snapshots dir: [dim]{storage.paths.snapshots_dir}[/dim]\n\n"
                f"Next steps:\n"
                f"  1. Run [bold cyan]runmark scan[/bold cyan] to inspect your environment.\n"
                f"  2. Run [bold cyan]runmark snapshot[/bold cyan] to create your first baseline.",
                border_style="green",
            )
        )
