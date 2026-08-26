# Runmark

> **Know what makes your code run.**
> *Git tracks your code. Runmark tracks what makes your code run.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## The Problem

Software frequently fails because the development environment differs between machines:
- Developer A has Python 3.12, Node 22, PostgreSQL 16, Redis 7, Docker 28, and valid `.env` variables.
- Developer B has Python 3.11, Node 20, PostgreSQL 17, Redis stopped, and a missing environment variable.

Both developers have the exact same Git repository commit, yet the application breaks.

Git answers questions about source code. Package managers and lockfiles lock application dependencies. Containers reproduce environments. **Runmark is the missing observation, fingerprinting, comparison, verification, and diagnosis layer.**

---

## Key Features

- 🔍 **Safe Scanning**: Inspects project signals, runtimes (Python, Node, Docker, Git), dependencies, local services (PostgreSQL, Redis), ports, and environment variable requirements.
- 🔒 **Zero Secret Persistence**: Analyzes variable existence and requirements, but never stores passwords, API keys, private keys, or tokens.
- 🏷️ **Deterministic Fingerprinting**: Computes a canonical SHA-256 environment fingerprint decoupled from source code commits.
- ⚡ **Semantic Diffing**: Categorizes drift as `ADDED`, `REMOVED`, `CHANGED` with rule-driven severity (`INFO`, `WARNING`, `CRITICAL`).
- 🛡️ **Environment Verification**: Verifies your current machine against a baseline snapshot with CI-ready exit codes (`0`, `1`, `2`, `3`, `4`).
- 🩺 **Doctor Mode**: Explains environment discrepancies and suggests actionable fixes.
- 💻 **Local-First**: 100% offline, zero telemetry, no cloud accounts, no AI magic required.

---

## Quick Start

### Installation

```bash
pip install runmark
```

### Basic Workflow

```bash
# 1. Initialize Runmark in your project
runmark init

# 2. Inspect your current development environment
runmark scan

# 3. Save a known-good baseline snapshot
runmark snapshot -m "Initial working dev environment"

# 4. Compare current machine state against the snapshot
runmark diff

# 5. Verify compliance in CI or on coworker machines
runmark verify

# 6. Diagnose and fix discrepancies
runmark doctor
```

---

## Output Examples

### Scanning an Environment
```text
RUNMARK SCAN

Project
✓ Python (pyproject.toml)
✓ Docker Compose (compose.yaml)

Runtime
✓ Python 3.12.4
✓ Node 22.5.1
✓ Docker 28.0.1
✓ Git 2.44.0

Services
✓ PostgreSQL 16 (running on port 5432)
✓ Redis 7 (running on port 6379)

Environment
✓ 8 required variables present
⚠ 1 missing variable (STRIPE_SECRET_KEY)

Git
✓ branch: main
✓ commit: a81f29c
✓ working tree: clean
```

### Running Doctor
```text
RUNMARK DOCTOR

🔴 CRITICAL: Required environment variable missing
  Variable: STRIPE_SECRET_KEY
  Expected: present
  Actual:   missing
  Action:   Add STRIPE_SECRET_KEY to your local .env or shell environment.

🟡 WARNING: Node.js version mismatch
  Expected: 22.x
  Detected: 20.18.0
  Action:   Switch to Node.js 22.x (e.g. nvm use 22).
```

---

## Security Philosophy

Runmark operates strictly on the rule: **Observe metadata, never collect secrets.**
- All secret names and sensitive file types are detected and redacted before storage or display.
- Subprocesses use argument arrays without `shell=True` and have strict timeouts.
- No arbitrary project scripts (`setup.sh`, `Makefile`, etc.) are ever executed.

---

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Specification](docs/specification.md)
- [Security Policy](docs/security.md)
- [Detectors Guide](docs/detectors.md)

---

## License

MIT © Runmark Maintainers
