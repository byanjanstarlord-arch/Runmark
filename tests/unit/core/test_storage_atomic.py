"""Hardened tests for atomic storage operations, snapshot immutability, and corruption resilience."""

import json

import pydantic
import pytest

from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.system import SystemState
from runmark.storage.filesystem import FilesystemStorage


def _make_dummy_state(snap_id="snap_123"):
    return RunmarkState(
        runmark=RunmarkMetadata(
            id=snap_id,
            created_at="2026-01-01T00:00:00Z",
            tool_version="0.1.0",
            schema_version="1.0",
            environment_fingerprint="abc123456789",
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


def test_storage_atomic_save_and_immutability(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.initialize()

    # 1. Save Snapshot A
    state_a = _make_dummy_state(snap_id="snap_alpha")
    storage.save_snapshot(state_a, set_as_current=True)

    # 2. Save Snapshot B
    state_b = _make_dummy_state(snap_id="snap_beta")
    storage.save_snapshot(state_b, set_as_current=True)

    # 3. Verify Snapshot A was not mutated
    loaded_a = storage.load_snapshot("snap_alpha")
    assert loaded_a.runmark.id == "snap_alpha"

    loaded_b = storage.load_snapshot("snap_beta")
    assert loaded_b.runmark.id == "snap_beta"

    # Current points to beta
    current = storage.load_current()
    assert current is not None
    assert current.runmark.id == "snap_beta"


def test_storage_corrupted_json_snapshot(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.initialize()

    corrupt_file = storage.paths.snapshots_dir / "snap_corrupted.json"
    corrupt_file.write_text("{ unclosed invalid json {{{", encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        storage.load_snapshot("snap_corrupted")
    assert "corrupted" in str(exc.value).lower()


def test_storage_missing_required_fields_in_snapshot(tmp_path):
    storage = FilesystemStorage(tmp_path)
    storage.initialize()

    invalid_file = storage.paths.snapshots_dir / "snap_incomplete.json"
    invalid_file.write_text(json.dumps({"runmark": {"id": "snap_incomplete"}}), encoding="utf-8")

    with pytest.raises(pydantic.ValidationError):
        storage.load_snapshot("snap_incomplete")
