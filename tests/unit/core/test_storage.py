"""Unit tests for filesystem storage manager."""

from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.system import SystemState
from runmark.storage.filesystem import FilesystemStorage


def _make_state(snap_id="snap_1", created_at="2026-01-01T00:00:00Z"):
    return RunmarkState(
        runmark=RunmarkMetadata(
            id=snap_id,
            created_at=created_at,
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="abc1234567890",
        ),
        project=ProjectState(name="app", root="app"),
        git=GitState(is_repository=False),
        system=SystemState(os_name="Linux", os_version="6.1", architecture="x86_64"),
        runtimes={},
        dependencies=[],
        services=[],
        environment=EnvironmentState(),
        network=[],
        containers=[],
    )


def test_storage_initialize(tmp_path):
    storage = FilesystemStorage(tmp_path)
    assert storage.paths.is_initialized() is False

    created = storage.initialize()
    assert created is True
    assert storage.paths.is_initialized() is True
    assert storage.paths.config_file.exists()

    # Re-initialization without force
    created_again = storage.initialize(force=False)
    assert created_again is False


def test_storage_save_and_load_snapshot(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.initialize()

    state = _make_state(snap_id="snap_test_999")
    storage.save_snapshot(state, set_as_current=True)

    loaded = storage.load_snapshot("snap_test_999")
    assert loaded.runmark.id == "snap_test_999"
    assert loaded.runmark.environment_fingerprint == "abc1234567890"

    current = storage.load_current()
    assert current is not None
    assert current.runmark.id == "snap_test_999"


def test_storage_list_snapshots_chronological(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.initialize()

    s1 = _make_state(snap_id="snap_1", created_at="2026-01-01T10:00:00Z")
    s2 = _make_state(snap_id="snap_2", created_at="2026-01-02T10:00:00Z")
    storage.save_snapshot(s2)
    storage.save_snapshot(s1)

    history = storage.list_snapshots()
    assert len(history) == 2
    assert history[0].runmark.id == "snap_1"
    assert history[1].runmark.id == "snap_2"
