"""Contract evaluation engine that verifies observed environment state against contract requirements."""

from runmark.contracts.version_constraints import VersionConstraint
from runmark.models.contract import RunmarkContract
from runmark.models.contract_result import (
    ContractCheck,
    ContractCheckResult,
    ContractCheckStatus,
    ContractCheckSummary,
)
from runmark.models.diagnostic import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticSeverity,
)
from runmark.models.runmark import RunmarkState


class ContractEvaluator:
    """Evaluates a RunmarkContract against a live or snapshot RunmarkState."""

    @classmethod
    def evaluate(cls, contract: RunmarkContract, state: RunmarkState) -> ContractCheckResult:
        """Run all contract component checks against the observed state."""
        checks: list[ContractCheck] = []
        issues: list[DiagnosticIssue] = []

        # 1. Platform Evaluation
        cls._evaluate_platform(contract, state, checks, issues)

        # 2. Runtime Evaluation
        cls._evaluate_runtimes(contract, state, checks, issues)

        # 3. Services Evaluation
        cls._evaluate_services(contract, state, checks, issues)

        # 4. Environment Variables Evaluation
        cls._evaluate_environment(contract, state, checks, issues)

        # 5. Network / Port Evaluation
        cls._evaluate_network(contract, state, checks, issues)

        # 6. Container Evaluation
        cls._evaluate_containers(contract, state, checks, issues)

        # 7. Dependencies Evaluation
        cls._evaluate_dependencies(contract, state, checks, issues)

        # Compute summary counts
        passed_count = sum(1 for c in checks if c.status == ContractCheckStatus.PASS)
        failed_count = sum(1 for c in checks if c.status == ContractCheckStatus.FAIL)
        unknown_count = sum(1 for c in checks if c.status == ContractCheckStatus.UNKNOWN)
        skipped_count = sum(1 for c in checks if c.status == ContractCheckStatus.SKIPPED)

        # Aggregate overall status: FAIL > UNKNOWN > PASS
        if failed_count > 0:
            overall_status = ContractCheckStatus.FAIL
        elif unknown_count > 0:
            overall_status = ContractCheckStatus.UNKNOWN
        else:
            overall_status = ContractCheckStatus.PASS

        project_name = contract.project.name or state.project.name

        return ContractCheckResult(
            status=overall_status,
            contract_version=contract.version,
            project_name=project_name,
            checks=checks,
            issues=issues,
            summary=ContractCheckSummary(
                total=len(checks),
                passed=passed_count,
                failed=failed_count,
                unknown=unknown_count,
                skipped=skipped_count,
            ),
        )

    @classmethod
    def _evaluate_platform(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate operating system and hardware architecture requirements."""
        # OS check
        if contract.platform.os:
            expected_os = [o.lower().strip() for o in contract.platform.os]
            observed_os = state.system.os_name.lower().strip()
            # Normalize darwin / macos
            norm_observed = (
                "darwin"
                if observed_os == "macos"
                else ("macos" if observed_os == "darwin" else observed_os)
            )

            if observed_os in expected_os or norm_observed in expected_os:
                checks.append(
                    ContractCheck(
                        id="platform.os",
                        category="platform",
                        title="Operating System",
                        status=ContractCheckStatus.PASS,
                        expected=", ".join(contract.platform.os),
                        observed=state.system.os_name,
                        message=f"Host OS '{state.system.os_name}' matches contract ({', '.join(contract.platform.os)})",
                    )
                )
            else:
                issue = DiagnosticIssue(
                    code="PLATFORM_OS_MISMATCH",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.SYSTEM,
                    title="Platform OS mismatch",
                    evidence={
                        "expected_os": contract.platform.os,
                        "observed_os": state.system.os_name,
                    },
                    explanation=f"Project contract requires OS in {contract.platform.os}, but host is running '{state.system.os_name}'.",
                    suggested_action=f"Run this project on a supported operating system: {', '.join(contract.platform.os)}.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id="platform.os",
                        category="platform",
                        title="Operating System",
                        status=ContractCheckStatus.FAIL,
                        expected=", ".join(contract.platform.os),
                        observed=state.system.os_name,
                        message=f"Host OS '{state.system.os_name}' is not supported by contract ({', '.join(contract.platform.os)})",
                        diagnostic_issue=issue,
                    )
                )

        # Architecture check
        if contract.platform.architecture:
            expected_arch = [a.lower().strip() for a in contract.platform.architecture]
            observed_arch = state.system.architecture.lower().strip()
            # Normalize x86_64 / amd64, aarch64 / arm64
            arch_aliases = {
                "x86_64": {"amd64", "x86_64"},
                "amd64": {"amd64", "x86_64"},
                "arm64": {"arm64", "aarch64"},
                "aarch64": {"arm64", "aarch64"},
            }
            allowed_set = set(expected_arch)
            for a in list(allowed_set):
                if a in arch_aliases:
                    allowed_set.update(arch_aliases[a])

            if observed_arch in allowed_set:
                checks.append(
                    ContractCheck(
                        id="platform.architecture",
                        category="platform",
                        title="Hardware Architecture",
                        status=ContractCheckStatus.PASS,
                        expected=", ".join(contract.platform.architecture),
                        observed=state.system.architecture,
                        message=f"Host architecture '{state.system.architecture}' matches contract ({', '.join(contract.platform.architecture)})",
                    )
                )
            else:
                issue = DiagnosticIssue(
                    code="PLATFORM_ARCH_MISMATCH",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.SYSTEM,
                    title="Platform architecture mismatch",
                    evidence={
                        "expected_architecture": contract.platform.architecture,
                        "observed_architecture": state.system.architecture,
                    },
                    explanation=f"Project contract requires architecture in {contract.platform.architecture}, but host is '{state.system.architecture}'.",
                    suggested_action=f"Run this project on a supported architecture: {', '.join(contract.platform.architecture)}.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id="platform.architecture",
                        category="platform",
                        title="Hardware Architecture",
                        status=ContractCheckStatus.FAIL,
                        expected=", ".join(contract.platform.architecture),
                        observed=state.system.architecture,
                        message=f"Host architecture '{state.system.architecture}' is not supported by contract",
                        diagnostic_issue=issue,
                    )
                )

    @classmethod
    def _evaluate_runtimes(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate programming language and runtime constraints."""
        for rt_name, constraint_expr in sorted(contract.runtime.items()):
            check_id = f"runtime.{rt_name.lower()}"
            title = f"{rt_name.capitalize()} Runtime"
            constraint = VersionConstraint.parse(constraint_expr)

            # Look up runtime in state
            rt_state = state.runtimes.get(rt_name.lower())

            if not rt_state or not rt_state.installed:
                issue = DiagnosticIssue(
                    code="RUNTIME_NOT_FOUND",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.RUNTIME,
                    title=f"{rt_name.capitalize()} runtime not found",
                    evidence={
                        "runtime": rt_name,
                        "expected": constraint_expr,
                        "status": "not_installed",
                    },
                    explanation=f"Project requires {rt_name} ({constraint_expr}), but {rt_name} is not installed or not found in PATH.",
                    suggested_action=f"Install {rt_name} version satisfying '{constraint_expr}'.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="runtime",
                        title=title,
                        status=ContractCheckStatus.FAIL,
                        expected=constraint_expr,
                        observed="not installed",
                        message=f"{rt_name.capitalize()} is not installed",
                        diagnostic_issue=issue,
                    )
                )
            elif not rt_state.version:
                # Installed but version could not be determined
                issue = DiagnosticIssue(
                    code="RUNTIME_VERSION_UNKNOWN",
                    severity=DiagnosticSeverity.WARNING,
                    category=DiagnosticCategory.RUNTIME,
                    title=f"{rt_name.capitalize()} version unknown",
                    evidence={
                        "runtime": rt_name,
                        "expected": constraint_expr,
                        "version": "unknown",
                    },
                    explanation=f"{rt_name.capitalize()} is installed, but its version could not be safely detected.",
                    suggested_action=f"Verify {rt_name} executable and version output manually.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="runtime",
                        title=title,
                        status=ContractCheckStatus.UNKNOWN,
                        expected=constraint_expr,
                        observed="unknown",
                        message=f"{rt_name.capitalize()} is installed but detected version is unknown",
                        diagnostic_issue=issue,
                    )
                )
            else:
                # Compare detected version against constraint
                if constraint.matches(rt_state.version):
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="runtime",
                            title=title,
                            status=ContractCheckStatus.PASS,
                            expected=constraint_expr,
                            observed=rt_state.version,
                            message=f"{rt_name.capitalize()} {rt_state.version} satisfies {constraint_expr}",
                        )
                    )
                else:
                    issue = DiagnosticIssue(
                        code="RUNTIME_VERSION_MISMATCH",
                        severity=DiagnosticSeverity.CRITICAL,
                        category=DiagnosticCategory.RUNTIME,
                        title=f"{rt_name.capitalize()} version mismatch",
                        evidence={
                            "runtime": rt_name,
                            "expected": constraint_expr,
                            "observed": rt_state.version,
                        },
                        explanation=f"Detected {rt_name} version '{rt_state.version}' does not satisfy contract requirement '{constraint_expr}'.",
                        suggested_action=f"Install or activate {rt_name} satisfying '{constraint_expr}'.",
                    )
                    issues.append(issue)
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="runtime",
                            title=title,
                            status=ContractCheckStatus.FAIL,
                            expected=constraint_expr,
                            observed=rt_state.version,
                            message=f"{rt_name.capitalize()} {rt_state.version} does not satisfy {constraint_expr}",
                            diagnostic_issue=issue,
                        )
                    )

    @classmethod
    def _evaluate_services(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate backing service requirements (e.g. postgresql, redis)."""
        # Map observed services by lowercase name
        observed_services = {s.name.lower(): s for s in state.services}

        for svc_name, svc_req in sorted(contract.services.items()):
            check_id = f"service.{svc_name.lower()}"
            title = f"{svc_name.capitalize()} Service"
            constraint = VersionConstraint.parse(svc_req.version)

            svc_state = observed_services.get(svc_name.lower())

            if not svc_state or not svc_state.running:
                if svc_req.required:
                    issue = DiagnosticIssue(
                        code="SERVICE_NOT_AVAILABLE",
                        severity=DiagnosticSeverity.CRITICAL,
                        category=DiagnosticCategory.SERVICE,
                        title=f"{svc_name.capitalize()} service not running",
                        evidence={
                            "service": svc_name,
                            "expected_version": svc_req.version,
                            "running": False,
                        },
                        explanation=f"Required service '{svc_name}' ({svc_req.version}) is not running on this machine.",
                        suggested_action=f"Start local {svc_name} service or container.",
                    )
                    issues.append(issue)
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="service",
                            title=title,
                            status=ContractCheckStatus.FAIL,
                            expected=f"{svc_req.version} (required)",
                            observed="stopped",
                            message=f"Required service '{svc_name}' is not running",
                            diagnostic_issue=issue,
                        )
                    )
                else:
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="service",
                            title=title,
                            status=ContractCheckStatus.SKIPPED,
                            expected=f"{svc_req.version} (optional)",
                            observed="stopped",
                            message=f"Optional service '{svc_name}' is not running (skipped)",
                        )
                    )
            else:
                # Service is running -> check version if detected
                if svc_state.detected_version:
                    if constraint.matches(svc_state.detected_version):
                        checks.append(
                            ContractCheck(
                                id=check_id,
                                category="service",
                                title=title,
                                status=ContractCheckStatus.PASS,
                                expected=svc_req.version,
                                observed=svc_state.detected_version,
                                message=f"{svc_name.capitalize()} {svc_state.detected_version} satisfies {svc_req.version}",
                            )
                        )
                    else:
                        issue = DiagnosticIssue(
                            code="SERVICE_VERSION_MISMATCH",
                            severity=DiagnosticSeverity.CRITICAL,
                            category=DiagnosticCategory.SERVICE,
                            title=f"{svc_name.capitalize()} version mismatch",
                            evidence={
                                "service": svc_name,
                                "expected_version": svc_req.version,
                                "observed_version": svc_state.detected_version,
                            },
                            explanation=f"Running {svc_name} version '{svc_state.detected_version}' does not satisfy requirement '{svc_req.version}'.",
                            suggested_action=f"Use {svc_name} version satisfying '{svc_req.version}'.",
                        )
                        issues.append(issue)
                        checks.append(
                            ContractCheck(
                                id=check_id,
                                category="service",
                                title=title,
                                status=ContractCheckStatus.FAIL,
                                expected=svc_req.version,
                                observed=svc_state.detected_version,
                                message=f"{svc_name.capitalize()} {svc_state.detected_version} does not satisfy {svc_req.version}",
                                diagnostic_issue=issue,
                            )
                        )
                else:
                    # Running but version not determinable
                    if svc_req.version in ("*", "any"):
                        checks.append(
                            ContractCheck(
                                id=check_id,
                                category="service",
                                title=title,
                                status=ContractCheckStatus.PASS,
                                expected=svc_req.version,
                                observed="running (version unknown)",
                                message=f"{svc_name.capitalize()} is running",
                            )
                        )
                    else:
                        checks.append(
                            ContractCheck(
                                id=check_id,
                                category="service",
                                title=title,
                                status=ContractCheckStatus.UNKNOWN,
                                expected=svc_req.version,
                                observed="running (version unknown)",
                                message=f"{svc_name.capitalize()} is running but version is unknown",
                            )
                        )

    @classmethod
    def _evaluate_environment(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate environment variable presence requirements (metadata only, zero secret leakage)."""
        observed_vars = state.environment.variables

        # 1. Required variables
        for var_name in sorted(contract.environment.required):
            check_id = f"environment.{var_name}"
            title = f"Env Var: {var_name}"
            var_state = observed_vars.get(var_name)

            if var_state and var_state.present:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="environment",
                        title=title,
                        status=ContractCheckStatus.PASS,
                        expected="present",
                        observed="present",
                        message=f"Required variable '{var_name}' is set",
                    )
                )
            else:
                issue = DiagnosticIssue(
                    code="REQUIRED_ENV_MISSING",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.ENVIRONMENT,
                    title=f"Missing required environment variable '{var_name}'",
                    evidence={
                        "variable": var_name,
                        "required": True,
                        "present": False,
                    },
                    explanation=f"Project contract requires '{var_name}', but it is not defined in active environment or .env.",
                    suggested_action=f"Define '{var_name}' in your local .env file or shell environment.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="environment",
                        title=title,
                        status=ContractCheckStatus.FAIL,
                        expected="present",
                        observed="missing",
                        message=f"Required variable '{var_name}' is missing",
                        diagnostic_issue=issue,
                    )
                )

        # 2. Optional variables
        for var_name in sorted(contract.environment.optional):
            check_id = f"environment.{var_name}"
            title = f"Env Var: {var_name} (optional)"
            var_state = observed_vars.get(var_name)

            if var_state and var_state.present:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="environment",
                        title=title,
                        status=ContractCheckStatus.PASS,
                        expected="optional",
                        observed="present",
                        message=f"Optional variable '{var_name}' is set",
                    )
                )
            else:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="environment",
                        title=title,
                        status=ContractCheckStatus.SKIPPED,
                        expected="optional",
                        observed="not set",
                        message=f"Optional variable '{var_name}' is not set (skipped)",
                    )
                )

    @classmethod
    def _evaluate_network(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate network port requirements."""
        observed_ports = {p.port: p for p in state.network}

        for port_str in sorted(contract.network.ports.keys(), key=lambda p: int(p)):
            port_req = contract.network.ports[port_str]
            port_num = int(port_str)
            check_id = f"network.{port_num}.{port_req.protocol}"
            title = f"Port {port_num}/{port_req.protocol}"

            p_state = observed_ports.get(port_num)
            # Port check passes if monitored
            checks.append(
                ContractCheck(
                    id=check_id,
                    category="network",
                    title=title,
                    status=ContractCheckStatus.PASS,
                    expected=f"{port_num}/{port_req.protocol}",
                    observed=p_state.status if p_state else "available",
                    message=f"Port {port_num} check registered",
                )
            )

    @classmethod
    def _evaluate_containers(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate container runtime requirements (Docker, Compose)."""
        docker_rt = state.runtimes.get("docker")

        if contract.containers.docker is not None and contract.containers.docker.required:
            check_id = "container.docker"
            title = "Docker Engine"
            if docker_rt and docker_rt.installed:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="container",
                        title=title,
                        status=ContractCheckStatus.PASS,
                        expected="available",
                        observed=f"installed ({docker_rt.version or 'version unknown'})",
                        message="Docker is available",
                    )
                )
            else:
                issue = DiagnosticIssue(
                    code="CONTAINER_RUNTIME_UNAVAILABLE",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.CONTAINER,
                    title="Docker runtime not available",
                    evidence={"runtime": "docker", "required": True, "status": "missing"},
                    explanation="Docker is required by the environment contract, but the Docker CLI/engine is not available.",
                    suggested_action="Install and start Docker Engine or Docker Desktop.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="container",
                        title=title,
                        status=ContractCheckStatus.FAIL,
                        expected="available",
                        observed="not installed",
                        message="Docker is not available",
                        diagnostic_issue=issue,
                    )
                )

        if contract.containers.compose is not None and contract.containers.compose.required:
            check_id = "container.compose"
            title = "Docker Compose"
            if "compose" in state.project.containerization or (docker_rt and docker_rt.installed):
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="container",
                        title=title,
                        status=ContractCheckStatus.PASS,
                        expected="available",
                        observed="available",
                        message="Docker Compose is available",
                    )
                )
            else:
                issue = DiagnosticIssue(
                    code="CONTAINER_COMPOSE_UNAVAILABLE",
                    severity=DiagnosticSeverity.CRITICAL,
                    category=DiagnosticCategory.CONTAINER,
                    title="Docker Compose not available",
                    evidence={"runtime": "compose", "required": True, "status": "missing"},
                    explanation="Docker Compose is required by the contract but is not detected.",
                    suggested_action="Ensure Docker Compose plugin or binary is installed.",
                )
                issues.append(issue)
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="container",
                        title=title,
                        status=ContractCheckStatus.FAIL,
                        expected="available",
                        observed="not available",
                        message="Docker Compose is not available",
                        diagnostic_issue=issue,
                    )
                )

    @classmethod
    def _evaluate_dependencies(
        cls,
        contract: RunmarkContract,
        state: RunmarkState,
        checks: list[ContractCheck],
        issues: list[DiagnosticIssue],
    ) -> None:
        """Evaluate locked/declared package dependency constraints against observed scanner state."""
        observed_deps = {d.name.lower(): d for d in state.dependencies}

        for pkg_name, constraint_expr in sorted(contract.dependencies.python.items()):
            check_id = f"dependency.python.{pkg_name.lower()}"
            title = f"Python Dependency: {pkg_name}"
            constraint = VersionConstraint.parse(constraint_expr)

            d_state = observed_deps.get(pkg_name.lower())
            if not d_state:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="dependency",
                        title=title,
                        status=ContractCheckStatus.UNKNOWN,
                        expected=constraint_expr,
                        observed="not locked",
                        message=f"Dependency '{pkg_name}' was not detected in lockfiles",
                    )
                )
            elif d_state.resolved:
                if constraint.matches(d_state.resolved):
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="dependency",
                            title=title,
                            status=ContractCheckStatus.PASS,
                            expected=constraint_expr,
                            observed=d_state.resolved,
                            message=f"{pkg_name} {d_state.resolved} satisfies {constraint_expr}",
                        )
                    )
                else:
                    issue = DiagnosticIssue(
                        code="DEPENDENCY_VERSION_MISMATCH",
                        severity=DiagnosticSeverity.WARNING,
                        category=DiagnosticCategory.DEPENDENCY,
                        title=f"Dependency {pkg_name} version mismatch",
                        evidence={
                            "package": pkg_name,
                            "expected": constraint_expr,
                            "observed": d_state.resolved,
                        },
                        explanation=f"Locked version '{d_state.resolved}' does not satisfy contract requirement '{constraint_expr}'.",
                        suggested_action=f"Update '{pkg_name}' to satisfy '{constraint_expr}'.",
                    )
                    issues.append(issue)
                    checks.append(
                        ContractCheck(
                            id=check_id,
                            category="dependency",
                            title=title,
                            status=ContractCheckStatus.FAIL,
                            expected=constraint_expr,
                            observed=d_state.resolved,
                            message=f"{pkg_name} {d_state.resolved} does not satisfy {constraint_expr}",
                            diagnostic_issue=issue,
                        )
                    )
            else:
                checks.append(
                    ContractCheck(
                        id=check_id,
                        category="dependency",
                        title=title,
                        status=ContractCheckStatus.PASS,
                        expected=constraint_expr,
                        observed="declared",
                        message=f"{pkg_name} is declared",
                    )
                )
