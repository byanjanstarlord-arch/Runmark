"""CLI command: runmark version."""

import platform

import typer
from rich.panel import Panel

from runmark import __schema_version__, __version__
from runmark.output.terminal import term


def version_command(
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Display Runmark tool version, schema version, and platform information."""
    info = {
        "tool_version": __version__,
        "schema_version": __schema_version__,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "architecture": platform.machine(),
    }

    if json_output:
        term.print_json(info)
    else:
        term.print(
            Panel(
                f"[bold cyan]Runmark[/bold cyan] [bold]{__version__}[/bold]\n\n"
                f"• Schema Version:  [cyan]{__schema_version__}[/cyan]\n"
                f"• Python Runtime:  [dim]{platform.python_version()}[/dim]\n"
                f"• OS / Platform:   [dim]{platform.system()} ({platform.machine()})[/dim]\n\n"
                f"[italic dim]Git tracks your code. Runmark tracks what makes your code run.[/italic dim]",
                border_style="cyan",
            )
        )
