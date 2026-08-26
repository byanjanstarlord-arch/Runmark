"""Environment variables state model."""

from pydantic import Field

from runmark.models.common import RunmarkBaseModel


class EnvironmentVariableState(RunmarkBaseModel):
    """Metadata about a single environment variable requirement (never stores values)."""

    name: str = Field(description="Environment variable name")
    required: bool = Field(
        default=False, description="Whether this variable is required by the project"
    )
    present: bool = Field(
        default=False, description="Whether this variable is set in the current process/environment"
    )
    secret: bool = Field(
        default=False, description="Whether this variable is classified as a secret"
    )
    source: str = Field(
        default="system", description="Source of variable discovery (e.g. .env.example, process)"
    )


class EnvironmentState(RunmarkBaseModel):
    """Environment configuration metadata state."""

    variables: dict[str, EnvironmentVariableState] = Field(
        default_factory=dict,
        description="Map of environment variable names to their state metadata",
    )
