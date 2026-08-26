"""Output package."""

from runmark.output.tables import (
    render_diff,
    render_doctor,
    render_history,
    render_scan,
    render_verify,
)
from runmark.output.terminal import Terminal, term

__all__ = [
    "Terminal",
    "render_diff",
    "render_doctor",
    "render_history",
    "render_scan",
    "render_verify",
    "term",
]
