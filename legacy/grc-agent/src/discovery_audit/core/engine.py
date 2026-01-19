"""
Discovery Engine - Orchestrateur principal
Coordonne tous les modules d'audit et gère le flux de découverte
"""

import asyncio
import uuid
from datetime import datetime
from typing import Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .models import (
    AuditConfig,
    AuditResult,
    AuditTarget,
    AuditPhase,
    Finding,
    HostInfo,
    TargetType,
)
from .scoring import ScoringEngine


console = Console()


class DiscoveryEngine:
    """
    Moteur principal d'audit Discovery
    Orchestre les différentes phases et modules d'audit
    """

    def __init__(self, config: AuditConfig | None = None):
        self.config = config or AuditConfig()
        self.scoring_engine = ScoringEngine()
        self.result: AuditResult | None = None

        # Modules (seront chargés dynamiquement)
        self._modules: dict[str, any] = {}

        # Callbacks pour le reporting en temps réel
        self._on_finding: Callable[[Finding], None] | None = None
        self._on_host_discovered: Callable[[HostInfo], None] | None = None
        self._on_phase_change: Callable[[AuditPhase], None] | None = None

    def register_callback(
        self,
        event: str,
        callback: Callable
    ) -> None:
        """Enregistre un callback pour un événement"""
        if event == "finding":
            self._on_finding = callback
        elif event == "host_discovered":
            self._on_host_discovered = callback
        elif event == "phase_change":
            self._on_phase_change = callback

    async def run_audit(self, targets: list[str | AuditTarget]) -> AuditResult:
        """
        Lance un audit complet en mode discovery

        Args:
            targets: Liste de cibles (IP, ranges, hostnames, URLs)

        Returns:
            AuditResult contenant tous les résultats
        """
        # Initialisation
        self.result = AuditResult(
            id=str(uuid.uuid4()),
            name=self.config.name,
            config=self.config.__dict__,
        )

        # Normaliser les cibles
        normalized_targets = self._normalize_targets(targets)
        self.result.targets = normalized_targets

        console.print("\n[bold blue]╔══════════════════════════════════════════╗[/]")
        console.print("[bold blue]║       DISCOVERY AUDIT - Starting         ║[/]")
        console.print("[bold blue]╚══════════════════════════════════════════╝[/]\n")

        console.print(f"[cyan]Audit ID:[/] {self.result.id}")
        console.print(f"[cyan]Targets:[/] {len(normalized_targets)}")
        console.print(f"[cyan]Started:[/] {self.result.started_at.isoformat()}\n")

        try:
            # Phase 1: Reconnaissance
            await self._run_phase(
                AuditPhase.RECONNAISSANCE,
                self._phase_reconnaissance
            )

            # Phase 2: Network Scan
            if self.config.enable_network_scan:
                await self._run_phase(
                    AuditPhase.NETWORK_SCAN,
                    self._phase_network_scan
                )

            # Phase 3: Service Enumeration
            await self._run_phase(
                AuditPhase.SERVICE_ENUM,
                self._phase_service_enumeration
            )

            # Phase 4: Vulnerability Scan
            if self.config.enable_vuln_scan:
                await self._run_phase(
                    AuditPhase.VULN_SCAN,
                    self._phase_vulnerability_scan
                )

            # Phase 5: System Audit
            if self.config.enable_system_audit:
                await self._run_phase(
                    AuditPhase.SYSTEM_AUDIT,
                    self._phase_system_audit
                )

            # Phase 6: Web Audit
            if self.config.enable_web_audit:
                await self._run_phase(
                    AuditPhase.WEB_AUDIT,
                    self._phase_web_audit
                )

            # Phase 7: Analysis
            await self._run_phase(
                AuditPhase.ANALYSIS,
                self._phase_analysis
            )

            # Phase 8: Reporting
            await self._run_phase(
                AuditPhase.REPORTING,
                self._phase_reporting
            )

        except Exception as e:
            self.result.errors.append(f"Critical error: {str(e)}")
            console.print(f"[red]Critical error during audit: {e}[/]")

        # Finalisation
        self.result.completed_at = datetime.now()
        self.result.duration_seconds = (
            self.result.completed_at - self.result.started_at
        ).total_seconds()

        # Calcul du score final
        self.result.score = self.scoring_engine.calculate_score(self.result)

        self._print_summary()

        return self.result

    def _normalize_targets(self, targets: list[str | AuditTarget]) -> list[AuditTarget]:
        """Normalise les cibles en objets AuditTarget"""
        normalized = []

        for target in targets:
            if isinstance(target, AuditTarget):
                normalized.append(target)
            elif isinstance(target, str):
                target_type = self._detect_target_type(target)
                normalized.append(AuditTarget(
                    value=target,
                    target_type=target_type
                ))

        return normalized

    def _detect_target_type(self, target: str) -> TargetType:
        """Détecte le type d'une cible"""
        import re

        # URL
        if target.startswith(('http://', 'https://')):
            return TargetType.URL

        # IP range (CIDR)
        if '/' in target and re.match(r'^\d+\.\d+\.\d+\.\d+/\d+$', target):
            return TargetType.NETWORK

        # IP range (dash notation)
        if '-' in target and re.match(r'^\d+\.\d+\.\d+\.\d+-\d+$', target):
            return TargetType.IP_RANGE

        # Single IP
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', target):
            return TargetType.IP

        # Hostname
        return TargetType.HOSTNAME

    async def _run_phase(
        self,
        phase: AuditPhase,
        phase_func: Callable
    ) -> None:
        """Exécute une phase d'audit"""
        if not self.result:
            return

        self.result.current_phase = phase

        if self._on_phase_change:
            self._on_phase_change(phase)

        console.print(f"\n[bold yellow]▶ Phase: {phase.value.upper()}[/]")

        try:
            await phase_func()
            self.result.phases_completed.append(phase)
            console.print(f"[green]✓ Phase {phase.value} completed[/]")
        except Exception as e:
            self.result.errors.append(f"Error in {phase.value}: {str(e)}")
            console.print(f"[red]✗ Phase {phase.value} failed: {e}[/]")

    async def _phase_reconnaissance(self) -> None:
        """Phase de reconnaissance initiale"""
        if not self.result:
            return

        console.print("  [dim]Gathering initial information...[/]")

        # DNS resolution, WHOIS, etc.
        for target in self.result.targets:
            if target.target_type in [TargetType.HOSTNAME, TargetType.URL]:
                # Résolution DNS
                await self._resolve_dns(target.value)

    async def _resolve_dns(self, hostname: str) -> None:
        """Résout un hostname en IP"""
        import socket

        try:
            # Extraire le hostname de l'URL si nécessaire
            if hostname.startswith(('http://', 'https://')):
                from urllib.parse import urlparse
                hostname = urlparse(hostname).netloc

            ip = socket.gethostbyname(hostname)
            console.print(f"  [dim]Resolved {hostname} → {ip}[/]")
        except socket.gaierror:
            console.print(f"  [dim]Could not resolve {hostname}[/]")

    async def _phase_network_scan(self) -> None:
        """Phase de scan réseau avec Nmap"""
        if not self.result:
            return

        console.print("  [dim]Scanning network...[/]")

        # Import du module network scanner
        try:
            from ..modules.network_scanner import NetworkScanner

            scanner = NetworkScanner(self.config)
            targets = [t.value for t in self.result.targets]

            hosts = await scanner.scan(targets)

            for host in hosts:
                self.result.add_host(host)
                if self._on_host_discovered:
                    self._on_host_discovered(host)

            console.print(f"  [dim]Discovered {len(hosts)} hosts[/]")

        except ImportError:
            console.print("  [yellow]Network scanner module not available[/]")

    async def _phase_service_enumeration(self) -> None:
        """Phase d'énumération des services"""
        if not self.result:
            return

        console.print("  [dim]Enumerating services...[/]")

        total_services = sum(len(h.services) for h in self.result.hosts)
        console.print(f"  [dim]Found {total_services} services across {len(self.result.hosts)} hosts[/]")

    async def _phase_vulnerability_scan(self) -> None:
        """Phase de scan de vulnérabilités"""
        if not self.result:
            return

        console.print("  [dim]Scanning for vulnerabilities...[/]")

        # Import du module vuln scanner
        try:
            from ..modules.vuln_scanner import VulnScanner

            scanner = VulnScanner(self.config)
            findings = await scanner.scan(self.result.hosts)

            for finding in findings:
                self.result.add_finding(finding)
                if self._on_finding:
                    self._on_finding(finding)

            console.print(f"  [dim]Found {len(findings)} potential vulnerabilities[/]")

        except ImportError:
            console.print("  [yellow]Vulnerability scanner module not available[/]")

    async def _phase_system_audit(self) -> None:
        """Phase d'audit système"""
        if not self.result:
            return

        console.print("  [dim]Auditing system configurations...[/]")

        try:
            from ..modules.system_auditor import SystemAuditor

            auditor = SystemAuditor(self.config)
            findings = await auditor.audit(self.result.hosts)

            for finding in findings:
                self.result.add_finding(finding)
                if self._on_finding:
                    self._on_finding(finding)

            console.print(f"  [dim]Found {len(findings)} system issues[/]")

        except ImportError:
            console.print("  [yellow]System auditor module not available[/]")

    async def _phase_web_audit(self) -> None:
        """Phase d'audit web"""
        if not self.result:
            return

        console.print("  [dim]Auditing web applications...[/]")

        # Filtrer les cibles web
        web_targets = [
            t for t in self.result.targets
            if t.target_type == TargetType.URL
        ]

        # Ajouter les services web découverts
        for host in self.result.hosts:
            for service in host.services:
                if service.service_name in ['http', 'https', 'http-proxy']:
                    proto = 'https' if service.port == 443 else 'http'
                    url = f"{proto}://{host.ip}:{service.port}"
                    web_targets.append(AuditTarget(
                        value=url,
                        target_type=TargetType.URL
                    ))

        if not web_targets:
            console.print("  [dim]No web targets found[/]")
            return

        try:
            from ..modules.web_scanner import WebScanner

            scanner = WebScanner(self.config)
            findings = await scanner.scan(web_targets)

            for finding in findings:
                self.result.add_finding(finding)
                if self._on_finding:
                    self._on_finding(finding)

            console.print(f"  [dim]Found {len(findings)} web vulnerabilities[/]")

        except ImportError:
            console.print("  [yellow]Web scanner module not available[/]")

    async def _phase_analysis(self) -> None:
        """Phase d'analyse et corrélation"""
        if not self.result:
            return

        console.print("  [dim]Analyzing and correlating findings...[/]")

        # Détecter les faux positifs
        # Corréler les findings
        # Enrichir avec CVE/CVSS

        # TODO: Implémentation avancée

    async def _phase_reporting(self) -> None:
        """Phase de génération du rapport"""
        if not self.result:
            return

        console.print("  [dim]Generating reports...[/]")

        try:
            from ..reports.generator import ReportGenerator

            generator = ReportGenerator(self.config)
            await generator.generate(self.result)

        except ImportError:
            console.print("  [yellow]Report generator not available[/]")

    def _print_summary(self) -> None:
        """Affiche le résumé de l'audit"""
        if not self.result:
            return

        console.print("\n[bold blue]╔══════════════════════════════════════════╗[/]")
        console.print("[bold blue]║          AUDIT SUMMARY                   ║[/]")
        console.print("[bold blue]╚══════════════════════════════════════════╝[/]\n")

        # Score
        if self.result.score:
            score = self.result.score
            grade_color = {
                'A': 'green',
                'B': 'green',
                'C': 'yellow',
                'D': 'red',
                'F': 'red',
            }.get(score.grade, 'white')

            console.print(f"[bold]Overall Score:[/] [{grade_color}]{score.overall_score:.1f}/100 (Grade: {score.grade})[/]")
            console.print(f"[bold]Risk Level:[/] {score.risk_level}\n")

        # Findings par sévérité
        console.print("[bold]Findings:[/]")
        if self.result.score:
            console.print(f"  [red]Critical:[/] {self.result.score.critical_count}")
            console.print(f"  [orange1]High:[/] {self.result.score.high_count}")
            console.print(f"  [yellow]Medium:[/] {self.result.score.medium_count}")
            console.print(f"  [blue]Low:[/] {self.result.score.low_count}")
            console.print(f"  [dim]Info:[/] {self.result.score.info_count}")

        # Durée
        if self.result.duration_seconds:
            minutes = int(self.result.duration_seconds // 60)
            seconds = int(self.result.duration_seconds % 60)
            console.print(f"\n[bold]Duration:[/] {minutes}m {seconds}s")

        # Erreurs
        if self.result.errors:
            console.print(f"\n[yellow]Warnings/Errors:[/] {len(self.result.errors)}")

        console.print("")
