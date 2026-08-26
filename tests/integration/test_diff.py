"""Integration test for snapshot and live diffing."""

from runmark.core.diff import DiffClassification, DiffEngine
from runmark.core.snapshot import SnapshotManager


def test_diff_against_modified_project(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("django>=5.0\n", encoding="utf-8")

    mgr = SnapshotManager(tmp_path)
    base_snapshot = mgr.create_snapshot(message="Base")

    # Modify requirements in project
    req_file.write_text("django>=5.0\nrequests>=2.31\n", encoding="utf-8")

    live_state = mgr.scanner.scan()
    diff = DiffEngine.compare(base_snapshot, live_state)

    assert not diff.is_identical
    added_req = next((i for i in diff.items if i.item_name == "requests"), None)
    assert added_req is not None
    assert added_req.classification == DiffClassification.ADDED
