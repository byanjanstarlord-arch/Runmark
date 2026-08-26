"""Unit tests for dependency manifest and lockfile detectors."""

from pathlib import Path

from runmark.detectors.base import DetectionContext
from runmark.detectors.dependencies.node import NodeDependencyDetector
from runmark.detectors.dependencies.python import PythonDependencyDetector
from runmark.models.common import DependencyKind, DetectionStatus

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_python_requirements_parsed(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("django>=5.0,<6.0\nrequests==2.31.0\n# comment\n", encoding="utf-8")

    detector = PythonDependencyDetector()
    context = DetectionContext(project_root=tmp_path)
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    deps = {d.name: d for d in res.data}
    assert "django" in deps
    assert deps["django"].declared == ">=5.0,<6.0"
    assert "requests" in deps
    assert deps["requests"].declared == "==2.31.0"


def test_python_pyproject_dependencies_parsed(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "my-app"
dependencies = [
    "fastapi>=0.110.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]
""",
        encoding="utf-8",
    )

    detector = PythonDependencyDetector()
    context = DetectionContext(project_root=tmp_path)
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    deps = {d.name: d for d in res.data}
    assert "fastapi" in deps
    assert deps["fastapi"].declared == ">=0.110.0"
    assert deps["fastapi"].kind == DependencyKind.DIRECT
    assert "pytest" in deps
    assert deps["pytest"].kind == DependencyKind.DEV


def test_python_lockfile_resolution_preferred():
    detector = PythonDependencyDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "python_project")
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    deps = {d.name: d for d in res.data}
    assert "django" in deps
    assert deps["django"].declared == ">=5.0,<6.0"
    assert deps["django"].resolved == "5.0.6"  # From uv.lock!


def test_poetry_lock_parsed(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry.dependencies]\npython = "^3.12"\nflask = "^3.0.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "poetry.lock").write_text(
        '[[package]]\nname = "flask"\nversion = "3.0.3"\n',
        encoding="utf-8",
    )
    detector = PythonDependencyDetector()
    res = detector.detect(DetectionContext(project_root=tmp_path))
    deps = {d.name: d for d in res.data}
    assert "flask" in deps
    assert deps["flask"].resolved == "3.0.3"


def test_yarn_lock_parsed(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"lodash": "^4.17.21"}}', encoding="utf-8"
    )
    (tmp_path / "yarn.lock").write_text('lodash@^4.17.21:\n  version "4.17.21"\n', encoding="utf-8")

    detector = NodeDependencyDetector()
    res = detector.detect(DetectionContext(project_root=tmp_path))
    deps = {d.name: d for d in res.data}
    assert "lodash" in deps
    assert deps["lodash"].resolved == "4.17.21"


def test_pnpm_lock_parsed(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"axios": "^1.7.2"}}', encoding="utf-8"
    )
    (tmp_path / "pnpm-lock.yaml").write_text(
        'lockfileVersion: "9.0"\npackages:\n  axios@1.7.2:\n    resolution: {integrity: sha512-...}\n',
        encoding="utf-8",
    )

    detector = NodeDependencyDetector()
    res = detector.detect(DetectionContext(project_root=tmp_path))
    deps = {d.name: d for d in res.data}
    assert "axios" in deps
    assert deps["axios"].resolved == "1.7.2"


def test_node_dependencies_parsed():
    detector = NodeDependencyDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "node_project")
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    deps = {d.name: d for d in res.data}
    assert "express" in deps
    assert deps["express"].declared == "^4.19.2"
    assert deps["express"].resolved == "4.19.2"  # From package-lock.json!
    assert "typescript" in deps
    assert deps["typescript"].kind == DependencyKind.DEV
