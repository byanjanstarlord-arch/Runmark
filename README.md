# Runmark

> **Know what makes your code run.**
> *Git tracks your code. Runmark tracks what makes your code run.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg)]()
[![Type Checked: mypy strict](https://img.shields.io/badge/mypy-strict-blue.svg)]()
[![Code Style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)]()

---

## The Problem

Software frequently fails because the development environment differs between machines:
- **Developer A** has Python 3.12, Node 22, PostgreSQL 16, Redis 7, Docker 28, and valid `.env` variables.
- **Developer B** has Python 3.11, Node 20, PostgreSQL 17, Redis stopped, and a missing environment variable.

Both developers have the exact same Git repository commit, yet the application breaks.

Git tracks source code. Package managers lock application dependencies. Containers reproduce environments. **Runmark is the missing observation, fingerprinting, comparison, verification, and diagnosis layer.**

---

## What Runmark Is NOT

To keep expectations clear, Runmark is deliberately focused:
- **Runmark is NOT a package manager.** It does not replace `pip`, `uv`, `npm`, `pnpm`, or `cargo`.
- **Runmark is NOT a container manager.** It does not replace `docker`, `podman`, or `k8s`.
- **Runmark is NOT an AI coding assistant.** It relies on deterministic facts and structural verification.
- **Runmark is NOT a cloud platform.** It is 100% local-first, offline, and zero-telemetry.
- **Runmark is NOT an environment installer.** It never automatically installs packages or mutates system state.
- **Runmark is NOT a replacement for Git or Docker.** It observes and diagnoses what makes your code run alongside them.

---

## Key Features

- 🏗️ **Contract Bootstrap (`runmark contract init`)**: Automatically synthesize canonical `runmark.json` contracts from project evidence manifests (`pyproject.toml`, `package.json`, `Dockerfile`, `compose.yaml`, `.env.example`).
- 🔄 **Semantic Contract Diffing (`runmark contract diff`)**: Compare contract requirement changes against Git baseline (`HEAD:runmark.json`) or previous versions before committing.
- 📜 **Environment Contracts (`runmark.json`)**: Declare project runtime, service, dependency, environment, network, and container requirements directly alongside source code.
- ⚡ **Contract Proof & Evaluation (`runmark check`)**: Prove deterministically whether the host machine satisfies project requirements before running builds or tests.
- 🔍 **Detailed Diagnostic Explanations (`runmark check --explain`)**: Deeply diagnose failed or unknown requirements with explicit evidence citations, causal explanations, and actionable remediation steps.
- 🛠️ **Contract Tooling (`runmark contract`)**: Validate syntax, JSON schema, domain semantics, and security (`runmark contract validate`), inspect normalized specifications (`runmark contract show`), or initialize contracts (`runmark contract init`).
- 📤 **Share & Diagnose**: Generate clean, sanitized, portable Markdown or JSON diagnostic reports (`runmark share`) ready to attach directly to GitHub Issues, Slack, or teammate chats.
- 🛡️ **Zero-Secret Guarantee & Security Boundaries**: Multi-pass secret scanning prevents credentials, API keys, passwords in URIs, or tokens from escaping in shared reports or being stored in contract files (exit code `4`).
- 🔍 **Safe Scanning**: Inspects project signals, runtimes (Python, Node, Docker, Git), dependencies, local services (PostgreSQL, Redis), ports, and environment variable requirements.
- 🏷️ **Deterministic Fingerprinting**: Computes a canonical SHA-256 environment fingerprint decoupled from source code commits and timestamps.
- ⚡ **Semantic Diffing**: Categorizes drift as `ADDED`, `REMOVED`, `CHANGED`, and `UNCHANGED` with rule-driven severity (`INFO`, `WARNING`, `CRITICAL`).
- 🛡️ **Environment Verification**: Verifies your current machine against a baseline snapshot with CI-ready exit codes (`0`, `1`, `2`, `3`, `4`).
- 🩺 **Doctor Mode**: Explains environment discrepancies with distinct observed evidence, inferred reasoning, and read-only remediation advice.
- 💻 **Local-First & Cross-Platform**: 100% offline, cross-platform (Windows, Linux, macOS), atomic filesystem storage, and zero telemetry.

---

## Quick Start

### Installation

```bash
pip install runmark
```

### Basic Workflow

```bash
# 1. Bootstrap an environment contract from project evidence
runmark contract init --dry-run
runmark contract init --yes

# 2. Check current machine against project environment contract
runmark check
runmark check --explain

# 3. Compare contract requirement changes against Git HEAD
runmark contract diff

# 4. Inspect your current development environment
runmark scan

# 5. Save a known-good baseline snapshot
runmark snapshot -m "Initial working dev environment"

# 6. Compare current machine state against the snapshot
runmark diff

# 7. Verify compliance in CI or on coworker machines
runmark verify --strict

# 8. Diagnose and fix discrepancies
runmark doctor

# 9. Safely share a sanitized diagnostic report with teammates
runmark share --output report.md

# 10. Inspect and validate environment contracts
runmark contract validate
runmark contract show
```

---

## Documentation

- [Environment Contracts Guide](docs/contracts.md)
- [Architecture Guide](docs/architecture.md)
- [Specification & Exit Codes](docs/specification.md)
- [Security Policy](docs/security.md)
- [Detectors Guide](docs/detectors.md)

---

## License

MIT © Runmark Maintainers
