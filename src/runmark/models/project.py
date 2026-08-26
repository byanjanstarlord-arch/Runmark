"""Project state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class ProjectState(RunmarkBaseModel):
    """Normalized project characteristics."""

    name: str = Field(description="Project name or root folder name")
    root: str = Field(description="Project root relative path or normalized name")
    languages: list[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: list[str] = Field(default_factory=list, description="Detected frameworks")
    package_managers: list[str] = Field(
        default_factory=list, description="Detected package managers"
    )
    containerization: list[str] = Field(
        default_factory=list, description="Detected container mechanisms"
    )
