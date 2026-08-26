"""Python dependency manifest and lockfile parser."""

import re
from typing import Any

import tomllib

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.dependency import DependencyState


class PythonDependencyDetector(Detector):
    """Detects and parses Python dependencies from requirements.txt, pyproject.toml, uv.lock, and poetry.lock."""

    @property
    def name(self) -> str:
        return "dependencies_python"

    @property
    def category(self) -> str:
        return "dependencies"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        declared_map: dict[str, dict[str, str]] = {}
        resolved_map: dict[str, str] = {}
        manager = "pip"

        # 1. Parse requirements.txt if present
        req_file = root / "requirements.txt"
        if req_file.exists():
            manager = "pip"
            self._parse_requirements_file(req_file, declared_map)

        # 2. Parse pyproject.toml if present
        pyproject_file = root / "pyproject.toml"
        if pyproject_file.exists():
            self._parse_pyproject_file(pyproject_file, declared_map)

        # 3. Check for lockfiles: uv.lock
        uv_lock_file = root / "uv.lock"
        if uv_lock_file.exists():
            manager = "uv"
            self._parse_toml_lockfile(uv_lock_file, resolved_map)

        # 4. Check for lockfiles: poetry.lock
        poetry_lock_file = root / "poetry.lock"
        if poetry_lock_file.exists():
            manager = "poetry"
            self._parse_toml_lockfile(poetry_lock_file, resolved_map)

        if not declared_map and not resolved_map:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=[],
            )

        # Merge into DependencyState list
        all_pkg_names = sorted(set(list(declared_map.keys()) + list(resolved_map.keys())))
        dependencies: list[DependencyState] = []

        for name in all_pkg_names:
            decl_info = declared_map.get(name, {})
            declared = decl_info.get("declared")
            kind_str = decl_info.get("kind", "direct")
            resolved = resolved_map.get(name)

            kind = DependencyKind.DEV if kind_str == "dev" else DependencyKind.DIRECT
            dependencies.append(
                DependencyState(
                    name=name,
                    manager=manager,
                    declared=declared,
                    resolved=resolved,
                    kind=kind,
                )
            )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=dependencies,
        )

    def _parse_requirements_file(self, req_path, out_map: dict[str, dict[str, Any]]) -> None:
        try:
            lines = req_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Split off environment markers
                if ";" in line:
                    line = line.split(";", 1)[0].strip()

                # Match name and version specifiers
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*(.*)$", line)
                if match:
                    name = match.group(1).lower()
                    spec = match.group(2).strip() or None
                    out_map[name] = {"declared": spec, "kind": "direct"}
        except Exception:
            pass

    def _parse_pyproject_file(self, pyproject_path, out_map: dict[str, dict[str, Any]]) -> None:
        try:
            data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            # Standard PEP 621 dependencies
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                if isinstance(dep, str):
                    clean = dep.split(";", 1)[0].strip()
                    m = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*(.*)$", clean)
                    if m:
                        name = m.group(1).lower()
                        spec = m.group(2).strip() or None
                        out_map[name] = {"declared": spec, "kind": "direct"}

            # Optional / dev dependencies
            opt_deps = data.get("project", {}).get("optional-dependencies", {})
            for group, deps in opt_deps.items():
                kind = "dev" if "dev" in group.lower() or "test" in group.lower() else "direct"
                for dep in deps:
                    if isinstance(dep, str):
                        clean = dep.split(";", 1)[0].strip()
                        m = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*(.*)$", clean)
                        if m:
                            name = m.group(1).lower()
                            spec = m.group(2).strip() or None
                            if name not in out_map:
                                out_map[name] = {"declared": spec, "kind": kind}

            # Poetry dependencies in [tool.poetry.dependencies]
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for name, val in poetry_deps.items():
                if name.lower() == "python":
                    continue
                spec = (
                    val
                    if isinstance(val, str)
                    else (val.get("version") if isinstance(val, dict) else None)
                )
                out_map[name.lower()] = {"declared": spec, "kind": "direct"}
        except Exception:
            pass

    def _parse_toml_lockfile(self, lock_path, out_map: dict[str, str]) -> None:
        try:
            data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
            # Both uv.lock and poetry.lock use [[package]] tables
            packages = data.get("package", [])
            for pkg in packages:
                name = pkg.get("name")
                version = pkg.get("version")
                if name and version:
                    out_map[name.lower()] = str(version)
        except Exception:
            pass
