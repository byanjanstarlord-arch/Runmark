"""Unit tests for ContractParser."""

from pathlib import Path

import pytest

from runmark.contracts.parser import ContractParseError, ContractParser
from runmark.contracts.validator import ContractValidationError

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "contracts"


class TestContractParser:
    """Tests for ContractParser file and string parsing."""

    def test_parse_valid_full_file(self) -> None:
        full_path = FIXTURES_DIR / "valid" / "valid_full.json"
        contract = ContractParser.parse_file(full_path)
        assert contract.version == 1
        assert contract.project.name == "full-stack-api"
        assert "linux" in contract.platform.os
        assert contract.runtime["python"] == ">=3.11,<3.13"
        assert contract.services["postgresql"].required is True
        assert contract.services["redis"].version == ">=6"
        assert "DATABASE_URL" in contract.environment.required

    def test_parse_valid_minimal_file(self) -> None:
        min_path = FIXTURES_DIR / "valid" / "valid_minimal.json"
        contract = ContractParser.parse_file(min_path)
        assert contract.version == 1
        assert contract.project.name is None

    def test_parse_string_valid(self) -> None:
        raw_json = '{"version": 1, "runtime": {"python": "3.12.x"}}'
        contract = ContractParser.parse_string(raw_json)
        assert contract.version == 1
        assert contract.runtime["python"] == "3.12.x"

    def test_parse_empty_string_fails(self) -> None:
        with pytest.raises(ContractParseError) as exc:
            ContractParser.parse_string("")
        assert "empty" in str(exc.value)

    def test_parse_malformed_json_fails(self) -> None:
        malformed_path = FIXTURES_DIR / "invalid" / "malformed.json"
        with pytest.raises(ContractParseError) as exc:
            ContractParser.parse_file(malformed_path)
        assert "Malformed JSON" in str(exc.value)

    def test_parse_missing_file_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            ContractParser.parse_file(FIXTURES_DIR / "non_existent.json")

    def test_parse_invalid_version_fails(self) -> None:
        inv_path = FIXTURES_DIR / "invalid" / "invalid_version.json"
        with pytest.raises(ContractValidationError):
            ContractParser.parse_file(inv_path)
