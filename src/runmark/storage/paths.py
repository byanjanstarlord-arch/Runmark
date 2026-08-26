"""Path resolution for Runmark storage and configuration."""

from pathlib import Path


class StoragePaths:
    """Manages paths for Runmark directory, configuration, and snapshots."""

    RUNMARK_DIR = ".runmark"
    CONFIG_FILE = "config.toml"
    CURRENT_FILE = "current.json"
    SNAPSHOTS_DIR = "snapshots"

    def __init__(self, project_root: Path | str):
        self.project_root = Path(project_root).resolve()

    @property
    def runmark_dir(self) -> Path:
        """Path to .runmark directory."""
        return self.project_root / self.RUNMARK_DIR

    @property
    def config_file(self) -> Path:
        """Path to .runmark/config.toml."""
        return self.runmark_dir / self.CONFIG_FILE

    @property
    def current_file(self) -> Path:
        """Path to .runmark/current.json."""
        return self.runmark_dir / self.CURRENT_FILE

    @property
    def snapshots_dir(self) -> Path:
        """Path to .runmark/snapshots/ directory."""
        return self.runmark_dir / self.SNAPSHOTS_DIR

    def get_snapshot_path(self, snapshot_id: str) -> Path:
        """Path to a specific snapshot JSON file."""
        clean_id = snapshot_id.removesuffix(".json")
        return self.snapshots_dir / f"{clean_id}.json"

    def is_initialized(self) -> bool:
        """Check if Runmark has been initialized in this project."""
        return self.runmark_dir.exists() and self.runmark_dir.is_dir()


def find_project_root(start_dir: Path | str | None = None) -> Path:
    """Traverse upwards to find the project root containing .runmark or .git or project manifest."""
    current = Path(start_dir or Path.cwd()).resolve()

    # Search upwards for .runmark, .git, or standard project root markers
    for parent in [current, *current.parents]:
        if (parent / StoragePaths.RUNMARK_DIR).exists():
            return parent
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists() or (parent / "package.json").exists():
            return parent

    return current
