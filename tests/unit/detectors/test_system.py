"""Unit tests for system detector."""

from runmark.detectors.base import DetectionContext
from runmark.detectors.system.system import SystemDetector
from runmark.models.common import DetectionStatus


def test_system_detector_returns_detected(tmp_path):
    detector = SystemDetector()
    context = DetectionContext(project_root=tmp_path)
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    assert res.data.os_name
    assert res.data.os_version
    assert res.data.architecture
