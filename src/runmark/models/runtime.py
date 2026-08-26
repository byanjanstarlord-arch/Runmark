"""Runtime state model."""

from pydantic import Field

from runmark.models.common import DetectionStatus, RunmarkBaseModel


class RuntimeState(RunmarkBaseModel):
    """Runtime environment state for a specific language or engine."""

    name: str = Field(description="Runtime identifier, e.g. python, node, docker, git")
    installed: bool = Field(default=False, description="Whether runtime is installed")
    version: str | None = Field(default=None, description="Semantic or standard detected version")
    status: DetectionStatus = Field(
        default=DetectionStatus.NOT_FOUND, description="Detector status"
    )
    executable_path: str | None = Field(
        default=None, description="Sanitized executable name or path"
    )
