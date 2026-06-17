"""
Petrix Agent — CLI entry point.

Usage:
    petrix-agent --server https://petrix.noellahome.org --email admin@example.com --password secret
    petrix-agent --server https://petrix.noellahome.org --token <jwt>
    petrix-agent --server https://petrix.noellahome.org --token <jwt> --target 192.168.1.10
"""

import platform
import sys
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import print as rprint

from petrix_agent.scanner.network import get_local_networks, discover_hosts, DiscoveredHost
from petrix_agent.scanner.ports import scan_host, PortResult, COMMON_PORTS
from petrix_agent.reporter import PetrixReporter

console = Console()
OS = platform.system()


@click.command()
@click.option("--server", required=True, help="URL du serveur Petrix (ex: https://petrix.noellahome.org)")
@click.option("--token", default=None, help="JWT token (si déjà authentifié)")
@click.option("--email", default=None, help="Email pour l'authentification")
@click.option("--password", default=None, help="Mot de passe")
@click.option("--target", default=None, help="Cible spécifique (IP ou CIDR). Sinon auto-détection du réseau local.")
@click.option("--name", default=None, help="Nom du scan (auto-généré si absent)")
@click.option("--no-upload", is_flag=True, help="Ne pas envoyer les résultats au serveur (mode local)")
def main(server: str, token: Optional[str], email: Optional[str], password: Optional[str],
         target: Optional[str], name: Optional[str], no_upload: bool):
    """Petrix Agent — Scan réseau local et envoi des résultats à Petrix."""

    console.rule("[bold cyan]Petrix Agent[/bold cyan]")
    console.print(f"OS détecté : [bold]{OS}[/bold]  |  Machine : [bold]{platform.node()}[/bold]")
    console.print()

    # Auth
    reporter = None
    if not no_upload:
        reporter = PetrixReporter(server, token or "")
        if not token and email and password:
            console.print("[yellow]Authentification...[/yellow]")
            tok = reporter.login(email, password)
            if not tok:
                console.print("[red]Échec de l'authentification. Vérifiez email/password.[/red]")
                sys.exit(1)
            console.print("[green]Authentifié.[/green]")
        elif not token:
            console.print("[red]Fournissez --token ou --email + --password.[/red]")
            sys.exit(1)

    # Auto-register this machine as an asset before doing anything else
    if reporter:
        console.print("[cyan]Enregistrement de la machine dans les assets Petrix...[/cyan]")
        asset_id = reporter.register_self()
        if asset_id:
            console.print(f"  [green]Asset enregistré :[/green] [bold]{asset_id}[/bold]")
        else:
            console.print("  [yellow]Enregistrement asset ignoré (serveur non joignable ou token invalide)[/yellow]")

    # Determine targets
    if target:
        targets_to_scan = [target]
        console.print(f"Mode greybox — cible : [bold]{target}[/bold]")
    else:
        console.print("[cyan]Mode blackbox — auto-détection du réseau local...[/cyan]")
        networks = get_local_networks()
        if not networks:
            console.print("[red]Aucun réseau local détecté.[/red]")
            sys.exit(1)
        for n in networks:
            console.print(f"  Interface [bold]{n.interface}[/bold] — {n.ip} → réseau [bold]{n.cidr}[/bold]")
        targets_to_scan = [n.cidr for n in networks]

    # Create scan on server
    scan_id = None
    scan_name = name or f"Agent scan — {platform.node()} ({OS})"
    if reporter:
        scan_id = reporter.create_scan(scan_name, scan_type="full")
        if scan_id:
            console.print(f"Scan créé sur le serveur : [bold]{scan_id}[/bold]")
        else:
            console.print("[yellow]Impossible de créer le scan sur le serveur — mode local.[/yellow]")

    # Host discovery
    all_hosts: list[DiscoveredHost] = []
    console.print()
    console.rule("Découverte d'hôtes")

    for cidr in targets_to_scan:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task(f"Scanning {cidr}...", total=None)
            discovered = discover_hosts(cidr, callback=lambda m: progress.update(task, description=m))
            all_hosts.extend(discovered)

    if not all_hosts:
        console.print("[yellow]Aucun hôte détecté.[/yellow]")
        if scan_id and reporter:
            reporter.complete_scan(scan_id, {"critical":0,"high":0,"medium":0,"low":0,"info":0}, 100.0, "A")
        return

    _print_hosts_table(all_hosts)

    # Port scan
    console.print()
    console.rule("Scan de ports")

    all_findings: list[dict] = []
    host_results: list[dict] = []
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for host in all_hosts:
        console.print(f"\n[bold]{host.ip}[/bold]" + (f" ({host.hostname})" if host.hostname else ""))

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task(f"Scanning {host.ip}...", total=None)
            ports = scan_host(host.ip, callback=lambda m: progress.update(task, description=m))

        open_ports = []
        for p in ports:
            severity = _classify(p.port, p.service)
            summary[severity] = summary.get(severity, 0) + 1

            port_dict = {
                "port": p.port, "protocol": p.protocol, "service": p.service,
                "product": p.product, "version": p.version,
                "banner": p.banner, "http_title": p.http_title,
                "ssl_subject": p.ssl_subject, "extra": p.extra,
                "severity": severity,
            }
            open_ports.append(port_dict)

            desc_parts = [f"{p.product} {p.version}".strip()]
            if p.banner:
                desc_parts.append(f"Banner: {p.banner}")
            if p.http_title:
                desc_parts.append(f"Page: {p.http_title}")
            if p.extra:
                desc_parts.extend(p.extra)

            all_findings.append({
                "host": host.ip,
                "severity": severity,
                "title": f"Port {p.port}/{p.protocol} — {p.service} {p.product}".rstrip(" —"),
                "description": " | ".join(filter(None, desc_parts)),
            })

            _print_port(p, severity)

        host_results.append({
            "ip": host.ip, "hostname": host.hostname, "mac": host.mac,
            "open_ports": open_ports,
        })

    # Score
    penalty = summary["critical"] * 25 + summary["high"] * 10 + summary["medium"] * 4 + summary["low"]
    score = max(0.0, 100.0 - penalty)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    # Summary
    console.print()
    console.rule("Résumé")
    console.print(
        f"Hôtes: [bold]{len(all_hosts)}[/bold]  |  "
        f"Critique: [red]{summary['critical']}[/red]  "
        f"Élevé: [orange1]{summary['high']}[/orange1]  "
        f"Moyen: [yellow]{summary['medium']}[/yellow]  "
        f"Faible: [green]{summary['low']}[/green]  "
        f"Score: [bold]{score:.0f}/100[/bold] ([bold]{grade}[/bold])"
    )

    # Upload
    if reporter and scan_id:
        console.print("\n[cyan]Envoi des résultats au serveur...[/cyan]")
        ok = reporter.push_results(scan_id, host_results, all_findings)
        reporter.complete_scan(scan_id, summary, score, grade)
        if ok:
            console.print(f"[green]Résultats envoyés.[/green] Voir : {server}/scans")
        else:
            console.print("[yellow]Envoi échoué — résultats disponibles en local uniquement.[/yellow]")


def _classify(port: int, service: str) -> str:
    critical = {21, 23, 135, 139, 445, 3389, 5900, 512, 513, 514}
    high = {22, 80, 443, 3306, 5432, 6379, 8080, 8443, 27017, 1433, 1521}
    svc = (service or "").lower()
    if any(s in svc for s in ("telnet", "ftp", "vnc", "rdp", "rsh", "rlogin")):
        return "critical"
    if port in critical:
        return "critical"
    if port in high:
        return "high"
    return "medium"


def _print_hosts_table(hosts: list[DiscoveredHost]):
    table = Table(title=f"{len(hosts)} hôte(s) découvert(s)", show_lines=False)
    table.add_column("IP", style="bold cyan")
    table.add_column("Hostname")
    table.add_column("MAC")
    table.add_column("Méthode")
    for h in hosts:
        table.add_row(h.ip, h.hostname or "—", h.mac or "—", h.method)
    console.print(table)


def _print_port(p: PortResult, severity: str):
    color = {"critical": "red", "high": "orange1", "medium": "yellow", "low": "green"}.get(severity, "white")
    line = f"  [{color}]{p.port}/{p.protocol}[/{color}]  {p.service}"
    if p.product:
        line += f"  {p.product} {p.version}".rstrip()
    if p.http_title:
        line += f"  [italic blue]\"{p.http_title}\"[/italic blue]"
    if p.ssl_subject:
        line += f"  [green]🔒 {p.ssl_subject}[/green]"
    console.print(line)
    if p.banner:
        console.print(f"    [dim]↳ {p.banner}[/dim]")
    for e in p.extra:
        console.print(f"    [red]⚠ {e}[/red]")


if __name__ == "__main__":
    main()
