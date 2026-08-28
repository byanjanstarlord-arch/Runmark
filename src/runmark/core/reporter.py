"""Reporter service for synthesizing, sanitizing, rendering, and exporting Diagnostic Reports."""

import os
import tempfile
from pathlib import Path

from runmark.core.diff import DiffEngine
from runmark.core.doctor import Doctor
from runmark.core.scanner import Scanner
from runmark.core.snapshot import SnapshotManager
from runmark.models.diagnostic import (
    DiagnosticIssue,
    DiagnosticReport,
    DiagnosticSeverity,
    ReportMetadata,
)
from runmark.models.runmark import RunmarkState
from runmark.output.json import JSONRenderer
from runmark.output.markdown import MarkdownRenderer
from runmark.security.export_sanitizer import ExportSanitizer


class Reporter:
    """Coordinates diagnostic report generation, export sanitization, and atomic output."""

    @classmethod
    def generate_report(
        cls,
        project_root: Path | str,
        state: RunmarkState | None = None,
    ) -> DiagnosticReport:
        """Construct and sanitize a portable DiagnosticReport for the given project."""
        root = Path(project_root).resolve()

        if state is None:
            scanner = Scanner(root)
            state = scanner.scan()

        # Collect diagnostics from baseline diff if baseline exists, else direct state
        mgr = SnapshotManager(root)
        baseline = mgr.get_current()

        diagnostics: list[DiagnosticIssue] = []
        if baseline:
            diff = DiffEngine.compare(baseline, state)
            diff_doc = Doctor.diagnose_diff(diff)
            diagnostics.extend(diff_doc.issues)
            state_doc = Doctor.diagnose_state(state)
            diagnostics.extend(state_doc.issues)
        else:
            doc_report = Doctor.diagnose_state(state)
            diagnostics = list(doc_report.issues)

        # Deduplicate diagnostics by code and title
        seen_codes: set[str] = set()
        deduped_diagnostics: list[DiagnosticIssue] = []
        for d in diagnostics:
            key = f"{d.code}:{d.title}"
            if key not in seen_codes:
                seen_codes.add(key)
                deduped_diagnostics.append(d)

        # Compute summary
        num_crit = sum(1 for d in deduped_diagnostics if d.severity == DiagnosticSeverity.CRITICAL)
        num_warn = sum(1 for d in deduped_diagnostics if d.severity == DiagnosticSeverity.WARNING)
        if num_crit == 0 and num_warn == 0:
            summary = "Healthy — no environment issues detected."
        else:
            parts: list[str] = []
            if num_crit > 0:
                parts.append(f"{num_crit} critical issue{'s' if num_crit > 1 else ''}")
            if num_warn > 0:
                parts.append(f"{num_warn} warning{'s' if num_warn > 1 else ''}")
            summary = f"Identified {', '.join(parts)}."

        raw_report = DiagnosticReport(
            metadata=ReportMetadata(
                environment_fingerprint=state.runmark.environment_fingerprint,
                summary=summary,
            ),
            project=state.project,
            system=state.system,
            runtimes=state.runtimes,
            dependencies=state.dependencies,
            services=state.services,
            environment=state.environment,
            network=state.network,
            containers=state.containers,
            git=state.git,
            diagnostics=deduped_diagnostics,
        )

        # Apply deep export sanitization
        sanitized_report = ExportSanitizer.sanitize_report(raw_report, base_path=root)
        return sanitized_report

    @classmethod
    def render_markdown(cls, report: DiagnosticReport) -> str:
        """Render report as Markdown and verify clean security boundary."""
        content = MarkdownRenderer.render(report)
        ExportSanitizer.verify_rendered_content_clean(content)
        return content

    @classmethod
    def render_json(cls, report: DiagnosticReport, indent: int = 2) -> str:
        """Render report as JSON and verify clean security boundary."""
        content = JSONRenderer.render(report, indent=indent)
        ExportSanitizer.verify_rendered_content_clean(content)
        return content

    @classmethod
    def export_to_file(
        cls,
        report: DiagnosticReport,
        destination: Path | str,
        as_json: bool = False,
        force: bool = False,
    ) -> Path:
        """Atomically render and write the report to a destination file.

        Refuses overwrite unless force=True.
        Enforces clean security boundary before writing.
        """
        dest = Path(destination).resolve()

        if dest.exists() and not force:
            raise FileExistsError(
                f"Destination file '{dest}' already exists. Use --force to overwrite."
            )

        # Infer format from extension or explicit flag
        if as_json or dest.suffix.lower() == ".json":
            rendered = cls.render_json(report)
        else:
            rendered = cls.render_markdown(report)

        # Ensure parent directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write via temporary file in target directory
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=dest.parent,
                delete=False,
                prefix=".tmp_report_",
            ) as f:
                temp_file = Path(f.name)
                f.write(rendered)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_file, dest)
            return dest
        except Exception:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise
