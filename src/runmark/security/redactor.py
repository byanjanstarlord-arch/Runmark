"""Redaction engine to strip secrets and sanitize environment variables."""

from typing import Any

from runmark.models.environment import EnvironmentVariableState
from runmark.security.secret_patterns import contains_secret_value, is_secret_variable_name


class SecretRedactor:
    """Detects and redacts sensitive data from environment variables and payloads."""

    REDACTED_PLACEHOLDER = "[REDACTED]"

    @classmethod
    def redact_env_variable(
        cls,
        name: str,
        value: Any = None,
        required: bool = False,
        present: bool = False,
        source: str = "environment",
    ) -> EnvironmentVariableState:
        """Create a safe EnvironmentVariableState without storing the raw secret value."""
        is_secret = is_secret_variable_name(name)
        if not is_secret and value and isinstance(value, str):
            is_secret = contains_secret_value(value)

        return EnvironmentVariableState(
            name=name,
            required=required,
            present=present,
            secret=is_secret,
            source=source,
        )

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Scrub secret patterns and embedded credentials from arbitrary text."""
        if not text:
            return ""

        from runmark.security.secret_patterns import SECRET_VALUE_PATTERNS

        redacted = text
        for pattern in SECRET_VALUE_PATTERNS:
            redacted = pattern.sub(cls.REDACTED_PLACEHOLDER, redacted)

        return redacted

    @classmethod
    def sanitize_dictionary(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively scrub any dictionary keys or values that might contain sensitive information."""
        sanitized: dict[str, Any] = {}
        for k, v in data.items():
            if is_secret_variable_name(k):
                sanitized[k] = cls.REDACTED_PLACEHOLDER
            elif isinstance(v, dict):
                sanitized[k] = cls.sanitize_dictionary(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    cls.sanitize_dictionary(item)
                    if isinstance(item, dict)
                    else (cls.redact_text(str(item)) if isinstance(item, str) else item)
                    for item in v
                ]
            elif isinstance(v, str):
                if "://" in v:
                    from runmark.security.sanitizer import Sanitizer

                    sanitized[k] = Sanitizer.sanitize_uri(v)
                else:
                    sanitized[k] = cls.redact_text(v)
            else:
                sanitized[k] = v
        return sanitized
