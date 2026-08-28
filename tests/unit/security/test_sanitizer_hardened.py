"""Hardened test suite for URI and Path Privacy Sanitization."""

from pathlib import Path

from runmark.security.sanitizer import Sanitizer


def test_sanitize_uri_various_schemes():
    cases = [
        (
            "postgres://superuser:supersecret@localhost:5432/my_database",
            "postgres://localhost:5432/my_database",
        ),
        (
            "postgresql://app_user:pwd1234@db.prod.internal:5432/app",
            "postgresql://db.prod.internal:5432/app",
        ),
        (
            "redis://:redispassword@127.0.0.1:6379/0",
            "redis://127.0.0.1:6379/0",
        ),
        (
            "mongodb://root:adminpwd@cluster0.mongodb.net:27017/admin",
            "mongodb://cluster0.mongodb.net:27017/admin",
        ),
        (
            "mysql://dbuser:mypassword@mysql.internal/app_db",
            "mysql://mysql.internal/app_db",
        ),
        (
            "amqp://guest:guest@rabbitmq.host:5672",
            "amqp://rabbitmq.host:5672",
        ),
        (
            "https://oauth2:ghp_1234567890abcdef@github.com/myorg/myrepo.git",
            "https://github.com/myorg/myrepo.git",
        ),
    ]

    for raw, expected in cases:
        sanitized = Sanitizer.sanitize_uri(raw)
        assert "supersecret" not in sanitized
        assert "pwd1234" not in sanitized
        assert "redispassword" not in sanitized
        assert "adminpwd" not in sanitized
        assert "mypassword" not in sanitized
        assert "ghp_1234567890abcdef" not in sanitized
        assert sanitized == expected, f"Expected {expected}, got {sanitized}"


def test_sanitize_uri_query_params():
    url = "https://api.example.com/webhook?token=secret_token_123&api_key=sk_test_456&env=production&debug=true"
    sanitized = Sanitizer.sanitize_uri(url)

    assert "secret_token_123" not in sanitized
    assert "sk_test_456" not in sanitized
    assert "token=%5BREDACTED%5D" in sanitized or "token=[REDACTED]" in sanitized
    assert "api_key=%5BREDACTED%5D" in sanitized or "api_key=[REDACTED]" in sanitized
    assert "env=production" in sanitized
    assert "debug=true" in sanitized


def test_sanitize_uri_malformed_input():
    # Empty, None, and broken URIs should not raise exceptions
    assert Sanitizer.sanitize_uri("") == ""
    assert Sanitizer.sanitize_uri(None) == ""  # type: ignore[arg-type]
    malformed = "not_a_valid_uri_http://user:pass@host"
    res = Sanitizer.sanitize_uri(malformed)
    assert "pass" not in res


def test_sanitize_path_relative_and_privacy():
    base_dir = Path("/home/developer/workspace/my-project")
    sub_file = base_dir / "src" / "index.ts"

    # Within project base -> returns relative POSIX path
    norm = Sanitizer.sanitize_path(sub_file, base=base_dir)
    assert norm == "src/index.ts"

    # User home directory masking
    home = Path.home()
    file_in_home = home / "Documents" / "secret_notes.txt"
    norm_home = Sanitizer.sanitize_path(file_in_home)
    assert norm_home.startswith("<USER_HOME>")
    assert "Documents/secret_notes.txt" in norm_home
