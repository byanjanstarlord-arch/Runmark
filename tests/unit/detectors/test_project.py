"""Unit tests for project signal detectors."""

from pathlib import Path

from runmark.detectors.base import DetectionContext
from runmark.detectors.project.docker import DockerProjectDetector
from runmark.detectors.project.node import NodeProjectDetector
from runmark.detectors.project.python import PythonProjectDetector
from runmark.models.common import DetectionStatus

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_python_project_detected_from_pyproject():
    detector = PythonProjectDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "python_project")
    res = detector.detect(context)
    assert res.status == DetectionStatus.DETECTED
    assert "python" in res.data["languages"]
    assert "django" in res.data["frameworks"]


def test_python_project_detected_from_requirements(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("flask>=2.0\n", encoding="utf-8")
    detector = PythonProjectDetector()
    context = DetectionContext(project_root=tmp_path)
    res = detector.detect(context)
    assert res.status == DetectionStatus.DETECTED
    assert "python" in res.data["languages"]
    assert "pip" in res.data["package_managers"]
    assert "flask" in res.data["frameworks"]


def test_node_project_detected_from_package_json():
    detector = NodeProjectDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "node_project")
    res = detector.detect(context)
    assert res.status == DetectionStatus.DETECTED
    assert "javascript" in res.data["languages"]
    assert "typescript" in res.data["languages"]
    assert "react" in res.data["frameworks"]
    assert "express" in res.data["frameworks"]
    assert "npm" in res.data["package_managers"]


def test_docker_project_detected_from_dockerfile():
    detector = DockerProjectDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "docker_project")
    res = detector.detect(context)
    assert res.status == DetectionStatus.DETECTED
    assert "docker" in res.data["containerization"]
    assert "docker-compose" in res.data["containerization"]


def test_docker_compose_detected_from_compose_yaml(tmp_path):
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  redis:\n    image: redis:7\n", encoding="utf-8")
    detector = DockerProjectDetector()
    context = DetectionContext(project_root=tmp_path)
    res = detector.detect(context)
    assert res.status == DetectionStatus.DETECTED
    assert "docker-compose" in res.data["containerization"]
