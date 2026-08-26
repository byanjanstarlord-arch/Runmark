"""Node.js runtime detector."""

import re

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.runtime import RuntimeState
from runmark.utils.commands import safe_run
from runmark.utils.platform import find_executable


class NodeRuntimeDetector(Detector):
    """Detects installed Node.js runtime version."""

    _VERSION_REGEX = re.compile(r"v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

    @property
    def name(self) -> str:
        return "node"

    @property
    def category(self) -> str:
        return "runtimes"

    def detect(self, context: DetectionContext) -> DetectionResult:
        res = safe_run(["node", "--version"], timeout=3.0)

        if res.succeeded:
            match = self._VERSION_REGEX.search(res.stdout)
            if match:
                version = match.group(1)
                exe_path = find_executable("node")
                state = RuntimeState(
                    name="node",
                    installed=True,
                    version=version,
                    status=DetectionStatus.DETECTED,
                    executable_path=exe_path,
                )
                return DetectionResult(
                    name=self.name,
                    category=self.category,
                    status=DetectionStatus.DETECTED,
                    data=state,
                )

        state = RuntimeState(
            name="node",
            installed=False,
            version=None,
            status=DetectionStatus.NOT_FOUND,
            executable_path=None,
        )
        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.NOT_FOUND,
            data=state,
        )
