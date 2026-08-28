# Runmark Specification (v1.0)

## 1. Data Model Specification

A Runmark representation encapsulates the runnable conditions of a project codebase.

### Top-Level State (`RunmarkState`)
```json
{
  "runmark": {
    "id": "snap_01HXYZ789...",
    "created_at": "2026-08-15T12:00:00Z",
    "tool_version": "0.1.0",
    "schema_version": "1.0",
    "environment_fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "message": "Baseline working state"
  },
  "project": {
    "name": "my-service",
    "root": "/path/to/project",
    "languages": ["python", "javascript"],
    "frameworks": ["django", "react"],
    "package_managers": ["uv", "pnpm"],
    "containerization": ["docker", "compose"]
  },
  "git": {
    "is_repository": true,
    "branch": "main",
    "commit": "a81f29c0f",
    "dirty": false
  },
  "system": {
    "os_name": "Windows",
    "os_version": "11.0.22631",
    "architecture": "AMD64"
  },
  "runtimes": {
    "python": {
      "name": "python",
      "installed": true,
      "version": "3.12.4",
      "status": "detected",
      "executable_path": null
    }
  },
  "dependencies": [
    {
      "name": "django",
      "manager": "uv",
      "declared": ">=5.0",
      "resolved": "5.0.6",
      "kind": "direct"
    }
  ],
  "services": [
    {
      "name": "postgresql",
      "installed": true,
      "running": true,
      "detected_version": "16.3",
      "expected_version": "16",
      "status": "detected",
      "port": 5432
    }
  ],
  "environment": {
    "variables": {
      "DATABASE_URL": {
        "name": "DATABASE_URL",
        "required": true,
        "present": true,
        "secret": true,
        "source": ".env.example"
      }
    }
  },
  "network": [
    {
      "port": 5432,
      "service": "postgresql",
      "expected": true,
      "occupied": true,
      "status": "in_use"
    }
  ],
  "containers": [
    {
      "service_name": "db",
      "image": "postgres",
      "tag": "16-alpine",
      "running_status": "running"
    }
  ]
}
```

## 2. Fingerprinting & Canonicalization

The `environment_fingerprint` represents the canonical digest of the environment:
1. **Scope**: Includes `system`, `runtimes`, `dependencies`, `services`, `environment` (variable presence/requirements), `network`, and `containers`.
2. **Exclusions**: Excludes `git.commit`, `git.dirty`, `runmark.id`, `runmark.created_at`, `runmark.message`, local absolute temporary paths, hostnames, and usernames.
3. **Ordering**: Unordered collections (e.g. `dependencies`, `services`, `containers`, `network`) are deterministically sorted by their natural primary keys (`name`, `service_name`, `port`).
4. **Digest**: Computed as `SHA-256(canonical_json_bytes)`.

## 3. Semantic Diffing Rules

Differences between two Runmark states are evaluated with strict classifications and rule-based severity:
- `CRITICAL`: Missing required runtime, missing required environment variable, stopped mandatory service, major runtime version incompatibility.
- `WARNING`: Runtime minor version mismatch, service version mismatch, port conflicts, unexpected container status.
- `INFO`: Dependency patch version changes, dev dependency additions/removals, branch change.

## 4. Verification & Share Exit Codes

The `runmark verify` and `runmark share` commands yield standard exit codes suitable for CI pipelines and automation:
- `0`: Success (verification passed / report generated cleanly).
- `1`: Verification failed (critical or warning environment drift detected).
- `2`: Invalid CLI usage, non-existent path, or file exists without `--force`.
- `3`: Internal error / detector failure.
- `4`: Security violation (credential contamination detected at export boundary or attempt to persist unredacted secret).

## 5. Diagnostic Report Specification (`DiagnosticReport`)

A `DiagnosticReport` synthesizes the environment state with structured diagnostic issues into a portable artifact:

```json
{
  "metadata": {
    "report_id": "rpt_39a1c8f072bd",
    "generated_at": "2026-08-26T12:00:00Z",
    "runmark_version": "0.2.0",
    "schema_version": "1.0",
    "report_format_version": 1,
    "environment_fingerprint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "summary": "1 critical issue, 1 warning detected"
  },
  "project": { ... },
  "system": { ... },
  "runtimes": { ... },
  "dependencies": [ ... ],
  "services": [ ... ],
  "environment": { ... },
  "network": [ ... ],
  "containers": [ ... ],
  "git": { ... },
  "diagnostics": [
    {
      "code": "ENV_MISSING_REQUIRED",
      "severity": "CRITICAL",
      "category": "environment",
      "title": "Required environment variable missing",
      "evidence": {
        "variable": "DATABASE_URL",
        "expected": "present",
        "actual": "missing"
      },
      "explanation": "The project configuration marks 'DATABASE_URL' as required, but it is not set.",
      "suggested_action": "Add 'DATABASE_URL' to your local environment or .env file."
    }
  ]
}
```

---

## 6. Environment Contract Specification (`RunmarkContract`)

An Environment Contract (`runmark.json`) formally defines expected platform, runtime, dependency, service, environment, network, and container requirements for a project repository.

```json
{
  "$schema": "https://runmark.dev/schemas/contract-v1.json",
  "version": 1,
  "project": { "name": "my-service" },
  "platform": { "os": ["linux", "windows"], "architecture": ["x86_64", "arm64"] },
  "runtime": { "python": "3.12.x", "node": ">=20" },
  "dependencies": { "python": { "fastapi": ">=0.100.0" } },
  "services": { "postgresql": { "version": ">=15", "required": true } },
  "environment": { "required": ["DATABASE_URL"], "optional": ["DEBUG"] },
  "network": { "ports": { "8000": { "protocol": "tcp", "required": true } } },
  "containers": { "docker": { "required": true }, "compose": { "required": true } }
}
```

### CLI Verification Exit Codes
- `0`: Success / Verified / Satisfied
- `1`: Contract unsatisfied / Drift detected
- `2`: Missing file / Schema validation failure / Bad arguments
- `3`: Internal detector failure / Uncaught exception
- `4`: Security violation / Credential leak detected
