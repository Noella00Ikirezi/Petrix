"""
CLI for GRC Security Audit Agent
Comprehensive security assessment tool for Windows and Linux
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .core.engine import DiscoveryEngine
from .core.models import AuditConfig, AuditTarget, TargetType


# Main app
app = typer.Typer(
    name="grc-agent",
    help="GRC Security Audit Agent - Comprehensive security assessment tool",
    add_completion=False,
)
console = Console()

# Sub-command groups
server_app = typer.Typer(help="Central server management commands")
agent_app = typer.Typer(help="Agent daemon commands")
compliance_app = typer.Typer(help="Compliance checking commands (CIS Benchmarks)")
ad_app = typer.Typer(help="Active Directory audit commands")

app.add_typer(server_app, name="server")
app.add_typer(agent_app, name="agent")
app.add_typer(compliance_app, name="compliance")
app.add_typer(ad_app, name="ad")


def version_callback(value: bool):
    if value:
        console.print(f"GRC Security Audit Agent v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        help="Show version"
    ),
):
    """
    GRC Security Audit Agent - Comprehensive security assessment tool

    Combines network scanning, vulnerability detection, system auditing,
    Active Directory assessment, and compliance checking in one tool.
    """
    pass


# ============== SCAN COMMANDS ==============

@app.command()
def scan(
    targets: list[str] = typer.Argument(
        ...,
        help="Targets to audit (IP, hostname, URL, CIDR)"
    ),
    name: str = typer.Option(
        "Security Audit",
        "--name", "-n",
        help="Audit name"
    ),
    output_dir: str = typer.Option(
        "./reports",
        "--output", "-o",
        help="Output directory for reports"
    ),
    ports: str = typer.Option(
        "1-1000",
        "--ports", "-p",
        help="Ports to scan (e.g., 1-1000, full, 22,80,443)"
    ),
    aggressive: bool = typer.Option(
        False,
        "--aggressive", "-A",
        help="Aggressive mode (OS detection, advanced scripts)"
    ),
    no_network: bool = typer.Option(
        False,
        "--no-network",
        help="Disable network scanning"
    ),
    no_system: bool = typer.Option(
        False,
        "--no-system",
        help="Disable system audit"
    ),
    no_web: bool = typer.Option(
        False,
        "--no-web",
        help="Disable web audit"
    ),
    no_vuln: bool = typer.Option(
        False,
        "--no-vuln",
        help="Disable vulnerability scanning"
    ),
    json_only: bool = typer.Option(
        False,
        "--json",
        help="Generate only JSON report"
    ),
    html_only: bool = typer.Option(
        False,
        "--html",
        help="Generate only HTML report"
    ),
    ssh_user: Optional[str] = typer.Option(
        None,
        "--ssh-user",
        help="SSH user for remote system audit"
    ),
    ssh_key: Optional[str] = typer.Option(
        None,
        "--ssh-key",
        help="Path to SSH key"
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        help="Central server URL to report results"
    ),
    timeout: int = typer.Option(
        3600,
        "--timeout", "-t",
        help="Total timeout in seconds"
    ),
):
    """
    Run a security audit on specified targets.

    Examples:
        grc-agent scan 192.168.1.0/24
        grc-agent scan example.com https://api.example.com
        grc-agent scan 10.0.0.1 -p full -A
        grc-agent scan localhost --server https://grc-server:8443
    """
    _print_banner()

    config = AuditConfig(
        name=name,
        output_dir=output_dir,
        scan_ports=ports,
        scan_aggressive=aggressive,
        enable_network_scan=not no_network,
        enable_system_audit=not no_system,
        enable_web_audit=not no_web,
        enable_vuln_scan=not no_vuln,
        generate_json=True if json_only else not html_only,
        generate_html=True if html_only else not json_only,
        generate_pdf=not (json_only or html_only),
        ssh_user=ssh_user,
        ssh_key_path=ssh_key,
        timeout_total=timeout,
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        engine = DiscoveryEngine(config)
        result = asyncio.run(engine.run_audit(targets))

        _print_result_summary(result)

        # Send to server if specified
        if server:
            asyncio.run(_send_to_server(server, result))

        # Exit code based on score
        if result.score:
            if result.score.grade in ['D', 'F']:
                raise typer.Exit(2)
            elif result.score.grade == 'C':
                raise typer.Exit(1)
        raise typer.Exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Audit interrupted by user[/]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def local(
    name: str = typer.Option(
        "Local System Audit",
        "--name", "-n",
        help="Audit name"
    ),
    output_dir: str = typer.Option(
        "./reports",
        "--output", "-o",
        help="Output directory"
    ),
    compliance: bool = typer.Option(
        False,
        "--compliance", "-c",
        help="Include CIS compliance checks"
    ),
):
    """
    Audit the local system only.

    Checks security configurations on the local machine.
    """
    _print_banner()

    config = AuditConfig(
        name=name,
        output_dir=output_dir,
        enable_network_scan=False,
        enable_web_audit=False,
        enable_vuln_scan=False,
        enable_system_audit=True,
    )

    try:
        engine = DiscoveryEngine(config)
        result = asyncio.run(engine.run_audit(["localhost"]))
        _print_result_summary(result)

        if compliance:
            console.print("\n[bold]Running CIS Compliance Checks...[/]")
            asyncio.run(_run_local_compliance())

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def quick(
    targets: list[str] = typer.Argument(
        ...,
        help="Targets to scan"
    ),
):
    """
    Quick scan - fast port scan with basic checks.
    """
    _print_banner()

    config = AuditConfig(
        name="Quick Scan",
        scan_ports="22,80,443,445,3389,8080,8443",
        enable_system_audit=False,
        enable_web_audit=False,
        enable_vuln_scan=False,
    )

    try:
        engine = DiscoveryEngine(config)
        result = asyncio.run(engine.run_audit(targets))
        _print_result_summary(result)

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        raise typer.Exit(1)


# ============== SERVER COMMANDS ==============

@server_app.command("start")
def server_start(
    host: str = typer.Option(
        "0.0.0.0",
        "--host", "-h",
        help="Host to bind to"
    ),
    port: int = typer.Option(
        8443,
        "--port", "-p",
        help="Port to listen on"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for authentication"
    ),
    ssl_cert: Optional[str] = typer.Option(
        None,
        "--ssl-cert",
        help="Path to SSL certificate"
    ),
    ssl_key: Optional[str] = typer.Option(
        None,
        "--ssl-key",
        help="Path to SSL key"
    ),
):
    """
    Start the central GRC server.

    The server collects results from agents and provides a dashboard.
    """
    try:
        from .server.api import run_server
        from .server.models import ServerConfig

        config = ServerConfig(
            host=host,
            port=port,
            api_key=api_key,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key,
        )

        console.print(f"[bold green]Starting GRC Server on {host}:{port}[/]")
        run_server(config)

    except ImportError as e:
        console.print(f"[red]Server dependencies not installed: {e}[/]")
        console.print("Install with: pip install fastapi uvicorn")
        raise typer.Exit(1)


# ============== AGENT COMMANDS ==============

@agent_app.command("start")
def agent_start(
    server_url: str = typer.Argument(
        ...,
        help="Central server URL (e.g., https://grc-server:8443)"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for server authentication"
    ),
    interval: int = typer.Option(
        30,
        "--interval", "-i",
        help="Heartbeat interval in seconds"
    ),
    no_verify_ssl: bool = typer.Option(
        False,
        "--no-verify-ssl",
        help="Disable SSL certificate verification"
    ),
):
    """
    Start the agent daemon.

    Connects to central server, receives tasks, and reports results.
    """
    try:
        from .agent.daemon import run_daemon

        console.print(f"[bold green]Starting GRC Agent[/]")
        console.print(f"Server: {server_url}")

        asyncio.run(run_daemon(
            server_url=server_url,
            api_key=api_key,
            heartbeat_interval=interval,
            verify_ssl=not no_verify_ssl,
        ))

    except Exception as e:
        console.print(f"[red]Agent error: {e}[/]")
        raise typer.Exit(1)


@agent_app.command("status")
def agent_status():
    """
    Show local agent status and capabilities.
    """
    from .platform.detector import PlatformDetector

    platform_info = PlatformDetector.detect_local()

    table = Table(title="Agent Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("OS Type", platform_info.os_type.value)
    table.add_row("OS Name", platform_info.os_name)
    table.add_row("OS Version", platform_info.os_version)
    table.add_row("Hostname", platform_info.hostname)
    table.add_row("Architecture", platform_info.architecture)
    table.add_row("Elevated", "Yes" if platform_info.is_elevated else "No")
    table.add_row("Current User", platform_info.current_user)

    if platform_info.is_domain_joined:
        table.add_row("Domain", platform_info.domain_name)
        table.add_row("Domain Controller", "Yes" if platform_info.is_domain_controller else "No")

    console.print(table)


# ============== COMPLIANCE COMMANDS ==============

@compliance_app.command("run")
def compliance_run(
    benchmark: str = typer.Option(
        "auto",
        "--benchmark", "-b",
        help="Benchmark to use (auto, linux, windows)"
    ),
    level: int = typer.Option(
        1,
        "--level", "-l",
        help="CIS Level (1 or 2)"
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category", "-c",
        help="Run specific category only"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Output file (JSON)"
    ),
):
    """
    Run CIS compliance checks.

    Examples:
        grc-agent compliance run
        grc-agent compliance run --level 2
        grc-agent compliance run --category SSH
    """
    asyncio.run(_run_compliance(benchmark, level, category, output))


@compliance_app.command("list")
def compliance_list():
    """
    List available compliance checks.
    """
    from .platform.detector import PlatformDetector

    platform_info = PlatformDetector.detect_local()

    if platform_info.os_type.value == "windows":
        from .modules.compliance.cis_windows import CISWindowsBenchmark
        benchmark = CISWindowsBenchmark()
    else:
        from .modules.compliance.cis_linux import CISLinuxBenchmark
        benchmark = CISLinuxBenchmark()

    console.print(f"[bold]{benchmark.benchmark_name} v{benchmark.benchmark_version}[/]")
    console.print(f"Total checks: {len(benchmark.checks)}\n")

    table = Table(title="Available Checks")
    table.add_column("ID", style="cyan")
    table.add_column("Level")
    table.add_column("Category")
    table.add_column("Title")

    for check in benchmark.checks[:50]:  # Limit display
        table.add_row(
            check.id,
            check.level.value,
            check.category,
            check.title[:50] + "..." if len(check.title) > 50 else check.title
        )

    console.print(table)

    if len(benchmark.checks) > 50:
        console.print(f"\n[dim]... and {len(benchmark.checks) - 50} more checks[/]")


# ============== AD COMMANDS ==============

@ad_app.command("scan")
def ad_scan(
    output_dir: str = typer.Option(
        "./reports",
        "--output", "-o",
        help="Output directory"
    ),
    bloodhound: bool = typer.Option(
        False,
        "--bloodhound",
        help="Run BloodHound collection"
    ),
):
    """
    Run Active Directory security audit.

    Similar to PingCastle - checks AD configuration, privileged accounts,
    Kerberos settings, trusts, and more.
    """
    _print_banner()
    asyncio.run(_run_ad_audit(output_dir, bloodhound))


@ad_app.command("quick")
def ad_quick():
    """
    Quick AD health check.
    """
    asyncio.run(_run_ad_quick_check())


# ============== REPORT COMMANDS ==============

@app.command()
def report(
    json_file: str = typer.Argument(
        ...,
        help="JSON file from a previous audit"
    ),
    output_format: str = typer.Option(
        "html",
        "--format", "-f",
        help="Output format (html, pdf)"
    ),
    output_dir: str = typer.Option(
        "./reports",
        "--output", "-o",
        help="Output directory"
    ),
):
    """
    Regenerate a report from an existing JSON file.
    """
    import json as json_module
    from .core.models import AuditResult
    from .reports.generator import ReportGenerator

    try:
        with open(json_file, 'r') as f:
            data = json_module.load(f)

        result = AuditResult(**data)

        config = AuditConfig(
            output_dir=output_dir,
            generate_html=output_format == 'html',
            generate_pdf=output_format == 'pdf',
            generate_json=False,
        )

        generator = ReportGenerator(config)
        generated = asyncio.run(generator.generate(result))

        for fmt, path in generated.items():
            console.print(f"[green]✓ {fmt.upper()} report:[/] {path}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def info():
    """
    Show information about available modules and tools.
    """
    _print_banner()

    # Check platform
    from .platform.detector import PlatformDetector
    platform_info = PlatformDetector.detect_local()

    console.print(f"[bold]Platform:[/] {platform_info.os_type.value} ({platform_info.os_name})")
    console.print(f"[bold]Elevated:[/] {'Yes' if platform_info.is_elevated else 'No'}")

    if platform_info.is_domain_joined:
        console.print(f"[bold]Domain:[/] {platform_info.domain_name}")

    console.print()

    # Check modules
    table = Table(title="Available Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")

    modules = [
        ("Network Scanner", _check_nmap(), "Network scanning with Nmap"),
        ("Web Scanner", _check_nuclei(), "Web vulnerability scanning with Nuclei"),
        ("System Auditor", True, "Local system security audit"),
        ("Windows Auditor", platform_info.os_type.value == "windows", "Windows-specific checks"),
        ("Linux Auditor", platform_info.os_type.value == "linux", "Linux-specific checks"),
        ("AD Auditor", platform_info.is_domain_joined, "Active Directory audit"),
        ("CIS Compliance", True, "CIS Benchmark compliance"),
        ("Vuln Scanner", True, "CVE vulnerability detection"),
        ("Report Generator", True, "HTML/PDF/JSON reports"),
    ]

    for name, available, desc in modules:
        if available is True:
            status = "[green]✓ Available[/]"
        elif available is False:
            status = "[dim]- N/A[/]"
        else:
            status = "[yellow]⚠ Partial[/]"
        table.add_row(name, status, desc)

    console.print(table)

    # Tool recommendations
    console.print("\n[bold]External Tools:[/]")

    if not _check_nmap():
        console.print("  [yellow]•[/] Nmap not found - install for network scanning")
        console.print("    brew install nmap  # macOS")
        console.print("    apt install nmap   # Debian/Ubuntu")

    if not _check_nuclei():
        console.print("  [yellow]•[/] Nuclei not found - install for web scanning")
        console.print("    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest")


# ============== HELPER FUNCTIONS ==============

def _print_banner():
    """Print the application banner"""
    console.print(Panel(
        f"[bold blue]GRC Security Audit Agent[/] v{__version__}\n"
        "[dim]Comprehensive security assessment for Windows & Linux[/]",
        border_style="blue"
    ))


def _print_result_summary(result):
    """Print audit result summary"""
    if not result.score:
        return

    table = Table(title="Audit Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    grade_colors = {'A': 'green', 'B': 'green', 'C': 'yellow', 'D': 'red', 'F': 'red'}
    grade_color = grade_colors.get(result.score.grade, 'white')

    table.add_row("Overall Score", f"{result.score.overall_score}/100")
    table.add_row("Grade", f"[{grade_color}]{result.score.grade}[/]")
    table.add_row("Risk Level", result.score.risk_level)
    table.add_row("", "")
    table.add_row("[red]Critical Findings[/]", str(result.score.critical_count))
    table.add_row("[orange1]High Findings[/]", str(result.score.high_count))
    table.add_row("[yellow]Medium Findings[/]", str(result.score.medium_count))
    table.add_row("[blue]Low Findings[/]", str(result.score.low_count))
    table.add_row("", "")
    table.add_row("Hosts Discovered", str(len(result.hosts)))
    table.add_row("Services Found", str(sum(len(h.services) for h in result.hosts)))

    console.print(table)
    console.print(f"\n[dim]{result.score.summary}[/]")


def _check_nmap() -> bool:
    """Check if Nmap is installed"""
    import subprocess
    try:
        result = subprocess.run(["which", "nmap"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def _check_nuclei() -> bool:
    """Check if Nuclei is installed"""
    import subprocess
    try:
        result = subprocess.run(["which", "nuclei"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


async def _send_to_server(server_url: str, result):
    """Send results to central server"""
    from .agent.client import AgentClient

    try:
        client = AgentClient(server_url)
        await client.register()
        await client.submit_results("local", result)
        console.print(f"[green]Results sent to {server_url}[/]")
    except Exception as e:
        console.print(f"[yellow]Could not send to server: {e}[/]")


async def _run_compliance(benchmark: str, level: int, category: Optional[str], output: Optional[str]):
    """Run compliance checks"""
    from .platform.detector import PlatformDetector
    from .modules.compliance.base import ComplianceLevel

    platform_info = PlatformDetector.detect_local()

    # Auto-detect benchmark
    if benchmark == "auto":
        if platform_info.os_type.value == "windows":
            from .modules.compliance.cis_windows import CISWindowsBenchmark
            bench = CISWindowsBenchmark()
        else:
            from .modules.compliance.cis_linux import CISLinuxBenchmark
            bench = CISLinuxBenchmark()
    elif benchmark == "windows":
        from .modules.compliance.cis_windows import CISWindowsBenchmark
        bench = CISWindowsBenchmark()
    else:
        from .modules.compliance.cis_linux import CISLinuxBenchmark
        bench = CISLinuxBenchmark()

    console.print(f"[bold]Running {bench.benchmark_name}[/]")
    console.print(f"Level: {level}")

    compliance_level = ComplianceLevel.LEVEL_1 if level == 1 else ComplianceLevel.LEVEL_2

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running compliance checks...", total=None)

        if category:
            results = await bench.run_category(category, compliance_level)
        else:
            results = await bench.run_all_checks(compliance_level)

    # Summary
    summary = bench.get_summary(results)

    table = Table(title="Compliance Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Checks", str(summary["total_checks"]))
    table.add_row("[green]Passed[/]", str(summary["passed"]))
    table.add_row("[red]Failed[/]", str(summary["failed"]))
    table.add_row("[yellow]Manual Review[/]", str(summary["manual_review"]))
    table.add_row("Compliance Score", f"{summary['compliance_score']}%")

    console.print(table)

    # Save to file if requested
    if output:
        import json
        with open(output, 'w') as f:
            json.dump({
                "summary": summary,
                "results": [r.__dict__ for r in results],
            }, f, indent=2, default=str)
        console.print(f"[green]Results saved to {output}[/]")


async def _run_local_compliance():
    """Quick local compliance check"""
    await _run_compliance("auto", 1, None, None)


async def _run_ad_audit(output_dir: str, bloodhound: bool):
    """Run AD security audit"""
    from .platform.detector import PlatformDetector

    platform_info = PlatformDetector.detect_local()

    if not platform_info.is_domain_joined:
        console.print("[yellow]This machine is not domain-joined.[/]")
        console.print("AD audit requires a domain-joined Windows machine.")
        return

    try:
        from .modules.ad.auditor import ADSecurityAuditor
        from .core.models import AuditConfig

        config = AuditConfig(output_dir=output_dir)
        auditor = ADSecurityAuditor(config)

        console.print("[bold]Starting Active Directory Security Audit[/]")
        console.print(f"Domain: {platform_info.domain_name}\n")

        findings = await auditor.audit()

        # Summary
        critical = sum(1 for f in findings if f.severity.value == "critical")
        high = sum(1 for f in findings if f.severity.value == "high")
        medium = sum(1 for f in findings if f.severity.value == "medium")

        table = Table(title="AD Audit Results")
        table.add_column("Severity", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("[red]Critical[/]", str(critical))
        table.add_row("[orange1]High[/]", str(high))
        table.add_row("[yellow]Medium[/]", str(medium))
        table.add_row("Total", str(len(findings)))

        console.print(table)

        # BloodHound collection
        if bloodhound:
            console.print("\n[bold]Running BloodHound collection...[/]")
            from .modules.ad.bloodhound import BloodHoundIntegration
            bh = BloodHoundIntegration(config)
            zip_path = await bh.collect()
            if zip_path:
                console.print(f"[green]BloodHound data: {zip_path}[/]")

    except Exception as e:
        console.print(f"[red]AD audit failed: {e}[/]")


async def _run_ad_quick_check():
    """Quick AD health check"""
    from .platform.detector import PlatformDetector

    platform_info = PlatformDetector.detect_local()

    if not platform_info.is_domain_joined:
        console.print("[yellow]Not domain-joined[/]")
        return

    console.print(f"[bold]Domain:[/] {platform_info.domain_name}")
    console.print(f"[bold]Domain Controller:[/] {'Yes' if platform_info.is_domain_controller else 'No'}")


if __name__ == "__main__":
    app()
