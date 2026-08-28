"""Hardened test suite for safe subprocess execution."""

import sys

from runmark.utils.commands import safe_run


def test_commands_argument_list_injection_defense():
    """Verify that malicious shell injection payloads are treated as literal arguments and never executed."""
    # When shell=False is enforced, arguments containing shell operators are not interpreted
    injection_args = [
        "; echo INJECTED",
        "&& echo INJECTED",
        "| echo INJECTED",
        "`echo INJECTED`",
        "$(echo INJECTED)",
    ]

    for arg in injection_args:
        # We invoke python -c "import sys; print(sys.argv[1])" <arg>
        res = safe_run([sys.executable, "-c", "import sys; print(sys.argv[1])", arg])
        assert res.succeeded
        # The output must be the exact literal string, NOT the executed subshell output
        assert res.stdout == arg
        assert "INJECTED" in res.stdout  # Printed literally by Python, not executed by shell!


def test_commands_timeout_bounded():
    """Verify that a hanging command is terminated safely within timeout."""
    # Command sleeps for 10 seconds with 1 second timeout
    res = safe_run(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        timeout=0.5,
    )
    assert res.timed_out is True
    assert res.exit_code == 124
    assert res.succeeded is False
    assert "timed out" in res.stderr.lower()


def test_commands_executable_not_found():
    """Verify that a missing binary fails cleanly without unhandled exception."""
    res = safe_run(["non_existent_binary_xyz_12345", "--version"])
    assert res.not_found is True
    assert res.exit_code == 127
    assert res.succeeded is False
    assert "not found" in res.stderr.lower()


def test_commands_output_size_limit():
    """Verify that commands emitting excessive output are safely truncated."""
    # Command generates 1 MB of characters, with max_output_bytes set to 1024 bytes (1 KB)
    res = safe_run(
        [sys.executable, "-c", "print('A' * 100000)"],
        max_output_bytes=1024,
    )
    assert res.succeeded
    assert res.truncated is True
    assert "[TRUNCATED: Output exceeded size limit]" in res.stdout
    assert len(res.stdout) < 2048


def test_commands_binary_and_invalid_utf8_output():
    """Verify that commands emitting arbitrary bytes or invalid UTF-8 do not crash."""
    # Python script printing raw invalid utf-8 bytes
    code = "import sys; sys.stdout.buffer.write(b'\\xff\\xfe\\xfd hello \\x80\\x81'); sys.stdout.flush()"
    res = safe_run([sys.executable, "-c", code])
    assert res.succeeded
    assert "hello" in res.stdout
