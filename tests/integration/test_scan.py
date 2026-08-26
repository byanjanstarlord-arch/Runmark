"""Integration test for full environment scan across fixtures."""

from pathlib import Path

from runmark.core.scanner import Scanner

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_scan_python_project():
    scanner = Scanner(FIXTURES_DIR / "python_project")
    state = scanner.scan()

    assert state.project.name == "python_project"
    assert "python" in state.project.languages
    assert state.runmark.environment_fingerprint
    assert len(state.dependencies) > 0
    assert "STRIPE_SECRET_KEY" in state.environment.variables


def test_scan_node_project():
    scanner = Scanner(FIXTURES_DIR / "node_project")
    state = scanner.scan()

    assert "javascript" in state.project.languages
    assert any(d.name == "express" for d in state.dependencies)


def test_scan_docker_project():
    scanner = Scanner(FIXTURES_DIR / "docker_project")
    state = scanner.scan()

    assert "docker" in state.project.containerization
    assert len(state.containers) > 0
    assert any(c.service_name == "db" for c in state.containers)


def test_scan_mixed_project():
    scanner = Scanner(FIXTURES_DIR / "mixed_project")
    state = scanner.scan()

    assert "python" in state.project.languages
    assert "javascript" in state.project.languages
    assert len(state.containers) > 0
