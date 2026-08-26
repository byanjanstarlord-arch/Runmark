"""Node.js / JavaScript / TypeScript project signals detector."""

import json

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus


class NodeProjectDetector(Detector):
    """Detects Node.js / JavaScript / TypeScript project signals, frameworks, and package managers."""

    @property
    def name(self) -> str:
        return "project_node"

    @property
    def category(self) -> str:
        return "project"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        languages: set[str] = set()
        frameworks: set[str] = set()
        package_managers: set[str] = set()

        pkg_json_file = root / "package.json"
        has_pkg = pkg_json_file.exists()
        has_pkg_lock = (root / "package-lock.json").exists()
        has_yarn = (root / "yarn.lock").exists()
        has_pnpm = (root / "pnpm-lock.yaml").exists()
        has_bun = (root / "bun.lockb").exists() or (root / "bun.lock").exists()
        has_tsconfig = (root / "tsconfig.json").exists()

        if has_pkg or has_pkg_lock or has_yarn or has_pnpm or has_bun:
            languages.add("javascript")

        if has_tsconfig:
            languages.add("typescript")

        if has_pkg_lock:
            package_managers.add("npm")
        if has_yarn:
            package_managers.add("yarn")
        if has_pnpm:
            package_managers.add("pnpm")
        if has_bun:
            package_managers.add("bun")
        if has_pkg and not package_managers:
            package_managers.add("npm")

        if has_pkg:
            try:
                pkg_data = json.loads(pkg_json_file.read_text(encoding="utf-8"))
                all_deps = {}
                all_deps.update(pkg_data.get("dependencies", {}))
                all_deps.update(pkg_data.get("devDependencies", {}))

                dep_names = {k.lower() for k in all_deps.keys()}
                if "typescript" in dep_names or has_tsconfig:
                    languages.add("typescript")
                if "next" in dep_names:
                    frameworks.add("next.js")
                if "react" in dep_names:
                    frameworks.add("react")
                if "vue" in dep_names or "nuxt" in dep_names:
                    frameworks.add("vue")
                if "svelte" in dep_names or "@sveltejs/kit" in dep_names:
                    frameworks.add("svelte")
                if "express" in dep_names:
                    frameworks.add("express")
                if "fastify" in dep_names:
                    frameworks.add("fastify")
                if "nestjs" in dep_names or "@nestjs/core" in dep_names:
                    frameworks.add("nestjs")
            except Exception:
                pass

        if not languages:
            return DetectionResult(
                name=self.name,
                category=self.category,
                status=DetectionStatus.NOT_APPLICABLE,
                data=None,
            )

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data={
                "languages": sorted(languages),
                "frameworks": sorted(frameworks),
                "package_managers": sorted(package_managers),
            },
        )
