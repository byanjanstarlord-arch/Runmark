"""Semantic Diff engine for comparing Runmark states."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from runmark.models.runmark import RunmarkState


class DiffClassification(str, Enum):
    """Classification of a difference."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


class DiffSeverity(str, Enum):
    """Severity of a detected difference."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class DiffItem:
    """Individual detected semantic difference."""

    category: str
    item_name: str
    classification: DiffClassification
    severity: DiffSeverity
    old_value: Any | None = None
    new_value: Any | None = None
    description: str = ""
    is_source_revision: bool = False


@dataclass
class RunmarkDiff:
    """Complete semantic diff between two Runmark states."""

    from_id: str
    to_id: str
    from_fingerprint: str
    to_fingerprint: str
    is_identical: bool
    items: list[DiffItem] = field(default_factory=list)

    @property
    def environment_items(self) -> list[DiffItem]:
        """Differences affecting the environment."""
        return [item for item in self.items if not item.is_source_revision]

    @property
    def source_items(self) -> list[DiffItem]:
        """Differences affecting the source code / Git state."""
        return [item for item in self.items if item.is_source_revision]

    @property
    def has_critical(self) -> bool:
        """Whether any critical severity difference was found."""
        return any(item.severity == DiffSeverity.CRITICAL for item in self.environment_items)

    @property
    def has_warning(self) -> bool:
        """Whether any warning severity difference was found."""
        return any(item.severity == DiffSeverity.WARNING for item in self.environment_items)


class DiffEngine:
    """Semantic comparison engine for Runmark states."""

    @classmethod
    def compare(cls, base: RunmarkState, current: RunmarkState) -> RunmarkDiff:
        """Compute semantic differences between base (expected) and current (actual)."""
        items: list[DiffItem] = []

        # 1. System Diff
        cls._diff_system(base, current, items)

        # 2. Runtimes Diff
        cls._diff_runtimes(base, current, items)

        # 3. Dependencies Diff
        cls._diff_dependencies(base, current, items)

        # 4. Services Diff
        cls._diff_services(base, current, items)

        # 5. Environment Variables Diff
        cls._diff_environment(base, current, items)

        # 6. Network / Ports Diff
        cls._diff_network(base, current, items)

        # 7. Containers Diff
        cls._diff_containers(base, current, items)

        # 8. Git / Source Revision Diff (marked as source revision)
        cls._diff_git(base, current, items)

        is_identical = (
            len([i for i in items if i.classification != DiffClassification.UNCHANGED]) == 0
        )

        return RunmarkDiff(
            from_id=base.runmark.id,
            to_id=current.runmark.id,
            from_fingerprint=base.runmark.environment_fingerprint,
            to_fingerprint=current.runmark.environment_fingerprint,
            is_identical=is_identical,
            items=items,
        )

    @classmethod
    def _diff_system(cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]) -> None:
        if base.system.os_name != current.system.os_name:
            out.append(
                DiffItem(
                    category="system",
                    item_name="os_name",
                    classification=DiffClassification.CHANGED,
                    severity=DiffSeverity.WARNING,
                    old_value=base.system.os_name,
                    new_value=current.system.os_name,
                    description=f"Operating system changed from {base.system.os_name} to {current.system.os_name}",
                )
            )
        if base.system.architecture != current.system.architecture:
            out.append(
                DiffItem(
                    category="system",
                    item_name="architecture",
                    classification=DiffClassification.CHANGED,
                    severity=DiffSeverity.WARNING,
                    old_value=base.system.architecture,
                    new_value=current.system.architecture,
                    description=f"CPU Architecture changed from {base.system.architecture} to {current.system.architecture}",
                )
            )

    @classmethod
    def _diff_runtimes(cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]) -> None:
        all_runtimes = set(base.runtimes.keys()) | set(current.runtimes.keys())
        for rt_name in sorted(all_runtimes):
            base_rt = base.runtimes.get(rt_name)
            curr_rt = current.runtimes.get(rt_name)

            if base_rt and base_rt.installed and (not curr_rt or not curr_rt.installed):
                out.append(
                    DiffItem(
                        category="runtime",
                        item_name=rt_name,
                        classification=DiffClassification.REMOVED,
                        severity=DiffSeverity.CRITICAL,
                        old_value=base_rt.version,
                        new_value=None,
                        description=f"Required runtime '{rt_name}' was removed or not found",
                    )
                )
            elif (not base_rt or not base_rt.installed) and curr_rt and curr_rt.installed:
                out.append(
                    DiffItem(
                        category="runtime",
                        item_name=rt_name,
                        classification=DiffClassification.ADDED,
                        severity=DiffSeverity.INFO,
                        old_value=None,
                        new_value=curr_rt.version,
                        description=f"Runtime '{rt_name}' ({curr_rt.version}) was added",
                    )
                )
            elif base_rt and curr_rt and base_rt.installed and curr_rt.installed:
                if base_rt.version != curr_rt.version:
                    # Check major vs minor/patch
                    sev = cls._evaluate_version_severity(base_rt.version, curr_rt.version)
                    out.append(
                        DiffItem(
                            category="runtime",
                            item_name=rt_name,
                            classification=DiffClassification.CHANGED,
                            severity=sev,
                            old_value=base_rt.version,
                            new_value=curr_rt.version,
                            description=f"Runtime '{rt_name}' version changed: {base_rt.version} -> {curr_rt.version}",
                        )
                    )

    @classmethod
    def _diff_dependencies(
        cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]
    ) -> None:
        base_deps = {f"{d.manager}:{d.name.lower()}": d for d in base.dependencies}
        curr_deps = {f"{d.manager}:{d.name.lower()}": d for d in current.dependencies}

        for key in sorted(set(base_deps.keys()) | set(curr_deps.keys())):
            b_dep = base_deps.get(key)
            c_dep = curr_deps.get(key)

            if b_dep and not c_dep:
                out.append(
                    DiffItem(
                        category="dependency",
                        item_name=b_dep.name,
                        classification=DiffClassification.REMOVED,
                        severity=DiffSeverity.WARNING,
                        old_value=b_dep.resolved or b_dep.declared,
                        new_value=None,
                        description=f"Dependency '{b_dep.name}' was removed",
                    )
                )
            elif not b_dep and c_dep:
                out.append(
                    DiffItem(
                        category="dependency",
                        item_name=c_dep.name,
                        classification=DiffClassification.ADDED,
                        severity=DiffSeverity.INFO,
                        old_value=None,
                        new_value=c_dep.resolved or c_dep.declared,
                        description=f"Dependency '{c_dep.name}' ({c_dep.resolved or c_dep.declared}) was added",
                    )
                )
            elif b_dep and c_dep:
                b_ver = b_dep.resolved or b_dep.declared
                c_ver = c_dep.resolved or c_dep.declared
                if b_ver != c_ver:
                    sev = cls._evaluate_version_severity(b_ver, c_ver)
                    out.append(
                        DiffItem(
                            category="dependency",
                            item_name=b_dep.name,
                            classification=DiffClassification.CHANGED,
                            severity=sev,
                            old_value=b_ver,
                            new_value=c_ver,
                            description=f"Dependency '{b_dep.name}' version changed: {b_ver} -> {c_ver}",
                        )
                    )

    @classmethod
    def _diff_services(cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]) -> None:
        base_svcs = {s.name.lower(): s for s in base.services}
        curr_svcs = {s.name.lower(): s for s in current.services}

        for s_name in sorted(set(base_svcs.keys()) | set(curr_svcs.keys())):
            b_svc = base_svcs.get(s_name)
            c_svc = curr_svcs.get(s_name)

            if b_svc and not c_svc:
                out.append(
                    DiffItem(
                        category="service",
                        item_name=s_name,
                        classification=DiffClassification.REMOVED,
                        severity=DiffSeverity.WARNING,
                        old_value="configured",
                        new_value="missing",
                        description=f"Service '{s_name}' was removed",
                    )
                )
            elif not b_svc and c_svc:
                out.append(
                    DiffItem(
                        category="service",
                        item_name=s_name,
                        classification=DiffClassification.ADDED,
                        severity=DiffSeverity.INFO,
                        old_value=None,
                        new_value="configured",
                        description=f"Service '{s_name}' was added",
                    )
                )
            elif b_svc and c_svc:
                if b_svc.running and not c_svc.running:
                    out.append(
                        DiffItem(
                            category="service",
                            item_name=s_name,
                            classification=DiffClassification.CHANGED,
                            severity=DiffSeverity.CRITICAL,
                            old_value="running",
                            new_value="stopped",
                            description=f"Service '{s_name}' is not running",
                        )
                    )
                elif not b_svc.running and c_svc.running:
                    out.append(
                        DiffItem(
                            category="service",
                            item_name=s_name,
                            classification=DiffClassification.CHANGED,
                            severity=DiffSeverity.INFO,
                            old_value="stopped",
                            new_value="running",
                            description=f"Service '{s_name}' was started",
                        )
                    )

                if (
                    b_svc.detected_version
                    and c_svc.detected_version
                    and b_svc.detected_version != c_svc.detected_version
                ):
                    sev = cls._evaluate_version_severity(
                        b_svc.detected_version, c_svc.detected_version
                    )
                    out.append(
                        DiffItem(
                            category="service",
                            item_name=f"{s_name}_version",
                            classification=DiffClassification.CHANGED,
                            severity=sev,
                            old_value=b_svc.detected_version,
                            new_value=c_svc.detected_version,
                            description=f"Service '{s_name}' version changed: {b_svc.detected_version} -> {c_svc.detected_version}",
                        )
                    )

    @classmethod
    def _diff_environment(
        cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]
    ) -> None:
        b_vars = base.environment.variables
        c_vars = current.environment.variables

        for var_name in sorted(set(b_vars.keys()) | set(c_vars.keys())):
            b_v = b_vars.get(var_name)
            c_v = c_vars.get(var_name)

            if b_v and not c_v:
                sev = DiffSeverity.CRITICAL if b_v.required else DiffSeverity.INFO
                out.append(
                    DiffItem(
                        category="environment",
                        item_name=var_name,
                        classification=DiffClassification.REMOVED,
                        severity=sev,
                        old_value="present" if b_v.present else "not_present",
                        new_value="missing",
                        description=f"Environment variable '{var_name}' requirement removed",
                    )
                )
            elif not b_v and c_v:
                sev = (
                    DiffSeverity.CRITICAL if c_v.required and not c_v.present else DiffSeverity.INFO
                )
                out.append(
                    DiffItem(
                        category="environment",
                        item_name=var_name,
                        classification=DiffClassification.ADDED,
                        severity=sev,
                        old_value=None,
                        new_value="present" if c_v.present else "missing",
                        description=f"Environment variable '{var_name}' declared ({'present' if c_v.present else 'missing'})",
                    )
                )
            elif b_v and c_v:
                if b_v.present and not c_v.present:
                    sev = (
                        DiffSeverity.CRITICAL
                        if c_v.required or b_v.required
                        else DiffSeverity.WARNING
                    )
                    out.append(
                        DiffItem(
                            category="environment",
                            item_name=var_name,
                            classification=DiffClassification.CHANGED,
                            severity=sev,
                            old_value="present",
                            new_value="missing",
                            description=f"Environment variable '{var_name}' is missing",
                        )
                    )
                elif not b_v.present and c_v.present:
                    out.append(
                        DiffItem(
                            category="environment",
                            item_name=var_name,
                            classification=DiffClassification.CHANGED,
                            severity=DiffSeverity.INFO,
                            old_value="missing",
                            new_value="present",
                            description=f"Environment variable '{var_name}' was set",
                        )
                    )

    @classmethod
    def _diff_network(cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]) -> None:
        b_ports = {p.port: p for p in base.network}
        c_ports = {p.port: p for p in current.network}

        for port_num in sorted(set(b_ports.keys()) | set(c_ports.keys())):
            b_p = b_ports.get(port_num)
            c_p = c_ports.get(port_num)

            if b_p and c_p:
                if b_p.occupied != c_p.occupied:
                    out.append(
                        DiffItem(
                            category="network",
                            item_name=f"port_{port_num}",
                            classification=DiffClassification.CHANGED,
                            severity=DiffSeverity.INFO,
                            old_value="in_use" if b_p.occupied else "available",
                            new_value="in_use" if c_p.occupied else "available",
                            description=f"Port {port_num} ({b_p.service}) occupancy changed: {'in_use' if b_p.occupied else 'available'} -> {'in_use' if c_p.occupied else 'available'}",
                        )
                    )

    @classmethod
    def _diff_containers(
        cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]
    ) -> None:
        b_cnts = {c.service_name: c for c in base.containers}
        c_cnts = {c.service_name: c for c in current.containers}

        for name in sorted(set(b_cnts.keys()) | set(c_cnts.keys())):
            b_c = b_cnts.get(name)
            c_c = c_cnts.get(name)

            if b_c and not c_c:
                out.append(
                    DiffItem(
                        category="container",
                        item_name=name,
                        classification=DiffClassification.REMOVED,
                        severity=DiffSeverity.WARNING,
                        old_value=b_c.image,
                        new_value=None,
                        description=f"Container service '{name}' removed",
                    )
                )
            elif not b_c and c_c:
                out.append(
                    DiffItem(
                        category="container",
                        item_name=name,
                        classification=DiffClassification.ADDED,
                        severity=DiffSeverity.INFO,
                        old_value=None,
                        new_value=c_c.image,
                        description=f"Container service '{name}' ({c_c.image}) added",
                    )
                )
            elif b_c and c_c:
                if b_c.image != c_c.image or b_c.tag != c_c.tag:
                    out.append(
                        DiffItem(
                            category="container",
                            item_name=name,
                            classification=DiffClassification.CHANGED,
                            severity=DiffSeverity.WARNING,
                            old_value=f"{b_c.image}:{b_c.tag or 'latest'}",
                            new_value=f"{c_c.image}:{c_c.tag or 'latest'}",
                            description=f"Container service '{name}' image changed: {b_c.image}:{b_c.tag} -> {c_c.image}:{c_c.tag}",
                        )
                    )

    @classmethod
    def _diff_git(cls, base: RunmarkState, current: RunmarkState, out: list[DiffItem]) -> None:
        if base.git.commit != current.git.commit:
            out.append(
                DiffItem(
                    category="git",
                    item_name="commit",
                    classification=DiffClassification.CHANGED,
                    severity=DiffSeverity.INFO,
                    old_value=base.git.commit,
                    new_value=current.git.commit,
                    description=f"Source commit changed: {base.git.commit} -> {current.git.commit}",
                    is_source_revision=True,
                )
            )
        if base.git.branch != current.git.branch:
            out.append(
                DiffItem(
                    category="git",
                    item_name="branch",
                    classification=DiffClassification.CHANGED,
                    severity=DiffSeverity.INFO,
                    old_value=base.git.branch,
                    new_value=current.git.branch,
                    description=f"Git branch changed: {base.git.branch} -> {current.git.branch}",
                    is_source_revision=True,
                )
            )
        if base.git.dirty != current.git.dirty:
            out.append(
                DiffItem(
                    category="git",
                    item_name="dirty",
                    classification=DiffClassification.CHANGED,
                    severity=DiffSeverity.INFO,
                    old_value=base.git.dirty,
                    new_value=current.git.dirty,
                    description=f"Working tree dirty state changed: {base.git.dirty} -> {current.git.dirty}",
                    is_source_revision=True,
                )
            )

    @classmethod
    def _evaluate_version_severity(cls, v1: str | None, v2: str | None) -> DiffSeverity:
        if not v1 or not v2:
            return DiffSeverity.INFO
        try:
            from packaging.version import parse

            parsed1 = parse(v1)
            parsed2 = parse(v2)
            if parsed1.major != parsed2.major:
                return DiffSeverity.CRITICAL
            if parsed1.minor != parsed2.minor:
                return DiffSeverity.WARNING
            return DiffSeverity.INFO
        except Exception:
            return DiffSeverity.WARNING
