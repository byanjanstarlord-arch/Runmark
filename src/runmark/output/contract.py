"""Terminal rendering functions for Runmark environment contracts, checks, init previews, and diffs."""

from typing import Any

from rich.panel import Panel
from rich.table import Table

from runmark.contracts.diff import ContractChangeKind, ContractDiffResult
from runmark.contracts.evidence import ProjectEvidence
from runmark.models.contract import RunmarkContract
from runmark.models.contract_result import (
    ContractCheckResult,
    ContractCheckStatus,
)
from runmark.models.diagnostic import DiagnosticSeverity
from runmark.output.terminal import term


def render_contract_check(result: ContractCheckResult, explain: bool = False) -> None:
    """Render the evaluation results of an environment contract check to terminal."""
    if result.status == ContractCheckStatus.PASS:
        status_text = "[bold green]✓ PASSED[/bold green]"
        panel_border = "green"
    elif result.status == ContractCheckStatus.FAIL:
        status_text = "[bold red]✗ FAILED[/bold red]"
        panel_border = "red"
    else:
        status_text = "[bold yellow]⚠ INCONCLUSIVE / UNKNOWN[/bold yellow]"
        panel_border = "yellow"

    header_content = (
        f"[bold]Project:[/bold] {result.project_name or 'unnamed'}  "
        f"[bold]Contract Version:[/bold] {result.contract_version}  "
        f"[bold]Overall Status:[/bold] {status_text}"
    )
    term.print(
        Panel(
            header_content,
            title="[bold]Runmark Environment Contract Check[/bold]",
            border_style=panel_border,
        )
    )

    # Checks Table
    table = Table(title="Requirement Evaluations", expand=True, show_lines=False)
    table.add_column("Status", width=10, justify="center")
    table.add_column("Category", style="cyan", width=14)
    table.add_column("Requirement", style="bold", width=26)
    table.add_column("Observed", width=22)
    table.add_column("Message")

    for check in result.checks:
        if check.status == ContractCheckStatus.PASS:
            status_str = "[bold green]✓ PASS[/bold green]"
        elif check.status == ContractCheckStatus.FAIL:
            status_str = "[bold red]✗ FAIL[/bold red]"
        elif check.status == ContractCheckStatus.UNKNOWN:
            status_str = "[bold yellow]⚠ UNKNOWN[/bold yellow]"
        else:
            status_str = "[dim]- SKIP[/dim]"

        table.add_row(
            status_str,
            check.category,
            check.title,
            check.observed or "-",
            check.message or "-",
        )

    term.print(table)

    # Explain Mode Breakdown
    if explain:
        non_passed = [
            c
            for c in result.checks
            if c.status in (ContractCheckStatus.FAIL, ContractCheckStatus.UNKNOWN)
        ]
        if non_passed:
            term.print("\n[bold]Detailed Diagnostic Explanations (--explain):[/bold]")
            for c in non_passed:
                status_icon = "🔴" if c.status == ContractCheckStatus.FAIL else "🟡"
                term.print(f"\n{status_icon} [bold]{c.title}[/bold] ({c.category})")
                term.print(f"   [cyan]Required:[/cyan]         {c.expected or '-'}")
                term.print(f"   [yellow]Detected:[/yellow]         {c.observed or '-'}")

                if c.diagnostic_issue:
                    term.print(f"   [dim]Why:[/dim]              {c.diagnostic_issue.explanation}")
                    term.print(
                        f"   [green]Suggested Action:[/green] {c.diagnostic_issue.suggested_action}"
                    )
                else:
                    term.print(f"   [dim]Why:[/dim]              {c.message}")
                    term.print(
                        f"   [green]Suggested Action:[/green] Inspect and satisfy the '{c.title}' requirement."
                    )

    # Diagnostics if there are issues and not already in explain mode
    elif result.issues:
        term.print("\n[bold]Diagnostic Recommendations:[/bold]")
        for issue in result.issues:
            if issue.severity == DiagnosticSeverity.CRITICAL:
                icon = "[bold red]🔴 CRITICAL[/bold red]"
            elif issue.severity == DiagnosticSeverity.WARNING:
                icon = "[bold yellow]🟡 WARNING[/bold yellow]"
            else:
                icon = "[bold blue]🔵 INFO[/bold blue]"

            term.print(f"\n{icon} [bold][{issue.code}][/bold] {issue.title}")
            term.print(f"   [dim]Explanation:[/dim] {issue.explanation}")
            term.print(f"   [cyan]Suggested Action:[/cyan] {issue.suggested_action}")

    # Summary count
    s = result.summary
    term.print(
        f"\n[dim]Summary: {s.total} checks ({s.passed} passed, {s.failed} failed, "
        f"{s.unknown} unknown, {s.skipped} skipped)[/dim]"
    )


def render_contract_preview(contract: RunmarkContract, evidence: ProjectEvidence) -> None:
    """Render a human-readable preview of detected signals and candidate contract before creation."""
    term.print(
        Panel(
            "[bold]Runmark Contract Generator[/bold]\n"
            "Synthesizing declarative environment requirements from discovered project manifests.",
            title="[bold green]Environment Contract Bootstrap[/bold green]",
            border_style="green",
        )
    )

    # Discovered Signals
    if evidence.signals:
        term.print("[bold cyan]Discovered Project Signals:[/bold cyan]")
        for sig in evidence.signals:
            details_str = (
                f" [dim]({', '.join(f'{k}={v}' for k, v in sig.details.items())})[/dim]"
                if sig.details
                else ""
            )
            term.print(
                f"  [green]✓[/green] [{sig.level.value.upper()}] [bold]{sig.name}[/bold] via [cyan]{sig.source}[/cyan]{details_str}"
            )
        term.print("")

    # Proposed Contract Summary
    term.print("[bold]Proposed Environment Contract Requirements:[/bold]")

    if contract.runtime:
        term.print("  [bold cyan]Runtimes:[/bold cyan]")
        for rt, ver in contract.runtime.items():
            term.print(f"    • {rt}: [green]{ver}[/green]")

    if contract.services:
        term.print("  [bold cyan]Backing Services:[/bold cyan]")
        for svc_name, s_req in contract.services.items():
            req_flag = "required" if s_req.required else "optional"
            term.print(f"    • {svc_name}: [green]{s_req.version}[/green] ({req_flag})")

    if contract.environment.required or contract.environment.optional:
        term.print("  [bold cyan]Environment Variables:[/bold cyan]")
        for ev in contract.environment.required:
            term.print(f"    • {ev} [green](required)[/green]")
        for ev in contract.environment.optional:
            term.print(f"    • {ev} [dim](optional)[/dim]")

    if contract.network.ports:
        term.print("  [bold cyan]Network Ports:[/bold cyan]")
        for p_num, p_req in contract.network.ports.items():
            term.print(f"    • {p_num}/{p_req.protocol} [dim](required={p_req.required})[/dim]")

    if contract.containers.docker or contract.containers.compose:
        term.print("  [bold cyan]Containers:[/bold cyan]")
        if contract.containers.docker and contract.containers.docker.required:
            term.print("    • Docker Engine [green](required)[/green]")
        if contract.containers.compose and contract.containers.compose.required:
            term.print("    • Docker Compose [green](required)[/green]")

    if contract.dependencies.python or contract.dependencies.node:
        total_deps = len(contract.dependencies.python) + len(contract.dependencies.node)
        term.print(
            f"  [bold cyan]Dependencies:[/bold cyan] {total_deps} package constraints pinned"
        )
    term.print("")


def render_contract_diff(diff_result: ContractDiffResult) -> None:
    """Render semantic diff between two contract specifications."""
    if not diff_result.has_changes:
        term.print(
            Panel(
                "[bold green]No differences detected.[/bold green] The environment contract matches the baseline specification.",
                title="[bold]Runmark Contract Diff[/bold]",
                border_style="green",
            )
        )
        return

    term.print(
        Panel(
            f"[bold]Status:[/bold] [yellow]{diff_result.status}[/yellow]  "
            f"[bold]Summary:[/bold] {diff_result.summary.changed} changed, "
            f"{diff_result.summary.added} added, {diff_result.summary.removed} removed",
            title="[bold]Runmark Contract Diff[/bold]",
            border_style="yellow",
        )
    )

    table = Table(title="Contract Requirement Changes", expand=True)
    table.add_column("Category", style="cyan", width=18)
    table.add_column("Requirement", style="bold", width=24)
    table.add_column("Change", justify="center", width=12)
    table.add_column("Baseline (Before)", width=24)
    table.add_column("Current (After)")

    for ch in diff_result.changes:
        if ch.change == ContractChangeKind.ADDED:
            change_badge = "[bold green]+ ADDED[/bold green]"
            before_str = "[dim]-[/dim]"
            after_str = f"[green]{ch.after}[/green]"
        elif ch.change == ContractChangeKind.REMOVED:
            change_badge = "[bold red]- REMOVED[/bold red]"
            before_str = f"[red]{ch.before}[/red]"
            after_str = "[dim]-[/dim]"
        elif ch.change == ContractChangeKind.CHANGED:
            change_badge = "[bold yellow]~ CHANGED[/bold yellow]"
            before_str = f"[red]{ch.before}[/red]"
            after_str = f"[green]{ch.after}[/green]"
        else:
            change_badge = "[dim]= SAME[/dim]"
            before_str = str(ch.before or "-")
            after_str = str(ch.after or "-")

        table.add_row(
            ch.category,
            ch.name,
            change_badge,
            before_str,
            after_str,
        )

    term.print(table)


def render_contract_show(
    contract: RunmarkContract, canonical: dict[str, Any], fingerprint: str
) -> None:
    """Render a human-readable normalized specification of an environment contract."""
    header = (
        f"[bold]Project:[/bold] {contract.project.name or '(unnamed)'}\n"
        f"[bold]Contract Version:[/bold] {contract.version}\n"
        f"[bold]Contract Fingerprint:[/bold] [cyan]{fingerprint}[/cyan]"
    )
    term.print(
        Panel(
            header,
            title="[bold]Runmark Environment Contract Specification[/bold]",
            border_style="cyan",
        )
    )

    # Platform Table
    if contract.platform.os or contract.platform.architecture:
        table_plat = Table(title="Platform Compatibility", expand=True)
        table_plat.add_column("Property", style="bold cyan", width=20)
        table_plat.add_column("Requirement")
        if contract.platform.os:
            table_plat.add_row("Operating System", ", ".join(contract.platform.os))
        if contract.platform.architecture:
            table_plat.add_row("Architecture", ", ".join(contract.platform.architecture))
        term.print(table_plat)

    # Runtimes Table
    if contract.runtime:
        table_rt = Table(title="Runtime Requirements", expand=True)
        table_rt.add_column("Runtime", style="bold cyan", width=20)
        table_rt.add_column("Version Constraint")
        for rt_name, expr in sorted(contract.runtime.items()):
            table_rt.add_row(rt_name.capitalize(), expr)
        term.print(table_rt)

    # Services Table
    if contract.services:
        table_svc = Table(title="Backing Services", expand=True)
        table_svc.add_column("Service", style="bold cyan", width=20)
        table_svc.add_column("Requirement Type", width=18)
        table_svc.add_column("Version Constraint")
        for svc_name, req in sorted(contract.services.items()):
            req_type = "[green]Required[/green]" if req.required else "[dim]Optional[/dim]"
            table_svc.add_row(svc_name.capitalize(), req_type, req.version)
        term.print(table_svc)

    # Environment Variables Table
    if contract.environment.required or contract.environment.optional:
        table_env = Table(title="Environment Variables (Presence Only)", expand=True)
        table_env.add_column("Variable Name", style="bold cyan", width=30)
        table_env.add_column("Requirement")
        for v in sorted(contract.environment.required):
            table_env.add_row(v, "[green]Required[/green]")
        for v in sorted(contract.environment.optional):
            table_env.add_row(v, "[dim]Optional[/dim]")
        term.print(table_env)

    # Network Ports Table
    if contract.network.ports:
        table_net = Table(title="Network Ports", expand=True)
        table_net.add_column("Port", style="bold cyan", width=15)
        table_net.add_column("Protocol", width=15)
        table_net.add_column("Requirement")
        for p_key in sorted(
            contract.network.ports.keys(), key=lambda p: int(p) if p.isdigit() else p
        ):
            p_req = contract.network.ports[p_key]
            req_type = "[green]Required[/green]" if p_req.required else "[dim]Optional[/dim]"
            table_net.add_row(p_key, p_req.protocol.upper(), req_type)
        term.print(table_net)

    # Containers Table
    if contract.containers.docker or contract.containers.compose:
        table_cnt = Table(title="Container Engine", expand=True)
        table_cnt.add_column("Component", style="bold cyan", width=20)
        table_cnt.add_column("Requirement")
        if contract.containers.docker:
            req_type = (
                "[green]Required[/green]"
                if contract.containers.docker.required
                else "[dim]Optional[/dim]"
            )
            table_cnt.add_row("Docker Engine", req_type)
        if contract.containers.compose:
            req_type = (
                "[green]Required[/green]"
                if contract.containers.compose.required
                else "[dim]Optional[/dim]"
            )
            table_cnt.add_row("Docker Compose", req_type)
        term.print(table_cnt)
