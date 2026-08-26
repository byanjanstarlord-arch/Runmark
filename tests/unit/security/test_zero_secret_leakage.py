"""Security test suite to guarantee zero secret leakage into state, snapshots, JSON, and reports."""

import json

from runmark.core.doctor import Doctor
from runmark.core.snapshot import SnapshotManager

SECRET_TEST_STRINGS = [
    "sk_live_super_secret_stripe_api_key_value_9999",
    "ghp_test_github_personal_access_token_1234567890",
    "super_secret_database_password_never_expose",
    "my_jwt_super_secret_signing_key_4567",
]


def test_secrets_never_leak_into_snapshot_state(tmp_path):
    env_example = tmp_path / ".env.example"
    env_example.write_text(
        "STRIPE_SECRET_KEY=\nGITHUB_TOKEN=\nDATABASE_PASSWORD=\nJWT_SECRET=\n",
        encoding="utf-8",
    )

    env_overrides = {
        "STRIPE_SECRET_KEY": SECRET_TEST_STRINGS[0],
        "GITHUB_TOKEN": SECRET_TEST_STRINGS[1],
        "DATABASE_PASSWORD": SECRET_TEST_STRINGS[2],
        "JWT_SECRET": SECRET_TEST_STRINGS[3],
    }

    mgr = SnapshotManager(tmp_path)
    # Inject overrides into scanner
    mgr.scanner.environment = env_overrides

    snapshot = mgr.create_snapshot(message="Security verification snapshot")
    json_serialized = snapshot.model_dump_json()

    # Verify that NONE of the secret strings exist anywhere in serialized JSON
    for secret in SECRET_TEST_STRINGS:
        assert secret not in json_serialized

    # Read the persisted snapshot file from disk and assert no secret
    disk_file = mgr.storage.paths.get_snapshot_path(snapshot.runmark.id)
    disk_content = disk_file.read_text(encoding="utf-8")
    for secret in SECRET_TEST_STRINGS:
        assert secret not in disk_content

    # Check Doctor diagnosis output
    doctor_report = Doctor.diagnose_state(snapshot)
    doctor_json = json.dumps(doctor_report.__dict__, default=str)
    for secret in SECRET_TEST_STRINGS:
        assert secret not in doctor_json
