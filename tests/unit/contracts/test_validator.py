"""Unit tests for ContractValidator."""

import pytest

from runmark.contracts.validator import (
    ContractValidationError,
    ContractValidator,
)
from runmark.models.contract import RunmarkContract


class TestContractValidator:
    """Tests for JSON schema and semantic validation."""

    def test_schema_valid_minimal(self) -> None:
        raw = {"version": 1}
        # Should not raise
        ContractValidator.validate_schema(raw)

    def test_schema_invalid_extra_field(self) -> None:
        raw = {"version": 1, "extra_unexpected_field": "disallowed"}
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_schema(raw)
        assert "validation failed" in str(exc.value)

    def test_semantics_valid_contract(self) -> None:
        contract = RunmarkContract.model_validate(
            {
                "version": 1,
                "project": {"name": "test-app"},
                "platform": {"os": ["linux", "windows"], "architecture": ["x86_64", "arm64"]},
                "runtime": {"python": ">=3.11", "node": "20.x"},
                "services": {"postgresql": {"version": ">=14", "required": True}},
                "environment": {"required": ["DATABASE_URL"], "optional": ["DEBUG"]},
                "network": {"ports": {"8000": {"protocol": "tcp", "required": True}}},
            }
        )
        ContractValidator.validate_semantics(contract)

    def test_semantics_invalid_os(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "platform": {"os": ["solaris_unknown"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid platform OS" in str(exc.value)

    def test_semantics_invalid_architecture(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "platform": {"architecture": ["mips64"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid platform architecture" in str(exc.value)

    def test_semantics_invalid_env_var_name(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "environment": {"required": ["123_INVALID"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid environment variable name" in str(exc.value)

    def test_semantics_duplicate_env_var(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "environment": {"required": ["FOO", "FOO"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Duplicate environment variable" in str(exc.value)

    def test_semantics_env_var_collision(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "environment": {"required": ["FOO"], "optional": ["FOO"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "cannot be declared in both required and optional" in str(exc.value)

    def test_semantics_invalid_port_range(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "network": {"ports": {"70000": {"protocol": "tcp"}}}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid network port" in str(exc.value)

    def test_semantics_invalid_runtime_constraint(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "runtime": {"python": "invalid!!!constraint"}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid version constraint" in str(exc.value)
