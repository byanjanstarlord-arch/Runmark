# Runmark Security Architecture

## 1. Zero-Secret Principle

Developer environments often contain sensitive secrets, such as API keys, tokens, and database credentials. Runmark is built with strict privacy and security guarantees:

> **Runmark observes metadata, never secret values.**

### Secret Detection Pipeline
All raw scanner results pass through an in-memory redactor before serialization, console rendering, or snapshot persistence:

```text
[Raw Detector Payload]
         │
         ▼
[Regex & Pattern Matching] (Variable names & value signatures)
         │
         ▼
[Masking Engine] (Transforms values -> {present: bool, secret: bool})
         │
         ▼
[Sanitization Engine] (Sanitizes URLs, paths, usernames)
         │
         ▼
[Canonical State Persistence]
```

## 2. Safe Subprocess Execution

Runmark never executes arbitrary project scripts (`setup.sh`, `Makefile`, `npm install`, `pip install`). Subprocesses run under the following constraints:
- **No Shell Interpolation**: Commands are passed as argument lists (`List[str]`), avoiding shell expansion and injection vulnerabilities (`shell=False`).
- **Bounded Timeouts**: All detector subprocesses have a default timeout (typically 2–5 seconds) to prevent hanging.
- **Read-Only Commands**: Detectors execute standard inspection commands (e.g. `python --version`, `git rev-parse HEAD`, `docker ps`).

## 3. Local-First & Zero Telemetry

Runmark v0.1:
- Never communicates with external analytics servers
- Does not collect telemetry or usage data
- Stores snapshots exclusively on the local filesystem in `.runmark/`
- Requires no cloud accounts or API keys
