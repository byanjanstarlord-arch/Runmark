"""Export security boundary and final sanitization layer for shareable reports."""

from pathlib import Path

from runmark.models.diagnostic import DiagnosticIssue, DiagnosticReport
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.security.redactor import SecretRedactor
from runmark.security.sanitizer import Sanitizer
from runmark.security.secret_patterns import contains_secret_value


class SecurityViolationError(Exception):
    """Raised when sensitive data or unredacted credentials are detected at the export boundary."""

    pass


class ExportSanitizer:
    """Sanitizes DiagnosticReport objects and enforces the export security boundary."""

    @classmethod
    def sanitize_report(
        cls,
        report: DiagnosticReport,
        base_path: Path | None = None,
    ) -> DiagnosticReport:
        """Perform deep export sanitization on all models within a DiagnosticReport."""
        # 1. Sanitize Project State
        clean_project = ProjectState(
            name=report.project.name,
            root=Sanitizer.sanitize_path(report.project.root, base=base_path),
            languages=list(report.project.languages),
            frameworks=list(report.project.frameworks),
            package_managers=list(report.project.package_managers),
            containerization=list(report.project.containerization),
        )

        # 2. Sanitize Git State
        clean_git = GitState(
            is_repository=report.git.is_repository,
            branch=report.git.branch,
            commit=report.git.commit,
            dirty=report.git.dirty,
        )

        # 3. Sanitize Runtimes (sanitize any local executable paths)
        clean_runtimes: dict[str, RuntimeState] = {}
        for rt_name, rt in report.runtimes.items():
            clean_path = None
            if rt.executable_path:
                clean_path = Sanitizer.sanitize_path(rt.executable_path, base=base_path)
            clean_runtimes[rt_name] = RuntimeState(
                name=rt.name,
                installed=rt.installed,
                version=rt.version,
                executable_path=clean_path,
                status=rt.status,
            )

        # 4. Sanitize Services
        clean_services: list[ServiceState] = []
        for svc in report.services:
            clean_services.append(
                ServiceState(
                    name=svc.name,
                    installed=svc.installed,
                    running=svc.running,
                    detected_version=svc.detected_version,
                    expected_version=svc.expected_version,
                    status=svc.status,
                    port=svc.port,
                )
            )

        # 5. Sanitize Environment Variables (strictly metadata only)
        clean_env_vars: dict[str, EnvironmentVariableState] = {}
        for k, v in report.environment.variables.items():
            clean_env_vars[k] = EnvironmentVariableState(
                name=v.name,
                required=v.required,
                present=v.present,
                secret=v.secret,
                source=v.source,
            )
        clean_environment = EnvironmentState(variables=clean_env_vars)

        # 6. Sanitize Diagnostics
        clean_diagnostics: list[DiagnosticIssue] = []
        for diag in report.diagnostics:
            clean_evidence = SecretRedactor.sanitize_dictionary(diag.evidence)
            # Ensure any URIs or paths in evidence values are sanitized
            for ek, ev in list(clean_evidence.items()):
                if isinstance(ev, str):
                    if "://" in ev:
                        clean_evidence[ek] = Sanitizer.sanitize_uri(ev)
                    elif "/" in ev or "\\" in ev:
                        clean_evidence[ek] = Sanitizer.sanitize_path(ev, base=base_path)

            clean_diagnostics.append(
                DiagnosticIssue(
                    code=diag.code,
                    severity=diag.severity,
                    category=diag.category,
                    title=SecretRedactor.redact_text(diag.title),
                    evidence=clean_evidence,
                    explanation=SecretRedactor.redact_text(diag.explanation),
                    suggested_action=SecretRedactor.redact_text(diag.suggested_action),
                )
            )

        return DiagnosticReport(
            metadata=report.metadata,
            project=clean_project,
            system=report.system,
            runtimes=clean_runtimes,
            dependencies=list(report.dependencies),
            services=clean_services,
            environment=clean_environment,
            network=list(report.network),
            containers=list(report.containers),
            git=clean_git,
            diagnostics=clean_diagnostics,
        )

    @classmethod
    def verify_rendered_content_clean(cls, content: str) -> None:
        """Scan rendered content immediately before export.

        Raises SecurityViolationError if any secret pattern or credential is detected.
        """
        if not content:
            return

        if contains_secret_value(content):
            raise SecurityViolationError(
                "Report generation aborted: sensitive data or unredacted credentials "
                "were detected during final export validation."
            )
