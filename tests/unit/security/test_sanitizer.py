"""Unit tests for string and URL sanitization."""

from runmark.security.sanitizer import Sanitizer


def test_sanitize_remote_url_removes_credentials():
    url_with_token = "https://x-access-token:ghp_1234567890abcdef@github.com/runmark/runmark.git"
    sanitized = Sanitizer.sanitize_remote_url(url_with_token)
    assert sanitized == "https://github.com/runmark/runmark.git"
    assert "ghp_" not in sanitized
    assert "x-access-token" not in sanitized


def test_sanitize_remote_url_preserves_clean_url():
    clean_url = "https://github.com/runmark/runmark.git"
    assert Sanitizer.sanitize_remote_url(clean_url) == clean_url


def test_normalize_path_relative(tmp_path):
    sub = tmp_path / "sub" / "file.txt"
    norm = Sanitizer.normalize_path(sub, base=tmp_path)
    assert norm == "sub/file.txt"
