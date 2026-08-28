"""Core service for initializing and generating Runmark environment contracts."""

import json
import os
import tempfile
from pathlib import Path

from runmark.contracts.canonicalizer import ContractCanonicalizer
from runmark.contracts.evidence import ProjectEvidence
from runmark.contracts.generator import ContractGenerator
from runmark.contracts.parser import ContractParser
from runmark.models.contract import RunmarkContract


class ContractInitService:
    """Orchestrates contract generation, dry-run simulation, and atomic persistence."""

    @classmethod
    def init_contract(
        cls,
        project_path: Path | str | None = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> tuple[RunmarkContract, ProjectEvidence, bool]:
        """Generate a candidate contract from project evidence and optionally persist it atomically."""
        root = Path(project_path).resolve() if project_path else Path.cwd().resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Project directory does not exist: {root}")
        target_file = root / "runmark.json"

        # Check existing file protection
        if target_file.exists() and not force and not dry_run:
            raise FileExistsError(
                f"Contract file '{target_file.name}' already exists in '{root}'. Use --force to replace it."
            )

        # Generate validated, canonical candidate contract
        contract, evidence = ContractGenerator.generate(root)

        if dry_run:
            return contract, evidence, False

        # Atomic persistence
        cls._write_contract_atomically(target_file, contract)

        # Verification pass after writing
        ContractParser.parse_file(target_file)

        return contract, evidence, True

    @classmethod
    def _write_contract_atomically(cls, target_path: Path, contract: RunmarkContract) -> None:
        """Write canonical contract JSON to a temporary file, fsync, and replace atomically."""
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        canonical_dict = ContractCanonicalizer.canonicalize(contract)
        json_str = json.dumps(canonical_dict, indent=2, sort_keys=True) + "\n"
        json_bytes = json_str.encode("utf-8")

        temp_fd, temp_path_str = tempfile.mkstemp(
            prefix=".runmark-contract-",
            suffix=".tmp",
            dir=str(target_dir),
        )
        temp_path = Path(temp_path_str)

        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(json_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise
