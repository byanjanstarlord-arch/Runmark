"""Unit tests for services detectors (PostgreSQL, Redis)."""

from pathlib import Path
from unittest.mock import patch

from runmark.detectors.base import DetectionContext
from runmark.detectors.services.postgres import PostgresDetector
from runmark.detectors.services.redis import RedisDetector
from runmark.models.common import DetectionStatus
from runmark.utils.commands import CommandResult

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_postgres_detector_from_compose(tmp_path):
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  db:\n    image: postgres:16.3-alpine\n", encoding="utf-8")

    detector = PostgresDetector()
    context = DetectionContext(project_root=tmp_path)

    with (
        patch("runmark.detectors.services.postgres.safe_run") as mock_run,
        patch("runmark.detectors.services.postgres.is_port_in_use", return_value=True),
    ):
        mock_run.return_value = CommandResult(
            command=["psql", "--version"],
            exit_code=0,
            stdout="psql (PostgreSQL) 16.3",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.running is True
        assert res.data.detected_version == "16.3"
        assert res.data.expected_version == "16.3"


def test_redis_detector_from_compose(tmp_path):
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  cache:\n    image: redis:7.2\n", encoding="utf-8")

    detector = RedisDetector()
    context = DetectionContext(project_root=tmp_path)

    with (
        patch("runmark.detectors.services.redis.safe_run") as mock_run,
        patch("runmark.detectors.services.redis.is_port_in_use", return_value=False),
    ):
        mock_run.return_value = CommandResult(
            command=["redis-server", "--version"],
            exit_code=0,
            stdout="Redis server v=7.2.4 sha=00000000:0",
            stderr="",
        )
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.installed is True
        assert res.data.running is False
        assert res.data.detected_version == "7.2.4"
        assert res.data.expected_version == "7.2"
