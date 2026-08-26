"""Git repository state detector."""

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.git import GitState
from runmark.utils.commands import safe_run


class GitDetector(Detector):
    """Detects Git repository status, current branch, HEAD commit, and dirty state."""

    @property
    def name(self) -> str:
        return "git_repo"

    @property
    def category(self) -> str:
        return "git"

    def detect(self, context: DetectionContext) -> DetectionResult:
        # Check if project root is or is inside a git repo
        rev_parse = safe_run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(context.project_root),
            timeout=3.0,
        )

        if not rev_parse.succeeded or rev_parse.stdout.lower() != "true":
            state = GitState(
                is_repository=False,
                branch=None,
                commit=None,
                dirty=False,
            )
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_FOUND,
                data=state,
            )

        # Get branch or detached HEAD indicator
        branch_res = safe_run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(context.project_root),
            timeout=3.0,
        )
        branch = branch_res.stdout if branch_res.succeeded and branch_res.stdout != "HEAD" else None
        if branch_res.succeeded and branch_res.stdout == "HEAD":
            # In detached HEAD state
            branch = "HEAD (detached)"

        # Get current commit hash (short or full)
        commit_res = safe_run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(context.project_root),
            timeout=3.0,
        )
        commit = commit_res.stdout if commit_res.succeeded else None

        # Check dirty state (uncommitted / unstaged changes)
        status_res = safe_run(
            ["git", "status", "--porcelain"],
            cwd=str(context.project_root),
            timeout=3.0,
        )
        dirty = bool(status_res.succeeded and status_res.stdout.strip())

        state = GitState(
            is_repository=True,
            branch=branch,
            commit=commit,
            dirty=dirty,
        )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=state,
        )
