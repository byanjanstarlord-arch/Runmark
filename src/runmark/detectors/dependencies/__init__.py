"""Dependency detectors package."""

from runmark.detectors.dependencies.node import NodeDependencyDetector
from runmark.detectors.dependencies.python import PythonDependencyDetector

__all__ = [
    "NodeDependencyDetector",
    "PythonDependencyDetector",
]
