"""Docker Compose and container state detector."""

import yaml

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.container import ContainerState
from runmark.utils.commands import safe_run


class ContainerDetector(Detector):
    """Detects Docker containers and Docker Compose service configurations without exposing secrets."""

    @property
    def name(self) -> str:
        return "containers_compose"

    @property
    def category(self) -> str:
        return "containers"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        containers: list[ContainerState] = []

        # 1. Query running containers via safe docker command
        running_names: dict[str, str] = {}
        docker_res = safe_run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], timeout=3.0)
        if docker_res.succeeded and docker_res.stdout:
            for line in docker_res.stdout.splitlines():
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    running_names[parts[0].strip().lower()] = parts[1].strip()

        # 2. Parse compose configurations
        for fname in ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"]:
            fpath = root / fname
            if fpath.exists():
                try:
                    data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "services" in data:
                        for s_name, s_cfg in data["services"].items():
                            if isinstance(s_cfg, dict):
                                img = s_cfg.get("image", "custom-build")
                                tag = None
                                if ":" in img:
                                    img_name, tag = img.split(":", 1)
                                else:
                                    img_name = img

                                # Match against running containers
                                status = "defined"
                                for r_name, r_status in running_names.items():
                                    if s_name.lower() in r_name:
                                        status = f"running ({r_status})"
                                        break

                                containers.append(
                                    ContainerState(
                                        service_name=s_name,
                                        image=img_name,
                                        tag=tag,
                                        running_status=status,
                                    )
                                )
                except Exception:
                    pass

        if not containers:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=[],
            )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=containers,
        )
