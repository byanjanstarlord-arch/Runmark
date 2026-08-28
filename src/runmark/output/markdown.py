"""Markdown renderer for Runmark Diagnostic Reports."""

from runmark.models.diagnostic import DiagnosticReport, DiagnosticSeverity


class MarkdownRenderer:
    """Renders a DiagnosticReport into clean, GitHub-flavored Markdown."""

    @classmethod
    def render(cls, report: DiagnosticReport) -> str:
        """Transform a sanitized DiagnosticReport into Markdown text."""
        lines: list[str] = []

        # Title
        lines.append("# Runmark Diagnostic Report")
        lines.append("")

        # Metadata Header Table
        lines.append("## Report Information")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| **Report ID** | `{report.metadata.report_id}` |")
        lines.append(f"| **Generated At** | `{report.metadata.generated_at}` |")
        lines.append(f"| **Runmark Version** | `v{report.metadata.runmark_version}` |")
        lines.append(f"| **Schema Version** | `{report.metadata.schema_version}` |")
        lines.append(f"| **Fingerprint** | `{report.metadata.environment_fingerprint}` |")
        if report.metadata.summary:
            lines.append(f"| **Summary** | {report.metadata.summary} |")
        lines.append("")

        # Diagnostics Section
        lines.append("## Diagnostics")
        lines.append("")
        if not report.diagnostics:
            lines.append("> [!NOTE]")
            lines.append(
                "> **No environment issues detected.** All required runtimes, services, and environment configurations are satisfied."
            )
            lines.append("")
        else:
            for issue in report.diagnostics:
                if issue.severity == DiagnosticSeverity.CRITICAL:
                    icon = "🔴"
                    alert = "CRITICAL"
                elif issue.severity == DiagnosticSeverity.WARNING:
                    icon = "🟡"
                    alert = "WARNING"
                else:
                    icon = "🔵"
                    alert = "INFO"

                lines.append(f"### {icon} [{issue.code}] {issue.title}")
                lines.append("")
                lines.append(f"- **Severity**: `{alert}`")
                lines.append(f"- **Category**: `{issue.category.value}`")
                lines.append(f"- **Explanation**: {issue.explanation}")
                lines.append(f"- **Suggested Action**: `{issue.suggested_action}`")
                lines.append("")

                if issue.evidence:
                    lines.append("**Observed Evidence**:")
                    lines.append("")
                    lines.append("| Key | Value |")
                    lines.append("|---|---|")
                    for ek in sorted(issue.evidence.keys()):
                        ev = issue.evidence[ek]
                        lines.append(f"| `{ek}` | `{ev}` |")
                    lines.append("")

        # Project & Host System
        lines.append("## Project & System")
        lines.append("")
        lines.append("| Property | Details |")
        lines.append("|---|---|")
        lines.append(f"| **Project Name** | `{report.project.name}` |")
        lines.append(
            f"| **Languages** | {', '.join(f'`{lang}`' for lang in sorted(report.project.languages)) if report.project.languages else 'none'} |"
        )
        lines.append(
            f"| **Frameworks** | {', '.join(f'`{fw}`' for fw in sorted(report.project.frameworks)) if report.project.frameworks else 'none'} |"
        )
        lines.append(
            f"| **Package Managers** | {', '.join(f'`{pm}`' for pm in sorted(report.project.package_managers)) if report.project.package_managers else 'none'} |"
        )
        lines.append(
            f"| **Containers** | {', '.join(f'`{c}`' for c in sorted(report.project.containerization)) if report.project.containerization else 'none'} |"
        )
        lines.append(f"| **Host OS** | {report.system.os_name} {report.system.os_version} |")
        lines.append(f"| **Architecture** | `{report.system.architecture}` |")
        lines.append("")

        # Runtimes
        lines.append("## Runtimes")
        lines.append("")
        if report.runtimes:
            lines.append("| Runtime | Status | Detected Version |")
            lines.append("|---|---|---|")
            for rt_name in sorted(report.runtimes.keys()):
                rt = report.runtimes[rt_name]
                status_str = "✓ Installed" if rt.installed else "✗ Missing"
                ver_str = f"`{rt.version}`" if rt.version else "-"
                lines.append(f"| **{rt.name.capitalize()}** | {status_str} | {ver_str} |")
            lines.append("")
        else:
            lines.append("*No runtimes detected.*")
            lines.append("")

        # Services
        lines.append("## Backing Services")
        lines.append("")
        if report.services:
            lines.append("| Service | Status | Port | Detected Version | Expected Version |")
            lines.append("|---|---|---|---|---|")
            for svc in sorted(report.services, key=lambda s: s.name):
                status_str = (
                    "✓ Running"
                    if svc.running
                    else ("⚠ Stopped" if svc.installed else "✗ Not Installed")
                )
                port_str = f"`{svc.port}`" if svc.port else "-"
                det_ver = f"`{svc.detected_version}`" if svc.detected_version else "-"
                exp_ver = f"`{svc.expected_version}`" if svc.expected_version else "-"
                lines.append(
                    f"| **{svc.name.capitalize()}** | {status_str} | {port_str} | {det_ver} | {exp_ver} |"
                )
            lines.append("")
        else:
            lines.append("*No local backing services detected.*")
            lines.append("")

        # Environment Variables
        lines.append("## Environment Variables")
        lines.append("")
        if report.environment.variables:
            lines.append("| Variable | Required | Present | Secret | Source |")
            lines.append("|---|---|---|---|---|")
            for v_name in sorted(report.environment.variables.keys()):
                var = report.environment.variables[v_name]
                req_str = "Yes" if var.required else "No"
                pres_str = "✓ Present" if var.present else "✗ Missing"
                sec_str = "Yes (redacted)" if var.secret else "No"
                src_str = f"`{var.source}`" if var.source else "-"
                lines.append(f"| `{var.name}` | {req_str} | {pres_str} | {sec_str} | {src_str} |")
            lines.append("")
        else:
            lines.append("*No environment variables tracked.*")
            lines.append("")

        # Git Status
        lines.append("## Git State")
        lines.append("")
        if report.git.is_repository:
            lines.append(f"- **Branch**: `{report.git.branch or 'HEAD'}`")
            lines.append(
                f"- **Commit**: `{report.git.commit[:12] if report.git.commit else 'none'}`"
            )
            lines.append(
                f"- **Working Tree**: `{'dirty (uncommitted changes)' if report.git.dirty else 'clean'}`"
            )
        else:
            lines.append("*Not a Git repository.*")
        lines.append("")

        # Fingerprint Summary
        lines.append("---")
        lines.append(
            f"**Canonical Environment Fingerprint**: `{report.metadata.environment_fingerprint}`"
        )
        lines.append("")

        return "\n".join(lines)
