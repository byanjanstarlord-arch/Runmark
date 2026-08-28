"""Contract file discovery utilities for Runmark."""

from pathlib import Path

DEFAULT_CONTRACT_FILENAME = "runmark.json"


def find_contract_file(target_path: Path | str | None = None) -> Path:
    """Locate the runmark.json contract file in the target directory or path.

    Raises FileNotFoundError if runmark.json does not exist.
    """
    if target_path is not None:
        p = Path(target_path).resolve()
        if p.is_file() and p.exists():
            return p
        if p.is_dir():
            candidate = p / DEFAULT_CONTRACT_FILENAME
            if candidate.exists() and candidate.is_file():
                return candidate
            raise FileNotFoundError(
                f"Contract file '{DEFAULT_CONTRACT_FILENAME}' not found in '{p}'."
            )
        raise FileNotFoundError(f"Target path '{p}' does not exist.")

    # Search in current working directory
    cwd_candidate = Path.cwd() / DEFAULT_CONTRACT_FILENAME
    if cwd_candidate.exists() and cwd_candidate.is_file():
        return cwd_candidate

    raise FileNotFoundError(
        f"Contract file '{DEFAULT_CONTRACT_FILENAME}' not found in current directory ({Path.cwd()})."
    )
