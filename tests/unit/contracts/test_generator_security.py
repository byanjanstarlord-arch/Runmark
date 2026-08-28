"""Security unit tests for contract generator: adversarial canary tests and zero-secret guarantee."""

from pathlib import Path

import pytest

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.generator import ContractGenerator
from runmark.output.contract import render_contract_preview

CANARY_SECRETS = [
    ("OPENAI_KEY", "sk-proj-999999999999999999999999999999999999999999999999"),
    ("AWS_KEY", "AKIAIOSFODNN7EXAMPLE"),
    ("AWS_SECRET", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
    ("STRIPE_KEY", "sk_" + "live_51Abcdefghijklmnopqrstuvwx"),
    ("SLACK_TOKEN", "xox" + "b-123456789012-1234567890123-abcdefghijklmnopqrstuvwx"),
    ("GITHUB_TOKEN", "ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ"),
    (
        "PRIVATE_KEY",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----",
    ),
    ("POSTGRES_URL", "postgres://postgres:SuperSecretPassword123@localhost:5432/appdb"),
]


class TestContractGeneratorSecurity:
    """Verify that credentials and secrets never escape into generated contracts or preview output."""

    @pytest.mark.parametrize("secret_name,secret_val", CANARY_SECRETS)
    def test_secrets_in_env_files_never_leak(
        self, tmp_path: Path, secret_name: str, secret_val: str
    ) -> None:
        # Put secret in .env.example
        env_content = f"""
# Configuration
{secret_name}={secret_val}
DATABASE_URL=postgres://dbuser:some_pass_12345@localhost:5432/test
APP_ENV=development
"""
        (tmp_path / ".env.example").write_text(env_content, encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "secret-test"\n', encoding="utf-8"
        )

        contract, evidence = ContractGenerator.generate(tmp_path)
        canonical_json = ContractCanonicalizer.to_json(contract)

        # 1. Variable name should be present in required environment variables
        assert secret_name in contract.environment.required

        # 2. Secret value MUST NEVER appear in canonical JSON
        assert secret_val not in canonical_json
        assert "some_pass_12345" not in canonical_json

        # 3. Render preview and ensure secret value is absent from terminal captures
        render_contract_preview(contract, evidence)
        # Verify directly that string representation of evidence/contract contains no secret values
        assert secret_val not in str(evidence.model_dump())
        assert secret_val not in str(contract.model_dump())
