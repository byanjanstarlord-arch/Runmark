# Runmark Detectors Guide

## Detector Architecture

Detectors are isolated, single-responsibility components responsible for inspecting a specific slice of the development environment.

### Abstract Base Class (`Detector`)

```python
from abc import ABC, abstractmethod
from runmark.detectors.base import DetectionContext, DetectionResult


class Detector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the detector (e.g. 'python_runtime')."""
        ...

    @property
    @abstractmethod
    def category(self) -> str:
        """Category (e.g. 'system', 'runtime', 'service', 'dependency', 'project')."""
        ...

    @abstractmethod
    def detect(self, context: DetectionContext) -> DetectionResult:
        """Executes safe inspection logic and returns a typed DetectionResult."""
        ...
```

### Detection Statuses

- `DETECTED`: The item was found and inspected.
- `NOT_FOUND`: The item is not installed or available on the host machine.
- `NOT_APPLICABLE`: The detector is not relevant for the current project context.
- `UNSUPPORTED`: The platform or architecture does not support this detector.
- `ERROR`: An unexpected exception occurred during detection (isolated gracefully).

## Standard Detectors in v0.1

1. **System**:
   - `SystemDetector`: Operating system name, version, and architecture.
2. **Git**:
   - `GitDetector`: Repository status, active branch, HEAD commit, dirty working tree.
3. **Runtimes**:
   - `PythonRuntimeDetector`: Python version & availability (`python`, `python3`, `py`).
   - `NodeRuntimeDetector`: Node.js version & availability (`node`).
   - `DockerRuntimeDetector`: Docker daemon & CLI availability (`docker`).
   - `GitRuntimeDetector`: Git binary availability (`git`).
4. **Project Signals**:
   - `PythonProjectDetector`: Detects Python projects (`pyproject.toml`, `requirements.txt`, `manage.py`, etc.).
   - `NodeProjectDetector`: Detects Node.js projects (`package.json`, `npm`, `yarn`, `pnpm`).
   - `DockerProjectDetector`: Detects containerized projects (`Dockerfile`, `compose.yaml`, `docker-compose.yml`).
5. **Dependencies**:
   - `PythonDependencyDetector`: Declared & locked dependencies (`requirements.txt`, `pyproject.toml`, `uv.lock`, `poetry.lock`).
   - `NodeDependencyDetector`: Declared & locked dependencies (`package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`).
6. **Services**:
   - `PostgresDetector`: PostgreSQL CLI, daemon status, port 5432, Docker Compose definitions.
   - `RedisDetector`: Redis CLI, daemon status, port 6379, Docker Compose definitions.
7. **Environment**:
   - `EnvDetector`: Reads `.env.example`, `.env.sample`, scans process environment for variable presence, applies secret redaction.
8. **Network / Ports**:
   - `PortDetector`: Probes standard expected ports (5432, 6379, 8000, 3000, 8080) for occupancy without hanging.
9. **Containers**:
   - `ContainerDetector`: Safe container and compose inspection.
