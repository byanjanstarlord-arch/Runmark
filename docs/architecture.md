# Runmark Architecture Guide

This document describes the architectural design and structural layers of Runmark v0.1.

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                           CLI App                           │
│     (init, scan, snapshot, diff, verify, doctor, version)   │
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
│ - Runtimes      │          │  - Immutable Snapshot Store    │
│ - Projects      │          └────────────────────────────────┘
│ - Dependencies  │                           ▲
│ - Services      │                           │
│ - Environment   │                           │
│ - Network/Ports │                  ┌────────────────┐
│ - Containers    │─────────────────►│Redaction Engine│
└─────────────────┘                  └────────────────┘
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

### 2. Security & Redaction Pipeline
Before any detector payload reaches persistence, the terminal, or diff engines, it passes through the Redaction Pipeline:
1. **Secret Pattern Scanning**: Identifies sensitive environment keys (`*KEY*`, `*SECRET*`, `*TOKEN*`, `*PASSWORD*`, `*PASSWD*`, `*PRIVATE_KEY*`, `AWS_*`, `GITHUB_*`, etc.).
2. **Value Redaction**: Masks actual secret values into `{"present": true, "secret": true}`.
3. **URL Sanitization**: Strips basic-auth credentials embedded in Git remote URLs (e.g., `https://user:token@github.com/...` -> `https://github.com/...`).

### 3. Canonicalization & Fingerprinting
Environment fingerprints must be 100% deterministic:
- Volatile fields (current timestamps, execution PIDs, random IDs, local temporary directory paths, and source code Git commits) are stripped from the fingerprint input.
- Dictionary keys and unordered lists (dependencies, containers, ports) are canonically sorted.
- JSON is serialized with sorted keys and no extraneous whitespace (`separators=(',', ':')`).
- A SHA-256 digest is generated from the canonical bytes.

### 4. Diff & Doctor Engine
- **Diff Engine**: Performs semantic comparison between baseline and current state, classifying items as `ADDED`, `REMOVED`, `CHANGED`, `UNCHANGED`.
- **Doctor Engine**: Consumes structured diffs and scan states to synthesize actionable diagnostics (`code`, `severity`, `title`, `evidence`, `explanation`, `suggested_action`).

### 5. Storage
Snapshots are stored as immutable JSON files in `.runmark/snapshots/<snapshot-id>.json`. The most recent snapshot is referenced in `.runmark/current.json`.
