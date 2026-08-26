"""Runmark CLI application entrypoint."""

import sys

import typer

from runmark.cli.commands.diff import diff_command
from runmark.cli.commands.doctor import doctor_command
from runmark.cli.commands.history import history_command
from runmark.cli.commands.init import init_command
from runmark.cli.commands.scan import scan_command
from runmark.cli.commands.snapshot import snapshot_command
from runmark.cli.commands.verify import verify_command
from runmark.cli.commands.version import version_command
from runmark.output.terminal import term

app = typer.Typer(
    name="runmark",
    help="Runmark — Know what makes your code run.\n\nGit tracks your code. Runmark tracks what makes your code run.",
    no_args_is_help=True,
    add_completion=False,
)

# Register subcommands
app.command("init", help="Initialize Runmark tracking in the current project.")(init_command)
app.command(
    "scan", help="Inspect and display the complete runtime, dependency, and service state."
)(scan_command)
app.command(
    "snapshot",
    help="Capture and persist current environment state into an immutable baseline snapshot.",
)(snapshot_command)
app.command(
    "diff", help="Compare environment state between snapshots or against live environment."
)(diff_command)
app.command("verify", help="Verify current machine environment against a baseline snapshot.")(
    verify_command
)
app.command(
    "doctor", help="Diagnose environment discrepancies and get actionable remediation advice."
)(doctor_command)
app.command("version", help="Display version and platform diagnostics.")(version_command)
app.command("history", help="List snapshot history.")(history_command)


def main() -> int:
    """Main CLI entrypoint."""
    try:
        app()
        return 0
    except typer.Exit as e:
        return e.exit_code
    except KeyboardInterrupt:
        term.print("\n[dim]Operation cancelled by user.[/dim]")
        return 130
    except Exception as exc:
        term.print_error(f"Unexpected error: {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
