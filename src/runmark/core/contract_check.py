"""Core orchestration service for environment contract checks and validations."""

from pathlib import Path
from typing import Any

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.discovery import find_contract_file
from runmark.contracts.evaluator import ContractEvaluator
from runmark.contracts.parser import ContractParser
from runmark.core.scanner import Scanner
from runmark.models.contract import RunmarkContract
from runmark.models.contract_result import ContractCheckResult


class ContractCheckService:
    """Coordinates contract discovery, parsing, validation, scanning, and evaluation."""

    @classmethod
    def check_environment(
        cls,
        project_path: Path | str | None = None,
        contract_file: Path | str | None = None,
    ) -> tuple[RunmarkContract, ContractCheckResult]:
        """Discover, validate contract, scan host environment, and evaluate compliance."""
        if contract_file is not None:
            c_path = Path(contract_file).resolve()
        else:
            c_path = find_contract_file(project_path)

        # 1. Parse and validate contract
        contract = ContractParser.parse_file(c_path)

        # 2. Determine project root and scan host environment
        project_root = c_path.parent
        scanner = Scanner(project_root)
        state = scanner.scan()

        # 3. Evaluate contract against state
        result = ContractEvaluator.evaluate(contract, state)
        return contract, result

    @classmethod
    def validate_contract(
        cls,
        project_path: Path | str | None = None,
        contract_file: Path | str | None = None,
    ) -> RunmarkContract:
        """Validate contract syntax, JSON schema, domain semantics, and security rules without scanning."""
        if contract_file is not None:
            c_path = Path(contract_file).resolve()
        else:
            c_path = find_contract_file(project_path)

        return ContractParser.parse_file(c_path)

    @classmethod
    def show_contract(
        cls,
        project_path: Path | str | None = None,
        contract_file: Path | str | None = None,
    ) -> tuple[RunmarkContract, dict[str, Any], str]:
        """Load and canonicalize contract for structured display and fingerprinting."""
        contract = cls.validate_contract(project_path, contract_file)
        canonical = ContractCanonicalizer.canonicalize(contract)
        fingerprint = ContractCanonicalizer.compute_fingerprint(contract)
        return contract, canonical, fingerprint
