"""Sanitizer for paths, URLs, and environment data."""

import re
from pathlib import Path


class Sanitizer:
    """Sanitizes sensitive information from strings, URLs, and paths."""

    _URL_CREDENTIALS_REGEX = re.compile(r"(https?://)([^:]+):([^@]+)@")

    @classmethod
    def sanitize_remote_url(cls, url: str) -> str:
        """Strip username and password/token from remote URLs.

        e.g., https://oauth2:secret_token@github.com/org/repo.git -> https://github.com/org/repo.git
        """
        if not url:
            return ""
        return cls._URL_CREDENTIALS_REGEX.sub(r"\1", url)

    @classmethod
    def normalize_path(cls, path: Path | str, base: Path | str | None = None) -> str:
        """Convert path to normalized POSIX format relative to base if within it."""
        p = Path(path).resolve()
        if base:
            try:
                base_path = Path(base).resolve()
                rel = p.relative_to(base_path)
                return rel.as_posix()
            except ValueError:
                pass
        return p.as_posix()
