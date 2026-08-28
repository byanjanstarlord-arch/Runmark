"""Pydantic domain models for Runmark environment contracts (runmark.json)."""

from typing import Any

from pydantic import Field, field_validator

from runmark.models.common import RunmarkBaseModel


class ProjectContract(RunmarkBaseModel):
    """Declared project identity requirements."""

    name: str | None = Field(default=None, description="Expected project name")


class PlatformContract(RunmarkBaseModel):
    """Declared OS and architecture compatibility requirements."""

    os: list[str] = Field(default_factory=list, description="Supported operating systems")
    architecture: list[str] = Field(default_factory=list, description="Supported architectures")


class ServiceRequirement(RunmarkBaseModel):
    """Requirement specification for a single backing service."""

    version: str = Field(description="Expected version constraint")
    required: bool = Field(default=True, description="Whether the service is mandatory")


class DependencyContract(RunmarkBaseModel):
    """Declared package dependency requirements by ecosystem."""

    python: dict[str, str] = Field(
        default_factory=dict, description="Python packages and version constraints"
    )
    node: dict[str, str] = Field(
        default_factory=dict, description="Node.js packages and version constraints"
    )


class EnvironmentContract(RunmarkBaseModel):
    """Declared environment variable existence requirements (names only)."""

    required: list[str] = Field(
        default_factory=list, description="Mandatory environment variable names"
    )
    optional: list[str] = Field(
        default_factory=list, description="Optional environment variable names"
    )


class PortRequirement(RunmarkBaseModel):
    """Requirement specification for a network port."""

    protocol: str = Field(default="tcp", description="Protocol: 'tcp' or 'udp'")
    required: bool = Field(default=True, description="Whether port availability is mandatory")


class NetworkContract(RunmarkBaseModel):
    """Declared network and port requirements."""

    ports: dict[str, PortRequirement] = Field(
        default_factory=dict,
        description="Port numbers mapped to port specifications",
    )


class DockerRequirement(RunmarkBaseModel):
    """Docker engine requirement."""

    required: bool = Field(default=True, description="Whether Docker is required")


class ComposeRequirement(RunmarkBaseModel):
    """Docker Compose requirement."""

    required: bool = Field(default=True, description="Whether Docker Compose is required")


class ContainerContract(RunmarkBaseModel):
    """Declared containerization requirements."""

    docker: DockerRequirement | None = Field(default=None, description="Docker requirements")
    compose: ComposeRequirement | None = Field(default=None, description="Compose requirements")


class RunmarkContract(RunmarkBaseModel):
    """Root model for an environment contract definition (runmark.json)."""

    schema_uri: str | None = Field(
        default=None,
        alias="$schema",
        description="Informational schema reference",
    )
    version: int = Field(default=1, description="Contract format version (must be 1)")
    project: ProjectContract = Field(default_factory=ProjectContract)
    platform: PlatformContract = Field(default_factory=PlatformContract)
    runtime: dict[str, str] = Field(
        default_factory=dict, description="Runtimes and version constraints"
    )
    dependencies: DependencyContract = Field(default_factory=DependencyContract)
    services: dict[str, ServiceRequirement] = Field(
        default_factory=dict,
        description="Services mapped to requirements",
    )
    environment: EnvironmentContract = Field(default_factory=EnvironmentContract)
    network: NetworkContract = Field(default_factory=NetworkContract)
    containers: ContainerContract = Field(default_factory=ContainerContract)

    @field_validator("services", mode="before")
    @classmethod
    def _coerce_service_requirements(cls, value: Any) -> Any:
        """Allow service definitions as simple version string shorthand or full objects."""
        if isinstance(value, dict):
            coerced: dict[str, Any] = {}
            for k, v in value.items():
                if isinstance(v, str):
                    coerced[k] = {"version": v, "required": True}
                else:
                    coerced[k] = v
            return coerced
        return value
