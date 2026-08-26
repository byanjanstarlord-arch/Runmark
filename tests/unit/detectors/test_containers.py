"""Unit tests for container detector."""

from pathlib import Path
from unittest.mock import patch

from runmark.detectors.base import DetectionContext
from runmark.detectors.containers.compose import ContainerDetector
from runmark.models.common import DetectionStatus
from runmark.utils.commands import CommandResult

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_compose_containers_detected():
    detector = ContainerDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "docker_project")

    with patch("runmark.detectors.containers.compose.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["docker", "ps"],
            exit_code=0,
            stdout="docker_project-db-1\tUp 2 hours\n",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        cnts = {c.service_name: c for c in res.data}
        assert "db" in cnts
        assert cnts["db"].image == "postgres"
        assert cnts["db"].tag == "16-alpine"
        assert "running" in cnts["db"].running_status
        assert "redis" in cnts
        assert cnts["redis"].tag == "7-alpine"
