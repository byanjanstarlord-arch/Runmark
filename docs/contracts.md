# Runmark Environment Contracts (`runmark.json`)

> **Define what a project needs, then prove whether the current environment satisfies those requirements.**

---

## 1. Overview

Runmark Environment Contracts allow engineering teams to define explicit, version-controlled machine environment requirements alongside their source code in a `runmark.json` contract file.

When team members, CI runners, or AI coding agents work in a project directory, `runmark check` automatically evaluates the live host environment against the contract to verify compatibility before builds or tests run.

---

## 2. The Contract File (`runmark.json`)

A standard `runmark.json` file is validated against the formal schema `schemas/contract-v1.json`:

```json
{
  "$schema": "https://runmark.dev/schemas/contract-v1.json",
  "version": 1,
  "project": {
    "name": "my-service"
  },
  "platform": {
    "os": ["linux", "darwin", "windows"],
    "architecture": ["x86_64", "arm64", "amd64"]
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
      "version": ">=14",
      "required": true
    },
    "redis": ">=7.0"
  },
  "environment": {
    "required": ["DATABASE_URL", "API_KEY"],
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

---

## 3. Version Constraint Syntax

Runmark evaluates version constraints numerically (never lexicographically) across all major, minor, and patch levels:

| Expression | Description | Matches | Does Not Match |
|---|---|---|---|
| `3.12.4` | Exact version | `3.12.4` | `3.12.5`, `3.11.4` |
| `3.12.x` | Wildcard minor | `3.12.0`, `3.12.4`, `3.12.10` | `3.11.9`, `3.13.0` |
| `3.x` | Wildcard major | `3.0.0`, `3.12.4` | `4.0.0` |
| `>=3.12` | Greater than or equal | `3.12.0`, `3.13.1` | `3.11.9` |
| `<4.0` | Strictly less than | `3.12.4`, `3.99.0` | `4.0.0`, `4.1.0` |
| `>=3.11,<3.13` | Compound range | `3.11.0`, `3.12.4` | `3.10.9`, `3.13.0` |
| `*` | Any installed version | `1.0.0`, `22.0.0` | Not installed |

---

## 4. Evaluation Semantics

Runmark separates **Environment Observation** (`Scanner`) from **Contract Evaluation** (`ContractEvaluator`). The evaluator consumes the live `RunmarkState` snapshot without independently executing shell scripts.

### Check Statuses

- **`PASS`**: The environment satisfies the contract requirement.
- **`FAIL`**: A mandatory requirement is missing or does not meet constraints.
- **`UNKNOWN`**: A component is installed or running, but its version could not be safely detected.
- **`SKIPPED`**: An optional component is absent (does not cause failure).

### Overall Status Aggregation
- If any check is `FAIL` $\to$ Overall status is `FAIL`.
- If no checks failed but at least one is `UNKNOWN` $\to$ Overall status is `UNKNOWN`.
- If all checks are `PASS` (or `SKIPPED`) $\to$ Overall status is `PASS`.

---

## 5. Evidence-Driven Contract Generation

Instead of writing contracts by hand, Runmark synthesizes canonical `runmark.json` contracts from project manifests using a strict evidence hierarchy:

1. **`EXPLICIT`**: Declared directly in project manifests (`pyproject.toml`, `package.json`, `.nvmrc`, `Dockerfile`, `compose.yaml`, `.env.example`).
2. **`INFERRED`**: Derived from structural signals (e.g., PostgreSQL service image + Python `asyncpg` dependency).
3. **`OBSERVED`**: Host machine observation (used only as fallback when no project manifests are available).

> **Rule**: `project evidence > machine observation`. Machine state is supporting evidence, not authoritative project requirements.

---

## 6. CLI Commands

### `runmark contract init`
Bootstraps a validated, canonical `runmark.json` from project evidence manifests.

```bash
# Preview contract and discovered evidence without modifying files
runmark contract init --dry-run

# Generate contract directly without interactive confirmation
runmark contract init --yes

# Overwrite existing contract
runmark contract init --yes --force

# Target specific project directory
runmark contract init --path /path/to/project --yes
```

### `runmark contract diff`
Performs semantic requirement comparison against the Git repository baseline (`HEAD:runmark.json`) or a reference file.

```bash
# Compare working tree runmark.json against Git HEAD
runmark contract diff

# Output structured JSON diff
runmark contract diff --json

# Diff specific project path
runmark contract diff --path /path/to/project
```

### `runmark check`
Evaluates live environment state against the project contract.

```bash
# Check current directory
runmark check

# Check with detailed diagnostic cards (Evidence, Explanation, Suggested Action)
runmark check --explain

# Check specific target project
runmark check --path /path/to/project

# Pure machine-readable JSON output
runmark check --json
```

### `runmark contract validate`
Validates contract syntax, schema compliance, domain semantics, and security without scanning host state.

```bash
runmark contract validate
runmark contract validate --json
```

### `runmark contract show`
Displays normalized contract specifications and deterministic SHA-256 fingerprint.

```bash
runmark contract show
runmark contract show --json
```

---

## 7. Exit Codes

| Code | Meaning | When Triggered |
|---|---|---|
| `0` | **Success** | Live environment satisfies contract (`PASS`), contract is valid, or dry-run succeeded. |
| `1` | **Unsatisfied** | At least one mandatory requirement failed (`FAIL`). |
| `2` | **Usage / Conflict / Syntax** | Missing contract, target file exists without `--force`, malformed JSON, or schema error. |
| `3` | **Internal Error** | System detector failure or unexpected error. |
| `4` | **Security Violation** | Secret token, credential, or password detected in contract or output. |

---

## 8. Security Boundary

Contracts declare **requirements**, not secret values or credentials.

- Environment variables in `runmark.json` are strictly variable names (`"required": ["DATABASE_URL"]`).
- Any attempt to store credentials, passwords in URIs, private keys, or API tokens inside `runmark.json` triggers an immediate **Security Violation (Exit Code 4)**.
- Contracts are strictly declarative data. No arbitrary code execution (`eval`, `exec`, `shell=True`) is performed.

