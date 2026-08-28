"""Security boundary enforcement for Runmark environment contracts."""

import json
from typing import Any

from runmark.security.export_sanitizer import SecurityViolationError
from runmark.security.secret_patterns import contains_secret_value


class ContractSecurityError(SecurityViolationError):
    """Raised when an environment contract contains embedded secrets or credentials."""


class ContractSanitizer:
    """Scans and validates environment contract definitions against secret contamination."""

    @classmethod
    def verify_contract_clean(cls, raw_content: str | dict[str, Any]) -> None:
        """Scan raw contract JSON or dictionary to ensure no secrets or credentials are embedded.

        Raises ContractSecurityError if sensitive tokens, keys, or passwords are detected.
        """
        if isinstance(raw_content, dict):
            text_to_scan = json.dumps(raw_content)
        else:
            text_to_scan = str(raw_content)

        if contains_secret_value(text_to_scan):
            raise ContractSecurityError(
                "Contract security violation: sensitive data or unredacted credentials "
                "were detected inside the environment contract definition. "
                "Contracts must define requirement names and constraints only, never values or secrets."
            )

    @classmethod
    def scan_raw(cls, raw_content: str | dict[str, Any]) -> None:
        """Alias for verify_contract_clean."""
        cls.verify_contract_clean(raw_content)
