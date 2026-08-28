"""Unit tests for project evidence discovery and signal extraction."""

import json
from pathlib import Path

from runmark.contracts.evidence import (
    EvidenceCollector,
)


class TestEvidenceCollector:
    """Test discovery and signal classification from project manifests."""

    def test_collect_python_project(self, tmp_path: Path) -> None:
        # Create pyproject.toml
        pyproject_content = """
[project]
name = "my-backend-app"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0"
]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
        (tmp_path / ".python-version").write_text("3.12.4\n", encoding="utf-8")

        evidence = EvidenceCollector.collect(tmp_path)

        assert evidence.project_name == "my-backend-app"
        assert evidence.runtimes.get("python") == ">=3.12"
        assert "fastapi" in evidence.dependencies.get("python", {})
        assert evidence.dependencies["python"]["fastapi"] == ">=0.109.0"

        # Verify evidence signals recorded
        sig_names = [s.name for s in evidence.signals]
        assert "python_runtime" in sig_names
        assert "python_project" in sig_names

    def test_collect_node_project(self, tmp_path: Path) -> None:
        pkg_data = {
            "name": "frontend-ui",
            "engines": {"node": ">=20.0.0"},
            "dependencies": {
                "react": "^18.2.0",
                "next": "^14.1.0",
            },
        }
        (tmp_path / "package.json").write_text(json.dumps(pkg_data), encoding="utf-8")
        (tmp_path / ".nvmrc").write_text("20\n", encoding="utf-8")

        evidence = EvidenceCollector.collect(tmp_path)

        assert evidence.project_name == "frontend-ui"
        assert evidence.runtimes.get("node") == ">=20.0.0"
        assert "react" in evidence.dependencies.get("node", {})
        assert evidence.dependencies["node"]["react"] == "^18.2.0"

    def test_collect_docker_compose_services(self, tmp_path: Path) -> None:
        compose_content = """
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
  cache:
    image: redis:7.2
"""
        (tmp_path / "compose.yml").write_text(compose_content, encoding="utf-8")

        evidence = EvidenceCollector.collect(tmp_path)

        assert evidence.containers.get("docker") is True
        assert evidence.containers.get("compose") is True
        assert "postgresql" in evidence.services
        assert "redis" in evidence.services
        assert "8000" in evidence.ports
        assert "5432" in evidence.ports

    def test_collect_env_template_variables(self, tmp_path: Path) -> None:
        env_example = """
# Database Configuration
DATABASE_URL=postgres://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379/0

# Secrets (Presence Only)
export SECRET_KEY=changeme-super-secret-key-12345
export API_KEY=sk-test-key-mock
PORT=8000
"""
        (tmp_path / ".env.example").write_text(env_example, encoding="utf-8")

        evidence = EvidenceCollector.collect(tmp_path)

        assert "DATABASE_URL" in evidence.required_env_vars
        assert "REDIS_URL" in evidence.required_env_vars
        assert "SECRET_KEY" in evidence.required_env_vars
        assert "API_KEY" in evidence.required_env_vars
        assert "PORT" in evidence.required_env_vars

        # Ensure no values leaked into evidence
        for var in evidence.required_env_vars:
            assert "=" not in var
            assert "changeme" not in var
            assert "sk-test" not in var

    def test_collect_empty_directory(self, tmp_path: Path) -> None:
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.project_name == tmp_path.name
        assert evidence.runtimes == {}
        assert evidence.dependencies == {}
        assert evidence.services == {}
        assert evidence.required_env_vars == []
