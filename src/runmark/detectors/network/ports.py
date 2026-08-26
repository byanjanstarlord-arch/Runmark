"""Network ports detector."""

import yaml

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.network import PortState
from runmark.utils.platform import is_port_in_use


class PortDetector(Detector):
    """Detects expected project ports and their current occupancy status."""

    @property
    def name(self) -> str:
        return "network_ports"

    @property
    def category(self) -> str:
        return "network"

    def detect(self, context: DetectionContext) -> DetectionResult:
        expected_ports: dict[int, str] = {}

        # 1. Inspect compose files for mapped ports
        root = context.project_root
        for fname in ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"]:
            fpath = root / fname
            if fpath.exists():
                try:
                    data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "services" in data:
                        for s_name, s_cfg in data["services"].items():
                            if isinstance(s_cfg, dict) and "ports" in s_cfg:
                                for p in s_cfg["ports"]:
                                    port_num = self._parse_port_entry(str(p))
                                    if port_num:
                                        expected_ports[port_num] = s_name
                except Exception:
                    pass

        # 2. Add standard framework defaults if project signals match
        if (root / "manage.py").exists() and 8000 not in expected_ports:
            expected_ports[8000] = "django"
        if (root / "package.json").exists() and 3000 not in expected_ports:
            expected_ports[3000] = "node_dev"

        if not expected_ports:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=[],
            )

        port_states: list[PortState] = []
        for port_num in sorted(expected_ports.keys()):
            svc_name = expected_ports[port_num]
            in_use = is_port_in_use(port_num)
            port_states.append(
                PortState(
                    port=port_num,
                    service=svc_name,
                    expected=True,
                    occupied=in_use,
                    status="in_use" if in_use else "available",
                )
            )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=port_states,
        )

    def _parse_port_entry(self, entry: str) -> int | None:
        try:
            # format: "5432:5432" or "127.0.0.1:5432:5432" or "5432"
            clean = entry.strip().strip("'").strip('"')
            parts = clean.split(":")
            if len(parts) == 1:
                return int(parts[0])
            elif len(parts) == 2:
                return int(parts[0])
            elif len(parts) == 3:
                return int(parts[1])
        except Exception:
            pass
        return None
