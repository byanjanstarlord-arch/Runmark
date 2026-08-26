"""Unit tests for runtime detectors."""

from unittest.mock import patch

from runmark.detectors.base import DetectionContext
from runmark.detectors.runtimes.docker import DockerRuntimeDetector
from runmark.detectors.runtimes.git import GitRuntimeDetector
from runmark.detectors.runtimes.node import NodeRuntimeDetector
from runmark.detectors.runtimes.python import PythonRuntimeDetector
from runmark.models.common import DetectionStatus
from runmark.utils.commands import CommandResult


def test_python_version_parsed_correctly(tmp_path):
    detector = PythonRuntimeDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.python.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["python", "--version"],
            exit_code=0,
            stdout="Python 3.12.4",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.version == "3.12.4"


def test_python_missing_returns_not_found(tmp_path):
    detector = PythonRuntimeDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.python.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["python", "--version"],
            exit_code=127,
            stdout="",
            stderr="Executable not found",
            not_found=True,
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.NOT_FOUND
        assert res.data.installed is False
        assert res.data.version is None


def test_node_version_parsed_correctly(tmp_path):
    detector = NodeRuntimeDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.node.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["node", "--version"],
            exit_code=0,
            stdout="v22.5.1\n",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.version == "22.5.1"


def test_docker_version_parsed_correctly(tmp_path):
    detector = DockerRuntimeDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.docker.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["docker", "--version"],
            exit_code=0,
            stdout="Docker version 28.0.1, build 068a01e",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.version == "28.0.1"


def test_git_runtime_version_parsed_correctly(tmp_path):
    detector = GitRuntimeDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.git.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["git", "--version"],
            exit_code=0,
            stdout="git version 2.44.0.windows.1",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.version == "2.44.0"
