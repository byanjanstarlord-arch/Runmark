"""Unit tests for ContractDiffEngine and semantic difference calculation."""

from runmark.contracts.diff import (
    ContractChangeKind,
    ContractDiffEngine,
)
from runmark.models.contract import (
    EnvironmentContract,
    NetworkContract,
    PortRequirement,
    ProjectContract,
    RunmarkContract,
    ServiceRequirement,
)


class TestContractDiffEngine:
    """Test comparing two contract definitions for semantic drift."""

    def test_no_changes_identical_contracts(self) -> None:
        c1 = RunmarkContract(
            version=1,
            project=ProjectContract(name="app"),
            runtime={"python": ">=3.12"},
            services={"postgresql": ServiceRequirement(version=">=16", required=True)},
        )
        c2 = RunmarkContract(
            version=1,
            project=ProjectContract(name="app"),
            runtime={"python": ">=3.12"},
            services={"postgresql": ServiceRequirement(version=">=16", required=True)},
        )

        res = ContractDiffEngine.diff(c1, c2)
        assert res.status == "UNCHANGED"
        assert not res.has_changes
        assert res.summary.added == 0
        assert res.summary.removed == 0
        assert res.summary.changed == 0

    def test_semantic_ordering_invariance(self) -> None:
        # Reordered environment variables and ports should be identical
        c1 = RunmarkContract(
            version=1,
            environment=EnvironmentContract(required=["DATABASE_URL", "REDIS_URL"]),
            network=NetworkContract(
                ports={
                    "8000": PortRequirement(protocol="tcp", required=True),
                    "5432": PortRequirement(protocol="tcp", required=False),
                }
            ),
        )
        c2 = RunmarkContract(
            version=1,
            environment=EnvironmentContract(required=["REDIS_URL", "DATABASE_URL"]),
            network=NetworkContract(
                ports={
                    "5432": PortRequirement(protocol="tcp", required=False),
                    "8000": PortRequirement(protocol="tcp", required=True),
                }
            ),
        )

        res = ContractDiffEngine.diff(c1, c2)
        assert res.status == "UNCHANGED"
        assert not res.has_changes

    def test_runtime_and_service_changes(self) -> None:
        c_before = RunmarkContract(
            version=1,
            runtime={"python": ">=3.11,<3.12", "node": ">=18"},
            services={"postgresql": ServiceRequirement(version=">=15", required=True)},
            environment=EnvironmentContract(required=["DATABASE_URL"]),
        )
        c_after = RunmarkContract(
            version=1,
            runtime={"python": ">=3.12,<3.13"},  # node removed, python upgraded
            services={
                "postgresql": ServiceRequirement(version=">=16", required=True),  # upgraded
                "redis": ServiceRequirement(version=">=7", required=True),  # added
            },
            environment=EnvironmentContract(
                required=["DATABASE_URL", "REDIS_URL"]
            ),  # REDIS_URL added
        )

        res = ContractDiffEngine.diff(c_before, c_after)
        assert res.status == "CHANGED"
        assert res.has_changes
        assert res.summary.added == 2  # redis service, REDIS_URL env
        assert res.summary.removed == 1  # node runtime
        assert res.summary.changed == 2  # python runtime, postgresql service

        change_map = {(c.category, c.name): c for c in res.changes}

        # Check Python runtime changed
        py_ch = change_map[("runtime", "python")]
        assert py_ch.change == ContractChangeKind.CHANGED
        assert py_ch.before == ">=3.11,<3.12"
        assert py_ch.after == ">=3.12,<3.13"

        # Check Node runtime removed
        node_ch = change_map[("runtime", "node")]
        assert node_ch.change == ContractChangeKind.REMOVED

        # Check Redis added
        redis_ch = change_map[("service", "redis")]
        assert redis_ch.change == ContractChangeKind.ADDED

        # Check REDIS_URL added
        redis_url_ch = change_map[("environment", "REDIS_URL")]
        assert redis_url_ch.change == ContractChangeKind.ADDED
