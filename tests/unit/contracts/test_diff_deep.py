"""Deep unit tests for contract diffing engine across all fields."""

from runmark.contracts.diff import ContractChangeKind, ContractDiffEngine
from runmark.models.contract import (
    ComposeRequirement,
    ContainerContract,
    DependencyContract,
    DockerRequirement,
    PlatformContract,
    ProjectContract,
    RunmarkContract,
)


class TestContractDiffDeep:
    """Test full diffing coverage for containers, platform, and dependencies."""

    def test_diff_containers_and_platform(self) -> None:
        c1 = RunmarkContract(
            version=1,
            project=ProjectContract(name="app-v1"),
            platform=PlatformContract(os=["linux"], architecture=["x86_64"]),
            containers=ContainerContract(docker=DockerRequirement(required=True)),
            dependencies=DependencyContract(
                python={"fastapi": ">=0.100.0"},
                node={"react": "^18.0.0"},
            ),
        )
        c2 = RunmarkContract(
            version=1,
            project=ProjectContract(name="app-v2"),
            platform=PlatformContract(os=["linux", "darwin"], architecture=["arm64"]),
            containers=ContainerContract(
                docker=DockerRequirement(required=False),
                compose=ComposeRequirement(required=True),
            ),
            dependencies=DependencyContract(
                python={"fastapi": ">=0.109.0", "pydantic": ">=2.0"},
                node={},
            ),
        )

        res = ContractDiffEngine.diff(c1, c2)
        assert res.status == "CHANGED"
        assert res.has_changes

        change_map = {(c.category, c.name): c for c in res.changes}

        # Project name
        assert change_map[("project", "name")].change == ContractChangeKind.CHANGED

        # Platform OS added darwin
        assert change_map[("platform", "os:darwin")].change == ContractChangeKind.ADDED

        # Platform Arch added arm64, removed x86_64
        assert change_map[("platform", "arch:arm64")].change == ContractChangeKind.ADDED
        assert change_map[("platform", "arch:x86_64")].change == ContractChangeKind.REMOVED

        # Containers
        assert change_map[("container", "docker")].change == ContractChangeKind.CHANGED
        assert change_map[("container", "compose")].change == ContractChangeKind.CHANGED

        # Dependencies
        assert change_map[("dependency:python", "fastapi")].change == ContractChangeKind.CHANGED
        assert change_map[("dependency:python", "pydantic")].change == ContractChangeKind.ADDED
        assert change_map[("dependency:node", "react")].change == ContractChangeKind.REMOVED
