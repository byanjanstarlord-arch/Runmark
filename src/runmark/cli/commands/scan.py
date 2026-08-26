"""CLI command: runmark scan."""

from pathlib import Path

import typer

from runmark.core.scanner import Scanner
from runmark.output.tables import render_scan
from runmark.output.terminal import term
from runmark.storage.paths import find_project_root


def scan_command(
    path: Path = typer.Option(None, "--path", "-p", help="Target project root directory"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Inspect and display the complete runtime, dependency, and service state."""
    root = find_project_root(path)
    scanner = Scanner(root)
    state = scanner.scan()

    if json_output:
        term.print_json(state)
    else:
        render_scan(state, term.console)
