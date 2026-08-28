"""Hardened edge case tests for Git repository detector."""

from unittest.mock import patch

from runmark.detectors.base import DetectionContext, DetectionStatus
from runmark.detectors.git.git import GitDetector
from runmark.utils.commands import CommandResult


def test_git_detector_detached_head(tmp_path):
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.git.git.safe_run") as mock_run:
        # 1. inside work tree
        # 2. abbrev-ref returns HEAD -> detached HEAD
        # 3. commit hash
        # 4. status porcelain clean
        mock_run.side_effect = [
            CommandResult(
                command=["git", "rev-parse", "--is-inside-work-tree"],
                exit_code=0,
                stdout="true",
                stderr="",
            ),
            CommandResult(
                command=["git", "rev-parse", "--abbrev-ref", "HEAD"],
                exit_code=0,
                stdout="HEAD",
                stderr="",
            ),
            CommandResult(
                command=["git", "rev-parse", "HEAD"], exit_code=0, stdout="a1b2c3d4e5f6", stderr=""
            ),
            CommandResult(
                command=["git", "status", "--porcelain"], exit_code=0, stdout="", stderr=""
            ),
        ]

        detector = GitDetector()
        res = detector.detect(context)

        assert res.status == DetectionStatus.DETECTED
        assert res.data.is_repository is True
        assert res.data.branch == "HEAD (detached)"
        assert res.data.commit == "a1b2c3d4e5f6"
        assert res.data.dirty is False


def test_git_detector_empty_unborn_repo(tmp_path):
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.git.git.safe_run") as mock_run:
        # 1. inside work tree
        # 2. abbrev-ref returns main (unborn)
        # 3. commit fails (no commits yet in unborn branch)
        # 4. status porcelain returns untracked file
        mock_run.side_effect = [
            CommandResult(
                command=["git", "rev-parse", "--is-inside-work-tree"],
                exit_code=0,
                stdout="true",
                stderr="",
            ),
            CommandResult(
                command=["git", "rev-parse", "--abbrev-ref", "HEAD"],
                exit_code=0,
                stdout="main",
                stderr="",
            ),
            CommandResult(
                command=["git", "rev-parse", "HEAD"],
                exit_code=128,
                stdout="",
                stderr="fatal: ambiguous argument 'HEAD'",
            ),
            CommandResult(
                command=["git", "status", "--porcelain"],
                exit_code=0,
                stdout="?? README.md",
                stderr="",
            ),
        ]

        detector = GitDetector()
        res = detector.detect(context)

        assert res.status == DetectionStatus.DETECTED
        assert res.data.is_repository is True
        assert res.data.branch == "main"
        assert res.data.commit is None
        assert res.data.dirty is True


def test_git_detector_binary_missing(tmp_path):
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.git.git.safe_run") as mock_run:
        mock_run.return_value = CommandResult(
            command=["git", "rev-parse"],
            exit_code=127,
            stdout="",
            stderr="git: not found",
            not_found=True,
        )

        detector = GitDetector()
        res = detector.detect(context)

        assert res.status == DetectionStatus.NOT_FOUND
        assert res.data.is_repository is False
        assert res.data.branch is None
        assert res.data.commit is None
