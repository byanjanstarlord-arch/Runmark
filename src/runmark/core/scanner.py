"""Scanner engine that coordinates all detectors to produce a unified RunmarkState."""

import os
import uuid
from pathlib import Path
from typing import Any

from runmark import __schema_version__, __version__
from runmark.detectors.base import DetectionContext, DetectionResult, DetectionStatus
from runmark.detectors.registry import DetectorRegistry, default_registry
from runmark.models.container import ContainerState
from runmark.models.dependency import DependencyState
from runmark.models.environment import EnvironmentState
from runmark.models.git import GitState
from runmark.models.network import PortState
from runmark.models.project import ProjectState
from runmark.models.runmark import RunmarkMetadata, RunmarkState
from runmark.models.runtime import RuntimeState
from runmark.models.service import ServiceState
from runmark.models.system import SystemState
from runmark.utils.hashing import calculate_environment_fingerprint
from runmark.utils.platform import get_os_info


class Scanner:
    """Orchestrates environment discovery and state synthesis."""

    def __init__(
        self,
        project_root: Path | str,
        registry: DetectorRegistry | None = None,
        environment_override: dict[str, str] | None = None,
        configuration: dict[str, Any] | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.registry = registry or default_registry
        self.environment = environment_override or dict(os.environ)
        self.configuration = configuration or {}

    def scan(self, message: str | None = None) -> RunmarkState:
        """Run all applicable detectors and construct a normalized, fingerprint RunmarkState."""
        context = DetectionContext(
            project_root=self.project_root,
            environment=self.environment,
            configuration=self.configuration,
        )

        results: list[DetectionResult] = []
        for detector in self.registry.get_all():
            try:
                res = detector.detect(context)
                results.append(res)
            except Exception as exc:
                results.append(
                    DetectionResult(
                        name=detector.name,
                        category=detector.category,
                        status=DetectionStatus.ERROR,
                        error_message=f"Detector '{detector.name}' unhandled error: {exc}",
                    )
                )

        # 1. Project state
        proj_name = self.project_root.name
        languages: set = set()
        frameworks: set = set()
        pkg_managers: set = set()
        containerization: set = set()

        for res in results:
            if (
                res.category == "project"
                and res.status == DetectionStatus.DETECTED
                and isinstance(res.data, dict)
            ):
                languages.update(res.data.get("languages", []))
                frameworks.update(res.data.get("frameworks", []))
                pkg_managers.update(res.data.get("package_managers", []))
                containerization.update(res.data.get("containerization", []))

        project_state = ProjectState(
            name=proj_name,
            root=self.project_root.name,
            languages=sorted(languages),
            frameworks=sorted(frameworks),
            package_managers=sorted(pkg_managers),
            containerization=sorted(containerization),
        )

        # 2. System state
        sys_res = next((r for r in results if r.category == "system" and r.data), None)
        if sys_res and isinstance(sys_res.data, SystemState):
            system_state = sys_res.data
        else:
            sys_info = get_os_info()
            system_state = SystemState(
                os_name=sys_info["os_name"],
                os_version=sys_info["os_version"],
                architecture=sys_info["architecture"],
            )

        # 3. Git state
        git_res = next((r for r in results if r.category == "git" and r.data), None)
        if git_res and isinstance(git_res.data, GitState):
            git_state = git_res.data
        else:
            git_state = GitState(is_repository=False, branch=None, commit=None, dirty=False)

        # 4. Runtimes
        runtimes_map: dict[str, RuntimeState] = {}
        for res in results:
            if res.category == "runtimes" and isinstance(res.data, RuntimeState):
                runtimes_map[res.data.name] = res.data

        # 5. Dependencies
        dependencies_list: list[DependencyState] = []
        for res in results:
            if res.category == "dependencies" and isinstance(res.data, list):
                dependencies_list.extend([d for d in res.data if isinstance(d, DependencyState)])

        # 6. Services
        services_list: list[ServiceState] = []
        for res in results:
            if res.category == "services" and isinstance(res.data, ServiceState):
                services_list.append(res.data)

        # 7. Environment
        env_res = next((r for r in results if r.category == "environment" and r.data), None)
        if env_res and isinstance(env_res.data, EnvironmentState):
            env_state = env_res.data
        else:
            env_state = EnvironmentState()

        # 8. Network
        network_list: list[PortState] = []
        for res in results:
            if res.category == "network" and isinstance(res.data, list):
                network_list.extend([p for p in res.data if isinstance(p, PortState)])

        # 9. Containers
        containers_list: list[ContainerState] = []
        for res in results:
            if res.category == "containers" and isinstance(res.data, list):
                containers_list.extend([c for d in res.data if isinstance(c := d, ContainerState)])

        # Initial draft metadata
        snap_id = f"snap_{uuid.uuid4().hex[:12]}"
        metadata = RunmarkMetadata(
            id=snap_id,
            tool_version=__version__,
            schema_version=__schema_version__,
            environment_fingerprint="",
            message=message,
        )

        state = RunmarkState(
            runmark=metadata,
            project=project_state,
            git=git_state,
            system=system_state,
            runtimes=runtimes_map,
            dependencies=dependencies_list,
            services=services_list,
            environment=env_state,
            network=network_list,
            containers=containers_list,
        )

        # Compute deterministic fingerprint
        fp = calculate_environment_fingerprint(state)
        state.runmark.environment_fingerprint = fp

        return state
