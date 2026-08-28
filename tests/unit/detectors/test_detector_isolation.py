"""Unit tests for detector failure isolation, missing software, and corrupted project manifests."""

from unittest.mock import patch

from runmark.core.scanner import Scanner
from runmark.detectors.base import DetectionContext, DetectionResult, DetectionStatus, Detector
from runmark.detectors.registry import DetectorRegistry
from runmark.detectors.runtimes.docker import DockerRuntimeDetector
from runmark.detectors.runtimes.node import NodeRuntimeDetector
from runmark.detectors.runtimes.python import PythonRuntimeDetector
from runmark.detectors.services.postgres import PostgresDetector
from runmark.detectors.services.redis import RedisDetector
from runmark.utils.commands import CommandResult


class FailingDetector(Detector):
    """A test detector that unexpectedly raises an exception."""

    @property
    def name(self) -> str:
        return "exploding_detector"

    @property
    def category(self) -> str:
        return "project"

    def detect(self, context: DetectionContext) -> DetectionResult:
        raise RuntimeError("Catastrophic detector explosion!")


def test_scanner_isolates_detector_exception(tmp_path):
    """Verify that an unhandled exception in a single detector does not crash the scan."""
    registry = DetectorRegistry()
    registry.register(FailingDetector())
    registry.register(PythonRuntimeDetector())

    scanner = Scanner(tmp_path, registry=registry)
    state = scanner.scan()

    # The scan must complete successfully and construct a valid RunmarkState
    assert state.project.name == tmp_path.name
    assert "python" in state.runtimes


def test_scanner_handles_malformed_manifests(tmp_path):
    """Verify that corrupt manifests in the project directory are safely handled without crash or corrupted state."""
    # Write broken / invalid syntax files
    (tmp_path / "pyproject.toml").write_text("invalid [toml syntax {{{", encoding="utf-8")
    (tmp_path / "package.json").write_text("{ unclosed json: ", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("invalid: yaml: :\n  - - [", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("\x00\x01\x02\xff", encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "VALID_VAR=123\nINVALID LINE WITHOUT EQUALS\n", encoding="utf-8"
    )

    scanner = Scanner(tmp_path)
    state = scanner.scan()

    # State must construct cleanly
    assert state.runmark.environment_fingerprint is not None
    assert "VALID_VAR" in state.environment.variables


def test_missing_software_returns_not_found(tmp_path):
    """Verify that when runtimes or services are absent, detectors return not_found status instead of error."""
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.runtimes.docker.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["docker", "--version"],
            exit_code=127,
            stdout="",
            stderr="not found",
            not_found=True,
        )
        res_docker = DockerRuntimeDetector().detect(context)
        assert res_docker.status == DetectionStatus.NOT_FOUND
        assert res_docker.data.installed is False

    with patch("runmark.detectors.runtimes.node.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["node", "--version"],
            exit_code=127,
            stdout="",
            stderr="not found",
            not_found=True,
        )
        res_node = NodeRuntimeDetector().detect(context)
        assert res_node.status == DetectionStatus.NOT_FOUND
        assert res_node.data.installed is False

    with (
        patch("runmark.detectors.services.postgres.safe_run") as mock_run,
        patch("runmark.detectors.services.postgres.is_port_in_use", return_value=False),
    ):
        mock_run.return_value = CommandResult(
            command=["postgres", "--version"],
            exit_code=127,
            stdout="",
            stderr="not found",
            not_found=True,
        )
        res_pg = PostgresDetector().detect(context)
        assert res_pg.status == DetectionStatus.NOT_FOUND
        assert res_pg.data.installed is False
        assert res_pg.data.running is False

    with (
        patch("runmark.detectors.services.redis.safe_run") as mock_run,
        patch("runmark.detectors.services.redis.is_port_in_use", return_value=False),
    ):
        mock_run.return_value = CommandResult(
            command=["redis-server", "--version"],
            exit_code=127,
            stdout="",
            stderr="not found",
            not_found=True,
        )
        res_redis = RedisDetector().detect(context)
        assert res_redis.status == DetectionStatus.NOT_FOUND
        assert res_redis.data.installed is False
        assert res_redis.data.running is False
