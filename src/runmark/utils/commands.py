"""Safe subprocess execution utilities."""

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_OUTPUT_BYTES = 5 * 1024 * 1024  # 5 MB safe memory limit


@dataclass(frozen=True)
class CommandResult:
    """Result of a safe subprocess execution."""

    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    not_found: bool = False
    truncated: bool = False

    @property
    def succeeded(self) -> bool:
        """Whether the command finished with code 0 and did not timeout/fail."""
        return self.exit_code == 0 and not self.timed_out and not self.not_found


def safe_run(
    cmd: list[str],
    timeout: float = 5.0,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> CommandResult:
    """Execute a command safely using an argument list, bounded timeout, and no shell interpolation.

    Args:
        cmd: List of command arguments.
        timeout: Maximum seconds to wait.
        cwd: Working directory.
        env: Environment variables override.
        max_output_bytes: Maximum allowed stdout/stderr bytes before truncation.

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
    process_env = dict(os.environ) if env is None else dict(env)

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

        stdout_raw = proc.stdout
        stderr_raw = proc.stderr
        truncated = False

        if len(stdout_raw.encode("utf-8", errors="replace")) > max_output_bytes:
            stdout_raw = stdout_raw[:max_output_bytes] + "\n[TRUNCATED: Output exceeded size limit]"
            truncated = True

        if len(stderr_raw.encode("utf-8", errors="replace")) > max_output_bytes:
            stderr_raw = stderr_raw[:max_output_bytes] + "\n[TRUNCATED: Error exceeded size limit]"
            truncated = True

        return CommandResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=stdout_raw.strip(),
            stderr=stderr_raw.strip(),
            timed_out=False,
            not_found=False,
            truncated=truncated,
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
