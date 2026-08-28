"""Diagnostic domain models for Runmark issues and shareable reports."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

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


class DiagnosticSeverity(str, Enum):
    """Severity classification for diagnostic issues."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class DiagnosticCategory(str, Enum):
    """Categorical classification of diagnostic issues."""

    RUNTIME = "runtime"
    DEPENDENCY = "dependency"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    NETWORK = "network"
    CONTAINER = "container"
    SYSTEM = "system"
    GIT = "git"
    SECURITY = "security"
    GENERAL = "general"


class DiagnosticIssue(RunmarkBaseModel):
    """A structured, evidence-backed diagnostic issue identified by Runmark."""

    code: str = Field(description="Machine-readable stable issue code, e.g. RUNTIME_PYTHON_MISSING")
    severity: DiagnosticSeverity = Field(description="Severity level (INFO, WARNING, or CRITICAL)")
    category: DiagnosticCategory = Field(
        default=DiagnosticCategory.GENERAL,
        description="System domain category of the issue",
    )
    title: str = Field(description="Short human-readable title of the issue")
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="Observed concrete facts supporting this diagnostic finding",
    )
    explanation: str = Field(description="Logical reasoning explaining the discrepancy or risk")
    suggested_action: str = Field(
        description="Read-only actionable recommendation to resolve the issue"
    )


class ReportMetadata(RunmarkBaseModel):
    """Metadata describing a generated diagnostic report."""

    report_id: str = Field(
        default_factory=lambda: f"rpt_{uuid.uuid4().hex[:12]}",
        description="Safe unique report identifier (does not affect environment fingerprint)",
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of report generation",
    )
    runmark_version: str = Field(
        default=__version__, description="Runmark package version used to generate report"
    )
    schema_version: str = Field(
        default=__schema_version__, description="Runmark core state schema version"
    )
    report_format_version: int = Field(
        default=1, description="Format version of the diagnostic report"
    )
    environment_fingerprint: str = Field(
        description="Deterministic SHA-256 fingerprint of the environment"
    )
    summary: str = Field(default="", description="High-level human-readable health summary")


class DiagnosticReport(RunmarkBaseModel):
    """A complete, sanitized, portable diagnostic report ready for sharing."""

    metadata: ReportMetadata = Field(description="Report metadata and timestamps")
    project: ProjectState = Field(description="Project signals and characteristics")
    system: SystemState = Field(description="Operating system and CPU architecture")
    runtimes: dict[str, RuntimeState] = Field(
        default_factory=dict, description="Detected runtime environments"
    )
    dependencies: list[DependencyState] = Field(
        default_factory=list, description="Project dependencies"
    )
    services: list[ServiceState] = Field(default_factory=list, description="Local backing services")
    environment: EnvironmentState = Field(
        default_factory=EnvironmentState,
        description="Environment variable requirements and presence (strictly zero secret values)",
    )
    network: list[PortState] = Field(
        default_factory=list, description="Network port occupancy and status"
    )
    containers: list[ContainerState] = Field(
        default_factory=list, description="Container and Compose configurations"
    )
    git: GitState = Field(description="Git repository state")
    diagnostics: list[DiagnosticIssue] = Field(
        default_factory=list, description="List of structured diagnostic findings"
    )

    @property
    def has_critical(self) -> bool:
        """Whether there are critical diagnostic issues in the report."""
        return any(d.severity == DiagnosticSeverity.CRITICAL for d in self.diagnostics)

    @property
    def has_warnings(self) -> bool:
        """Whether there are warning diagnostic issues in the report."""
        return any(d.severity == DiagnosticSeverity.WARNING for d in self.diagnostics)

    @property
    def is_healthy(self) -> bool:
        """Whether the reported environment is completely healthy without issues."""
        return not self.has_critical and not self.has_warnings
