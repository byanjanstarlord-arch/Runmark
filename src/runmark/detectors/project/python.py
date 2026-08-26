"""Python project signals detector."""

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus


class PythonProjectDetector(Detector):
    """Detects Python project signals, frameworks, and package managers."""

    @property
    def name(self) -> str:
        return "project_python"

    @property
    def category(self) -> str:
        return "project"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        languages: set[str] = set()
        frameworks: set[str] = set()
        package_managers: set[str] = set()

        # Check Python manifest indicators
        has_pyproject = (root / "pyproject.toml").exists()
        has_requirements = (root / "requirements.txt").exists()
        has_setup = (root / "setup.py").exists() or (root / "setup.cfg").exists()
        has_pipfile = (root / "Pipfile").exists()
        has_uv = (root / "uv.lock").exists()
        has_poetry = (root / "poetry.lock").exists()
        has_manage_py = (root / "manage.py").exists()

        if any(
            [
                has_pyproject,
                has_requirements,
                has_setup,
                has_pipfile,
                has_uv,
                has_poetry,
                has_manage_py,
            ]
        ):
            languages.add("python")

        if has_requirements:
            package_managers.add("pip")
        if has_pipfile:
            package_managers.add("pipenv")
        if has_poetry:
            package_managers.add("poetry")
        if has_uv:
            package_managers.add("uv")
        if has_pyproject and not has_poetry and not has_uv:
            package_managers.add("pip")

        # Framework detection by file presence
        if has_manage_py:
            frameworks.add("django")

        # Inspect requirements.txt or pyproject.toml for framework keywords
        manifest_files = [root / "requirements.txt", root / "pyproject.toml", root / "Pipfile"]
        for mf in manifest_files:
            if mf.exists():
                try:
                    content = mf.read_text(encoding="utf-8", errors="ignore").lower()
                    if "django" in content:
                        frameworks.add("django")
                    if "fastapi" in content:
                        frameworks.add("fastapi")
                    if "flask" in content:
                        frameworks.add("flask")
                    if "celery" in content:
                        frameworks.add("celery")
                    if "tornado" in content:
                        frameworks.add("tornado")
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
