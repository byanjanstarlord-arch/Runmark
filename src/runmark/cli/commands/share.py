"""CLI command: runmark share."""

import sys
from pathlib import Path

import typer

from runmark.core.reporter import Reporter
from runmark.output.terminal import term
from runmark.security.export_sanitizer import SecurityViolationError
from runmark.storage.paths import find_project_root


def share_command(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Target output report path (e.g. report.md, report.json)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Generate report in structured JSON format instead of Markdown",
    ),
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Print only the raw sanitized report content directly to stdout",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output file if it exists",
    ),
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
) -> None:
    """Generate a sanitized, portable diagnostic report to safely share environment state."""
    if path is not None and not path.exists():
        term.print_error(f"Project directory '{path}' not found.")
        raise typer.Exit(code=2)
    root = find_project_root(path)

    try:
        report = Reporter.generate_report(root)
    except SecurityViolationError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except Exception as exc:
        term.print_error(f"Failed to generate diagnostic report: {exc}")
        raise typer.Exit(code=3) from None

    if stdout:
        try:
            if json_output:
                content = Reporter.render_json(report)
            else:
                content = Reporter.render_markdown(report)
            sys.stdout.write(content + "\n")
            sys.stdout.flush()
            return
        except SecurityViolationError as sec_err:
            term.print_error(str(sec_err))
            raise typer.Exit(code=4) from None
        except Exception as exc:
            term.print_error(f"Failed to render report: {exc}")
            raise typer.Exit(code=3) from None

    dest = output
    if dest is None:
        default_name = "runmark-report.json" if json_output else "runmark-report.md"
        dest = root / default_name

    try:
        out_path = Reporter.export_to_file(
            report=report,
            destination=dest,
            as_json=json_output,
            force=force,
        )
        term.print_success(f"Sanitized diagnostic report written to: {out_path}")
        term.print(
            f"[dim]Report ID: {report.metadata.report_id} | "
            f"Fingerprint: {report.metadata.environment_fingerprint}[/dim]"
        )
        if not json_output:
            term.print(
                "[dim]You can now safely attach this Markdown report to GitHub Issues, Slack, or Discussions.[/dim]"
            )
    except SecurityViolationError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except FileExistsError as file_err:
        term.print_error(str(file_err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Failed to export report: {exc}")
        raise typer.Exit(code=3) from None
