"""Network and ports state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class PortState(RunmarkBaseModel):
    """Network port configuration and occupancy."""

    port: int = Field(description="Network port number, e.g. 5432, 6379, 8000")
    service: str = Field(description="Associated service or expected use")
    expected: bool = Field(default=True, description="Whether port is expected by project")
    occupied: bool = Field(default=False, description="Whether port is currently in use/bound")
    status: str = Field(
        default="unknown", description="Port status description, e.g. open, in_use, available"
    )
