"""Terminal rendering and console output management."""

import json
import os
import sys
from typing import Any

from rich.console import Console


class Terminal:
    """Rich console wrapper with graceful degradation for no-color and non-interactive environments."""

    def __init__(self, force_terminal: bool | None = None, no_color: bool = False):
        if sys.platform == "win32":
            try:
                if hasattr(sys.stdout, "reconfigure"):
                    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
                if hasattr(sys.stderr, "reconfigure"):
                    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        # Respect NO_COLOR env var (https://no-color.org/)
        has_no_color = no_color or bool(os.environ.get("NO_COLOR"))
        self.console = Console(
            no_color=has_no_color,
            highlight=False,
            force_terminal=force_terminal,
            legacy_windows=False,
        )
        self.err_console = Console(
            stderr=True,
            no_color=has_no_color,
            highlight=False,
            force_terminal=force_terminal,
            legacy_windows=False,
        )

    def print(self, *args, **kwargs) -> None:
        """Print to standard output."""
        self.console.print(*args, **kwargs)

    def print_success(self, message: str) -> None:
        """Print success message to stdout."""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message to stdout."""
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    def print_error(self, message: str) -> None:
        """Print error message to stderr."""
        self.err_console.print(f"[bold red]✗ Error:[/bold red] {message}")

    def print_json(self, data: Any) -> None:
        """Print machine-readable JSON to stdout."""
        if hasattr(data, "model_dump_json"):
            sys.stdout.write(data.model_dump_json(indent=2) + "\n")
        elif hasattr(data, "model_dump"):
            sys.stdout.write(json.dumps(data.model_dump(mode="json"), indent=2) + "\n")
        elif isinstance(data, dict) or isinstance(data, list):
            sys.stdout.write(json.dumps(data, indent=2) + "\n")
        else:
            sys.stdout.write(json.dumps(data, default=str, indent=2) + "\n")
        sys.stdout.flush()


# Default singleton console
term = Terminal()
