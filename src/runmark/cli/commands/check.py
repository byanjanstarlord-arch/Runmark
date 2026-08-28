"""CLI command: runmark check."""

from pathlib import Path

import typer

from runmark.contracts.parser import ContractParseError
from runmark.contracts.security import ContractSecurityError
from runmark.contracts.validator import ContractValidationError
from runmark.core.contract_check import ContractCheckService
from runmark.output.contract import render_contract_check
from runmark.output.terminal import term


def check_command(
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Target project root directory (defaults to current directory)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output evaluation results as machine-readable JSON",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Display detailed diagnostic breakdown and suggested actions for unsatisfied requirements",
    ),
) -> None:
    """Evaluate whether current host environment satisfies the project environment contract (runmark.json)."""
    try:
        contract, result = ContractCheckService.check_environment(project_path=path)
    except ContractSecurityError as sec_err:
        term.print_error(str(sec_err))
        raise typer.Exit(code=4) from None
    except (FileNotFoundError, ContractParseError, ContractValidationError) as err:
        term.print_error(str(err))
        raise typer.Exit(code=2) from None
    except Exception as exc:
        term.print_error(f"Internal error during contract evaluation: {exc}")
        raise typer.Exit(code=3) from None

    if json_output:
        term.print_json(result)
    else:
        render_contract_check(result, explain=explain)

    if result.is_passed:
        raise typer.Exit(code=0)
    else:
        raise typer.Exit(code=1)
