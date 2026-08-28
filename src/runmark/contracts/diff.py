"""Semantic contract diffing engine comparing environment requirements."""

from enum import Enum
from typing import Any

from runmark.models.common import RunmarkBaseModel
from runmark.models.contract import RunmarkContract


class ContractChangeKind(str, Enum):
    """Classification of requirement differences."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


class ContractChange(RunmarkBaseModel):
    """A discrete difference between two contract definitions."""

    category: str
    name: str
    change: ContractChangeKind
    before: Any | None = None
    after: Any | None = None
    details: dict[str, Any] = {}


class ContractDiffSummary(RunmarkBaseModel):
    """Aggregated counters for contract changes."""

    added: int = 0
    removed: int = 0
    changed: int = 0
    unchanged: int = 0


class ContractDiffResult(RunmarkBaseModel):
    """Root model for semantic contract comparison results."""

    status: str  # "CHANGED" or "UNCHANGED"
    summary: ContractDiffSummary
    changes: list[ContractChange]

    @property
    def has_changes(self) -> bool:
        """Return True if any requirements were added, removed, or changed."""
        return self.summary.added > 0 or self.summary.removed > 0 or self.summary.changed > 0


class ContractDiffEngine:
    """Performs semantic comparison between two RunmarkContract definitions."""

    @classmethod
    def diff(cls, before: RunmarkContract, after: RunmarkContract) -> ContractDiffResult:
        """Compare two contracts and produce a normalized list of semantic changes."""
        changes: list[ContractChange] = []

        # 1. Project identity
        b_name = before.project.name
        a_name = after.project.name
        if b_name != a_name:
            changes.append(
                ContractChange(
                    category="project",
                    name="name",
                    change=ContractChangeKind.CHANGED,
                    before=b_name,
                    after=a_name,
                )
            )

        # 2. Platform OS
        b_os = set(before.platform.os)
        a_os = set(after.platform.os)
        for os_name in sorted(a_os - b_os):
            changes.append(
                ContractChange(
                    category="platform",
                    name=f"os:{os_name}",
                    change=ContractChangeKind.ADDED,
                    before=None,
                    after=os_name,
                )
            )
        for os_name in sorted(b_os - a_os):
            changes.append(
                ContractChange(
                    category="platform",
                    name=f"os:{os_name}",
                    change=ContractChangeKind.REMOVED,
                    before=os_name,
                    after=None,
                )
            )

        # Platform Architecture
        b_arch = set(before.platform.architecture)
        a_arch = set(after.platform.architecture)
        for arch_name in sorted(a_arch - b_arch):
            changes.append(
                ContractChange(
                    category="platform",
                    name=f"arch:{arch_name}",
                    change=ContractChangeKind.ADDED,
                    before=None,
                    after=arch_name,
                )
            )
        for arch_name in sorted(b_arch - a_arch):
            changes.append(
                ContractChange(
                    category="platform",
                    name=f"arch:{arch_name}",
                    change=ContractChangeKind.REMOVED,
                    before=arch_name,
                    after=None,
                )
            )

        # 3. Runtimes
        all_runtimes = sorted(set(before.runtime.keys()) | set(after.runtime.keys()))
        for r_name in all_runtimes:
            b_val = before.runtime.get(r_name)
            a_val = after.runtime.get(r_name)
            if b_val is None and a_val is not None:
                changes.append(
                    ContractChange(
                        category="runtime",
                        name=r_name,
                        change=ContractChangeKind.ADDED,
                        before=None,
                        after=a_val,
                    )
                )
            elif b_val is not None and a_val is None:
                changes.append(
                    ContractChange(
                        category="runtime",
                        name=r_name,
                        change=ContractChangeKind.REMOVED,
                        before=b_val,
                        after=None,
                    )
                )
            elif b_val != a_val:
                changes.append(
                    ContractChange(
                        category="runtime",
                        name=r_name,
                        change=ContractChangeKind.CHANGED,
                        before=b_val,
                        after=a_val,
                    )
                )

        # 4. Dependencies
        cls._diff_deps(
            "dependency:python", before.dependencies.python, after.dependencies.python, changes
        )
        cls._diff_deps(
            "dependency:node", before.dependencies.node, after.dependencies.node, changes
        )

        # 5. Services
        all_services = sorted(set(before.services.keys()) | set(after.services.keys()))
        for s_name in all_services:
            b_svc = before.services.get(s_name)
            a_svc = after.services.get(s_name)
            if b_svc is None and a_svc is not None:
                changes.append(
                    ContractChange(
                        category="service",
                        name=s_name,
                        change=ContractChangeKind.ADDED,
                        before=None,
                        after=a_svc.version,
                        details={"required": a_svc.required},
                    )
                )
            elif b_svc is not None and a_svc is None:
                changes.append(
                    ContractChange(
                        category="service",
                        name=s_name,
                        change=ContractChangeKind.REMOVED,
                        before=b_svc.version,
                        after=None,
                        details={"required": b_svc.required},
                    )
                )
            elif b_svc is not None and a_svc is not None:
                if b_svc.version != a_svc.version or b_svc.required != a_svc.required:
                    changes.append(
                        ContractChange(
                            category="service",
                            name=s_name,
                            change=ContractChangeKind.CHANGED,
                            before=b_svc.version,
                            after=a_svc.version,
                            details={
                                "before_required": b_svc.required,
                                "after_required": a_svc.required,
                            },
                        )
                    )

        # 6. Environment variables
        b_req = set(before.environment.required)
        a_req = set(after.environment.required)
        for var in sorted(a_req - b_req):
            changes.append(
                ContractChange(
                    category="environment",
                    name=var,
                    change=ContractChangeKind.ADDED,
                    before=None,
                    after="required",
                )
            )
        for var in sorted(b_req - a_req):
            changes.append(
                ContractChange(
                    category="environment",
                    name=var,
                    change=ContractChangeKind.REMOVED,
                    before="required",
                    after=None,
                )
            )

        b_opt = set(before.environment.optional)
        a_opt = set(after.environment.optional)
        for var in sorted(a_opt - b_opt):
            changes.append(
                ContractChange(
                    category="environment",
                    name=var,
                    change=ContractChangeKind.ADDED,
                    before=None,
                    after="optional",
                )
            )
        for var in sorted(b_opt - a_opt):
            changes.append(
                ContractChange(
                    category="environment",
                    name=var,
                    change=ContractChangeKind.REMOVED,
                    before="optional",
                    after=None,
                )
            )

        # 7. Network Ports
        all_ports = sorted(
            set(before.network.ports.keys()) | set(after.network.ports.keys()),
            key=lambda x: int(x) if x.isdigit() else x,
        )
        for p_str in all_ports:
            b_p = before.network.ports.get(p_str)
            a_p = after.network.ports.get(p_str)
            if b_p is None and a_p is not None:
                changes.append(
                    ContractChange(
                        category="network",
                        name=f"port:{p_str}/{a_p.protocol}",
                        change=ContractChangeKind.ADDED,
                        before=None,
                        after=f"{p_str}/{a_p.protocol}",
                    )
                )
            elif b_p is not None and a_p is None:
                changes.append(
                    ContractChange(
                        category="network",
                        name=f"port:{p_str}/{b_p.protocol}",
                        change=ContractChangeKind.REMOVED,
                        before=f"{p_str}/{b_p.protocol}",
                        after=None,
                    )
                )
            elif b_p is not None and a_p is not None:
                if b_p.protocol != a_p.protocol or b_p.required != a_p.required:
                    changes.append(
                        ContractChange(
                            category="network",
                            name=f"port:{p_str}",
                            change=ContractChangeKind.CHANGED,
                            before=f"{b_p.protocol} (required={b_p.required})",
                            after=f"{a_p.protocol} (required={a_p.required})",
                        )
                    )

        # 8. Containers
        b_docker = before.containers.docker.required if before.containers.docker else False
        a_docker = after.containers.docker.required if after.containers.docker else False
        if b_docker != a_docker:
            changes.append(
                ContractChange(
                    category="container",
                    name="docker",
                    change=ContractChangeKind.CHANGED,
                    before=f"required={b_docker}",
                    after=f"required={a_docker}",
                )
            )

        b_compose = before.containers.compose.required if before.containers.compose else False
        a_compose = after.containers.compose.required if after.containers.compose else False
        if b_compose != a_compose:
            changes.append(
                ContractChange(
                    category="container",
                    name="compose",
                    change=ContractChangeKind.CHANGED,
                    before=f"required={b_compose}",
                    after=f"required={a_compose}",
                )
            )

        # Compute summary
        added_count = sum(1 for c in changes if c.change == ContractChangeKind.ADDED)
        removed_count = sum(1 for c in changes if c.change == ContractChangeKind.REMOVED)
        changed_count = sum(1 for c in changes if c.change == ContractChangeKind.CHANGED)
        unchanged_count = sum(1 for c in changes if c.change == ContractChangeKind.UNCHANGED)

        summary = ContractDiffSummary(
            added=added_count,
            removed=removed_count,
            changed=changed_count,
            unchanged=unchanged_count,
        )

        status = (
            "CHANGED"
            if (added_count > 0 or removed_count > 0 or changed_count > 0)
            else "UNCHANGED"
        )

        return ContractDiffResult(
            status=status,
            summary=summary,
            changes=changes,
        )

    @classmethod
    def _diff_deps(
        cls,
        cat: str,
        before_deps: dict[str, str],
        after_deps: dict[str, str],
        changes: list[ContractChange],
    ) -> None:
        """Helper to diff package dependencies."""
        all_pkgs = sorted(set(before_deps.keys()) | set(after_deps.keys()))
        for pkg in all_pkgs:
            b_v = before_deps.get(pkg)
            a_v = after_deps.get(pkg)
            if b_v is None and a_v is not None:
                changes.append(
                    ContractChange(
                        category=cat,
                        name=pkg,
                        change=ContractChangeKind.ADDED,
                        before=None,
                        after=a_v,
                    )
                )
            elif b_v is not None and a_v is None:
                changes.append(
                    ContractChange(
                        category=cat,
                        name=pkg,
                        change=ContractChangeKind.REMOVED,
                        before=b_v,
                        after=None,
                    )
                )
            elif b_v != a_v:
                changes.append(
                    ContractChange(
                        category=cat,
                        name=pkg,
                        change=ContractChangeKind.CHANGED,
                        before=b_v,
                        after=a_v,
                    )
                )
