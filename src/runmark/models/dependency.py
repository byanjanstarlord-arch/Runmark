"""Dependency state model."""

from pydantic import Field

from runmark.models.common import DependencyKind, RunmarkBaseModel


class DependencyState(RunmarkBaseModel):
    """Normalized dependency entry."""

    name: str = Field(description="Package or module name (e.g. django, react)")
    manager: str = Field(description="Package manager source (e.g. pip, uv, npm, poetry)")
    declared: str | None = Field(
        default=None, description="Declared version constraint, e.g. '>=5.0,<6'"
    )
    resolved: str | None = Field(default=None, description="Resolved locked version, e.g. '5.0.6'")
    kind: DependencyKind = Field(
        default=DependencyKind.DIRECT, description="Direct, dev, peer, or transitive"
    )
