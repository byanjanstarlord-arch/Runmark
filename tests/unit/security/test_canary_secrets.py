"""Adversarial security canary test suite.

Validates that fake canary secrets of all types (API keys, tokens, passwords, private keys, URIs)
never escape into snapshots, JSON outputs, terminal renders, diagnostics, doctor reports,
or persisted filesystem storage.
"""

import json

from runmark.core.doctor import Doctor
from runmark.core.scanner import Scanner
from runmark.core.snapshot import SnapshotManager
from runmark.detectors.base import DetectionContext
from runmark.detectors.environment.env import EnvDetector
from runmark.models.common import DetectionStatus
from runmark.security.redactor import SecretRedactor
from runmark.security.secret_patterns import contains_secret_value, is_secret_variable_name

CANARY_SECRETS = {
    "OPENAI_KEY": "sk-proj-CANARY_SECRET_OPENAI_9999999999999999999999999999",
    "AWS_KEY_ID": "AKIAIOSFODNN7CANARY01",
    "AWS_SECRET": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYCANARYSECRET",
    "AWS_TOKEN": "AQoDYXdzEJr1CANARY_SESSION_TOKEN_MUST_NEVER_ESCAPE_TEST_1234567890",
    "GITHUB_TOKEN": "ghp_CANARY_GITHUB_PAT_TOKEN_SECRET_NEVER_LEAK_36CHARS_LONG",
    "GITLAB_TOKEN": "glpat-CANARY_GITLAB_PAT_SECRET_VAL",
    "DB_PASS": "SuperSecret_Postgres_Password_Canary!#",
    "STRIPE_KEY": "sk_live_CANARY_STRIPE_LIVE_KEY_123456789012",
    "SLACK_TOKEN": "CANARY_SECRET_SLACK_TOKEN_1234567890",
    "GOOGLE_API_KEY": "AIzaSyCANARY_GOOGLE_API_KEY_SEC_1234567",
    "JWT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvbmRvZSIsImlhdCI6MTUxNjIzOTAyMn0.CANARY_JWT_SIGNATURE_MUST_NEVER_ESCAPE_ANYWHERE",
    "BEARER_TOKEN": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_CANARY_BEARER_TOKEN_9999",
    "PRIVATE_KEY_PEM": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0CANARY_PRIVATE_KEY_MATERIAL_NEVER_LEAK_OUTSIDE==\n-----END RSA PRIVATE KEY-----",
    "DATABASE_URI": "postgres://superuser:CANARY_DB_PASS_123@db.internal.host:5432/production_db",
    "REDIS_URI": "redis://default:CANARY_REDIS_PASS_456@redis.internal.host:6379/0",
    "MONGO_URI": "mongodb://admin:CANARY_MONGO_PASS_789@mongo.internal.host:27017/admin",
    "GENERIC_PASSWORD": "P@ssw0rd_CANARY_NEVER_ESCAPE_VAL_2026",
}


def test_canary_variable_names_classified_as_secret():
    secret_names = [
        "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GITHUB_TOKEN",
        "DATABASE_PASSWORD",
        "DB_PASSWD",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "MONGO_INITDB_ROOT_PASSWORD",
        "STRIPE_SECRET_KEY",
        "JWT_SECRET",
        "MASTER_KEY",
        "DEPLOY_KEY",
        "WEBHOOK_SECRET",
        "CANARY_SECRET_VAR",
        "SESSION_SECRET",
        "CLIENT_SECRET",
    ]
    for name in secret_names:
        assert is_secret_variable_name(name) is True, (
            f"Failed to classify secret variable name: {name}"
        )


def test_canary_secret_values_classified_as_secret():
    for name, value in CANARY_SECRETS.items():
        if name in {"GENERIC_PASSWORD", "AWS_SECRET", "DB_PASS"}:
            continue  # Protected by variable name classification rather than prefix pattern
        assert contains_secret_value(value) is True, (
            f"Failed to detect canary secret value for: {name}"
        )


def test_env_detector_never_stores_canary_values(tmp_path):
    # Write .env and .env.example with canary secrets
    env_content = "\n".join(f"{name}={val}" for name, val in CANARY_SECRETS.items())
    (tmp_path / ".env").write_text(env_content, encoding="utf-8")
    (tmp_path / ".env.example").write_text(env_content, encoding="utf-8")

    detector = EnvDetector()
    context = DetectionContext(project_root=tmp_path, environment={})
    res = detector.detect(context)

    assert res.status == DetectionStatus.DETECTED
    env_state = res.data

    # Dump the environment state to JSON
    json_dump = json.dumps(env_state.model_dump(mode="json"))

    # Assert that NONE of the secret values appear in the serialized JSON
    for secret_key, canary_val in CANARY_SECRETS.items():
        assert canary_val not in json_dump, f"Canary value leaked in env state for {secret_key}"


def test_full_pipeline_canary_zero_leakage_in_snapshots(tmp_path):
    # Set up project with sensitive files and environment
    env_file = tmp_path / ".env"
    env_content = (
        f"DATABASE_URL={CANARY_SECRETS['DATABASE_URI']}\n"
        f"OPENAI_API_KEY={CANARY_SECRETS['OPENAI_KEY']}\n"
        f"JWT_SECRET={CANARY_SECRETS['JWT_TOKEN']}\n"
        f"AWS_SECRET_ACCESS_KEY={CANARY_SECRETS['AWS_SECRET']}\n"
    )
    env_file.write_text(env_content, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "canary-test"\n', encoding="utf-8")

    # Run scan
    scanner = Scanner(tmp_path, environment_override=dict(CANARY_SECRETS))
    state = scanner.scan()

    # Save snapshot
    storage = SnapshotManager(tmp_path)
    storage.storage.save_snapshot(state, set_as_current=True)

    # Read all files in .runmark/ recursively
    runmark_dir = tmp_path / ".runmark"
    all_persisted_content = ""
    for f in runmark_dir.rglob("*.json"):
        all_persisted_content += f.read_text(encoding="utf-8") + "\n"

    # Verify zero canary secret leakage in any persisted file
    for secret_name, secret_val in CANARY_SECRETS.items():
        assert secret_val not in all_persisted_content, (
            f"Canary secret {secret_name} leaked in .runmark storage!"
        )

    # Verify Doctor report zero secret leakage
    report = Doctor.diagnose_state(state)
    report_dump = json.dumps([i.__dict__ for i in report.issues], default=str)
    for secret_name, secret_val in CANARY_SECRETS.items():
        assert secret_val not in report_dump, (
            f"Canary secret {secret_name} leaked in Doctor report!"
        )


def test_text_and_dictionary_redaction():
    payload = {
        "user": "developer",
        "api_key": CANARY_SECRETS["OPENAI_KEY"],
        "connection": CANARY_SECRETS["DATABASE_URI"],
        "nested": {
            "token": CANARY_SECRETS["GITHUB_TOKEN"],
            "private_key": CANARY_SECRETS["PRIVATE_KEY_PEM"],
        },
        "list_items": [
            CANARY_SECRETS["STRIPE_KEY"],
            CANARY_SECRETS["JWT_TOKEN"],
        ],
    }

    sanitized = SecretRedactor.sanitize_dictionary(payload)
    sanitized_str = json.dumps(sanitized)

    for secret_name, secret_val in CANARY_SECRETS.items():
        assert secret_val not in sanitized_str, (
            f"Secret {secret_name} leaked after dictionary sanitization!"
        )
