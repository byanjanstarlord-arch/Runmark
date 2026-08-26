"""System state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class SystemState(RunmarkBaseModel):
    """Host operating system and machine architecture metadata."""

    os_name: str = Field(description="Operating system name, e.g. Linux, Darwin, Windows")
    os_version: str = Field(description="Safe release or version identifier")
    architecture: str = Field(description="CPU architecture, e.g. x86_64, arm64, AMD64")
