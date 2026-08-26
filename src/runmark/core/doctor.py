"""Doctor diagnostic engine for synthesizing triage issues and actionable fixes."""

from dataclasses import dataclass, field
from typing import Any

from runmark.core.diff import DiffClassification, DiffSeverity, RunmarkDiff
from runmark.models.runmark import RunmarkState


@dataclass
class DiagnosticIssue:
    """A structured diagnostic issue identified by Runmark Doctor."""

    code: str
    severity: DiffSeverity
    title: str
    evidence: dict[str, Any]
    explanation: str
    suggested_action: str


@dataclass
class DoctorReport:
    """Comprehensive diagnostic report."""

    project_name: str
    fingerprint: str
    issues: list[DiagnosticIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        """Whether there are critical diagnostic issues."""
        return any(i.severity == DiffSeverity.CRITICAL for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Whether there are warning diagnostic issues."""
        return any(i.severity == DiffSeverity.WARNING for i in self.issues)

    @property
    def is_healthy(self) -> bool:
        """Whether the environment is healthy without criticals or warnings."""
        return not self.has_critical and not self.has_warnings


class Doctor:
    """Synthesizes diagnostic triage issues from scan states and diffs."""

    @classmethod
    def diagnose_state(cls, state: RunmarkState) -> DoctorReport:
        """Diagnose issues directly from a single scan state (e.g. missing required env vars, missing runtimes)."""
        issues: list[DiagnosticIssue] = []

        # 1. Check missing required environment variables
        for var_name, var_state in state.environment.variables.items():
            if var_state.required and not var_state.present:
                issues.append(
                    DiagnosticIssue(
                        code="ENV_MISSING_REQUIRED",
                        severity=DiffSeverity.CRITICAL,
                        title="Required environment variable missing",
                        evidence={
                            "variable": var_name,
                            "expected": "present",
                            "actual": "missing",
                            "source": var_state.source,
                        },
                        explanation=f"The project configuration ({var_state.source}) marks '{var_name}' as required, but it is not set in the active environment.",
                        suggested_action=f"Add '{var_name}' to your local environment or .env file (secret values are never stored or tracked by Runmark).",
                    )
                )

        # 2. Check runtimes required by project languages
        if "python" in state.project.languages:
            py_rt = state.runtimes.get("python")
            if not py_rt or not py_rt.installed:
                issues.append(
                    DiagnosticIssue(
                        code="RUNTIME_PYTHON_MISSING",
                        severity=DiffSeverity.CRITICAL,
                        title="Python runtime missing",
                        evidence={"runtime": "python", "status": "not_found"},
                        explanation="This project contains Python manifests (e.g. pyproject.toml or requirements.txt), but Python is not installed or accessible in PATH.",
                        suggested_action="Install Python >= 3.10 and ensure the 'python' executable is available in your PATH.",
                    )
                )

        if "javascript" in state.project.languages or "typescript" in state.project.languages:
            node_rt = state.runtimes.get("node")
            if not node_rt or not node_rt.installed:
                issues.append(
                    DiagnosticIssue(
                        code="RUNTIME_NODE_MISSING",
                        severity=DiffSeverity.CRITICAL,
                        title="Node.js runtime missing",
                        evidence={"runtime": "node", "status": "not_found"},
                        explanation="This project contains Node.js manifests (package.json), but Node.js is not installed or accessible in PATH.",
                        suggested_action="Install Node.js (e.g. via nvm, fnm, or official installer).",
                    )
                )

        if "docker" in state.project.containerization:
            docker_rt = state.runtimes.get("docker")
            if not docker_rt or not docker_rt.installed:
                issues.append(
                    DiagnosticIssue(
                        code="RUNTIME_DOCKER_MISSING",
                        severity=DiffSeverity.WARNING,
                        title="Docker runtime not found",
                        evidence={"runtime": "docker", "status": "not_found"},
                        explanation="This project contains Docker/Compose configuration, but Docker CLI is not installed or accessible.",
                        suggested_action="Install Docker Desktop or Docker Engine if you intend to run containerized services.",
                    )
                )

        # 3. Check services configured in compose that are not running
        for svc in state.services:
            if svc.expected_version and not svc.running:
                issues.append(
                    DiagnosticIssue(
                        code=f"SERVICE_{svc.name.upper()}_STOPPED",
                        severity=DiffSeverity.WARNING,
                        title=f"{svc.name.capitalize()} service is not running",
                        evidence={
                            "service": svc.name,
                            "port": svc.port,
                            "expected_version": svc.expected_version,
                            "running": False,
                        },
                        explanation=f"Project Docker Compose defines '{svc.name}', but no active instance is listening on port {svc.port}.",
                        suggested_action=f"Start {svc.name} using 'docker compose up -d {svc.name}' or run local {svc.name} service.",
                    )
                )

        return DoctorReport(
            project_name=state.project.name,
            fingerprint=state.runmark.environment_fingerprint,
            issues=issues,
        )

    @classmethod
    def diagnose_diff(cls, diff: RunmarkDiff) -> DoctorReport:
        """Diagnose issues from a diff against an expected baseline."""
        issues: list[DiagnosticIssue] = []

        for item in diff.environment_items:
            if item.classification == DiffClassification.UNCHANGED:
                continue

            if item.category == "environment" and item.severity == DiffSeverity.CRITICAL:
                issues.append(
                    DiagnosticIssue(
                        code="DIFF_ENV_MISSING",
                        severity=DiffSeverity.CRITICAL,
                        title="Required environment variable missing",
                        evidence={
                            "variable": item.item_name,
                            "expected": str(item.old_value),
                            "actual": str(item.new_value),
                        },
                        explanation=item.description,
                        suggested_action=f"Add '{item.item_name}' to your local environment.",
                    )
                )
            elif item.category == "runtime" and item.severity == DiffSeverity.CRITICAL:
                issues.append(
                    DiagnosticIssue(
                        code="DIFF_RUNTIME_CRITICAL",
                        severity=DiffSeverity.CRITICAL,
                        title=f"Runtime '{item.item_name}' incompatibility",
                        evidence={
                            "runtime": item.item_name,
                            "expected": str(item.old_value),
                            "actual": str(item.new_value),
                        },
                        explanation=item.description,
                        suggested_action=f"Switch your {item.item_name} runtime to version {item.old_value} to match the project baseline.",
                    )
                )
            elif item.category == "runtime" and item.severity == DiffSeverity.WARNING:
                issues.append(
                    DiagnosticIssue(
                        code="DIFF_RUNTIME_WARNING",
                        severity=DiffSeverity.WARNING,
                        title=f"Runtime '{item.item_name}' version mismatch",
                        evidence={
                            "runtime": item.item_name,
                            "expected": str(item.old_value),
                            "actual": str(item.new_value),
                        },
                        explanation=item.description,
                        suggested_action=f"Consider matching runtime {item.item_name} version {item.old_value}.",
                    )
                )
            elif item.category == "service" and item.severity in {
                DiffSeverity.CRITICAL,
                DiffSeverity.WARNING,
            }:
                issues.append(
                    DiagnosticIssue(
                        code="DIFF_SERVICE_DISCREPANCY",
                        severity=item.severity,
                        title=f"Service '{item.item_name}' discrepancy",
                        evidence={
                            "service": item.item_name,
                            "expected": str(item.old_value),
                            "actual": str(item.new_value),
                        },
                        explanation=item.description,
                        suggested_action=f"Ensure service {item.item_name} matches baseline state ({item.old_value}).",
                    )
                )
            elif item.category == "dependency" and item.severity in {
                DiffSeverity.CRITICAL,
                DiffSeverity.WARNING,
            }:
                issues.append(
                    DiagnosticIssue(
                        code="DIFF_DEPENDENCY_DRIFT",
                        severity=item.severity,
                        title=f"Dependency '{item.item_name}' drift",
                        evidence={
                            "dependency": item.item_name,
                            "expected": str(item.old_value),
                            "actual": str(item.new_value),
                        },
                        explanation=item.description,
                        suggested_action=f"Sync dependencies using your package manager lockfile (expected {item.old_value}).",
                    )
                )

        return DoctorReport(
            project_name=diff.to_id,
            fingerprint=diff.to_fingerprint,
            issues=issues,
        )
