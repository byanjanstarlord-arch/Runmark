"""Project evidence extraction and signal classification engine for Runmark contracts."""

import re
from enum import Enum
from pathlib import Path
from typing import Any

import tomllib
import yaml

from runmark.models.common import RunmarkBaseModel


class EvidenceLevel(str, Enum):
    """Confidence level of discovered project signals."""

    EXPLICIT = (
        "explicit"  # Directly declared in project manifest (.python-version, pyproject.toml, etc.)
    )
    INFERRED = (
        "inferred"  # Derived from multiple strong signals (compose image + driver dependency)
    )
    OBSERVED = "observed"  # Fallback detected on host system


class EvidenceSignal(RunmarkBaseModel):
    """A discrete signal extracted from project files."""

    name: str
    category: str
    level: EvidenceLevel
    source: str
    details: dict[str, Any] = {}


class ProjectEvidence(RunmarkBaseModel):
    """Synthesized evidence extracted across all project sources."""

    signals: list[EvidenceSignal] = []
    project_name: str | None = None
    runtimes: dict[str, str] = {}
    dependencies: dict[str, dict[str, str]] = {}
    services: dict[str, dict[str, Any]] = {}
    required_env_vars: list[str] = []
    optional_env_vars: list[str] = []
    ports: dict[str, dict[str, Any]] = {}
    containers: dict[str, bool] = {}


class EvidenceCollector:
    """Discovers project manifests and extracts normalized requirement evidence."""

    KNOWN_SERVICE_IMAGES: dict[str, tuple[str, str, int]] = {
        "postgres": ("postgresql", "16", 5432),
        "postgresql": ("postgresql", "16", 5432),
        "redis": ("redis", "7", 6379),
        "mysql": ("mysql", "8", 3306),
        "mariadb": ("mariadb", "10", 3306),
        "mongo": ("mongodb", "6", 27017),
        "mongodb": ("mongodb", "6", 27017),
        "rabbitmq": ("rabbitmq", "3", 5672),
        "elasticsearch": ("elasticsearch", "8", 9200),
    }

    @classmethod
    def collect(cls, project_root: Path | str) -> ProjectEvidence:
        """Scan project files and gather all evidence signals."""
        root = Path(project_root).resolve()
        evidence = ProjectEvidence()

        cls._collect_python_signals(root, evidence)
        cls._collect_node_signals(root, evidence)
        cls._collect_docker_compose_signals(root, evidence)
        cls._collect_env_signals(root, evidence)

        # Normalize project name if missing
        if not evidence.project_name:
            evidence.project_name = root.name

        return evidence

    @classmethod
    def _collect_python_signals(cls, root: Path, evidence: ProjectEvidence) -> None:
        """Extract signals from Python project files."""
        # 1. .python-version
        pv_file = root / ".python-version"
        if pv_file.is_file():
            try:
                raw_ver = (
                    pv_file.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[0]
                )
                clean_ver = re.sub(r"[^\d.]", "", raw_ver)
                if clean_ver:
                    parts = clean_ver.split(".")
                    if len(parts) >= 2:
                        constraint = f">={parts[0]}.{parts[1]}"
                    else:
                        constraint = f">={clean_ver}"
                    evidence.runtimes["python"] = constraint
                    evidence.signals.append(
                        EvidenceSignal(
                            name="python_runtime",
                            category="runtime",
                            level=EvidenceLevel.EXPLICIT,
                            source=".python-version",
                            details={"version": raw_ver, "constraint": constraint},
                        )
                    )
            except Exception:
                pass

        # 2. pyproject.toml
        pyproject_file = root / "pyproject.toml"
        if pyproject_file.is_file():
            try:
                data = tomllib.loads(pyproject_file.read_text(encoding="utf-8", errors="ignore"))
                project_table = data.get("project", {})
                if isinstance(project_table, dict):
                    if "name" in project_table and isinstance(project_table["name"], str):
                        evidence.project_name = project_table["name"]

                    if "requires-python" in project_table and isinstance(
                        project_table["requires-python"], str
                    ):
                        req_py = project_table["requires-python"].strip()
                        evidence.runtimes["python"] = req_py
                        evidence.signals.append(
                            EvidenceSignal(
                                name="python_runtime",
                                category="runtime",
                                level=EvidenceLevel.EXPLICIT,
                                source="pyproject.toml",
                                details={"requires-python": req_py},
                            )
                        )

                    # Dependencies in project.dependencies
                    deps = project_table.get("dependencies", [])
                    if isinstance(deps, list):
                        py_deps: dict[str, str] = evidence.dependencies.setdefault("python", {})
                        for item in deps:
                            if isinstance(item, str):
                                parsed_name, parsed_constraint = cls._parse_pep508_dep(item)
                                if parsed_name is not None and parsed_constraint is not None:
                                    py_deps[parsed_name] = parsed_constraint

                # Check tool.poetry
                tool_table = data.get("tool", {})
                if isinstance(tool_table, dict):
                    poetry_table = tool_table.get("poetry", {})
                    if isinstance(poetry_table, dict):
                        if "name" in poetry_table and isinstance(poetry_table["name"], str):
                            if not evidence.project_name:
                                evidence.project_name = poetry_table["name"]
                        poetry_deps = poetry_table.get("dependencies", {})
                        if isinstance(poetry_deps, dict):
                            py_deps = evidence.dependencies.setdefault("python", {})
                            for dep_name, dep_val in poetry_deps.items():
                                if dep_name.lower() == "python":
                                    if isinstance(dep_val, str):
                                        evidence.runtimes["python"] = dep_val
                                        evidence.signals.append(
                                            EvidenceSignal(
                                                name="python_runtime",
                                                category="runtime",
                                                level=EvidenceLevel.EXPLICIT,
                                                source="pyproject.toml (poetry)",
                                                details={"constraint": dep_val},
                                            )
                                        )
                                elif isinstance(dep_val, str) and dep_val != "*":
                                    py_deps[dep_name.lower()] = dep_val

                evidence.signals.append(
                    EvidenceSignal(
                        name="python_project",
                        category="project",
                        level=EvidenceLevel.EXPLICIT,
                        source="pyproject.toml",
                        details={"manifest": "pyproject.toml"},
                    )
                )
            except Exception:
                pass

        # 3. requirements.txt
        req_file = root / "requirements.txt"
        if req_file.is_file():
            try:
                lines = req_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                py_deps = evidence.dependencies.setdefault("python", {})
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    req_name, req_constraint = cls._parse_pep508_dep(line)
                    if req_name is not None and req_constraint is not None:
                        py_deps[req_name] = req_constraint
                evidence.signals.append(
                    EvidenceSignal(
                        name="python_dependencies",
                        category="dependencies",
                        level=EvidenceLevel.EXPLICIT,
                        source="requirements.txt",
                        details={"count": len(py_deps)},
                    )
                )
            except Exception:
                pass

    @classmethod
    def _collect_node_signals(cls, root: Path, evidence: ProjectEvidence) -> None:
        """Extract signals from Node.js project files."""
        # 1. .nvmrc or .node-version
        for n_file, src_name in [(".nvmrc", ".nvmrc"), (".node-version", ".node-version")]:
            nv_path = root / n_file
            if nv_path.is_file():
                try:
                    raw_ver = (
                        nv_path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[0]
                    )
                    clean_ver = raw_ver.lstrip("vV")
                    if clean_ver:
                        parts = clean_ver.split(".")
                        constraint = f">={parts[0]}" if parts else f">={clean_ver}"
                        evidence.runtimes["node"] = constraint
                        evidence.signals.append(
                            EvidenceSignal(
                                name="node_runtime",
                                category="runtime",
                                level=EvidenceLevel.EXPLICIT,
                                source=src_name,
                                details={"version": raw_ver, "constraint": constraint},
                            )
                        )
                        break
                except Exception:
                    pass

        # 2. package.json
        pkg_file = root / "package.json"
        if pkg_file.is_file():
            try:
                import json

                pkg_data = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
                if isinstance(pkg_data, dict):
                    if "name" in pkg_data and isinstance(pkg_data["name"], str):
                        if not evidence.project_name:
                            evidence.project_name = pkg_data["name"]

                    engines = pkg_data.get("engines", {})
                    if isinstance(engines, dict) and "node" in engines:
                        node_engine = str(engines["node"]).strip()
                        evidence.runtimes["node"] = node_engine
                        evidence.signals.append(
                            EvidenceSignal(
                                name="node_runtime",
                                category="runtime",
                                level=EvidenceLevel.EXPLICIT,
                                source="package.json (engines)",
                                details={"node": node_engine},
                            )
                        )

                    deps = pkg_data.get("dependencies", {})
                    if isinstance(deps, dict):
                        node_deps: dict[str, str] = evidence.dependencies.setdefault("node", {})
                        for dep_k, dep_v in deps.items():
                            if isinstance(dep_v, str) and dep_v != "*":
                                node_deps[dep_k] = dep_v

                    evidence.signals.append(
                        EvidenceSignal(
                            name="node_project",
                            category="project",
                            level=EvidenceLevel.EXPLICIT,
                            source="package.json",
                            details={"manifest": "package.json"},
                        )
                    )
            except Exception:
                pass

    @classmethod
    def _collect_docker_compose_signals(cls, root: Path, evidence: ProjectEvidence) -> None:
        """Extract signals from Dockerfile and Compose configurations."""
        # 1. Dockerfile
        dockerfile = root / "Dockerfile"
        if dockerfile.is_file():
            evidence.containers["docker"] = True
            try:
                content = dockerfile.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if line.upper().startswith("FROM "):
                        from_img = line[5:].strip()
                        if "python:" in from_img.lower() and "python" not in evidence.runtimes:
                            match = re.search(r"python:(\d+\.\d+)", from_img, re.IGNORECASE)
                            if match:
                                evidence.runtimes["python"] = f">={match.group(1)}"
                        elif "node:" in from_img.lower() and "node" not in evidence.runtimes:
                            match = re.search(r"node:(\d+)", from_img, re.IGNORECASE)
                            if match:
                                evidence.runtimes["node"] = f">={match.group(1)}"
                    elif line.upper().startswith("EXPOSE "):
                        exposed = line[7:].strip()
                        for port_part in exposed.split():
                            p_clean = port_part.split("/")[0]
                            if p_clean.isdigit():
                                evidence.ports[p_clean] = {"protocol": "tcp", "required": True}
                evidence.signals.append(
                    EvidenceSignal(
                        name="dockerfile",
                        category="container",
                        level=EvidenceLevel.EXPLICIT,
                        source="Dockerfile",
                        details={"docker": True},
                    )
                )
            except Exception:
                pass

        # 2. Compose files
        compose_names = ["compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"]
        for cname in compose_names:
            cfile = root / cname
            if cfile.is_file():
                evidence.containers["docker"] = True
                evidence.containers["compose"] = True
                try:
                    data = yaml.safe_load(cfile.read_text(encoding="utf-8", errors="ignore"))
                    if (
                        isinstance(data, dict)
                        and "services" in data
                        and isinstance(data["services"], dict)
                    ):
                        for _s_name, s_cfg in data["services"].items():
                            if not isinstance(s_cfg, dict):
                                continue
                            img = s_cfg.get("image", "")
                            if isinstance(img, str) and img:
                                img_base = img.split(":")[0].lower().split("/")[-1]
                                tag = img.split(":")[1] if ":" in img else None
                                if img_base in cls.KNOWN_SERVICE_IMAGES:
                                    svc_name, def_ver, def_port = cls.KNOWN_SERVICE_IMAGES[img_base]
                                    ver_constraint = (
                                        f">={tag}"
                                        if tag and re.match(r"^\d+", tag)
                                        else f">={def_ver}"
                                    )
                                    evidence.services[svc_name] = {
                                        "version": ver_constraint,
                                        "required": True,
                                    }
                                    evidence.ports[str(def_port)] = {
                                        "protocol": "tcp",
                                        "required": False,
                                    }
                                    evidence.signals.append(
                                        EvidenceSignal(
                                            name=f"service_{svc_name}",
                                            category="service",
                                            level=EvidenceLevel.EXPLICIT,
                                            source=cname,
                                            details={"service": svc_name, "image": img},
                                        )
                                    )

                            # Parse published ports
                            ports_cfg = s_cfg.get("ports", [])
                            if isinstance(ports_cfg, list):
                                for p_entry in ports_cfg:
                                    p_str = str(p_entry)
                                    # format "host:container" or "host:container/proto" or "port"
                                    if ":" in p_str:
                                        host_part = p_str.split(":")[0].strip()
                                        if host_part.isdigit():
                                            evidence.ports[host_part] = {
                                                "protocol": "tcp",
                                                "required": True,
                                            }
                                    elif p_str.isdigit():
                                        evidence.ports[p_str] = {
                                            "protocol": "tcp",
                                            "required": True,
                                        }

                    evidence.signals.append(
                        EvidenceSignal(
                            name="compose_config",
                            category="container",
                            level=EvidenceLevel.EXPLICIT,
                            source=cname,
                            details={"compose": True},
                        )
                    )
                except Exception:
                    pass

    @classmethod
    def _collect_env_signals(cls, root: Path, evidence: ProjectEvidence) -> None:
        """Extract required environment variable names from templates without values or secrets."""
        env_files = [".env.example", ".env.sample", ".env.template", ".env.dist"]
        required_set: set[str] = set()

        for ef in env_files:
            epath = root / ef
            if epath.is_file():
                try:
                    lines = epath.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("export "):
                            line = line[len("export ") :].strip()
                        if "=" in line:
                            var_name = line.split("=", 1)[0].strip()
                        else:
                            var_name = line.strip()
                        # Strictly validate POSIX environment variable name syntax
                        if var_name and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", var_name):
                            required_set.add(var_name)
                    evidence.signals.append(
                        EvidenceSignal(
                            name="environment_template",
                            category="environment",
                            level=EvidenceLevel.EXPLICIT,
                            source=ef,
                            details={"variables_count": len(required_set)},
                        )
                    )
                except Exception:
                    pass

        evidence.required_env_vars = sorted(required_set)

    @classmethod
    def _parse_pep508_dep(cls, dep_str: str) -> tuple[str | None, str | None]:
        """Parse package name and constraint from PEP 508 string (e.g. 'fastapi>=0.100.0,<1.0')."""
        clean = dep_str.split(";")[0].strip()  # Remove environment markers
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([~^<>=!].*)?$", clean)
        if match:
            name = match.group(1).lower().replace("_", "-")
            constraint = match.group(2).strip() if match.group(2) else None
            return name, constraint
        return None, None
