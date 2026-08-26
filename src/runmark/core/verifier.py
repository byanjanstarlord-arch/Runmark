"""Verification engine to validate current environment against expected baseline."""

from dataclasses import dataclass, field
from enum import Enum

from runmark.core.diff import DiffEngine, DiffSeverity, RunmarkDiff
from runmark.models.runmark import RunmarkState


class VerificationStatus(str, Enum):
    """Verification outcome status."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class VerificationResult:
    """Result of verifying current state against expected baseline."""

    status: VerificationStatus
    exit_code: int
    diff: RunmarkDiff
    reasons: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Whether verification succeeded (PASS or WARN if non-strict)."""
        return self.exit_code == 0


class Verifier:
    """Validates development environments against Runmark baselines."""

    EXIT_CODE_SUCCESS = 0
    EXIT_CODE_FAILURE = 1
    EXIT_CODE_INVALID_USAGE = 2
    EXIT_CODE_INTERNAL_ERROR = 3
    EXIT_CODE_SECURITY_VIOLATION = 4

    def __init__(self, strict: bool = False):
        self.strict = strict

    def verify(self, expected: RunmarkState, current: RunmarkState) -> VerificationResult:
        """Verify current state against expected baseline snapshot."""
        diff = DiffEngine.compare(expected, current)
        reasons: list[str] = []

        # Check critical environment discrepancies
        for item in diff.environment_items:
            if item.severity == DiffSeverity.CRITICAL:
                reasons.append(f"Critical: {item.description}")

        # Check warnings
        for item in diff.environment_items:
            if item.severity == DiffSeverity.WARNING:
                reasons.append(f"Warning: {item.description}")

        if diff.has_critical:
            return VerificationResult(
                status=VerificationStatus.FAIL,
                exit_code=self.EXIT_CODE_FAILURE,
                diff=diff,
                reasons=reasons,
            )

        if diff.has_warning:
            status = VerificationStatus.FAIL if self.strict else VerificationStatus.WARN
            exit_code = self.EXIT_CODE_FAILURE if self.strict else self.EXIT_CODE_SUCCESS
            return VerificationResult(
                status=status,
                exit_code=exit_code,
                diff=diff,
                reasons=reasons,
            )

        return VerificationResult(
            status=VerificationStatus.PASS,
            exit_code=self.EXIT_CODE_SUCCESS,
            diff=diff,
            reasons=[],
        )
