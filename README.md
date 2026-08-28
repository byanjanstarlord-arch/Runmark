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

- 📤 **Share & Diagnose**: Generate clean, sanitized, portable Markdown or JSON diagnostic reports (`runmark share`) ready to attach directly to GitHub Issues, Slack, or teammate chats.
- 🛡️ **Export Security Boundary**: Deep multi-pass sanitization ensures zero URI passwords, credentials, tokens, or local username paths escape in shared reports.
- 🔍 **Safe Scanning**: Inspects project signals, runtimes (Python, Node, Docker, Git), dependencies, local services (PostgreSQL, Redis), ports, and environment variable requirements.
- 🔒 **Zero Secret Retention Guarantee**: Analyzes variable existence, requirement flags, and metadata, but never stores passwords, API keys, private keys, or tokens.
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
# 1. Initialize Runmark in your project
runmark init

# 2. Inspect your current development environment
runmark scan

# 3. Save a known-good baseline snapshot
runmark snapshot -m "Initial working dev environment"

# 4. Compare current machine state against the snapshot
runmark diff

# 5. Verify compliance in CI or on coworker machines
runmark verify --strict

# 6. Diagnose and fix discrepancies
runmark doctor

# 7. Safely share a sanitized diagnostic report with teammates or in a bug report
runmark share --output report.md
# Or pipe directly to clipboard / stdout:
runmark share --stdout
```

---

## Output Examples

### Sharing a Sanitized Diagnostic Report (`runmark share`)
```markdown
# Runmark Diagnostic Report

## Report Information
| Field | Value |
|---|---|
| **Report ID** | `rpt_7f2b10a9c8e1` |
| **Generated At** | `2026-08-26T12:30:00Z` |
| **Runmark Version** | `v0.1.2` |
| **Schema Version** | `1.0` |
| **Fingerprint** | `rm_33c858105c969ef1...` |

## Diagnostics
### 🔴 [ENV_MISSING_REQUIRED] Required environment variable missing
- **Severity**: `CRITICAL`
- **Category**: `environment`
- **Explanation**: The project configuration (.env.example) marks 'STRIPE_SECRET_KEY' as required, but it is not set.
- **Suggested Action**: `Add 'STRIPE_SECRET_KEY' to your local environment or .env file.`
```

---

## Security & Reliability Guarantees (v0.1.2)

Runmark operates strictly on the rule: **Observe metadata, never collect secrets.**
- **Export Security Boundary**: All exported diagnostic reports pass through deep URI credential stripping, path normalization (`<USER_HOME>`, `<PROJECT_ROOT>`), and a final canary secret scan. If any credential survives, export immediately aborts with exit code `4` and deletes temporary files.
- **Adversarial Secret Redaction**: Multi-stage redactor scrubs API keys, bearer tokens, JWTs, cloud credentials, private keys, and database connection strings before state construction, hashing, or persistence.
- **Atomic Storage & File Export**: All snapshots, configurations, and shared reports use atomic tempfile replacement (`os.replace` + `fsync`) and overwrite protection (`--force`).
- **Read-Only Architecture**: Runmark never executes arbitrary project scripts (`setup.sh`, `Makefile`, `npm install`) and never modifies the developer machine.

---

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Specification & Exit Codes](docs/specification.md)
- [Security Policy](docs/security.md)
- [Detectors Guide](docs/detectors.md)

---

## License

MIT © Runmark Maintainers
