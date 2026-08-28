"""Validation tests verifying that generated states match schemas/runmark-v1.json."""

import json
from pathlib import Path

import jsonschema
import pydantic
import pytest

from runmark.core.scanner import Scanner
from runmark.models.runmark import RunmarkState

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "runmark-v1.json"


@pytest.fixture
def runmark_json_schema():
    assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_validates_live_scan_state(tmp_path, runmark_json_schema):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "schema-test"\n', encoding="utf-8")
    (tmp_path / ".env.example").write_text(
        "DATABASE_URL=postgres://localhost:5432/db\n", encoding="utf-8"
    )

    scanner = Scanner(tmp_path)
    state = scanner.scan()

    # Convert state to plain JSON dict
    state_json = json.loads(state.model_dump_json())

    # Validate against formal JSON Schema
    jsonschema.validate(instance=state_json, schema=runmark_json_schema)


def test_schema_rejects_missing_required_fields(runmark_json_schema):
    invalid_data = {
        "runmark": {"id": "snap_1"},
        "project": {"name": "test"},
        # missing git, system, runtimes, dependencies, services, environment, network, containers
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=runmark_json_schema)


def test_schema_rejects_extra_fields_in_root_or_models(tmp_path, runmark_json_schema):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\n', encoding="utf-8")
    scanner = Scanner(tmp_path)
    state_dict = json.loads(scanner.scan().model_dump_json())

    # Inject unknown extra field into root
    state_dict["unknown_field_123"] = "invalid"

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=state_dict, schema=runmark_json_schema)

    # Also verify Pydantic model rejects extra fields (extra="forbid")
    with pytest.raises(pydantic.ValidationError):
        RunmarkState.model_validate(state_dict)
