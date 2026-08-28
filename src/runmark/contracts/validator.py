"""Contract schema and semantic validation."""

import json
import re
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]

from runmark.contracts.version_constraints import VersionConstraint
from runmark.models.contract import RunmarkContract

SCHEMA_FILE = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "contract-v1.json"

VALID_OS_NAMES = {"windows", "linux", "darwin", "macos", "freebsd", "openbsd"}
VALID_ARCHITECTURES = {"amd64", "x86_64", "arm64", "aarch64", "x86", "i386", "i686"}
ENV_VAR_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class ContractValidationError(ValueError):
    """Raised when a contract is structurally or semantically invalid."""


class ContractValidator:
    """Performs structural (JSON schema) and semantic validation on Runmark contracts."""

    _cached_schema: dict[str, Any] | None = None

    @classmethod
    def get_schema(cls) -> dict[str, Any]:
        """Load and cache contract-v1.json schema."""
        if cls._cached_schema is None:
            if not SCHEMA_FILE.exists():
                raise FileNotFoundError(f"Schema file not found at: {SCHEMA_FILE}")
            with open(SCHEMA_FILE, encoding="utf-8") as f:
                cls._cached_schema = json.load(f)
        return cls._cached_schema

    @classmethod
    def validate_schema(cls, raw_dict: dict[str, Any]) -> None:
        """Validate raw dictionary structure against contract-v1.json JSON Schema."""
        schema = cls.get_schema()
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(raw_dict))
        if errors:
            first_err = errors[0]
            path = ".".join(str(p) for p in first_err.absolute_path) or "root"
            raise ContractValidationError(
                f"Contract schema validation failed at '{path}': {first_err.message}"
            )

    @classmethod
    def validate(cls, raw_dict: dict[str, Any]) -> None:
        """Alias for validate_schema."""
        cls.validate_schema(raw_dict)

    @classmethod
    def validate_semantics(cls, contract: RunmarkContract) -> None:
        """Validate logical and domain semantics of a typed RunmarkContract."""
        # 1. Version validation
        if contract.version != 1:
            raise ContractValidationError(
                f"Unsupported contract version '{contract.version}'. Only version 1 is supported in this release."
            )

        # 2. Platform OS and Architecture
        for os_name in contract.platform.os:
            if os_name.lower() not in VALID_OS_NAMES:
                raise ContractValidationError(
                    f"Invalid platform OS '{os_name}'. Supported operating systems: {sorted(VALID_OS_NAMES)}"
                )

        for arch in contract.platform.architecture:
            if arch.lower() not in VALID_ARCHITECTURES:
                raise ContractValidationError(
                    f"Invalid platform architecture '{arch}'. Supported architectures: {sorted(VALID_ARCHITECTURES)}"
                )

        # 3. Runtime version constraints
        for rt_name, constraint_expr in contract.runtime.items():
            try:
                VersionConstraint.parse(constraint_expr)
            except Exception as e:
                raise ContractValidationError(
                    f"Invalid version constraint for runtime '{rt_name}': '{constraint_expr}'. {e}"
                ) from None

        # 4. Service requirements
        for svc_name, svc_req in contract.services.items():
            try:
                VersionConstraint.parse(svc_req.version)
            except Exception as e:
                raise ContractValidationError(
                    f"Invalid version constraint for service '{svc_name}': '{svc_req.version}'. {e}"
                ) from None

        # 5. Environment variable names & duplicates
        req_set = set()
        for var_name in contract.environment.required:
            if not ENV_VAR_REGEX.match(var_name):
                raise ContractValidationError(
                    f"Invalid environment variable name '{var_name}' in required list. Must be a valid POSIX identifier."
                )
            if var_name in req_set:
                raise ContractValidationError(
                    f"Duplicate environment variable '{var_name}' in required list."
                )
            req_set.add(var_name)

        opt_set = set()
        for var_name in contract.environment.optional:
            if not ENV_VAR_REGEX.match(var_name):
                raise ContractValidationError(
                    f"Invalid environment variable name '{var_name}' in optional list. Must be a valid POSIX identifier."
                )
            if var_name in req_set:
                raise ContractValidationError(
                    f"Environment variable '{var_name}' cannot be declared in both required and optional lists."
                )
            if var_name in opt_set:
                raise ContractValidationError(
                    f"Duplicate environment variable '{var_name}' in optional list."
                )
            opt_set.add(var_name)

        # 6. Network ports
        for port_key, port_req in contract.network.ports.items():
            try:
                port_num = int(port_key)
                if not (1 <= port_num <= 65535):
                    raise ValueError()
            except ValueError:
                raise ContractValidationError(
                    f"Invalid network port '{port_key}'. Port must be an integer between 1 and 65535."
                ) from None

            if port_req.protocol not in ("tcp", "udp"):
                raise ContractValidationError(
                    f"Invalid protocol '{port_req.protocol}' for port {port_key}. Must be 'tcp' or 'udp'."
                )

        # 7. Package dependencies
        for pkg_name, pkg_constraint in contract.dependencies.python.items():
            try:
                VersionConstraint.parse(pkg_constraint)
            except Exception as e:
                raise ContractValidationError(
                    f"Invalid Python dependency version constraint for '{pkg_name}': '{pkg_constraint}'. {e}"
                ) from None

        for pkg_name, pkg_constraint in contract.dependencies.node.items():
            try:
                VersionConstraint.parse(pkg_constraint)
            except Exception as e:
                raise ContractValidationError(
                    f"Invalid Node dependency version constraint for '{pkg_name}': '{pkg_constraint}'. {e}"
                ) from None
