"""Integration test for snapshot creation and persistence."""

from runmark.core.snapshot import SnapshotManager


def test_snapshot_lifecycle(tmp_path):
    # Setup mock project files
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-snap"\n', encoding="utf-8")
    (tmp_path / ".env.example").write_text("API_KEY=\n", encoding="utf-8")

    mgr = SnapshotManager(tmp_path)
    snapshot = mgr.create_snapshot(message="Integration baseline test")

    assert snapshot.runmark.id.startswith("snap_")
    assert snapshot.runmark.message == "Integration baseline test"
    assert snapshot.runmark.environment_fingerprint

    # Retrieve current
    current = mgr.get_current()
    assert current is not None
    assert current.runmark.id == snapshot.runmark.id
    assert current.runmark.environment_fingerprint == snapshot.runmark.environment_fingerprint

    # List history
    history = mgr.list_history()
    assert len(history) == 1
    assert history[0].runmark.id == snapshot.runmark.id
