"""Central registry for discovering and executing Runmark detectors."""

from runmark.detectors.base import Detector


class DetectorRegistry:
    """Registry maintaining all active detector classes."""

    def __init__(self) -> None:
        self._detectors: dict[str, Detector] = {}

    def register(self, detector: Detector) -> None:
        """Register a detector instance."""
        self._detectors[detector.name] = detector

    def register_class(self, detector_cls: type[Detector]) -> None:
        """Instantiate and register a detector class."""
        instance = detector_cls()
        self.register(instance)

    def unregister(self, name: str) -> None:
        """Remove a detector by name."""
        self._detectors.pop(name, None)

    def get(self, name: str) -> Detector | None:
        """Get a specific detector by name."""
        return self._detectors.get(name)

    def get_all(self) -> list[Detector]:
        """Return all registered detectors in order."""
        return list(self._detectors.values())

    def get_by_category(self, category: str) -> list[Detector]:
        """Return all detectors matching a category."""
        return [d for d in self._detectors.values() if d.category == category]


# Global default registry instance
default_registry = DetectorRegistry()
