"""Unit tests for safe subprocess execution utility."""

import sys

from runmark.utils.commands import safe_run


def test_safe_run_executes_successfully():
    res = safe_run([sys.executable, "--version"], timeout=5.0)
    assert res.succeeded is True
    assert res.exit_code == 0
    assert "Python" in res.stdout


def test_safe_run_missing_executable():
    res = safe_run(["non_existent_binary_123456789_xyz"], timeout=1.0)
    assert res.succeeded is False
    assert res.not_found is True
    assert res.exit_code == 127


def test_safe_run_timeout():
    # Run a python one-liner that sleeps longer than timeout
    res = safe_run([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.2)
    assert res.succeeded is False
    assert res.timed_out is True
    assert res.exit_code == 124


def test_safe_run_empty_command():
    res = safe_run([])
    assert res.succeeded is False
    assert res.not_found is True
