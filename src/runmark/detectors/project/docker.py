"""Docker and container project signals detector."""

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus


class DockerProjectDetector(Detector):
    """Detects Dockerfile, Compose files, and containerization signals."""

    @property
    def name(self) -> str:
        return "project_docker"

    @property
    def category(self) -> str:
        return "project"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        containerization: set[str] = set()

        has_dockerfile = (root / "Dockerfile").exists() or (root / "Containerfile").exists()
        has_compose = (
            (root / "compose.yaml").exists()
            or (root / "compose.yml").exists()
            or (root / "docker-compose.yml").exists()
            or (root / "docker-compose.yaml").exists()
        )

        if has_dockerfile:
            containerization.add("docker")
        if has_compose:
            containerization.add("docker-compose")

        if not containerization:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=None,
            )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data={"containerization": sorted(containerization)},
        )
