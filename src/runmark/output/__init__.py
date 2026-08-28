"""Output package."""

from runmark.output.json import JSONRenderer
from runmark.output.markdown import MarkdownRenderer
from runmark.output.tables import (
    render_diff,
    render_doctor,
    render_history,
    render_scan,
    render_verify,
)
from runmark.output.terminal import Terminal, term

__all__ = [
    "JSONRenderer",
    "MarkdownRenderer",
    "Terminal",
    "render_diff",
    "render_doctor",
    "render_history",
    "render_scan",
    "render_verify",
    "term",
]
