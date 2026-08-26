"""Rich tables and formatting for Runmark commands."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runmark.core.diff import DiffClassification, DiffSeverity, RunmarkDiff
from runmark.core.doctor import DoctorReport
from runmark.core.verifier import VerificationResult, VerificationStatus
from runmark.models.common import DetectionStatus
from runmark.models.runmark import RunmarkState


def render_scan(state: RunmarkState, console: Console) -> None:
    """Render comprehensive scan state."""
    console.print()
    console.print(
        Panel(
            f"[bold cyan]RUNMARK ENVIRONMENT SCAN[/bold cyan]\n"
            f"[dim]Project:[/dim] [bold]{state.project.name}[/bold]   "
            f"[dim]Fingerprint:[/dim] [green]{state.runmark.environment_fingerprint[:16]}...[/green]",
            border_style="cyan",
        )
    )

    # 1. Project & System
    p_table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
    p_table.add_column("Category", style="dim")
    p_table.add_column("Details")

    langs = ", ".join(state.project.languages) if state.project.languages else "none detected"
    fworks = ", ".join(state.project.frameworks) if state.project.frameworks else "none detected"
    pkgs = (
        ", ".join(state.project.package_managers)
        if state.project.package_managers
        else "none detected"
    )
    cnts = ", ".join(state.project.containerization) if state.project.containerization else "none"

    p_table.add_row("Languages", langs)
    p_table.add_row("Frameworks", fworks)
    p_table.add_row("Package Managers", pkgs)
    p_table.add_row("Containers", cnts)
    p_table.add_row(
        "System", f"{state.system.os_name} {state.system.os_version} ({state.system.architecture})"
    )

    console.print("[bold]Project & Host[/bold]")
    console.print(p_table)
    console.print()

    # 2. Runtimes
    rt_table = Table(show_header=True, header_style="bold blue", box=None, padding=(0, 2))
    rt_table.add_column("Runtime", style="bold")
    rt_table.add_column("Status")
    rt_table.add_column("Version")

    for name, rt in sorted(state.runtimes.items()):
        if rt.installed:
            status_text = Text("✓ detected", style="bold green")
            ver_text = rt.version or "installed"
        elif rt.status == DetectionStatus.ERROR:
            status_text = Text("✗ error", style="bold red")
            ver_text = "-"
        else:
            status_text = Text("✗ not found", style="dim")
            ver_text = "-"
        rt_table.add_row(name.capitalize(), status_text, ver_text)

    console.print("[bold]Runtimes[/bold]")
    console.print(rt_table)
    console.print()

    # 3. Services
    if state.services:
        svc_table = Table(show_header=True, header_style="bold yellow", box=None, padding=(0, 2))
        svc_table.add_column("Service", style="bold")
        svc_table.add_column("Status")
        svc_table.add_column("Port")
        svc_table.add_column("Detected Ver")
        svc_table.add_column("Expected Ver")

        for s in state.services:
            if s.running:
                status_text = Text("✓ running", style="bold green")
            elif s.installed:
                status_text = Text("⚠ stopped (installed)", style="yellow")
            else:
                status_text = Text("✗ not found", style="dim")

            svc_table.add_row(
                s.name.capitalize(),
                status_text,
                str(s.port or "-"),
                s.detected_version or "-",
                s.expected_version or "-",
            )

        console.print("[bold]Services[/bold]")
        console.print(svc_table)
        console.print()

    # 4. Environment Variables
    env_table = Table(show_header=True, header_style="bold green", box=None, padding=(0, 2))
    env_table.add_column("Variable", style="bold")
    env_table.add_column("Required")
    env_table.add_column("Status")
    env_table.add_column("Secret")
    env_table.add_column("Source", style="dim")

    for var_name, v in sorted(state.environment.variables.items()):
        req_text = "yes" if v.required else "no"
        sec_text = "[yellow]yes (redacted)[/yellow]" if v.secret else "no"
        if v.present:
            status_text = Text("✓ present", style="green")
        elif v.required:
            status_text = Text("✗ missing (required)", style="bold red")
        else:
            status_text = Text("not set", style="dim")

        env_table.add_row(var_name, req_text, status_text, sec_text, v.source)

    console.print("[bold]Environment Variables[/bold]")
    console.print(env_table)
    console.print()

    # 5. Git State
    console.print("[bold]Git Source Control[/bold]")
    if state.git.is_repository:
        dirty_str = (
            "[bold yellow]dirty (uncommitted changes)[/bold yellow]"
            if state.git.dirty
            else "[green]clean[/green]"
        )
        console.print(f"  Branch: [bold]{state.git.branch or 'HEAD'}[/bold]")
        console.print(f"  Commit: [cyan]{(state.git.commit or '')[:8]}[/cyan]")
        console.print(f"  Tree:   {dirty_str}")
    else:
        console.print("  [dim]Not a Git repository[/dim]")
    console.print()


def render_diff(diff: RunmarkDiff, console: Console) -> None:
    """Render semantic diff comparison table."""
    console.print()
    if diff.is_identical:
        console.print(
            Panel(
                "[bold green]✓ ZERO ENVIRONMENT DRIFT DETECTED[/bold green]\n"
                f"Fingerprint: [cyan]{diff.to_fingerprint[:16]}...[/cyan] matches baseline.",
                border_style="green",
            )
        )
        return

    console.print(
        Panel(
            f"[bold yellow]ENVIRONMENT DRIFT DETECTED[/bold yellow]\n"
            f"[dim]From Baseline:[/dim] [cyan]{diff.from_id}[/cyan] ({diff.from_fingerprint[:12]}...)\n"
            f"[dim]To Current:   [/dim] [cyan]{diff.to_id}[/cyan] ({diff.to_fingerprint[:12]}...)",
            border_style="yellow",
        )
    )

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Severity", style="bold")
    table.add_column("Category")
    table.add_column("Item", style="bold")
    table.add_column("Classification")
    table.add_column("Expected (Base)")
    table.add_column("Actual (Current)")

    for item in diff.items:
        if item.classification == DiffClassification.UNCHANGED:
            continue

        if item.severity == DiffSeverity.CRITICAL:
            sev_text = Text("🔴 CRITICAL", style="bold red")
        elif item.severity == DiffSeverity.WARNING:
            sev_text = Text("🟡 WARNING", style="bold yellow")
        else:
            sev_text = Text("🔵 INFO", style="bold blue")

        cls_color = (
            "green"
            if item.classification == DiffClassification.ADDED
            else ("red" if item.classification == DiffClassification.REMOVED else "yellow")
        )
        cls_text = Text(item.classification.value, style=cls_color)

        table.add_row(
            sev_text,
            item.category,
            item.item_name,
            cls_text,
            str(item.old_value or "-"),
            str(item.new_value or "-"),
        )

    console.print(table)
    console.print()


def render_verify(result: VerificationResult, console: Console) -> None:
    """Render verification outcome and reasons."""
    console.print()
    if result.status == VerificationStatus.PASS:
        console.print(
            Panel(
                "[bold green]✓ VERIFICATION PASSED[/bold green]\n"
                "Current machine matches all expected Runmark specifications.",
                border_style="green",
            )
        )
    elif result.status == VerificationStatus.WARN:
        console.print(
            Panel(
                "[bold yellow]⚠ VERIFICATION PASSED WITH WARNINGS[/bold yellow]\n"
                "Environment is operational but non-critical drift was detected.",
                border_style="yellow",
            )
        )
        for r in result.reasons:
            console.print(f"  [yellow]•[/yellow] {r}")
    else:
        console.print(
            Panel(
                "[bold red]✗ VERIFICATION FAILED[/bold red]\n"
                "Critical environment drift or missing prerequisites detected.",
                border_style="red",
            )
        )
        for r in result.reasons:
            console.print(f"  [red]•[/red] {r}")
    console.print()


def render_doctor(report: DoctorReport, console: Console) -> None:
    """Render doctor diagnostics and remediation steps."""
    console.print()
    if report.is_healthy:
        console.print(
            Panel(
                "[bold green]✓ RUNMARK DOCTOR — ALL SYSTEMS HEALTHY[/bold green]\n"
                "No environment discrepancies, missing dependencies, or missing variables detected.",
                border_style="green",
            )
        )
        return

    console.print(
        Panel(
            "[bold red]RUNMARK DOCTOR DIAGNOSTIC REPORT[/bold red]\n"
            f"Diagnosed [bold]{len(report.issues)}[/bold] issue(s) in project [bold]{report.project_name}[/bold].",
            border_style="red",
        )
    )

    for issue in report.issues:
        if issue.severity == DiffSeverity.CRITICAL:
            sev_icon = "🔴 [bold red]CRITICAL[/bold red]"
        elif issue.severity == DiffSeverity.WARNING:
            sev_icon = "🟡 [bold yellow]WARNING[/bold yellow]"
        else:
            sev_icon = "🔵 [bold blue]INFO[/bold blue]"

        console.print(f"{sev_icon}: [bold]{issue.title}[/bold] [dim]({issue.code})[/dim]")
        console.print(f"  [dim]Explanation:[/dim]      {issue.explanation}")
        console.print(f"  [bold cyan]Suggested Action:[/bold cyan] {issue.suggested_action}")
        console.print()


def render_history(snapshots: list[RunmarkState], console: Console) -> None:
    """Render chronological list of snapshots."""
    console.print()
    if not snapshots:
        console.print("[dim]No snapshots found in .runmark/snapshots/[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Date (UTC)")
    table.add_column("Snapshot ID", style="bold")
    table.add_column("Git Commit", style="cyan")
    table.add_column("Fingerprint", style="green")
    table.add_column("Message")

    for s in snapshots:
        commit_str = (s.git.commit or "")[:8] if s.git.commit else "none"
        table.add_row(
            s.runmark.created_at[:19].replace("T", " "),
            s.runmark.id,
            commit_str,
            f"{s.runmark.environment_fingerprint[:12]}...",
            s.runmark.message or "-",
        )

    console.print(Panel("[bold]RUNMARK SNAPSHOT HISTORY[/bold]", border_style="cyan"))
    console.print(table)
    console.print()
