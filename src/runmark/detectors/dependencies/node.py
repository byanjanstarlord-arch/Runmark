"""Node.js dependency manifest and lockfile parser."""

import json

import yaml

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DependencyKind, DetectionStatus
from runmark.models.dependency import DependencyState


class NodeDependencyDetector(Detector):
    """Detects and parses Node.js dependencies from package.json, package-lock.json, yarn.lock, and pnpm-lock.yaml."""

    @property
    def name(self) -> str:
        return "dependencies_node"

    @property
    def category(self) -> str:
        return "dependencies"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        declared_map: dict[str, dict[str, str]] = {}
        resolved_map: dict[str, str] = {}
        manager = "npm"

        pkg_json = root / "package.json"
        if not pkg_json.exists():
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=[],
            )

        # 1. Parse package.json
        self._parse_package_json(pkg_json, declared_map)

        # 2. Parse package-lock.json if present
        pkg_lock = root / "package-lock.json"
        if pkg_lock.exists():
            manager = "npm"
            self._parse_package_lock(pkg_lock, resolved_map)

        # 3. Parse yarn.lock if present
        yarn_lock = root / "yarn.lock"
        if yarn_lock.exists():
            manager = "yarn"
            self._parse_yarn_lock(yarn_lock, resolved_map)

        # 4. Parse pnpm-lock.yaml if present
        pnpm_lock = root / "pnpm-lock.yaml"
        if pnpm_lock.exists():
            manager = "pnpm"
            self._parse_pnpm_lock(pnpm_lock, resolved_map)

        all_pkg_names = sorted(set(list(declared_map.keys()) + list(resolved_map.keys())))
        dependencies: list[DependencyState] = []

        for name in all_pkg_names:
            decl_info = declared_map.get(name, {})
            declared = decl_info.get("declared")
            kind_str = decl_info.get("kind", "direct")
            resolved = resolved_map.get(name)

            if kind_str == "dev":
                kind = DependencyKind.DEV
            elif kind_str == "peer":
                kind = DependencyKind.PEER
            else:
                kind = DependencyKind.DIRECT

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

    def _parse_package_json(self, pkg_path, out_map: dict[str, dict[str, str]]) -> None:
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            for name, spec in data.get("dependencies", {}).items():
                out_map[name] = {"declared": str(spec), "kind": "direct"}
            for name, spec in data.get("devDependencies", {}).items():
                if name not in out_map:
                    out_map[name] = {"declared": str(spec), "kind": "dev"}
            for name, spec in data.get("peerDependencies", {}).items():
                if name not in out_map:
                    out_map[name] = {"declared": str(spec), "kind": "peer"}
        except Exception:
            pass

    def _parse_package_lock(self, lock_path, out_map: dict[str, str]) -> None:
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
            # npm lockfile v2 / v3 packages
            packages = data.get("packages", {})
            for pkg_key, pkg_info in packages.items():
                if not pkg_key:  # root package
                    continue
                # Extract clean package name from node_modules/<pkg_name>
                clean_name = pkg_key.replace("node_modules/", "").strip()
                if clean_name and "version" in pkg_info:
                    out_map[clean_name] = str(pkg_info["version"])

            # npm lockfile v1 fallback
            deps = data.get("dependencies", {})
            for name, info in deps.items():
                if isinstance(info, dict) and "version" in info and name not in out_map:
                    out_map[name] = str(info["version"])
        except Exception:
            pass

    def _parse_yarn_lock(self, lock_path, out_map: dict[str, str]) -> None:
        try:
            content = lock_path.read_text(encoding="utf-8", errors="ignore")
            # Matches header blocks like "package-name@^1.0.0:" or "@scope/pkg@^1.0.0:"
            # followed by "  version "1.2.3""
            current_pkgs: list[str] = []
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.endswith(":") and not line_str.startswith("#"):
                    headers = [h.strip().strip('"').strip("'") for h in line_str[:-1].split(",")]
                    current_pkgs = []
                    for h in headers:
                        # Extract name before @version
                        if h.startswith("@"):
                            parts = h[1:].split("@", 1)
                            if len(parts) == 2:
                                current_pkgs.append(f"@{parts[0]}")
                        else:
                            parts = h.split("@", 1)
                            if len(parts) == 2:
                                current_pkgs.append(parts[0])
                elif line_str.startswith("version ") and current_pkgs:
                    version_val = line_str.split("version ", 1)[1].strip().strip('"').strip("'")
                    for p in current_pkgs:
                        out_map[p] = version_val
                    current_pkgs = []
        except Exception:
            pass

    def _parse_pnpm_lock(self, lock_path, out_map: dict[str, str]) -> None:
        try:
            data = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return
            packages = data.get("packages", {})
            for pkg_key in packages.keys():
                # Formats: /pkg-name/1.2.3 or pkg-name@1.2.3
                clean_key = str(pkg_key).lstrip("/")
                if "@" in clean_key:
                    if clean_key.startswith("@"):
                        # Scoped package @scope/name@1.2.3
                        parts = clean_key[1:].split("@", 1)
                        if len(parts) == 2:
                            name = f"@{parts[0]}"
                            ver = parts[1].split("(", 1)[0].strip()
                            out_map[name] = ver
                    else:
                        parts = clean_key.split("@", 1)
                        if len(parts) == 2:
                            name = parts[0]
                            ver = parts[1].split("(", 1)[0].strip()
                            out_map[name] = ver
                elif "/" in clean_key:
                    parts = clean_key.rsplit("/", 1)
                    if len(parts) == 2:
                        name, ver = parts[0], parts[1].split("(", 1)[0].strip()
                        out_map[name] = ver
        except Exception:
            pass
