"""Core orchestration service for environment contract diffing."""

from pathlib import Path

from runmark.contracts.diff import ContractDiffEngine, ContractDiffResult
from runmark.contracts.discovery import find_contract_file
from runmark.contracts.parser import ContractParser
from runmark.models.contract import RunmarkContract
from runmark.utils.commands import safe_run


class ContractDiffService:
    """Coordinates baseline resolution and contract diffing."""

    @classmethod
    def diff_contracts(
        cls,
        project_path: Path | str | None = None,
        baseline_path: Path | str | None = None,
        current_contract_path: Path | str | None = None,
    ) -> ContractDiffResult:
        """Compare current project contract against baseline from Git or specified file."""
        root = Path(project_path).resolve() if project_path else Path.cwd().resolve()

        # 1. Resolve current contract
        if current_contract_path is not None:
            c_path = Path(current_contract_path).resolve()
        else:
            c_path = find_contract_file(root)

        current_contract = ContractParser.parse_file(c_path)

        # 2. Resolve baseline contract
        baseline_contract: RunmarkContract
        if baseline_path is not None:
            b_path = Path(baseline_path).resolve()
            baseline_contract = ContractParser.parse_file(b_path)
        else:
            baseline_contract = cls._load_git_baseline(root, c_path)

        # 3. Compute semantic diff
        return ContractDiffEngine.diff(baseline_contract, current_contract)

    @classmethod
    def _load_git_baseline(cls, project_root: Path, contract_file: Path) -> RunmarkContract:
        """Attempt to retrieve runmark.json from Git repository HEAD."""
        # Find relative path from git root or project root
        try:
            rel_path = contract_file.relative_to(project_root).as_posix()
        except ValueError:
            rel_path = "runmark.json"

        git_cmd = ["git", "show", f"HEAD:{rel_path}"]
        res = safe_run(git_cmd, cwd=project_root, timeout=3.0)

        if not res.succeeded or not res.stdout:
            # Try fallback to just runmark.json in repo root
            res = safe_run(["git", "show", "HEAD:runmark.json"], cwd=project_root, timeout=3.0)

        if not res.succeeded or not res.stdout:
            raise FileNotFoundError(
                f"No baseline contract found at Git HEAD:{rel_path}. Provide an explicit baseline file to compare."
            )

        return ContractParser.parse_string(res.stdout)
