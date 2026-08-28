# Security Policy

## Security Philosophy

Runmark observes and fingerprints the conditions under which a software project runs. Because developer environments frequently contain secrets, credentials, and API keys, **security and data privacy are non-negotiable architectural principles**.

### Core Guarantees

1. **Observe Metadata, Never Collect Secrets**: Runmark inspects configuration metadata (e.g. `present: true`, `secret: true`, `required: true`) and never stores secret values, API keys, private keys, database passwords, or auth tokens.
2. **Deterministic Redaction**: All detected data passes through a mandatory redaction pipeline before any terminal output, log emission, JSON serialization, or file persistence.
3. **Export Security Boundary**: Diagnostic exports generated via `runmark share` undergo deep structural sanitization followed by canary pattern scanning. If any credential or secret pattern is detected in the rendered export, generation is immediately aborted with exit code `4` and all temporary files are purged.
4. **Local-First & Zero Telemetry**: Runmark runs 100% locally on your machine. There is no telemetry, cloud upload, analytics, or remote API interaction.
5. **Safe Subprocesses Only**: Runmark never executes arbitrary project scripts (`setup.sh`, `Makefile`, `npm install`, `pip install`). Subprocesses are strictly read-only commands with bounded timeouts executed without shell interpolation.

## What Runmark Never Stores or Shares

- Environment variable values that match secret patterns or `.env` credential structures
- Database passwords and connection strings containing credentials (e.g. `postgres://user:pass@host/db` is sanitized to `postgres://host/db`)
- API keys, OAuth tokens, personal access tokens, session tokens, JWTs, cloud provider keys
- Private keys (`*.pem`, `*.key`, etc.)
- Absolute user home directories and local usernames (masked to `<USER_HOME>` or `<PROJECT_ROOT>`)
- Unsanitized Git remote URLs containing basic auth credentials

## Reporting a Vulnerability

If you discover a potential security issue or secret leak in Runmark:

1. **Do NOT** open a public GitHub issue.
2. Email security reports to `security@runmark.dev` (or open a private GitHub Security Advisory).
3. Include detailed steps to reproduce the vulnerability, along with relevant environment details.
4. We will acknowledge receipt within 48 hours and work with you on coordinated disclosure.
