"""Unit tests for network port detector."""

from pathlib import Path
from unittest.mock import patch

from runmark.detectors.base import DetectionContext
from runmark.detectors.network.ports import PortDetector
from runmark.models.common import DetectionStatus

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def test_network_ports_detected_from_compose():
    detector = PortDetector()
    context = DetectionContext(project_root=FIXTURES_DIR / "docker_project")

    with patch("runmark.detectors.network.ports.is_port_in_use", return_value=True):
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        ports = {p.port: p for p in res.data}
        assert 5432 in ports
        assert ports[5432].service == "db"
        assert ports[5432].occupied is True
        assert 6379 in ports
        assert ports[6379].service == "redis"
        assert 8000 in ports
        assert ports[8000].service == "web"
