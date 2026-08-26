"""Unit tests for secret pattern detection and redaction."""

from runmark.security.redactor import SecretRedactor
from runmark.security.secret_patterns import (
    contains_secret_value,
    is_secret_variable_name,
)


def test_is_secret_variable_name():
    # Names that must be flagged as secrets
    assert is_secret_variable_name("API_KEY") is True
    assert is_secret_variable_name("STRIPE_SECRET_KEY") is True
    assert is_secret_variable_name("AWS_SECRET_ACCESS_KEY") is True
    assert is_secret_variable_name("GITHUB_TOKEN") is True
    assert is_secret_variable_name("DATABASE_PASSWORD") is True
    assert is_secret_variable_name("DB_PASSWD") is True
    assert is_secret_variable_name("JWT_SECRET") is True
    assert is_secret_variable_name("SESSION_KEY") is True
    assert is_secret_variable_name("AUTH_TOKEN") is True

    # Safe variable names
    assert is_secret_variable_name("PORT") is False
    assert is_secret_variable_name("DEBUG") is False
    assert is_secret_variable_name("ENVIRONMENT") is False
    assert is_secret_variable_name("NODE_ENV") is False
    assert is_secret_variable_name("APP_NAME") is False


def test_contains_secret_value():
    assert contains_secret_value("ghp_1234567890abcdefghijklmnopqrstuvwxyzAB") is True
    assert contains_secret_value("sk-proj-1234567890abcdef1234567890") is True
    assert contains_secret_value("-----BEGIN RSA PRIVATE KEY-----\nMIIEow...") is True
    assert contains_secret_value("AKIAIOSFODNN7EXAMPLE") is True
    assert contains_secret_value("regular_non_secret_string_123") is False


def test_redact_env_variable_never_stores_value():
    state = SecretRedactor.redact_env_variable(
        name="STRIPE_SECRET_KEY",
        value="stripe_test_placeholder_value",
        required=True,
        present=True,
        source=".env",
    )

    assert state.name == "STRIPE_SECRET_KEY"
    assert state.secret is True
    assert state.present is True
    assert state.required is True
    # The actual secret string value is not a property of the model!
    assert not hasattr(state, "value")
    data = state.model_dump(mode="json")
    assert "sk_live" not in str(data)
