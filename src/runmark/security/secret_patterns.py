"""Regex patterns and heuristics for secret detection and redaction."""

import re
from re import Pattern

# Variable name patterns indicating sensitive credentials
SECRET_NAME_PATTERNS: list[Pattern[str]] = [
    re.compile(r"API[_-]?KEY", re.IGNORECASE),
    re.compile(r"ACCESS[_-]?TOKEN", re.IGNORECASE),
    re.compile(r"AUTH[_-]?TOKEN", re.IGNORECASE),
    re.compile(r"SECRET", re.IGNORECASE),
    re.compile(r"PASS(WORD|WD)?", re.IGNORECASE),
    re.compile(r"PRIVATE[_-]?KEY", re.IGNORECASE),
    re.compile(r"AWS[_-]?(SECRET|SESSION|KEY|TOKEN)", re.IGNORECASE),
    re.compile(r"GITHUB[_-]?(TOKEN|KEY|PAT)", re.IGNORECASE),
    re.compile(r"GITLAB[_-]?TOKEN", re.IGNORECASE),
    re.compile(r"DATABASE[_-]?(PASSWORD|PASSWD|URL)", re.IGNORECASE),
    re.compile(r"DB[_-]?(PASSWORD|PASSWD|PASS)", re.IGNORECASE),
    re.compile(r"STRIPE[_-]?(SECRET|KEY|WEBHOOK)", re.IGNORECASE),
    re.compile(r"OPENAI[_-]?API[_-]?KEY", re.IGNORECASE),
    re.compile(r"SENTRY[_-]?(AUTH[_-]?TOKEN|DSN)", re.IGNORECASE),
    re.compile(r"BEARER[_-]?TOKEN", re.IGNORECASE),
    re.compile(r"CREDENTIAL(S)?", re.IGNORECASE),
    re.compile(r"CERTIFICATE", re.IGNORECASE),
    re.compile(r"ENCRYPTION[_-]?KEY", re.IGNORECASE),
    re.compile(r"SIGNING[_-]?(KEY|SECRET)", re.IGNORECASE),
    re.compile(r"SESSION[_-]?(KEY|SECRET)", re.IGNORECASE),
    re.compile(r"CLIENT[_-]?SECRET", re.IGNORECASE),
]

# Sensitive value content signatures
SECRET_VALUE_PATTERNS: list[Pattern[str]] = [
    re.compile(r"-----BEGIN\s+(?:[A-Z0-9_\-]+\s+)*(?:PRIVATE\s+)?KEY", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,255}\b"),  # GitHub tokens
    re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,255}\b"),  # GitLab PAT
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,255}\b"),  # OpenAI / generic secret keys
    re.compile(r"\bsk_(live|test)_[0-9a-zA-Z]{24,}\b"),  # Stripe keys
    re.compile(r"\bxox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}\b"),  # Slack
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS Access Key ID
    re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),  # Google API Key
    re.compile(r"https?://[^:]+:[^@]+@[^/\s]+"),  # URLs with embedded basic auth password
]

# File names considered strictly sensitive
SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
    ".env.test",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
    "id_ecdsa",
}

# File extensions considered sensitive
SENSITIVE_FILE_EXTENSIONS = {
    ".pem",
    ".key",
    ".pkcs12",
    ".pfx",
    ".p12",
    ".kdbx",
}


def is_secret_variable_name(name: str) -> bool:
    """Check whether an environment variable name denotes a secret."""
    if not name:
        return False
    return any(pattern.search(name) for pattern in SECRET_NAME_PATTERNS)


def contains_secret_value(value: str) -> bool:
    """Check whether a string value matches known high-confidence secret signatures."""
    if not value or not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)
