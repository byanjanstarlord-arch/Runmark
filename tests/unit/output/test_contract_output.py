"""Unit tests for contract output renderers."""

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.models.contract import RunmarkContract
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
from runmark.output.contract import render_contract_check, render_contract_show


class TestContractOutput:
    """Tests for terminal rendering of contracts and check results."""

    def test_render_contract_check_pass(self) -> None:
        result = ContractCheckResult(
            status=ContractCheckStatus.PASS,
            contract_version=1,
            project_name="demo-pass",
            checks=[
                ContractCheck(
                    id="runtime.python",
                    category="runtime",
                    title="Python Runtime",
                    status=ContractCheckStatus.PASS,
                    expected="3.12.x",
                    observed="3.12.4",
                    message="Python 3.12.4 satisfies 3.12.x",
                )
            ],
            issues=[],
            summary=ContractCheckSummary(total=1, passed=1, failed=0, unknown=0, skipped=0),
        )
        # Should render without error
        render_contract_check(result)

    def test_render_contract_check_fail_and_unknown(self) -> None:
        issue = DiagnosticIssue(
            code="RUNTIME_NOT_FOUND",
            severity=DiagnosticSeverity.CRITICAL,
            category=DiagnosticCategory.RUNTIME,
            title="Node runtime not found",
            evidence={},
            explanation="Node.js is missing.",
            suggested_action="Install Node.js.",
        )
        warn_issue = DiagnosticIssue(
            code="RUNTIME_VERSION_UNKNOWN",
            severity=DiagnosticSeverity.WARNING,
            category=DiagnosticCategory.RUNTIME,
            title="Ruby version unknown",
            evidence={},
            explanation="Could not detect Ruby version.",
            suggested_action="Check Ruby PATH.",
        )
        result = ContractCheckResult(
            status=ContractCheckStatus.FAIL,
            contract_version=1,
            project_name="demo-fail",
            checks=[
                ContractCheck(
                    id="runtime.node",
                    category="runtime",
                    title="Node Runtime",
                    status=ContractCheckStatus.FAIL,
                    expected=">=18",
                    observed="not installed",
                    message="Node is missing",
                    diagnostic_issue=issue,
                ),
                ContractCheck(
                    id="runtime.ruby",
                    category="runtime",
                    title="Ruby Runtime",
                    status=ContractCheckStatus.UNKNOWN,
                    expected=">=3",
                    observed="unknown",
                    message="Ruby version unknown",
                    diagnostic_issue=warn_issue,
                ),
                ContractCheck(
                    id="service.redis",
                    category="service",
                    title="Redis Service",
                    status=ContractCheckStatus.SKIPPED,
                    expected=">=6 (optional)",
                    observed="stopped",
                    message="Skipped optional service",
                ),
            ],
            issues=[issue, warn_issue],
            summary=ContractCheckSummary(total=3, passed=0, failed=1, unknown=1, skipped=1),
        )
        render_contract_check(result)

    def test_render_contract_show_full(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "project": {"name": "full-demo"},
                "platform": {"os": ["linux", "windows"], "architecture": ["x86_64", "arm64"]},
                "runtime": {"python": "3.12.x", "node": ">=20"},
                "services": {
                    "postgresql": {"version": ">=15", "required": True},
                    "redis": {"version": ">=7", "required": False},
                },
                "environment": {
                    "required": ["DATABASE_URL"],
                    "optional": ["DEBUG"],
                },
                "network": {
                    "ports": {
                        "8000": {"protocol": "tcp", "required": True},
                        "5432": {"protocol": "tcp", "required": False},
                    }
                },
                "containers": {
                    "docker": {"required": True},
                    "compose": {"required": False},
                },
            }
        )
        canonical = ContractCanonicalizer.canonicalize(contract)
        fingerprint = ContractCanonicalizer.compute_fingerprint(contract)
        render_contract_show(contract, canonical, fingerprint)
