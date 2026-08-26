"""Top-level Runmark state model."""

from datetime import datetime, timezone

from pydantic import Field

from runmark import __schema_version__, __version__
from runmark.models.common import RunmarkBaseModel
from runmark.models.container import ContainerState
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.network import PortState
from runmark.models.project import ProjectState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState


class RunmarkMetadata(RunmarkBaseModel):
    """Metadata describing the Runmark snapshot generation."""

    id: str = Field(description="Unique snapshot identifier, e.g. snap_01HXYZ...")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of snapshot creation",
    )
    tool_version: str = Field(default=__version__, description="Runmark tool version")
    schema_version: str = Field(default=__schema_version__, description="Runmark schema version")
    environment_fingerprint: str = Field(
        default="", description="Deterministic SHA-256 fingerprint of the environment"
    )
    message: str | None = Field(
        default=None, description="Optional user snapshot note or description"
    )


class RunmarkState(RunmarkBaseModel):
    """Complete canonical development environment state representation."""

    runmark: RunmarkMetadata = Field(description="Runmark metadata and fingerprint")
    project: ProjectState = Field(description="Project characteristics and structure")
    git: GitState = Field(description="Git source revision metadata")
    system: SystemState = Field(description="Host OS and hardware architecture")
    runtimes: dict[str, RuntimeState] = Field(
        default_factory=dict, description="Detected runtime environments"
    )
    dependencies: list[DependencyState] = Field(
        default_factory=list, description="Project dependencies"
    )
    services: list[ServiceState] = Field(default_factory=list, description="Local backing services")
    environment: EnvironmentState = Field(
        default_factory=EnvironmentState, description="Environment variable requirements"
    )
    network: list[PortState] = Field(default_factory=list, description="Network ports")
    containers: list[ContainerState] = Field(
        default_factory=list, description="Container and Compose configurations"
    )
