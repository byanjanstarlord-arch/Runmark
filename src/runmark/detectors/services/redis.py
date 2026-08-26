"""Redis service detector."""

import re

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.service import ServiceState
from runmark.utils.commands import safe_run
from runmark.utils.platform import is_port_in_use


class RedisDetector(Detector):
    """Detects Redis installation, running state, and version."""

    _VERSION_REGEX = re.compile(r"([0-9]+\.[0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

    @property
    def name(self) -> str:
        return "service_redis"

    @property
    def category(self) -> str:
        return "services"

    def detect(self, context: DetectionContext) -> DetectionResult:
        installed = False
        detected_version = None
        port = 6379

        # 1. Check redis-server or redis-cli
        res = safe_run(["redis-server", "--version"], timeout=3.0)
        if not res.succeeded:
            res = safe_run(["redis-cli", "--version"], timeout=3.0)

        if res.succeeded:
            installed = True
            m = self._VERSION_REGEX.search(res.stdout)
            if m:
                detected_version = m.group(1)

        # 2. Check if port 6379 is bound / listening
        running = is_port_in_use(port)

        # 3. Check expected version from compose files if any
        expected_version = self._detect_expected_compose_version(context)

        if not installed and not running and not expected_version:
            state = ServiceState(
                name="redis",
                installed=False,
                running=False,
                detected_version=None,
                expected_version=None,
                status=DetectionStatus.NOT_FOUND,
                port=port,
            )
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_FOUND,
                data=state,
            )

        status = DetectionStatus.DETECTED if (installed or running) else DetectionStatus.NOT_FOUND

        state = ServiceState(
            name="redis",
            installed=installed,
            running=running,
            detected_version=detected_version,
            expected_version=expected_version,
            status=status,
            port=port,
        )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=state,
        )

    def _detect_expected_compose_version(self, context: DetectionContext) -> str | None:
        root = context.project_root
        for fname in ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"]:
            fpath = root / fname
            if fpath.exists():
                try:
                    import yaml

                    data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "services" in data:
                        for _s_name, s_cfg in data["services"].items():
                            if isinstance(s_cfg, dict):
                                img = s_cfg.get("image", "")
                                if "redis" in img:
                                    tag = img.split(":", 1)[1] if ":" in img else None
                                    if tag:
                                        m = re.search(r"([0-9]+(?:\.[0-9]+)?)", tag)
                                        if m:
                                            return m.group(1)
                except Exception:
                    pass
        return None
