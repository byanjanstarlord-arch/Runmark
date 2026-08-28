"""JSON parsing, schema validation, and domain construction for Runmark contracts."""

import json
from pathlib import Path

from runmark.contracts.security import ContractSanitizer
from runmark.contracts.validator import ContractValidator
from runmark.models.contract import RunmarkContract


class ContractParseError(ValueError):
    """Raised when contract JSON is malformed or unparseable."""


class ContractParser:
    """Safely parses, validates, and constructs typed RunmarkContract objects."""

    @classmethod
    def parse_string(cls, json_text: str) -> RunmarkContract:
        """Parse raw JSON string into a validated RunmarkContract."""
        if not json_text or not json_text.strip():
            raise ContractParseError("Contract content is empty.")

        try:
            raw_data = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ContractParseError(f"Malformed JSON in contract definition: {exc}") from None

        if not isinstance(raw_data, dict):
            raise ContractParseError("Contract root must be a JSON object.")

        # 1. Security validation: ensure zero embedded secrets or credentials
        ContractSanitizer.verify_contract_clean(raw_data)

        # 2. Structural schema validation
        ContractValidator.validate_schema(raw_data)

        # 3. Model construction
        contract = RunmarkContract.model_validate(raw_data)

        # 4. Semantic validation
        ContractValidator.validate_semantics(contract)

        return contract

    @classmethod
    def parse_file(cls, file_path: Path | str) -> RunmarkContract:
        """Read and parse a contract JSON file from disk."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Contract file '{p}' does not exist.")

        try:
            content = p.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ContractParseError(
                f"Failed to read contract file '{p}' as UTF-8: {exc}"
            ) from None

        return cls.parse_string(content)
