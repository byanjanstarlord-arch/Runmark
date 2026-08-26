"""Service state model."""

from pydantic import Field

from runmark.models.common import DetectionStatus, RunmarkBaseModel


class ServiceState(RunmarkBaseModel):
    """Local service status (e.g. PostgreSQL, Redis)."""

    name: str = Field(description="Service name, e.g. postgresql, redis")
    installed: bool = Field(default=False, description="Whether service CLI or binary is installed")
    running: bool = Field(default=False, description="Whether service instance is actively running")
    detected_version: str | None = Field(default=None, description="Detected service version")
    expected_version: str | None = Field(
        default=None, description="Expected service version from compose or config"
    )
    status: DetectionStatus = Field(
        default=DetectionStatus.NOT_FOUND, description="Detector status"
    )
    port: int | None = Field(default=None, description="Standard or configured port")
