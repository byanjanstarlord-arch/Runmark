"""Unit tests for check explain mode and structured diagnostic breakdowns."""

from runmark.models.contract_result import (
    ContractCheck,
    ContractCheckResult,
    ContractCheckStatus,
    ContractCheckSummary,
)
from runmark.models.diagnostic import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticSeverity,
)
from runmark.output.contract import render_contract_check


class TestCheckExplainMode:
    """Test render_contract_check with explain=True for structured breakdowns."""

    def test_explain_rendering_with_issues(self) -> None:
        issue = DiagnosticIssue(
            code="RUNTIME_VERSION_MISMATCH",
            severity=DiagnosticSeverity.CRITICAL,
            category=DiagnosticCategory.RUNTIME,
            title="Python version mismatch",
            evidence={
                "runtime": "python",
                "expected": ">=3.12,<3.13",
                "detected": "3.11.9",
            },
            explanation="The project contract requires a Python 3.12-compatible runtime, but 3.11.9 is currently active.",
            suggested_action="Install or activate Python 3.12 and rerun `runmark check`.",
        )

        check = ContractCheck(
            id="runtime.python",
            category="runtime",
            title="Python Runtime",
            status=ContractCheckStatus.FAIL,
            expected=">=3.12,<3.13",
            observed="3.11.9",
            message="Version mismatch",
            diagnostic_issue=issue,
        )

        result = ContractCheckResult(
            status=ContractCheckStatus.FAIL,
            contract_version=1,
            project_name="demo-app",
            checks=[check],
            issues=[issue],
            summary=ContractCheckSummary(total=1, passed=0, failed=1, unknown=0, skipped=0),
        )

        # Render in normal mode
        render_contract_check(result, explain=False)

        # Render in explain mode
        render_contract_check(result, explain=True)

        assert not result.is_passed
        assert result.issues[0].evidence["detected"] == "3.11.9"
        assert result.issues[0].suggested_action.startswith("Install or activate")
