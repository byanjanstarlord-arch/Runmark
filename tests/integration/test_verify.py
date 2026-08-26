"""Integration test for environment verification."""

from runmark.core.snapshot import SnapshotManager
from runmark.core.verifier import Verifier


def test_verify_identical_environment_succeeds(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "verify-app"\n', encoding="utf-8")
    mgr = SnapshotManager(tmp_path)
    snapshot = mgr.create_snapshot()

    live_state = mgr.scanner.scan()
    verifier = Verifier()
    result = verifier.verify(snapshot, live_state)

    assert result.exit_code == 0
    assert result.passed is True
