"""Environment variable requirements detector and secret redactor."""

import os

from runmark.detectors.base import DetectionContext, DetectionResult, Detector
from runmark.models.common import DetectionStatus
from runmark.models.environment import EnvironmentState, EnvironmentVariableState
from runmark.security.redactor import SecretRedactor


class EnvDetector(Detector):
    """Detects required environment variables from .env.example / .env.sample and process environment."""

    @property
    def name(self) -> str:
        return "environment"

    @property
    def category(self) -> str:
        return "environment"

    def detect(self, context: DetectionContext) -> DetectionResult:
        root = context.project_root
        declared_required: dict[str, str] = {}
        example_files = [".env.example", ".env.sample", ".env.template", ".env.dist"]

        for fname in example_files:
            fpath = root / fname
            if fpath.exists():
                try:
                    lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        # format: KEY=... or export KEY=...
                        if line.startswith("export "):
                            line = line[len("export ") :].strip()
                        if "=" in line:
                            var_name = line.split("=", 1)[0].strip()
                            if var_name:
                                declared_required[var_name] = fname
                        else:
                            var_name = line.strip()
                            if var_name:
                                declared_required[var_name] = fname
                except Exception:
                    pass

        # Also inspect current process environment or passed env
        active_env = context.environment if context.environment else dict(os.environ)

        variables_map: dict[str, EnvironmentVariableState] = {}

        # 1. Add all declared required variables
        for var_name, source_file in declared_required.items():
            is_present = var_name in active_env and bool(active_env[var_name].strip())
            # Use redactor to produce safe metadata
            state = SecretRedactor.redact_env_variable(
                name=var_name,
                value=active_env.get(var_name),
                required=True,
                present=is_present,
                source=source_file,
            )
            variables_map[var_name] = state

        # 2. Add relevant environment variables present in process that start with project-specific prefixes
        for k, v in active_env.items():
            if k not in variables_map:
                # Include standard dev env flags if present
                if k in {"DEBUG", "ENVIRONMENT", "NODE_ENV", "PORT", "DATABASE_URL", "REDIS_URL"}:
                    state = SecretRedactor.redact_env_variable(
                        name=k,
                        value=v,
                        required=False,
                        present=bool(v.strip()),
                        source="process",
                    )
                    variables_map[k] = state

        env_state = EnvironmentState(variables=variables_map)

        return DetectionResult(
            name=self.name,
            category=self.category,
            status=DetectionStatus.DETECTED,
            data=env_state,
        )
