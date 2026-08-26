"""Git source revision state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class GitState(RunmarkBaseModel):
    """Git repository source control metadata."""

    is_repository: bool = Field(
        default=False, description="Whether project root is a Git repository"
    )
    branch: str | None = Field(default=None, description="Current checked out branch name")
    commit: str | None = Field(default=None, description="Current HEAD commit SHA")
    dirty: bool = Field(default=False, description="Whether working tree has uncommitted changes")
