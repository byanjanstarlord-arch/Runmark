"""CLI command group: runmark contract."""

from pathlib import Path

import typer

from runmark.contracts.parser import ContractParseError
from runmark.contracts.security import ContractSecurityError
from runmark.contracts.validator import ContractValidationError
from runmark.core.contract_check import ContractCheckService
from runmark.core.contract_diff import ContractDiffService
from runmark.core.contract_init import ContractInitService
from runmark.output.contract import (
    render_contract_diff,
    render_contract_preview,
    render_contract_show,
)
from runmark.output.terminal import term

contract_app = typer.Typer(
    name="contract",
    help="Inspect, validate, initialize, and display project environment contracts (runmark.json).",
    no_args_is_help=True,
)


@contract_app.command(
    "init", help="Bootstrap a runmark.json contract from discovered project evidence."
)
def init_contract_command(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip interactive confirmation and generate contract directly",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview generated contract without modifying any files",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing runmark.json contract",
    ),
) -> None:
    """Bootstrap an environment contract from project evidence."""
    target_root = path.resolve() if path else Path.cwd().resolve()
    target_file = target_root / "runmark.json"

    # Pre-check for existing contract if not using force/dry-run
    if target_file.exists() and not force and not dry_run:
        term.print_error(
            f"Environment contract 'runmark.json' already exists in '{target_root}'.\n"
            "Use --force to replace the existing contract."
        )
        raise typer.Exit(code=2)

    try:
        contract, evidence, _ = ContractInitService.init_contract(
            project_path=path,
            force=force,
            dry_run=True,  # Always generate in dry-run first for preview and validation
        )
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except FileExistsError as fe_err:
        term.print_error(str(fe_err))
        raise typer.Exit(code=2) from None
    except (FileNotFoundError, ContractParseError, ContractValidationError) as err:
        term.print_error(str(err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Internal error generating contract: {exc}")
        raise typer.Exit(code=3) from None

    # Render Preview
    render_contract_preview(contract, evidence)

    if dry_run:
        term.print_warning("Dry-run mode enabled. No files were modified.")
        raise typer.Exit(code=0)

    # Interactive confirmation if not skipped with --yes
    if not yes:
        confirmed = typer.confirm("Create runmark.json?", default=True)
        if not confirmed:
            term.print("Aborted. No files were modified.")
            raise typer.Exit(code=0)

    # Persist contract atomically
    try:
        ContractInitService.init_contract(
            project_path=path,
            force=force,
            dry_run=False,
        )
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except Exception as exc:
        term.print_error(f"Failed to persist contract: {exc}")
        raise typer.Exit(code=3) from None

    term.print_success("Environment contract 'runmark.json' created successfully.")
    raise typer.Exit(code=0)


@contract_app.command(
    "diff", help="Show semantic differences between working contract and baseline."
)
def diff_contract_command(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output semantic contract diff as machine-readable JSON",
    ),
) -> None:
    """Compare working runmark.json against Git repository baseline."""
    try:
        diff_result = ContractDiffService.diff_contracts(project_path=path)
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except (FileNotFoundError, ContractParseError, ContractValidationError) as err:
        term.print_error(str(err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Internal error diffing contracts: {exc}")
        raise typer.Exit(code=3) from None

    if json_output:
        term.print_json(diff_result)
    else:
        render_contract_diff(diff_result)
    raise typer.Exit(code=0)


@contract_app.command(
    "validate", help="Validate runmark.json syntax, schema, domain semantics, and security."
)
def validate_contract_command(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output validation status as machine-readable JSON",
    ),
) -> None:
    """Validate that runmark.json is structurally, semantically, and securely valid."""
    try:
        contract = ContractCheckService.validate_contract(project_path=path)
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except (FileNotFoundError, ContractParseError, ContractValidationError) as err:
        term.print_error(str(err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Internal error validating contract: {exc}")
        raise typer.Exit(code=3) from None

    if json_output:
        term.print_json(
            {
                "status": "valid",
                "version": contract.version,
                "project": contract.project.name,
            }
        )
    else:
        term.print_success(
            f"Environment contract 'runmark.json' is valid (version {contract.version})."
        )
    raise typer.Exit(code=0)


@contract_app.command(
    "show", help="Display the canonical / normalized interpretation of runmark.json."
)
def show_contract_command(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output canonical contract definition as machine-readable JSON",
    ),
) -> None:
    """Display normalized contract specifications and canonical fingerprint."""
    try:
        contract, canonical, fingerprint = ContractCheckService.show_contract(project_path=path)
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except (FileNotFoundError, ContractParseError, ContractValidationError) as err:
        term.print_error(str(err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Internal error displaying contract: {exc}")
        raise typer.Exit(code=3) from None

    if json_output:
        term.print_json(
            {
                "contract": canonical,
                "fingerprint": fingerprint,
            }
        )
    else:
        render_contract_show(contract, canonical, fingerprint)
    raise typer.Exit(code=0)
