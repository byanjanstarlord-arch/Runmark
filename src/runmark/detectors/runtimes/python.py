"""Python runtime detector."""

import re

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.runtime import RuntimeState
from runmark.utils.commands import safe_run
from runmark.utils.platform import find_executable


class PythonRuntimeDetector(Detector):
    """Detects installed Python runtime version."""

    _VERSION_REGEX = re.compile(r"Python\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

    @property
    def name(self) -> str:
        return "python"

    @property
    def category(self) -> str:
        return "runtimes"

    def detect(self, context: DetectionContext) -> DetectionResult:
        # Candidates in order of preference
        candidates = [["python", "--version"], ["python3", "--version"], ["py", "-3", "--version"]]

        for cmd in candidates:
            res = safe_run(cmd, timeout=3.0)
            output = f"{res.stdout} {res.stderr}".strip()
            match = self._VERSION_REGEX.search(output)
            if match:
                version = match.group(1)
                exe_path = find_executable(cmd[0])
                state = RuntimeState(
                    name="python",
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
            name="python",
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
