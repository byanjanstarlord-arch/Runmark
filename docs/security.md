# Runmark Security Architecture

## 1. Zero-Secret Principle

Developer environments often contain sensitive secrets, such as API keys, tokens, private keys, and database connection strings. Runmark provides a formal security guarantee:

> **Runmark observes metadata, never secret values.**

### Secret Detection Pipeline
All raw detector results pass through an in-memory redactor before model construction, canonical hashing, console rendering, or snapshot persistence:

```text
[Raw Detector Payload]
         │
         ▼
[Regex & Pattern Matching] (Variable names, value signatures, JWT, Bearer, DB URI credentials)
         │
         ▼
[Masking Engine] (Transforms values -> {present: bool, secret: bool, source: str})
         │
         ▼
[Sanitization Engine] (Sanitizes URLs, strips query params, masks <USER_HOME> paths)
         │
         ▼
[Canonical State & Atomic Persistence]
```

### Supported Secret Signatures
Runmark's multi-pattern redactor automatically recognizes and redacts:
- **API Keys & Cloud Tokens**: OpenAI (`sk-...`), Stripe (`sk_live_...`, `sk_test_...`), GitHub (`ghp_...`, `gho_...`), GitLab (`glpat-...`), Slack (`xoxb-...`), Google API Keys (`AIza...`), AWS (`AKIA...`, `ASIA...`, `AQoDYXdz...`).
- **Cryptographic Materials**: RSA, EC, OPENSSH, PGP, and DSA private keys (`-----BEGIN ... PRIVATE KEY-----`).
- **Authentication Tokens**: JSON Web Tokens (`eyJ...`), Bearer headers.
- **Database & Network URIs**: Embedded credentials across `postgres://`, `mysql://`, `redis://`, `mongodb://`, `amqp://`, `couchdb://`, `https://`, `ftp://`.
- **Sensitive Query Parameters**: Strips `token`, `key`, `api_key`, `secret`, `password`, `auth`, `signature`, `sig` from URLs.
- **Variable Name Matching**: Automatically flags variables containing `PASSWORD`, `PASSWD`, `SECRET`, `TOKEN`, `API_KEY`, `AUTH`, `PRIVATE_KEY`, `CREDENTIAL`, `SALT`, `PIN`, etc.

---

## 2. Path Privacy Masking

To prevent username and personal path leakage across developer machines and team repositories:
- Paths within the project root are stored as clean relative POSIX paths (`src/index.ts`).
- Absolute paths under user home directories are masked as `<USER_HOME>/...`.

---

## 3. Safe Subprocess Execution

Runmark never executes arbitrary user scripts (`setup.sh`, `Makefile`, `npm install`, `pip install`). Subprocesses run under strict security guardrails:
- **Zero Shell Interpolation**: Commands are strictly passed as argument lists (`list[str]`), enforcing `shell=False` to neutralize injection attacks.
- **Bounded Execution Time**: All commands run with an enforced timeout (default: 5.0 seconds).
- **Buffer & Memory Clamping**: Output streams are capped at 5MB (`DEFAULT_MAX_OUTPUT_BYTES`) with safe truncation markers to eliminate denial-of-service memory exhaustion.
- **Safe Binary Decoding**: Decodes stdout/stderr with `errors="replace"` to prevent Unicode decode crashes on corrupt or binary outputs.

---

## 4. Atomic Filesystem Storage

To prevent race conditions, half-written snapshots, or corruption during power loss:
- Snapshots are written to a unique temporary file (`.tmp_*`) in the target directory with explicit `os.fsync()`.
- Atomic rename via `os.replace` commits the snapshot atomically.
- Corrupted snapshot files are caught and isolated with clear error diagnostics without crashing the application.

---

## 5. Local-First & Zero Telemetry

Runmark:
- Never communicates with external networks, analytics, or telemetry servers.
- Does not require cloud accounts, user registration, or authentication tokens.
- Stores snapshots exclusively on the local filesystem in `.runmark/`.
- Operates 100% offline.

---

## 6. Export Security Boundary (`runmark share`)

When exporting diagnostic reports to Markdown or JSON for external communication (e.g. GitHub issues, Slack, bug reports), Runmark enforces a dedicated export security boundary via `ExportSanitizer`:

1. **Multi-Scheme URI Sanitization**: Removes passwords and basic auth credentials from all connection URIs in state and diagnostic evidence dictionaries.
2. **Deep Path Normalization**: Masks user home directories (`<USER_HOME>`) and project roots (`<PROJECT_ROOT>`) across all diagnostic titles, explanations, and suggested remediation steps.
3. **Pre-Export Canary Secret Scanning**: Scans the rendered Markdown or JSON text immediately prior to file writing or stdout emission.
4. **Immediate Abort on Contamination (Exit Code 4)**: If any secret pattern is detected in the rendered export, the export aborts instantly with exit code `4`, deletes all temporary files, leaves existing files untouched, and outputs a generic security alert without echoing the secret value.

---

## 7. Contract Security Boundary (`runmark contract init`, `validate`, `check`)

Runmark enforces strict zero-secret guarantees across the entire contract lifecycle:

1. **Requirement-Only Definition**: Contracts declare requirement names and constraints only (e.g. `"required": ["DATABASE_URL"]`), never secrets, API keys, credentials, or values.
2. **Multi-Pass Sanitizer Scanning**: During `runmark contract init`, `runmark contract validate`, and `runmark check`, `ContractSanitizer` scans canonical contract JSON representations against known secret signatures and canary patterns.
3. **Fail-Safe Abort (Exit Code 4)**: If unredacted credentials or sensitive tokens are detected in contract candidate data, temporary files are immediately deleted, existing contracts are untouched, and execution halts with exit code `4`.


