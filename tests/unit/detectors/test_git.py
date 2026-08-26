"""Unit tests for Git repository detector."""

from unittest.mock import patch

from runmark.detectors.base import DetectionContext
from runmark.detectors.git.git import GitDetector
from runmark.models.common import DetectionStatus
from runmark.utils.commands import CommandResult


def test_git_repository_state_detected(tmp_path):
    detector = GitDetector()
    context = DetectionContext(project_root=tmp_path)

    def fake_safe_run(cmd, cwd=None, timeout=3.0):
        if "rev-parse" in cmd and "--is-inside-work-tree" in cmd:
            return CommandResult(cmd, 0, "true", "")
        if "rev-parse" in cmd and "--abbrev-ref" in cmd:
            return CommandResult(cmd, 0, "main", "")
        if "rev-parse" in cmd and "HEAD" in cmd:
            return CommandResult(cmd, 0, "a81f29c0fabcd12345", "")
        if "status" in cmd:
            return CommandResult(cmd, 0, " M file.py\n", "")
        return CommandResult(cmd, 1, "", "unknown")

    with patch("runmark.detectors.git.git.safe_run", side_effect=fake_safe_run):
        res = detector.detect(context)
        assert res.status == DetectionStatus.DETECTED
        assert res.data.is_repository is True
        assert res.data.branch == "main"
        assert res.data.commit == "a81f29c0fabcd12345"
        assert res.data.dirty is True


def test_git_non_repository_handled(tmp_path):
    detector = GitDetector()
    context = DetectionContext(project_root=tmp_path)

    with patch("runmark.detectors.git.git.safe_run") as mock_run:
        mock_run.return_value = CommandResult(["git"], 128, "", "fatal: not a git repository")
        res = detector.detect(context)
        assert res.status == DetectionStatus.NOT_FOUND
        assert res.data.is_repository is False
        assert res.data.branch is None
