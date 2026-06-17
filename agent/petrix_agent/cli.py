"""
Petrix Agent — CLI entry point.

Modes:
  petrix-agent --server URL --token JWT               # Scan ponctuel auto (blackbox)
  petrix-agent --server URL --token JWT --target IP   # Scan ciblé
  petrix-agent --server URL --token JWT --daemon      # Service — polling toutes les 5 min
"""

import platform
import socket
import sys
import time
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from petrix_agent.scanner.network import get_local_networks, discover_hosts, DiscoveredHost
from petrix_agent.scanner.ports import scan_host, PortResult
from petrix_agent.reporter import PetrixReporter

console = Console()
OS = platform.system()


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--server",   required=True, help="URL du serveur Petrix")
@click.option("--token",    default=None,  help="JWT token agent (30 jours)")
@click.option("--email",    default=None,  help="Email (si pas de token)")
@click.option("--password", default=None,  help="Mot de passe")
@click.option("--target",   default=None,  help="IP ou CIDR cible (mode ponctuel)")
@click.option("--name",     default=None,  help="Nom du scan")
@click.option("--daemon",   is_flag=True,  help="Mode service — polling continu pour jobs assignés depuis Petrix")
@click.option("--interval", default=300,   help="Intervalle de polling en secondes (daemon, défaut : 300)")
@click.option("--no-upload", is_flag=True, help="Mode local — pas d'envoi au serveur")
def main(server, token, email, password, target, name, daemon, interval, no_upload):
    """Petrix Agent — scan réseau et remontée automatique dans Petrix."""

    reporter = None
    if not no_upload:
        reporter = PetrixReporter(server, token or "")
        if not token and email and password:
            tok = reporter.login(email, password)
            if not tok:
                console.print("[red]Authentification échouée.[/red]")
                sys.exit(1)
        elif not token:
            console.print("[red]--token requis (téléchargez l'installeur depuis Petrix).[/red]")
            sys.exit(1)

    if daemon:
        _run_daemon(server, reporter, interval)
    else:
        _run_once(server, reporter, target, name)


# ─────────────────────────────────────────────────────────────────────────────
# Mode service (daemon) — modèle marché : polling pour jobs assignés
# ─────────────────────────────────────────────────────────────────────────────

def _run_daemon(server: str, reporter: Optional[PetrixReporter], interval: int):
    """Boucle infinie :
    1. register_self() → la machine apparaît dans Assets
    2. Interroge /agent/jobs avec ses IPs locales
    3. Si un job est assigné → claim → scan → résultats
    4. Dort `interval` secondes et recommence
    """
    console.rule("[bold cyan]Petrix Agent — Mode Service[/bold cyan]")
    console.print(f"Machine : [bold]{platform.node()}[/bold]  |  OS : [bold]{OS}[/bold]")
    console.print(f"Polling toutes les [bold]{interval}[/bold]s  |  Serveur : [bold]{server}[/bold]")
    console.print()

    iteration = 0
    while True:
        iteration += 1
        ips = _get_local_ips()
        console.print(f"[dim][#{iteration}] IPs : {', '.join(ips) or '?'}[/dim]")

        if reporter:
            # Mise à jour de la machine dans Assets
            reporter.register_self()

            # Cherche un job en attente pour cette machine
            jobs = reporter.get_pending_jobs(ips)
            if jobs:
                job = jobs[0]
                console.print(f"  [green]Job trouvé :[/green] {job['name']} ({job['scan_type']})")
                if reporter.claim_job(job["id"]):
                    console.print("  [cyan]Job claimé — démarrage du scan...[/cyan]")
                    _run_job(job, reporter, server)
                else:
                    console.print("  [yellow]Claim échoué (déjà pris ?)[/yellow]")
            else:
                console.print("  Aucun job en attente.")

        console.print(f"  [dim]Prochain poll dans {interval}s...[/dim]\n")
        time.sleep(interval)


def _run_job(job: dict, reporter: PetrixReporter, server: str):
    """Exécute un job assigné depuis Petrix."""
    scan_id = job["id"]

    # Cibles : utilise targets du job si présentes, sinon réseau local
    targets_raw = job.get("targets", [])
    if targets_raw:
        targets_to_scan = [t["value"] for t in targets_raw if t.get("value")]
    else:
        networks = get_local_networks()
        targets_to_scan = [n.cidr for n in networks]

    _do_scan(scan_id, targets_to_scan, reporter, server)


# ─────────────────────────────────────────────────────────────────────────────
# Mode ponctuel — scan auto sans job assigné
# ─────────────────────────────────────────────────────────────────────────────

def _run_once(server: str, reporter: Optional[PetrixReporter], target: Optional[str], name: Optional[str]):
    """Scan ponctuel : crée son propre scan, scanne, remonte les résultats."""
    console.rule("[bold cyan]Petrix Agent[/bold cyan]")
    console.print(f"OS : [bold]{OS}[/bold]  |  Machine : [bold]{platform.node()}[/bold]")
    console.print()

    if reporter:
        console.print("[cyan]Enregistrement dans Assets Petrix...[/cyan]")
        asset_id = reporter.register_self()
        if asset_id:
            console.print(f"  [green]Asset :[/green] {asset_id}")

    if target:
        targets_to_scan = [target]
        console.print(f"Cible : [bold]{target}[/bold]")
    else:
        console.print("[cyan]Auto-détection du réseau local...[/cyan]")
        networks = get_local_networks()
        if not networks:
            console.print("[red]Aucun réseau détecté.[/red]")
            sys.exit(1)
        for n in networks:
            console.print(f"  {n.interface} → [bold]{n.cidr}[/bold]")
        targets_to_scan = [n.cidr for n in networks]

    scan_id = None
    scan_name = name or f"Agent scan — {platform.node()} ({OS})"
    if reporter:
        scan_id = reporter.create_scan(scan_name, scan_type="full")
        if scan_id:
            console.print(f"Scan créé : [bold]{scan_id}[/bold]")

    _do_scan(scan_id, targets_to_scan, reporter, server)


# ─────────────────────────────────────────────────────────────────────────────
# Moteur de scan commun
# ─────────────────────────────────────────────────────────────────────────────

def _do_scan(scan_id: Optional[str], targets: list[str], reporter: Optional[PetrixReporter], server: str):
    all_hosts: list[DiscoveredHost] = []
    console.print()
    console.rule("Découverte d'hôtes")

    for cidr in targets:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
            task = p.add_task(f"Scanning {cidr}...", total=None)
            discovered = discover_hosts(cidr, callback=lambda m: p.update(task, description=m))
            all_hosts.extend(discovered)

    if not all_hosts:
        console.print("[yellow]Aucun hôte détecté.[/yellow]")
        if scan_id and reporter:
            reporter.complete_scan(scan_id, {"critical":0,"high":0,"medium":0,"low":0,"info":0}, 100.0, "A")
        return

    _print_hosts_table(all_hosts)

    console.print()
    console.rule("Scan de ports")

    all_findings: list[dict] = []
    host_results: list[dict] = []
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for host in all_hosts:
        console.print(f"\n[bold]{host.ip}[/bold]" + (f" ({host.hostname})" if host.hostname else ""))
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
            task = p.add_task(f"Scanning {host.ip}...", total=None)
            ports = scan_host(host.ip, callback=lambda m: p.update(task, description=m))

        open_ports = []
        for p in ports:
            sev = _classify(p.port, p.service)
            summary[sev] = summary.get(sev, 0) + 1
            port_dict = {
                "port": p.port, "protocol": p.protocol, "service": p.service,
                "product": p.product, "version": p.version, "severity": sev,
                "banner": p.banner, "http_title": p.http_title,
            }
            open_ports.append(port_dict)
            all_findings.append({
                "host": host.ip, "severity": sev,
                "title": f"Port {p.port}/{p.protocol} — {p.service} {p.product}".rstrip(" —"),
                "description": " | ".join(filter(None, [
                    f"{p.product} {p.version}".strip(),
                    f"Banner: {p.banner}" if p.banner else None,
                    f"Page: {p.http_title}" if p.http_title else None,
                ])),
            })
            _print_port(p, sev)

        host_results.append({"ip": host.ip, "hostname": host.hostname, "mac": host.mac, "open_ports": open_ports})

    penalty = summary["critical"] * 25 + summary["high"] * 10 + summary["medium"] * 4 + summary["low"]
    score = max(0.0, 100.0 - penalty)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    console.print()
    console.rule("Résumé")
    console.print(
        f"Hôtes: [bold]{len(all_hosts)}[/bold]  "
        f"Critique: [red]{summary['critical']}[/red]  "
        f"Élevé: [orange1]{summary['high']}[/orange1]  "
        f"Moyen: [yellow]{summary['medium']}[/yellow]  "
        f"Score: [bold]{score:.0f}/100[/bold] ([bold]{grade}[/bold])"
    )

    if reporter and scan_id:
        console.print("\n[cyan]Envoi des résultats...[/cyan]")
        reporter.push_results(scan_id, host_results, all_findings)
        reporter.complete_scan(scan_id, summary, score, grade)
        console.print(f"[green]Résultats envoyés.[/green] → {server}/scans")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_local_ips() -> list[str]:
    ips: list[str] = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ":" not in ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def _classify(port: int, service: str) -> str:
    if port in {21, 23, 135, 139, 445, 3389, 5900, 512, 513, 514}:
        return "critical"
    svc = (service or "").lower()
    if any(s in svc for s in ("telnet", "ftp", "vnc", "rdp")):
        return "critical"
    if port in {22, 80, 443, 3306, 5432, 6379, 8080, 8443, 27017, 1433, 1521}:
        return "high"
    return "medium"


def _print_hosts_table(hosts: list[DiscoveredHost]):
    table = Table(title=f"{len(hosts)} hôte(s)", show_lines=False)
    table.add_column("IP", style="bold cyan")
    table.add_column("Hostname")
    table.add_column("MAC")
    for h in hosts:
        table.add_row(h.ip, h.hostname or "—", h.mac or "—")
    console.print(table)


def _print_port(p: PortResult, severity: str):
    color = {"critical": "red", "high": "orange1", "medium": "yellow"}.get(severity, "white")
    line = f"  [{color}]{p.port}/{p.protocol}[/{color}]  {p.service}"
    if p.product:
        line += f"  {p.product} {p.version}".rstrip()
    if p.http_title:
        line += f"  [italic blue]\"{p.http_title}\"[/italic blue]"
    console.print(line)
    if p.banner:
        console.print(f"    [dim]↳ {p.banner}[/dim]")


if __name__ == "__main__":
    main()
