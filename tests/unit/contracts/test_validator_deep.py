"""Deep tests for contract validator edge cases."""

import pytest

from runmark.contracts.validator import (
    ContractValidationError,
    ContractValidator,
)
from runmark.models.contract import RunmarkContract


class TestContractValidatorDeep:
    """Additional validator tests for coverage."""

    def test_invalid_service_version_constraint(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "services": {"postgres": {"version": "invalid-syntax!"}}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid version constraint for service" in str(exc.value)

    def test_invalid_node_dependency_constraint(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "dependencies": {"node": {"react": "invalid-syntax!"}}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid Node dependency version constraint" in str(exc.value)

    def test_invalid_port_protocol(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "network": {"ports": {"8080": {"protocol": "http"}}}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid protocol" in str(exc.value)

    def test_duplicate_optional_env_var(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "environment": {"optional": ["OPT_VAR", "OPT_VAR"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Duplicate environment variable 'OPT_VAR' in optional list" in str(exc.value)

    def test_invalid_optional_env_var_name(self) -> None:
        contract = RunmarkContract.model_validate(
            {"version": 1, "environment": {"optional": ["123-bad-name"]}}
        )
        with pytest.raises(ContractValidationError) as exc:
            ContractValidator.validate_semantics(contract)
        assert "Invalid environment variable name" in str(exc.value)
