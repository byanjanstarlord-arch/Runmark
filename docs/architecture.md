# Runmark Architecture Guide

This document describes the architectural design and structural layers of Runmark v0.1.1.

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                           CLI App                           │
│   (init, scan, snapshot, diff, verify, doctor, history, ...)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                         Core Engine                         │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Scanner  │  │ Snapshot  │  │   Diff   │  │ Verifier  │  │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│        │              │             │              │        │
│        │              ▼             │              │        │
│        │        ┌───────────┐       │              │        │
│        │        │  Doctor   │       │              │        │
│        │        └───────────┘       │              │        │
└────────┼────────────────────────────┼──────────────┼────────┘
         │                            │              │
         ▼                            ▼              ▼
┌─────────────────┐          ┌────────────────────────────────┐
│Detector Registry│          │   Canonicalization & Storage   │
│                 │          │  - Volatile Data Stripping     │
│ - System        │          │  - Key & List Normalization    │
│ - Git           │          │  - SHA-256 Fingerprinting      │
│ - Runtimes      │          │  - Atomic Snapshot Storage     │
│ - Projects      │          └────────────────────────────────┘
│ - Dependencies  │                           ▲
│ - Services      │                           │
│ - Environment   │                           │
│ - Network/Ports │                  ┌────────────────┐
│ - Containers    │─────────────────►│Redaction Engine│
│                 │                  │- Multi-Pattern │
│                 │                  │- URL Sanitizer │
│                 │                  │- Path Privacy  │
│                 │                  └────────────────┘
└─────────────────┘
```

## Subsystem Details

### 1. Detectors & Detection Context
Each detector inherits from `Detector` and receives a read-only `DetectionContext` (containing project root path, environment overrides, and configuration). Detectors never execute arbitrary project scripts or mutative commands.

Detector results return a typed `DetectionStatus`:
- `DETECTED`: Successfully inspected and found.
- `NOT_FOUND`: Successfully inspected, but the tool/service is not installed on this machine.
- `NOT_APPLICABLE`: Checked, but not relevant for this project type (e.g. Node detector in a pure Python project).
- `UNSUPPORTED`: Platform does not support this inspection.
- `ERROR`: An unexpected exception occurred during detector execution (gracefully isolated without crashing the scan).

### 2. Safe Subprocess Execution
Subprocesses run under strict security guardrails:
- `shell=False` enforced across all executions with direct argument lists (`list[str]`).
- Bounded timeouts (default: 5.0 seconds).
- Buffer and memory limit clamping (default: 5MB) with truncation markers.
- Robust exception handling mapping missing executables to exit code `127` and timeouts to `124`.

### 3. Security & Redaction Pipeline
Before any detector payload reaches persistence, the terminal, or diff engines, it passes through the Redaction Pipeline:
1. **Secret Pattern Scanning**: Identifies sensitive environment keys (`*KEY*`, `*SECRET*`, `*TOKEN*`, `*PASSWORD*`, `*PASSWD*`, `*PRIVATE_KEY*`, `AWS_*`, `GITHUB_*`, JWT, Bearer tokens, etc.).
2. **Value Redaction**: Masks actual secret values into `{"present": true, "secret": true}`.
3. **URL Sanitization**: Strips credentials across database and web schemes (`postgres://`, `redis://`, `mongodb://`, `mysql://`, `amqp://`, `https://`) and redacts query parameters (`?token=...`, `?key=...`).
4. **Path Privacy**: Masks user home directories as `<USER_HOME>/...` and normalizes relative project paths.

### 4. Canonicalization & Deterministic Fingerprinting
Environment fingerprints are 100% deterministic:
- Volatile fields (current timestamps, execution PIDs, random IDs, local temporary directory paths, and source code Git commits) are stripped from the fingerprint input.
- Dictionary keys and unordered lists (dependencies, containers, ports) are canonically sorted by primary keys.
- JSON is serialized with sorted keys and no extraneous whitespace (`separators=(',', ':')`).
- A SHA-256 digest is generated from the canonical bytes.

### 5. Diff & Doctor Engine
- **Diff Engine**: Performs semantic comparison between baseline and current state, classifying items as `ADDED`, `REMOVED`, `CHANGED`, `UNCHANGED`.
- **Doctor Engine**: Consumes structured diffs and scan states to synthesize actionable diagnostics (`code`, `severity`, `title`, `evidence`, `explanation`, `suggested_action`). Maintains strict separation between observed facts (`evidence`), inferred explanations, and read-only remediation advice.

### 6. Atomic Storage Engine
Snapshots are stored in `.runmark/snapshots/<snapshot-id>.json`.
- Uses atomic file replacement (`_atomic_write` via temporary file + `os.fsync` + `os.replace`) to prevent corrupted states.
- The active snapshot pointer is stored atomically in `.runmark/current.json`.
- Corrupted JSON or schema-incompatible snapshot files are caught safely with structured error handling.

### 7. Export Sanitization & Diagnostic Reporting Subsystem (`v0.1.2`)
The `Reporter` service coordinates report synthesis and export:
```text
RunmarkState + Doctor -> DiagnosticReport
                              │
                              ▼
                   [ExportSanitizer Engine]
                   - Multi-scheme URI credential stripping
                   - Deep path normalization (<USER_HOME>, <PROJECT_ROOT>)
                   - Evidence & diagnostic field scrub
                              │
                              ▼
                   [Markdown / JSON Renderers]
                              │
                              ▼
                   [Pre-Export Security Boundary Scan]
                   - Zero credential leakage verification
                   - Immediate abort with exit code 4 on violation
                              │
                              ▼
                   [Atomic File Export / Clean stdout]
```
### 8. Environment Contracts & Evidence Architecture (`v0.2.0` & `v0.2.1`)
Runmark provides full contract lifecycle management from project evidence manifests to live runtime proof:

```text
┌─────────────────────────────────────────────────────────────┐
│                      Project Manifests                      │
│   (pyproject.toml, package.json, Dockerfile, compose.yaml)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      EvidenceCollector                      │
│  - Signal classification: EXPLICIT > INFERRED > OBSERVED    │
│  - Strict manifest parsing (PEP 508, npm ranges, compose)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      ContractGenerator                      │
│  - Normalizes runtimes, dependencies, services, env, ports  │
│  - ContractCanonicalizer: deterministic structure & hash    │
│  - Multi-pass Security Boundary & JSON Schema Validation    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
   ┌───────────────────────────┐ ┌───────────────────────────┐
   │    ContractInitService    │ │    ContractDiffService    │
   │  - Atomic runmark.json    │ │  - Semantic Diff Engine   │
   │  - --dry-run / --force    │ │  - Git HEAD baseline      │
   └───────────────────────────┘ └───────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                     ContractEvaluator                       │
│  - Evaluates Live RunmarkState vs Contract Requirements     │
│  - VersionConstraint matching (numerical, compound ranges)  │
│  - Produces ContractCheckResult                             │
│  - Detailed Diagnostic Explanations (--explain mode)        │
└─────────────────────────────────────────────────────────────┘
```

- **EvidenceCollector**: Discovers signals across manifests and classifies them (`EXPLICIT`, `INFERRED`, `OBSERVED`).
- **ContractGenerator**: Synthesizes a valid, canonical `RunmarkContract` with guaranteed zero secret retention.
- **ContractDiffEngine**: Computes structured semantic changes (`ADDED`, `REMOVED`, `CHANGED`, `UNCHANGED`) against previous or Git-committed contracts.
- **ContractEvaluator & Diagnostic Breakdown**: Evaluates compatibility and generates rich diagnostic breakdowns with explicit evidence, causal why explanations, and actionable remediation steps.


