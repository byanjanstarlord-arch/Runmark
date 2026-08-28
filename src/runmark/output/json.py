"""JSON renderer for Runmark Diagnostic Reports."""

import json

from runmark.models.diagnostic import DiagnosticReport


class JSONRenderer:
    """Renders a DiagnosticReport into deterministic, structured JSON."""

    @classmethod
    def render(cls, report: DiagnosticReport, indent: int = 2) -> str:
        """Serialize a DiagnosticReport into a formatted JSON string."""
        # Dump using Pydantic mode='json'
        dumped = report.model_dump(mode="json")
        return json.dumps(dumped, indent=indent, sort_keys=True)
