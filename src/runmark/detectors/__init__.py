"""Detectors module initialization and default registration."""

from runmark.detectors.base import (
    DetectionContext,
    DetectionResult,
    DetectionStatus,
    DetectionWarning,
    Detector,
)
from runmark.detectors.containers.compose import ContainerDetector
from runmark.detectors.dependencies.node import NodeDependencyDetector
from runmark.detectors.dependencies.python import PythonDependencyDetector
from runmark.detectors.environment.env import EnvDetector
from runmark.detectors.git.git import GitDetector
from runmark.detectors.network.ports import PortDetector
from runmark.detectors.project.docker import DockerProjectDetector
from runmark.detectors.project.node import NodeProjectDetector
from runmark.detectors.project.python import PythonProjectDetector
from runmark.detectors.registry import DetectorRegistry, default_registry
from runmark.detectors.runtimes.docker import DockerRuntimeDetector
from runmark.detectors.runtimes.git import GitRuntimeDetector
from runmark.detectors.runtimes.node import NodeRuntimeDetector
from runmark.detectors.runtimes.python import PythonRuntimeDetector
from runmark.detectors.services.postgres import PostgresDetector
from runmark.detectors.services.redis import RedisDetector
from runmark.detectors.system.system import SystemDetector


def register_standard_detectors(registry: DetectorRegistry = default_registry) -> None:
    """Register all built-in standard detectors into the registry."""
    # System
    registry.register(SystemDetector())
    # Git
    registry.register(GitDetector())
    # Runtimes
    registry.register(PythonRuntimeDetector())
    registry.register(NodeRuntimeDetector())
    registry.register(DockerRuntimeDetector())
    registry.register(GitRuntimeDetector())
    # Project
    registry.register(PythonProjectDetector())
    registry.register(NodeProjectDetector())
    registry.register(DockerProjectDetector())
    # Dependencies
    registry.register(PythonDependencyDetector())
    registry.register(NodeDependencyDetector())
    # Services
    registry.register(PostgresDetector())
    registry.register(RedisDetector())
    # Environment
    registry.register(EnvDetector())
    # Network
    registry.register(PortDetector())
    # Containers
    registry.register(ContainerDetector())


# Automatically register standard detectors on import
register_standard_detectors(default_registry)

__all__ = [
    "ContainerDetector",
    "DetectionContext",
    "DetectionResult",
    "DetectionStatus",
    "DetectionWarning",
    "Detector",
    "DetectorRegistry",
    "DockerProjectDetector",
    "DockerRuntimeDetector",
    "EnvDetector",
    "GitDetector",
    "GitRuntimeDetector",
    "NodeDependencyDetector",
    "NodeProjectDetector",
    "NodeRuntimeDetector",
    "PortDetector",
    "PostgresDetector",
    "PythonDependencyDetector",
    "PythonProjectDetector",
    "PythonRuntimeDetector",
    "RedisDetector",
    "SystemDetector",
    "default_registry",
    "register_standard_detectors",
]
