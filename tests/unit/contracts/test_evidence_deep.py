"""Deep unit tests for evidence collection edge cases."""

from pathlib import Path

from runmark.contracts.evidence import EvidenceCollector


class TestEvidenceDeep:
    """Test poetry, Pipfile, Dockerfile, and Compose variants."""

    def test_collect_poetry_manifest(self, tmp_path: Path) -> None:
        pyproject_content = """
[tool.poetry]
name = "poetry-app"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.project_name == "poetry-app"
        assert evidence.runtimes.get("python") == "^3.11"
        assert "requests" in evidence.dependencies.get("python", {})

    def test_collect_dockerfile_node(self, tmp_path: Path) -> None:
        dockerfile_content = """
FROM node:20-alpine
WORKDIR /app
COPY . .
EXPOSE 3000/tcp
CMD ["npm", "start"]
"""
        (tmp_path / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.containers.get("docker") is True
        assert evidence.runtimes.get("node") == ">=20"
        assert "3000" in evidence.ports

    def test_collect_node_version_file(self, tmp_path: Path) -> None:
        (tmp_path / ".node-version").write_text("v18.17.0\n", encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.runtimes.get("node") == ">=18"

    def test_collect_nvmrc_file(self, tmp_path: Path) -> None:
        (tmp_path / ".nvmrc").write_text("20.10.0\n", encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.runtimes.get("node") == ">=20"

    def test_collect_env_dist_and_template(self, tmp_path: Path) -> None:
        (tmp_path / ".env.dist").write_text("DIST_VAR=123\n", encoding="utf-8")
        (tmp_path / ".env.template").write_text("TEMPLATE_VAR=abc\n", encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert "DIST_VAR" in evidence.required_env_vars
        assert "TEMPLATE_VAR" in evidence.required_env_vars

    def test_collect_dockerfile_python(self, tmp_path: Path) -> None:
        dockerfile = """
FROM python:3.11-slim
WORKDIR /src
EXPOSE 8080 9090
"""
        (tmp_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")
        evidence = EvidenceCollector.collect(tmp_path)
        assert evidence.runtimes.get("python") == ">=3.11"
        assert "8080" in evidence.ports
        assert "9090" in evidence.ports
