"""Filesystem storage manager for Runmark snapshots and configuration."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from runmark import __schema_version__, __version__
from runmark.models.runmark import RunmarkState
from runmark.storage.paths import StoragePaths


def _atomic_write(target_path: Path, content: str) -> None:
    """Safely write string content to target_path using atomic replacement."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=str(target_path.parent),
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, target_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


class FilesystemStorage:
    """Handles local storage of Runmark configuration, snapshots, and current state."""

    def __init__(self, project_root: Path | str):
        self.paths = StoragePaths(project_root)

    def initialize(self, force: bool = False) -> bool:
        """Initialize .runmark directory structure and default config.toml.

        Returns True if created or updated, False if already initialized and not forced.
        """
        if self.paths.is_initialized() and not force:
            return False

        self.paths.runmark_dir.mkdir(parents=True, exist_ok=True)
        self.paths.snapshots_dir.mkdir(parents=True, exist_ok=True)

        if not self.paths.config_file.exists() or force:
            default_config = (
                f"# Runmark configuration\n"
                f'tool_version = "{__version__}"\n'
                f'schema_version = "{__schema_version__}"\n'
                f"\n"
                f"[project]\n"
                f"auto_detect = true\n"
                f"\n"
                f"[verification]\n"
                f"strict_versions = false\n"
            )
            _atomic_write(self.paths.config_file, default_config)

        return True

    def save_snapshot(self, state: RunmarkState, set_as_current: bool = True) -> Path:
        """Persist a Runmark state snapshot to the filesystem using atomic writes."""
        self.paths.snapshots_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = self.paths.get_snapshot_path(state.runmark.id)
        content = state.model_dump_json(indent=2)
        _atomic_write(snapshot_path, content)

        if set_as_current:
            _atomic_write(self.paths.current_file, content)

        return snapshot_path

    def load_snapshot(self, snapshot_id: str) -> RunmarkState:
        """Load a specific snapshot by ID or filename."""
        snapshot_path = self.paths.get_snapshot_path(snapshot_id)
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot '{snapshot_id}' not found at {snapshot_path}")

        try:
            raw_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Snapshot '{snapshot_id}' contains corrupted or invalid JSON: {exc}"
            ) from exc

        return RunmarkState.model_validate(raw_data)

    def load_current(self) -> RunmarkState | None:
        """Load the current active baseline snapshot."""
        if not self.paths.current_file.exists():
            return None
        try:
            raw_data = json.loads(self.paths.current_file.read_text(encoding="utf-8"))
            return RunmarkState.model_validate(raw_data)
        except Exception:
            return None

    def list_snapshots(self) -> list[RunmarkState]:
        """List all saved snapshots in chronological order."""
        if not self.paths.snapshots_dir.exists():
            return []

        snapshots: list[RunmarkState] = []
        for file in sorted(self.paths.snapshots_dir.glob("*.json")):
            try:
                raw_data = json.loads(file.read_text(encoding="utf-8"))
                snapshots.append(RunmarkState.model_validate(raw_data))
            except Exception:
                continue

        # Sort by creation timestamp
        return sorted(snapshots, key=lambda s: s.runmark.created_at)

    def load_config(self) -> dict[str, Any]:
        """Load project config from config.toml."""
        if not self.paths.config_file.exists():
            return {}
        try:
            import tomllib

            return tomllib.loads(self.paths.config_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
