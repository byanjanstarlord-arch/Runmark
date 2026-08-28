"""Sanitizer for paths, URLs, and environment data."""

import re
import urllib.parse
from pathlib import Path

from runmark.security.secret_patterns import SENSITIVE_QUERY_PARAMS


class Sanitizer:
    """Sanitizes sensitive information from strings, URLs, and paths."""

    _GENERIC_URI_CREDENTIALS_REGEX = re.compile(
        r"([a-zA-Z0-9+.-]+://)([^:]+):([^@]+)@",
        re.IGNORECASE,
    )

    @classmethod
    def sanitize_uri(cls, uri: str) -> str:
        """Strip username and password/token from URIs and redact sensitive query params.

        Examples:
            postgres://admin:password@localhost:5432/app -> postgres://localhost:5432/app
            redis://user:password@localhost:6379 -> redis://localhost:6379
            https://user:token@example.com/api?token=secret123&env=prod -> https://example.com/api?token=[REDACTED]&env=prod
        """
        if not uri or not isinstance(uri, str):
            return ""

        try:
            parts = urllib.parse.urlsplit(uri)
            if parts.scheme:
                netloc = parts.netloc
                if "@" in netloc:
                    # Strip userinfo (username:password@)
                    _, _, host_port = netloc.rpartition("@")
                    netloc = host_port

                # Redact sensitive query parameters
                query = parts.query
                if query:
                    parsed_query = urllib.parse.parse_qsl(query, keep_blank_values=True)
                    clean_query = []
                    for k, v in parsed_query:
                        if k.lower() in SENSITIVE_QUERY_PARAMS:
                            clean_query.append((k, "[REDACTED]"))
                        else:
                            clean_query.append((k, v))
                    query = urllib.parse.urlencode(clean_query)

                sanitized = urllib.parse.urlunsplit(
                    (parts.scheme, netloc, parts.path, query, parts.fragment)
                )
                return sanitized
        except Exception:
            # Fallback regex redaction if URL parsing encounters malformed data
            pass

        return cls._GENERIC_URI_CREDENTIALS_REGEX.sub(r"\1", uri)

    @classmethod
    def sanitize_remote_url(cls, url: str) -> str:
        """Alias for sanitize_uri for backward compatibility."""
        return cls.sanitize_uri(url)

    @classmethod
    def sanitize_path(cls, path: Path | str, base: Path | str | None = None) -> str:
        """Normalize path and mask personal user home directories for privacy.

        If path is within `base`, returns the relative POSIX path.
        If path is outside `base` but within user home, replaces home directory with '<USER_HOME>'.
        """
        if not path:
            return ""

        try:
            p = Path(path).resolve()
        except Exception:
            return str(path)

        if base:
            try:
                base_path = Path(base).resolve()
                rel = p.relative_to(base_path)
                return rel.as_posix()
            except ValueError:
                pass

        # Protect personal home directory
        try:
            home = Path.home().resolve()
            try:
                rel_home = p.relative_to(home)
                return f"<USER_HOME>/{rel_home.as_posix()}"
            except ValueError:
                pass
        except Exception:
            pass

        return p.as_posix()

    @classmethod
    def normalize_path(cls, path: Path | str, base: Path | str | None = None) -> str:
        """Convert path to normalized POSIX format relative to base if within it."""
        return cls.sanitize_path(path, base=base)
