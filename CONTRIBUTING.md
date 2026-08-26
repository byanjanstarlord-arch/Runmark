# Contributing to Runmark

Thank you for contributing to Runmark! Runmark is an open-source tool built to give developers complete clarity over their development environments.

## Development Setup

### Prerequisites
- Python >= 3.10
- Git

### Setting up the Environment
```bash
# Clone the repository
git clone https://github.com/runmark/runmark.git
cd runmark

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

## Running Tests & Quality Checks

Run the automated test suite:
```bash
pytest
```

Run code formatting and linting:
```bash
ruff check .
ruff format --check .
```

Run type checks:
```bash
mypy src/runmark
```

## Adding a Detector

1. Subclass `Detector` in `src/runmark/detectors/base.py`.
2. Implement `name`, `category`, and `detect(context: DetectionContext) -> DetectionResult`.
3. Register your detector in `src/runmark/detectors/registry.py`.
4. Ensure all subprocess calls use `safe_run` and never execute arbitrary user project code.
5. Add unit and fixture tests under `tests/unit/detectors/`.

## Code Guidelines

- **Determinism**: Fingerprints and diffs must be 100% deterministic across runs on identical environments.
- **Security First**: Ensure data passes through the redaction and sanitization pipeline.
- **Graceful Degradation**: A missing tool or service on the host machine must produce `NOT_FOUND` or `ERROR` without crashing the scan.
- **Type Annotations**: All public functions and classes must include explicit type annotations.
