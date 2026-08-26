"""Base interfaces and structures for all Runmark detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runmark.models.common import DetectionStatus


@dataclass(frozen=True)
class DetectionWarning:
    """Warning emitted by a detector during scanning."""

    message: str
    code: str | None = None
    level: str = "warning"


@dataclass
class DetectionContext:
    """Context provided to detectors during execution."""

    project_root: Path
    environment: dict[str, str] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)

    def resolve_path(self, relative_or_absolute: str | Path) -> Path:
        """Resolve a file path relative to the project root."""
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()


@dataclass
class DetectionResult:
    """Result payload produced by a detector."""

    name: str
    category: str
    status: DetectionStatus
    data: Any | None = None
    warnings: list[DetectionWarning] = field(default_factory=list)
    error_message: str | None = None


class Detector(ABC):
    """Abstract Base Class for all environment and project detectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this detector."""
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        """Category of detector: system, git, runtimes, project, dependencies, services, environment, network, containers."""
        ...

    @abstractmethod
    def detect(self, context: DetectionContext) -> DetectionResult:
        """Execute safe inspection and return structured DetectionResult."""
        ...
