"""Unit tests for ContractGenerator and candidate contract synthesis."""

import json
from pathlib import Path

from runmark.contracts.generator import ContractGenerator
from runmark.contracts.validator import ContractValidator
from runmark.models.contract import RunmarkContract


class TestContractGenerator:
    """Test generating valid RunmarkContract models from various project structures."""

    def test_generate_full_stack_contract(self, tmp_path: Path) -> None:
        # 1. Python signals
        pyproject = """
[project]
name = "enterprise-api"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.100.0",
    "sqlalchemy>=2.0.0"
]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")

        # 2. Docker & Compose signals
        compose = """
services:
  api:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:16
  redis:
    image: redis:7
"""
        (tmp_path / "docker-compose.yml").write_text(compose, encoding="utf-8")

        # 3. Environment signals
        env_example = """
DATABASE_URL=
REDIS_URL=
APP_SECRET=
"""
        (tmp_path / ".env.example").write_text(env_example, encoding="utf-8")

        contract, evidence = ContractGenerator.generate(tmp_path)

        assert isinstance(contract, RunmarkContract)
        assert contract.version == 1
        assert contract.project.name == "enterprise-api"
        assert contract.runtime.get("python") == ">=3.12"
        assert "postgresql" in contract.services
        assert "redis" in contract.services
        assert "DATABASE_URL" in contract.environment.required
        assert "REDIS_URL" in contract.environment.required
        assert "APP_SECRET" in contract.environment.required
        assert "8000" in contract.network.ports
        assert (
            contract.containers.docker is not None and contract.containers.docker.required is True
        )
        assert (
            contract.containers.compose is not None and contract.containers.compose.required is True
        )

        # Ensure schema & semantic validation pass
        ContractValidator.validate_semantics(contract)

    def test_generate_node_project_contract(self, tmp_path: Path) -> None:
        pkg = {
            "name": "react-web-client",
            "engines": {"node": ">=18"},
            "dependencies": {
                "react": "^18.0.0",
            },
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

        contract, _ = ContractGenerator.generate(tmp_path)

        assert contract.project.name == "react-web-client"
        assert contract.runtime.get("node") == ">=18"
        assert contract.dependencies.node.get("react") == "^18.0.0"
        ContractValidator.validate_semantics(contract)

    def test_generate_empty_project_contract(self, tmp_path: Path) -> None:
        contract, evidence = ContractGenerator.generate(tmp_path)
        assert contract.version == 1
        assert contract.project.name == tmp_path.name
        ContractValidator.validate_semantics(contract)
