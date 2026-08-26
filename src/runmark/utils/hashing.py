"""Deterministic canonical JSON hashing and environment fingerprinting."""

import hashlib
import json
from typing import Any

from runmark.models.runmark import RunmarkState


def canonicalize_state_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Strip volatile and source-code metadata to prepare pure environment state for hashing."""
    canonical: dict[str, Any] = {}

    # 1. Project metadata (keep language/framework signals, omit local absolute root)
    if "project" in data and data["project"]:
        p = data["project"]
        p_dict = (
            p
            if isinstance(p, dict)
            else (p.model_dump(mode="json") if hasattr(p, "model_dump") else {})
        )
        canonical["project"] = {
            "name": p_dict.get("name", ""),
            "languages": sorted(p_dict.get("languages", [])),
            "frameworks": sorted(p_dict.get("frameworks", [])),
            "package_managers": sorted(p_dict.get("package_managers", [])),
            "containerization": sorted(p_dict.get("containerization", [])),
        }

    # 2. System (OS and architecture)
    if "system" in data and data["system"]:
        s = data["system"]
        s_dict = (
            s
            if isinstance(s, dict)
            else (s.model_dump(mode="json") if hasattr(s, "model_dump") else {})
        )
        canonical["system"] = {
            "os_name": s_dict.get("os_name", ""),
            "os_version": s_dict.get("os_version", ""),
            "architecture": s_dict.get("architecture", ""),
        }

    # 3. Runtimes (sort keys)
    if "runtimes" in data and data["runtimes"]:
        runtimes = data["runtimes"]
        canonical["runtimes"] = {
            k: {
                "name": (v.get("name", k) if isinstance(v, dict) else getattr(v, "name", k)),
                "installed": (
                    v.get("installed", False)
                    if isinstance(v, dict)
                    else getattr(v, "installed", False)
                ),
                "version": (
                    v.get("version") if isinstance(v, dict) else getattr(v, "version", None)
                ),
                "status": (v.get("status") if isinstance(v, dict) else getattr(v, "status", None)),
            }
            for k, v in sorted(runtimes.items())
        }

    # 4. Dependencies (sort by name and manager)
    if "dependencies" in data and data["dependencies"]:
        deps = data["dependencies"]
        canonical["dependencies"] = sorted(
            [
                {
                    "name": (
                        d.get("name", "") if isinstance(d, dict) else getattr(d, "name", "")
                    ).lower(),
                    "manager": (
                        d.get("manager", "") if isinstance(d, dict) else getattr(d, "manager", "")
                    ),
                    "declared": (
                        d.get("declared") if isinstance(d, dict) else getattr(d, "declared", None)
                    ),
                    "resolved": (
                        d.get("resolved") if isinstance(d, dict) else getattr(d, "resolved", None)
                    ),
                    "kind": str(
                        d.get("kind", "direct")
                        if isinstance(d, dict)
                        else getattr(d, "kind", "direct")
                    ),
                }
                for d in deps
            ],
            key=lambda x: (x["manager"], x["name"]),
        )

    # 5. Services (sort by name)
    if "services" in data and data["services"]:
        svcs = data["services"]
        canonical["services"] = sorted(
            [
                {
                    "name": (
                        s.get("name", "") if isinstance(s, dict) else getattr(s, "name", "")
                    ).lower(),
                    "installed": (
                        s.get("installed", False)
                        if isinstance(s, dict)
                        else getattr(s, "installed", False)
                    ),
                    "running": (
                        s.get("running", False)
                        if isinstance(s, dict)
                        else getattr(s, "running", False)
                    ),
                    "detected_version": (
                        s.get("detected_version")
                        if isinstance(s, dict)
                        else getattr(s, "detected_version", None)
                    ),
                    "expected_version": (
                        s.get("expected_version")
                        if isinstance(s, dict)
                        else getattr(s, "expected_version", None)
                    ),
                    "status": str(
                        s.get("status") if isinstance(s, dict) else getattr(s, "status", None)
                    ),
                    "port": (s.get("port") if isinstance(s, dict) else getattr(s, "port", None)),
                }
                for s in svcs
            ],
            key=lambda x: x["name"],
        )

    # 6. Environment variables (sort keys, ignore values, only record presence & requirements)
    if "environment" in data and data["environment"]:
        env = data["environment"]
        vars_map = (
            env.get("variables", {})
            if isinstance(env, dict)
            else (getattr(env, "variables", {}) or {})
        )
        canonical["environment"] = {
            "variables": {
                k: {
                    "name": (v.get("name", k) if isinstance(v, dict) else getattr(v, "name", k)),
                    "required": (
                        v.get("required", False)
                        if isinstance(v, dict)
                        else getattr(v, "required", False)
                    ),
                    "present": (
                        v.get("present", False)
                        if isinstance(v, dict)
                        else getattr(v, "present", False)
                    ),
                    "secret": (
                        v.get("secret", False)
                        if isinstance(v, dict)
                        else getattr(v, "secret", False)
                    ),
                    "source": (
                        v.get("source", "system")
                        if isinstance(v, dict)
                        else getattr(v, "source", "system")
                    ),
                }
                for k, v in sorted(vars_map.items())
            }
        }

    # 7. Network / Ports (sort by port number)
    if "network" in data and data["network"]:
        ports = data["network"]
        canonical["network"] = sorted(
            [
                {
                    "port": (p.get("port") if isinstance(p, dict) else getattr(p, "port", 0)),
                    "service": (
                        p.get("service", "") if isinstance(p, dict) else getattr(p, "service", "")
                    ),
                    "expected": (
                        p.get("expected", True)
                        if isinstance(p, dict)
                        else getattr(p, "expected", True)
                    ),
                    "occupied": (
                        p.get("occupied", False)
                        if isinstance(p, dict)
                        else getattr(p, "occupied", False)
                    ),
                    "status": (
                        p.get("status", "") if isinstance(p, dict) else getattr(p, "status", "")
                    ),
                }
                for p in ports
            ],
            key=lambda x: x["port"] or 0,
        )

    # 8. Containers (sort by service_name)
    if "containers" in data and data["containers"]:
        containers = data["containers"]
        canonical["containers"] = sorted(
            [
                {
                    "service_name": (
                        c.get("service_name", "")
                        if isinstance(c, dict)
                        else getattr(c, "service_name", "")
                    ),
                    "image": (
                        c.get("image", "") if isinstance(c, dict) else getattr(c, "image", "")
                    ),
                    "tag": (c.get("tag") if isinstance(c, dict) else getattr(c, "tag", None)),
                    "running_status": (
                        c.get("running_status", "")
                        if isinstance(c, dict)
                        else getattr(c, "running_status", "")
                    ),
                }
                for c in containers
            ],
            key=lambda x: x["service_name"],
        )

    return canonical


def to_canonical_json(data: dict[str, Any]) -> str:
    """Serialize data into a deterministic, sorted, compact JSON string."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def calculate_environment_fingerprint(state_or_dict: RunmarkState | dict[str, Any]) -> str:
    """Compute deterministic SHA-256 fingerprint for the environment."""
    if isinstance(state_or_dict, RunmarkState):
        raw_dict = state_or_dict.model_dump(mode="json")
    else:
        raw_dict = state_or_dict

    canonical_dict = canonicalize_state_dict(raw_dict)
    canonical_json_str = to_canonical_json(canonical_dict)
    return hashlib.sha256(canonical_json_str.encode("utf-8")).hexdigest()
