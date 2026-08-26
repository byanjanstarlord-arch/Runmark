"""Safe subprocess execution utilities."""

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Result of a safe subprocess execution."""

    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    not_found: bool = False

    @property
    def succeeded(self) -> bool:
        """Whether the command finished with code 0 and did not timeout/fail."""
        return self.exit_code == 0 and not self.timed_out and not self.not_found


def safe_run(
    cmd: list[str],
    timeout: float = 5.0,
    cwd: str | None = None,
    env: dict | None = None,
) -> CommandResult:
    """Execute a command safely using an argument list, bounded timeout, and no shell interpolation.

    Args:
        cmd: List of command arguments.
        timeout: Maximum seconds to wait.
        cwd: Working directory.
        env: Environment variables override.

    Returns:
        CommandResult object.
    """
    if not cmd:
        return CommandResult(
            command=cmd,
            exit_code=1,
            stdout="",
            stderr="Empty command list",
            not_found=True,
        )

    # Use clean environment or inherited env
    process_env = os.environ.copy() if env is None else env.copy()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            cwd=cwd,
            env=process_env,
            encoding="utf-8",
            errors="replace",
        )
        return CommandResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            timed_out=False,
            not_found=False,
        )
    except FileNotFoundError:
        return CommandResult(
            command=cmd,
            exit_code=127,
            stdout="",
            stderr=f"Executable '{cmd[0]}' not found.",
            not_found=True,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            command=cmd,
            exit_code=124,
            stdout="",
            stderr=f"Command timed out after {timeout}s.",
            timed_out=True,
        )
    except Exception as exc:
        return CommandResult(
            command=cmd,
            exit_code=1,
            stdout="",
            stderr=f"Execution error: {exc}",
        )
