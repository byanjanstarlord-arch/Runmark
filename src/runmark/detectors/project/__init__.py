"""Project detectors package."""

from runmark.detectors.project.docker import DockerProjectDetector
from runmark.detectors.project.node import NodeProjectDetector
from runmark.detectors.project.python import PythonProjectDetector

__all__ = [
    "DockerProjectDetector",
    "NodeProjectDetector",
    "PythonProjectDetector",
]
