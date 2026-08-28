"""Contract canonicalization and deterministic fingerprinting."""

import hashlib
import json
from typing import Any

from runmark.models.contract import RunmarkContract


class ContractCanonicalizer:
    """Transforms a RunmarkContract into a normalized, canonical data structure and digest."""

    @classmethod
    def canonicalize(cls, contract: RunmarkContract) -> dict[str, Any]:
        """Produce a normalized dictionary representing the semantic contract requirements.

        Excludes informational fields ($schema), normalizes ordering of unordered lists,
        and standardizes key structures.
        """
        canonical: dict[str, Any] = {
            "version": contract.version,
        }

        # Project identity
        if contract.project.name:
            canonical["project"] = {"name": contract.project.name}
        else:
            canonical["project"] = {}

        # Platform requirements (lowercased, deduplicated, sorted)
        clean_os = sorted(
            {os_name.lower().strip() for os_name in contract.platform.os if os_name.strip()}
        )
        clean_arch = sorted(
            {arch.lower().strip() for arch in contract.platform.architecture if arch.strip()}
        )
        canonical["platform"] = {
            "architecture": clean_arch,
            "os": clean_os,
        }

        # Runtimes (sorted by name, cleaned expressions)
        clean_runtimes: dict[str, str] = {}
        for rt_name in sorted(contract.runtime.keys()):
            clean_runtimes[rt_name.lower().strip()] = contract.runtime[rt_name].strip()
        canonical["runtime"] = clean_runtimes

        # Dependencies
        clean_py_deps = {
            k.lower().strip(): v.strip() for k, v in sorted(contract.dependencies.python.items())
        }
        clean_node_deps = {
            k.lower().strip(): v.strip() for k, v in sorted(contract.dependencies.node.items())
        }
        canonical["dependencies"] = {
            "node": clean_node_deps,
            "python": clean_py_deps,
        }

        # Services (sorted by name)
        clean_services: dict[str, dict[str, Any]] = {}
        for svc_name in sorted(contract.services.keys()):
            svc_req = contract.services[svc_name]
            clean_services[svc_name.lower().strip()] = {
                "required": svc_req.required,
                "version": svc_req.version.strip(),
            }
        canonical["services"] = clean_services

        # Environment variables (sorted, deduplicated)
        clean_required = sorted({v.strip() for v in contract.environment.required if v.strip()})
        clean_optional = sorted({v.strip() for v in contract.environment.optional if v.strip()})
        canonical["environment"] = {
            "optional": clean_optional,
            "required": clean_required,
        }

        # Network ports (sorted numerically)
        sorted_port_keys = sorted(contract.network.ports.keys(), key=lambda p: int(p))
        clean_ports: dict[str, dict[str, Any]] = {}
        for p_key in sorted_port_keys:
            p_req = contract.network.ports[p_key]
            clean_ports[str(int(p_key))] = {
                "protocol": p_req.protocol.lower().strip(),
                "required": p_req.required,
            }
        canonical["network"] = {"ports": clean_ports}

        # Containers
        clean_containers: dict[str, Any] = {}
        if contract.containers.docker is not None:
            clean_containers["docker"] = {"required": contract.containers.docker.required}
        if contract.containers.compose is not None:
            clean_containers["compose"] = {"required": contract.containers.compose.required}
        canonical["containers"] = clean_containers

        return canonical

    @classmethod
    def to_canonical_json(cls, contract: RunmarkContract) -> str:
        """Serialize the canonical representation to a deterministic JSON string."""
        canonical_dict = cls.canonicalize(contract)
        return json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))

    @classmethod
    def to_json(cls, contract: RunmarkContract) -> str:
        """Alias for to_canonical_json."""
        return cls.to_canonical_json(contract)

    @classmethod
    def compute_fingerprint(cls, contract: RunmarkContract) -> str:
        """Compute deterministic SHA-256 digest of the canonical contract representation."""
        canonical_bytes = cls.to_canonical_json(contract).encode("utf-8")
        return hashlib.sha256(canonical_bytes).hexdigest()

    @classmethod
    def fingerprint(cls, contract: RunmarkContract) -> str:
        """Alias for compute_fingerprint."""
        return cls.compute_fingerprint(contract)
