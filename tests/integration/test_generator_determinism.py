"""Integration tests verifying deterministic generation of environment contracts."""

from pathlib import Path

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.generator import ContractGenerator


class TestGeneratorDeterminism:
    """Verify that repeated contract generation on identical project sources produces identical canonical contracts."""

    def test_repeated_generation_determinism_50_iterations(self, tmp_path: Path) -> None:
        # Create a rich project structure
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
name = "determinism-project"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0"
]
""",
            encoding="utf-8",
        )
        (tmp_path / "compose.yml").write_text(
            """
services:
  app:
    build: .
    ports:
      - "8080:8080"
  cache:
    image: redis:7
  database:
    image: postgres:16
""",
            encoding="utf-8",
        )
        (tmp_path / ".env.example").write_text(
            """
ZEBRA_VAR=1
ALPHA_VAR=2
BETA_VAR=3
DATABASE_URL=
""",
            encoding="utf-8",
        )

        initial_contract, _ = ContractGenerator.generate(tmp_path)
        initial_json = ContractCanonicalizer.to_json(initial_contract)
        initial_fingerprint = ContractCanonicalizer.fingerprint(initial_contract)

        for _ in range(50):
            contract, _ = ContractGenerator.generate(tmp_path)
            cand_json = ContractCanonicalizer.to_json(contract)
            cand_fingerprint = ContractCanonicalizer.fingerprint(contract)

            assert cand_json == initial_json
            assert cand_fingerprint == initial_fingerprint
