"""Container state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class ContainerState(RunmarkBaseModel):
    """Container and compose service definition and status."""

    service_name: str = Field(description="Container or compose service name")
    image: str = Field(description="Container image name")
    tag: str | None = Field(default=None, description="Image version or tag")
    running_status: str = Field(default="defined", description="Current container runtime status")
