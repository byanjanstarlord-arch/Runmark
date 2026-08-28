"""Unit tests for contract discovery."""

from pathlib import Path

import pytest

from runmark.contracts.discovery import find_contract_file


def test_discovery_by_directory(tmp_path: Path) -> None:
    contract_file = tmp_path / "runmark.json"
    contract_file.write_text('{"version": 1}', encoding="utf-8")

    found = find_contract_file(tmp_path)
    assert found == contract_file


def test_discovery_by_explicit_file(tmp_path: Path) -> None:
    contract_file = tmp_path / "custom_runmark.json"
    contract_file.write_text('{"version": 1}', encoding="utf-8")

    found = find_contract_file(contract_file)
    assert found == contract_file


def test_discovery_missing_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError) as exc:
        find_contract_file(tmp_path)
    assert "not found" in str(exc.value)


def test_discovery_non_existent_target_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError) as exc:
        find_contract_file(tmp_path / "non_existent_dir")
    assert "does not exist" in str(exc.value)


def test_discovery_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    contract_file = tmp_path / "runmark.json"
    contract_file.write_text('{"version": 1}', encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    found = find_contract_file(None)
    assert found.name == "runmark.json"
