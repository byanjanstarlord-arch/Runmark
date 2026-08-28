"""Domain models for contract check evaluations and outcomes."""

from enum import Enum

from pydantic import Field

from runmark.models.common import RunmarkBaseModel
from runmark.models.diagnostic import DiagnosticIssue


class ContractCheckStatus(str, Enum):
    """Evaluation status for individual contract requirements and overall outcomes."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


class ContractCheck(RunmarkBaseModel):
    """Structured result of evaluating a single contract requirement."""

    id: str = Field(
        description="Stable machine-readable identifier (e.g. runtime.python, environment.DATABASE_URL)"
    )
    category: str = Field(
        description="Category domain (e.g. platform, runtime, service, environment, network, container)"
    )
    title: str = Field(description="Human-readable description of the check")
    status: ContractCheckStatus = Field(description="Outcome status of the check")
    expected: str | None = Field(default=None, description="Declared requirement or constraint")
    observed: str | None = Field(
        default=None, description="Actual observed condition in environment"
    )
    message: str | None = Field(default=None, description="Human-readable result explanation")
    diagnostic_issue: DiagnosticIssue | None = Field(
        default=None,
        description="Linked diagnostic issue if check failed or is unknown",
    )


class ContractCheckSummary(RunmarkBaseModel):
    """Aggregate counts of contract check outcomes."""

    total: int = Field(default=0, description="Total number of evaluated checks")
    passed: int = Field(default=0, description="Number of passed checks")
    failed: int = Field(default=0, description="Number of failed checks")
    unknown: int = Field(default=0, description="Number of unknown checks")
    skipped: int = Field(default=0, description="Number of skipped checks")


class ContractCheckResult(RunmarkBaseModel):
    """Complete evaluation report of an environment contract against host state."""

    status: ContractCheckStatus = Field(description="Overall status: FAIL > UNKNOWN > PASS")
    contract_version: int = Field(default=1, description="Evaluated contract format version")
    project_name: str | None = Field(
        default=None, description="Project name from contract or environment"
    )
    checks: list[ContractCheck] = Field(
        default_factory=list, description="List of evaluated individual checks"
    )
    issues: list[DiagnosticIssue] = Field(
        default_factory=list,
        description="Diagnostic issues synthesized from failed or unknown checks",
    )
    summary: ContractCheckSummary = Field(
        default_factory=ContractCheckSummary, description="Outcome count summary"
    )

    @property
    def is_passed(self) -> bool:
        """Whether the entire contract was satisfied."""
        return self.status == ContractCheckStatus.PASS

    @property
    def is_failed(self) -> bool:
        """Whether any mandatory contract requirement failed."""
        return self.status == ContractCheckStatus.FAIL

    @property
    def is_unknown(self) -> bool:
        """Whether any check was inconclusive with no mandatory failures."""
        return self.status == ContractCheckStatus.UNKNOWN
