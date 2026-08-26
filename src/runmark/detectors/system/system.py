"""Host system detector."""

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.system import SystemState
from runmark.utils.platform import get_os_info


class SystemDetector(Detector):
    """Detects host operating system, version, and CPU architecture."""

    @property
    def name(self) -> str:
        return "system"

    @property
    def category(self) -> str:
        return "system"

    def detect(self, context: DetectionContext) -> DetectionResult:
        try:
            info = get_os_info()
            state = SystemState(
                os_name=info["os_name"],
                os_version=info["os_version"],
                architecture=info["architecture"],
            )
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.DETECTED,
                data=state,
            )
        except Exception as exc:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.ERROR,
                error_message=f"Failed to query system information: {exc}",
            )
