"""Snapshot manager for creating, persisting, and querying Runmark snapshots."""

from pathlib import Path

from runmark.core.scanner import Scanner
from runmark.models.runmark import RunmarkState
from runmark.storage.filesystem import FilesystemStorage


class SnapshotManager:
    """Coordinates scan capture and persistent storage."""

    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root).resolve()
        self.storage = FilesystemStorage(self.project_root)
        self.scanner = Scanner(self.project_root)

    def create_snapshot(self, message: str | None = None, set_current: bool = True) -> RunmarkState:
        """Scan the current environment and persist the snapshot."""
        state = self.scanner.scan(message=message)
        self.storage.save_snapshot(state, set_as_current=set_current)
        return state

    def get_current(self) -> RunmarkState | None:
        """Get the current baseline snapshot if any exists."""
        return self.storage.load_current()

    def get_snapshot(self, snapshot_id: str) -> RunmarkState:
        """Load a snapshot by ID."""
        return self.storage.load_snapshot(snapshot_id)

    def list_history(self) -> list[RunmarkState]:
        """List all snapshots in chronological order."""
        return self.storage.list_snapshots()
