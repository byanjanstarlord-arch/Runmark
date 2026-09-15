<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-runmark-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-runmark-light.png">
    <img src="assets/logo-runmark-dark.png" alt="Runmark Logo" width="500">
  </picture>
</p>

<p align="center">
  <strong>Know what makes your code run.</strong><br>
  <em>Git tracks your code. Runmark tracks what makes your code run.</em>
</p>

<p align="center">
  <a href="https://runmark.live"><img src="https://img.shields.io/badge/website-runmark.live-ff572f.svg?style=flat-square&logo=google-chrome&logoColor=white" alt="Official Website"></a>
  <a href="https://pypi.org/project/runmark/"><img src="https://img.shields.io/pypi/v/runmark.svg?color=ff572f&style=flat-square&logo=pypi&logoColor=white" alt="PyPI Version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3776ab.svg?style=flat-square&logo=python&logoColor=white" alt="Python Version"></a>
  <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type--checking-mypy--strict-2e74b5.svg?style=flat-square" alt="Type Checking"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat-square&logo=ruff&logoColor=white" alt="Code Style"></a>
  <a href="docs/security.md"><img src="https://img.shields.io/badge/security-zero--secrets%20guaranteed-27A85B.svg?style=flat-square" alt="Zero Secrets"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-27A85B.svg?style=flat-square" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-the-problem--why-runmark">Why Runmark</a> •
  <a href="#-the-4-step-pipeline-workflow">Workflow</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-environment-contracts-runmarkjson">Environment Contracts</a> •
  <a href="#-cli-command-reference">CLI Reference</a> •
  <a href="#-security-architecture--zero-secret-guarantee">Security</a> •
  <a href="#-ci-gatekeeping--exit-codes">CI / Exit Codes</a> •
  <a href="#-documentation">Docs</a>
</p>

---

## ⚡ Overview

**Runmark** is a local-first development environment observability, fingerprinting, comparison, and verification tool designed to eliminate *"works on my machine"* forever.

Modern applications depend on complex webs of system runtimes (Python, Node), binary CLI tools (Docker, Git), local databases (PostgreSQL, Redis), occupied network ports, and environment configurations. When environments drift between teammates or CI runners, code breaks despite having identical Git commits.

Runmark introduces **declarative Environment Contracts (`runmark.json`)** and **deterministic environment verification**, giving teams a lightweight, zero-secret way to prove compatibility, diagnose discrepancies, and share sanitized debugging reports.

🌐 **Explore the live interactive experience at [runmark.live](https://runmark.live)**

---

## 🧩 The Problem & Why Runmark

Software frequently fails because development environments diverge across machines:

| Machine | Python | Node | Database | Redis | `.env` State | Build Result |
|---|---|---|---|---|---|---|
| **Developer A** | `3.12.4` | `22.4.1` | PostgreSQL `16.3` | Redis `7.2` (Running) | `DATABASE_URL` set |  **Passes** |
| **Developer B** | `3.11.2` | `20.10.0` | PostgreSQL `17.0` | Redis (Stopped) | `DATABASE_URL` missing | ❌ **Fails** |

> Both developers share the exact same Git commit and lockfiles, yet the application crashes.

### The Missing Layer in Modern DevOps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Source Control (Git)          Tracks code history & changes                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Package Managers (pip, npm)   Locks application-level dependencies         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Container Runtimes (Docker)   Virtualizes execution environments           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ⚡ RUNMARK (Observability)     Fingerprints, verifies, diffs, & diagnoses    │
│                                host machine state against project contracts │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚫 What Runmark Is NOT

To maintain laser focus, Runmark is deliberately scoped:

- **NOT a package manager**: It does not replace `pip`, `uv`, `npm`, `pnpm`, or `cargo`.
- **NOT a container manager**: It does not replace `docker`, `podman`, or `kubernetes`.
- **NOT an AI hallucination engine**: It relies on 100% deterministic rules and structural inspection.
- **NOT a cloud platform / telemetry collector**: It is 100% local-first, offline, and zero-telemetry.
- **NOT an environment mutator**: It never silently installs packages, runs scripts, or alters your system state without permission.

---

## 🔄 The 4-Step Pipeline Workflow

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   01. SCAN      │  ──►  │  02. CONTRACT   │  ──►  │   03. DIFF      │  ──►  │   04. VERIFY    │
│                 │       │                 │       │                 │       │                 │
│ Deep inspection │       │ Synthesize &    │       │ Semantic drift  │       │ Deterministic   │
│ of host runtimes│       │ version specs   │       │ vs baseline/Git │       │ gate in CI & dev│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Scan (`runmark scan`)**: Safely observes system architecture, installed runtimes, package managers, services, listening ports, Docker containers, and `.env` presence.
2. **Contract (`runmark contract init`)**: Synthesizes a formal `runmark.json` contract directly from project evidence (`pyproject.toml`, `package.json`, `Dockerfile`, `compose.yaml`, `.env.example`).
3. **Diff (`runmark diff` / `runmark contract diff`)**: Compares your live machine against a frozen baseline snapshot or Git `HEAD:runmark.json` with semantic severity categorization (`CRITICAL`, `WARNING`, `INFO`).
4. **Verify (`runmark check` / `runmark verify`)**: Proves compatibility before builds or tests run, returning deterministic exit codes (`0`, `1`, `2`, `3`, `4`) for CI/CD gates.

---

## ✨ Key Features

- 📜 **Declarative Environment Contracts (`runmark.json`)**: Declare project runtime, service, dependency, environment, network, and container requirements directly alongside source code.
- 🏗️ **Evidence-Driven Synthesis (`runmark contract init`)**: Automatically synthesizes canonical contracts from project evidence manifests with `--dry-run` safety.
- ⚡ **Deterministic Contract Proofs (`runmark check`)**: Evaluates host compliance in milliseconds without running intrusive scripts.
- 🔍 **Causal Explanations & Doctor Mode (`runmark doctor` / `--explain`)**: Pinpoints exact root causes with structured *Evidence*, *Explanation*, and actionable *Suggested Remediation*.
- 🔄 **Semantic Git Diffing (`runmark contract diff`)**: Compares contract requirement changes against Git baseline (`HEAD:runmark.json`) before committing.
- 🏷️ **Decoupled SHA-256 Fingerprinting**: Generates canonical hashes of environment state that remain stable across git commits, timestamps, and usernames.
- 🛡️ **Zero-Secret Security Engine**: Multi-pass pattern scanning, URL credential stripping (`postgres://user:pass@host`), home directory masking (`<USER_HOME>`), and **Exit Code 4** violation protection.
- 📤 **Sanitized Diagnostic Sharing (`runmark share`)**: Generates portable, zero-secret Markdown or JSON reports ready to paste directly into GitHub Issues, Discord, or Slack.
- 🚦 **CI/CD Gatekeeping**: Deterministic exit codes designed for GitHub Actions, GitLab CI, pre-commit hooks, and development scripts.
- 💻 **100% Offline & Local-First**: Cross-platform (Linux, macOS, Windows) with zero telemetry, zero daemons, and atomic `.runmark/` storage.

---

## 🚀 Quick Start

### Installation

Install Runmark using `pip`, `uv`, or `pipx`:

```bash
# Using pip
pip install runmark

# Using uv
uv pip install runmark

# Using pipx (isolated CLI)
pipx install runmark
```

### 60-Second Walkthrough

#### 1. Bootstrap an Environment Contract
Synthesize a formal contract from existing project files:
```bash
# Preview discovered evidence
runmark contract init --dry-run

# Write canonical runmark.json
runmark contract init --yes
```

#### 2. Check Host Machine Compliance
Verify whether your machine satisfies all project requirements:
```bash
runmark check
```

```text
Runmark Check: my-service (v1)
Environment Fingerprint: a8f4e912c409...

Component         Expected           Actual             Status
────────────────────────────────────────────────────────────────
python            >=3.11,<3.13       3.12.4             PASS
node              >=20               20.10.0            PASS
postgresql        >=15               16.3 (running)     PASS
redis             >=7.0              7.2.4 (running)    PASS
DATABASE_URL      present            present (secret)   PASS
port:8000         available          listening          PASS

Result: PASS (All 6 requirements satisfied)
```

#### 3. Diagnose Any Failures with Explanations
```bash
runmark check --explain
```

```text
┌─ [CRITICAL] Service PostgreSQL Not Running ───────────────────────┐
│ Evidence:    PostgreSQL 16.3 installed, but port 5432 is inactive │
│ Explanation: Contract requires postgresql >=15 in running status. │
│ Action:      Start service via: docker compose up -d db           │
└───────────────────────────────────────────────────────────────────┘
```

#### 4. Save a Baseline & Diff Against Drift
```bash
# Freeze known-working state
runmark snapshot -m "Working onboarding setup"

# Later, check what changed
runmark diff
```

#### 5. Generate a Sanitized Issue Report
```bash
runmark share --output report.md
```

---

## 📜 Environment Contracts (`runmark.json`)

An Environment Contract is a version-controlled declaration of what an application needs to run:

```json
{
  "$schema": "https://runmark.dev/schemas/contract-v1.json",
  "version": 1,
  "project": {
    "name": "my-service"
  },
  "platform": {
    "os": ["linux", "darwin", "windows"],
    "architecture": ["x86_64", "arm64"]
  },
  "runtime": {
    "python": ">=3.11,<3.13",
    "node": ">=20"
  },
  "dependencies": {
    "python": {
      "fastapi": ">=0.100.0",
      "pydantic": ">=2.0"
    }
  },
  "services": {
    "postgresql": {
      "version": ">=15",
      "required": true
    },
    "redis": ">=7.0"
  },
  "environment": {
    "required": ["DATABASE_URL", "STRIPE_API_KEY"],
    "optional": ["DEBUG", "LOG_LEVEL"]
  },
  "network": {
    "ports": {
      "8000": {
        "protocol": "tcp",
        "required": true
      }
    }
  },
  "containers": {
    "docker": {
      "required": true
    },
    "compose": {
      "required": true
    }
  }
}
```

### Version Constraint Syntax

Runmark evaluates numeric version constraints safely:

| Constraint | Meaning | Example Matches | Non-Matches |
|---|---|---|---|
| `3.12.4` | Exact version | `3.12.4` | `3.12.5`, `3.11.4` |
| `3.12.x` | Wildcard minor | `3.12.0`, `3.12.4`, `3.12.9` | `3.11.9`, `3.13.0` |
| `>=3.12` | Minimum version | `3.12.0`, `3.13.1` | `3.11.9` |
| `<4.0` | Strictly less than | `3.12.4`, `3.99.0` | `4.0.0`, `4.1.0` |
| `>=3.11,<3.13` | Compound range | `3.11.0`, `3.12.4` | `3.10.9`, `3.13.0` |
| `*` | Any installed version | `1.0.0`, `22.0.0` | Not installed |

---

## 🛠️ CLI Command Reference

### Contract Management

| Command | Flags | Description |
|---|---|---|
| `runmark check` | `--explain`, `--json`, `--path` | Evaluates live host environment against `runmark.json` contract |
| `runmark contract init` | `--dry-run`, `--yes`, `--force`, `--path` | Synthesizes canonical `runmark.json` from project evidence manifests |
| `runmark contract diff` | `--json`, `--path` | Compares working tree contract against Git baseline (`HEAD:runmark.json`) |
| `runmark contract validate` | `--json`, `--path` | Validates contract JSON schema, domain semantics, and security rules |
| `runmark contract show` | `--json`, `--path` | Displays normalized contract specifications and fingerprint |

### Environment Observation & Drift

| Command | Flags | Description |
|---|---|---|
| `runmark scan` | `--json`, `--path` | Inspects and displays full host environment state |
| `runmark snapshot` | `-m / --message`, `--path` | Freezes current environment state into an atomic snapshot |
| `runmark diff` | `--against <id>`, `--json` | Performs semantic drift comparison between snapshots |
| `runmark verify` | `--against <id>`, `--strict`, `--json` | Verifies environment compliance with deterministic CI exit codes |
| `runmark doctor` | `--against <id>`, `--json` | Generates causal diagnostics and suggested remediation steps |
| `runmark share` | `--output <file>`, `--format md\|json` | Exports a sanitized, zero-secret diagnostic report for troubleshooting |
| `runmark history` | `--limit <n>` | Lists snapshot history and active pointers |
| `runmark version` | `--json` | Displays Runmark version, schema version, and platform metadata |

---

## 🛡️ Security Architecture & Zero-Secret Guarantee

Runmark is engineered around strict security boundaries:

```text
Raw Machine Inspection / Contracts
               │
               ▼
   [Redaction Pipeline Engine]
   ├─ Secret Pattern Scanner (AWS, GitHub, JWT, Bearer, Passwords)
   ├─ Multi-Scheme URI Credential Stripper (postgres://, redis://, https://)
   ├─ Path Privacy Engine (Masks <USER_HOME>, normalizes roots)
   └─ Safe Subprocess Runner (shell=False, bounded timeouts, output clamps)
               │
               ▼
   Sanitized Output / Atomic Storage (.runmark/)
   (If any credential leaks: Immediate EXIT CODE 4)
```

- **Contracts declare requirements, not secrets**: Variables are declared as names only (`"required": ["DATABASE_URL"]`).
- **Zero-Secret Export**: `runmark share` strips all user tokens, passwords, and private directory paths.
- **Fail-Closed Security**: Any detected secret contamination triggers an immediate **Exit Code 4** violation.

---

## 🚦 CI Gatekeeping & Exit Codes

Runmark adheres to standard, predictable exit codes suitable for CI/CD automation:

| Code | Status | Meaning |
|:---:|---|---|
| `0` | **Success** | Environment satisfies contract / verification passed / valid syntax |
| `1` | **Unsatisfied** | Mandatory requirement missing or version drift detected |
| `2` | **Usage Error** | Missing contract, bad CLI arguments, or schema validation failure |
| `3` | **Internal Error** | System detector execution failure or unhandled exception |
| `4` | **Security Violation** | Secret token, credential, or password detected at boundary |

### GitHub Actions Integration Example

```yaml
name: Environment Verification
on: [push, pull_request]

jobs:
  verify-environment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install Runmark
        run: pip install runmark
        
      - name: Verify Environment Contract
        run: runmark check --explain
```

---

## 📚 Documentation

For in-depth architectural guides and developer specifications:

- 📖 **[Environment Contracts Guide](docs/contracts.md)**: Deep dive into schema structure and evidence synthesis rules.
- 🏛️ **[Architecture Guide](docs/architecture.md)**: Detailed subsystem design, atomic storage, and redaction pipeline.
- 📐 **[Specification & Exit Codes](docs/specification.md)**: Complete JSON data models and CI status codes.
- 🛡️ **[Security Policy](docs/security.md)**: Threat modeling, subprocess safety, and secret sanitization guarantees.
- 🔍 **[Detectors Guide](docs/detectors.md)**: Guide to runtime, dependency, service, port, and container detectors.

---

## 💻 Development & Contributing

We welcome contributions from the community!

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/byanjanstarlord-arch/Runmark.git
cd Runmark

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 3. Install in editable mode with development dependencies
pip install -e ".[dev]"

# 4. Run test suite
pytest

# 5. Run type checking & linting
mypy src tests
ruff check .
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more details.

---

<p align="center">
  Crafted with care by the <strong>Runmark Maintainers & Community</strong>.<br>
  Explore the web experience at <a href="https://runmark.live"><strong>runmark.live</strong></a>
</p>
