"""Unit tests for Contract Security and Secret Prevention."""

from pathlib import Path

import pytest

from runmark.contracts.parser import ContractParser
from runmark.contracts.security import (
    ContractSanitizer,
    ContractSecurityError,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "contracts"


class TestContractSecurity:
    """Tests ensuring zero-secret tolerance in contracts."""

    def test_secret_in_contract_file_raises_security_error(self) -> None:
        malicious_file = FIXTURES_DIR / "malicious" / "secret_in_contract.json"
        with pytest.raises(ContractSecurityError) as exc:
            ContractParser.parse_file(malicious_file)
        assert "security violation" in str(exc.value).lower()
        # Verify secret itself is never printed in error message
        assert "my_secret_production_password" not in str(exc.value)

    def test_direct_sanitizer_with_api_key_raises(self) -> None:
        canary = {
            "version": 1,
            "project": {"name": "secret-holder"},
            "runtime": {"python": "sk-proj-123456789012345678901234567890123456789012345678"},
        }
        with pytest.raises(ContractSecurityError):
            ContractSanitizer.verify_contract_clean(canary)

    def test_clean_contract_passes_sanitizer(self) -> None:
        clean = {
            "version": 1,
            "project": {"name": "safe-project"},
            "environment": {"required": ["API_KEY", "DATABASE_URL"]},
        }
        # Should not raise
        ContractSanitizer.verify_contract_clean(clean)
