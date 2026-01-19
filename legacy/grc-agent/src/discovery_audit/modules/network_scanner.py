"""
Network Scanner Module
Scan réseau avec intégration Nmap pour découvrir les hôtes et services
"""

import asyncio
import subprocess
import xml.etree.ElementTree as ET
from typing import Any
from rich.console import Console

from ..core.models import (
    AuditConfig,
    HostInfo,
    ServiceInfo,
    Finding,
    Severity,
)


console = Console()


class NetworkScanner:
    """
    Scanner réseau basé sur Nmap
    Découvre les hôtes, ports ouverts, services et versions
    """

    def __init__(self, config: AuditConfig):
        self.config = config
        self._nmap_path = self._find_nmap()

    def _find_nmap(self) -> str | None:
        """Trouve le chemin de Nmap"""
        try:
            result = subprocess.run(
                ["which", "nmap"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Chemins communs
        common_paths = [
            "/usr/bin/nmap",
            "/usr/local/bin/nmap",
            "/opt/homebrew/bin/nmap",
        ]
        for path in common_paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True)
                if result.returncode == 0:
                    return path
            except Exception:
                continue

        return None

    async def scan(self, targets: list[str]) -> list[HostInfo]:
        """
        Effectue un scan réseau sur les cibles

        Args:
            targets: Liste d'IPs, ranges ou hostnames

        Returns:
            Liste des hôtes découverts avec leurs services
        """
        if not self._nmap_path:
            console.print("  [yellow]Warning: Nmap not found, using fallback scanner[/]")
            return await self._fallback_scan(targets)

        hosts = []

        for target in targets:
            try:
                host_results = await self._scan_target(target)
                hosts.extend(host_results)
            except Exception as e:
                console.print(f"  [red]Error scanning {target}: {e}[/]")

        return hosts

    async def _scan_target(self, target: str) -> list[HostInfo]:
        """Scanne une cible spécifique avec Nmap"""
        # Construire la commande Nmap
        cmd = self._build_nmap_command(target)

        console.print(f"  [dim]Scanning {target}...[/]")

        # Exécuter Nmap
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.config.timeout_per_host
        )

        if process.returncode != 0:
            raise Exception(f"Nmap failed: {stderr.decode()}")

        # Parser le XML
        return self._parse_nmap_xml(stdout.decode())

    def _build_nmap_command(self, target: str) -> list[str]:
        """Construit la commande Nmap"""
        cmd = [self._nmap_path]

        # Output XML
        cmd.extend(["-oX", "-"])

        # Détection de version
        cmd.append("-sV")

        # Détection OS (si agressif)
        if self.config.scan_aggressive:
            cmd.append("-O")
            cmd.append("-A")

        # Ports
        if self.config.scan_ports == "full":
            cmd.extend(["-p", "1-65535"])
        else:
            cmd.extend(["-p", self.config.scan_ports])

        # UDP (optionnel, plus lent)
        if self.config.scan_udp:
            cmd.append("-sU")

        # Scripts NSE basiques
        cmd.append("--script=default,vuln")

        # Timing (T4 = aggressive)
        cmd.append("-T4")

        # Cible
        cmd.append(target)

        return cmd

    def _parse_nmap_xml(self, xml_output: str) -> list[HostInfo]:
        """Parse le XML Nmap et retourne les hôtes"""
        hosts = []

        try:
            root = ET.fromstring(xml_output)

            for host_elem in root.findall('.//host'):
                host = self._parse_host_element(host_elem)
                if host:
                    hosts.append(host)

        except ET.ParseError as e:
            console.print(f"  [red]Error parsing Nmap XML: {e}[/]")

        return hosts

    def _parse_host_element(self, host_elem: ET.Element) -> HostInfo | None:
        """Parse un élément host XML"""
        # État de l'hôte
        status = host_elem.find('status')
        if status is None or status.get('state') != 'up':
            return None

        # Adresse IP
        address = host_elem.find("address[@addrtype='ipv4']")
        if address is None:
            address = host_elem.find("address[@addrtype='ipv6']")
        if address is None:
            return None

        ip = address.get('addr', '')

        # Adresse MAC
        mac_elem = host_elem.find("address[@addrtype='mac']")
        mac = mac_elem.get('addr') if mac_elem is not None else None

        # Hostname
        hostname = None
        hostnames = host_elem.find('hostnames')
        if hostnames is not None:
            hostname_elem = hostnames.find('hostname')
            if hostname_elem is not None:
                hostname = hostname_elem.get('name')

        # OS Detection
        os_guess = None
        os_accuracy = None
        os_elem = host_elem.find('.//osmatch')
        if os_elem is not None:
            os_guess = os_elem.get('name')
            os_accuracy = int(os_elem.get('accuracy', 0))

        # Services/Ports
        services = []
        ports = host_elem.find('ports')
        if ports is not None:
            for port_elem in ports.findall('port'):
                service = self._parse_port_element(port_elem)
                if service:
                    services.append(service)

        # Scripts output
        scripts_output = {}
        for script in host_elem.findall('.//script'):
            script_id = script.get('id', 'unknown')
            script_output = script.get('output', '')
            scripts_output[script_id] = script_output

        return HostInfo(
            ip=ip,
            hostname=hostname,
            mac_address=mac,
            os_guess=os_guess,
            os_accuracy=os_accuracy,
            state='up',
            services=services,
            scripts_output=scripts_output,
        )

    def _parse_port_element(self, port_elem: ET.Element) -> ServiceInfo | None:
        """Parse un élément port XML"""
        state = port_elem.find('state')
        if state is None or state.get('state') != 'open':
            return None

        port = int(port_elem.get('portid', 0))
        protocol = port_elem.get('protocol', 'tcp')

        service = port_elem.find('service')
        service_name = None
        version = None
        product = None
        extra_info = None
        cpe = []

        if service is not None:
            service_name = service.get('name')
            version = service.get('version')
            product = service.get('product')
            extra_info = service.get('extrainfo')

            for cpe_elem in service.findall('cpe'):
                if cpe_elem.text:
                    cpe.append(cpe_elem.text)

        return ServiceInfo(
            port=port,
            protocol=protocol,
            state='open',
            service_name=service_name,
            version=version,
            product=product,
            extra_info=extra_info,
            cpe=cpe,
        )

    async def _fallback_scan(self, targets: list[str]) -> list[HostInfo]:
        """
        Scanner de fallback sans Nmap
        Utilise des sockets Python basiques
        """
        import socket

        hosts = []
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 3306, 3389, 5432, 8080, 8443]

        for target in targets:
            console.print(f"  [dim]Fallback scanning {target}...[/]")

            # Résoudre le hostname
            try:
                ip = socket.gethostbyname(target)
            except socket.gaierror:
                ip = target

            services = []

            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    sock.close()

                    if result == 0:
                        services.append(ServiceInfo(
                            port=port,
                            protocol='tcp',
                            state='open',
                            service_name=self._guess_service(port),
                        ))
                except Exception:
                    continue

            if services:
                hosts.append(HostInfo(
                    ip=ip,
                    hostname=target if target != ip else None,
                    services=services,
                ))

        return hosts

    def _guess_service(self, port: int) -> str:
        """Devine le service basé sur le port"""
        port_services = {
            21: 'ftp',
            22: 'ssh',
            23: 'telnet',
            25: 'smtp',
            53: 'dns',
            80: 'http',
            110: 'pop3',
            143: 'imap',
            443: 'https',
            445: 'microsoft-ds',
            993: 'imaps',
            995: 'pop3s',
            3306: 'mysql',
            3389: 'ms-wbt-server',
            5432: 'postgresql',
            8080: 'http-proxy',
            8443: 'https-alt',
        }
        return port_services.get(port, 'unknown')

    def analyze_findings(self, hosts: list[HostInfo]) -> list[Finding]:
        """
        Analyse les résultats du scan et génère des findings

        Détecte:
        - Ports dangereux ouverts
        - Services obsolètes
        - Configurations risquées
        """
        findings = []

        dangerous_ports = {
            21: ("FTP ouvert", "FTP transmet les identifiants en clair"),
            23: ("Telnet ouvert", "Telnet est non chiffré et obsolète"),
            445: ("SMB exposé", "SMB peut être vulnérable à des attaques"),
            3389: ("RDP exposé", "RDP est souvent ciblé par les attaquants"),
        }

        for host in hosts:
            for service in host.services:
                # Ports dangereux
                if service.port in dangerous_ports:
                    title, desc = dangerous_ports[service.port]
                    findings.append(Finding(
                        id=f"NET-{host.ip}-{service.port}",
                        title=title,
                        description=desc,
                        severity=Severity.MEDIUM if service.port in [21, 23] else Severity.HIGH,
                        category="network",
                        target=host.ip,
                        port=service.port,
                        service=service.service_name,
                        protocol=service.protocol,
                        remediation=f"Désactiver ou restreindre l'accès au port {service.port}",
                        discovered_by="network_scanner",
                    ))

                # Services obsolètes
                if service.version:
                    version_finding = self._check_outdated_version(
                        host, service
                    )
                    if version_finding:
                        findings.append(version_finding)

        return findings

    def _check_outdated_version(
        self,
        host: HostInfo,
        service: ServiceInfo
    ) -> Finding | None:
        """Vérifie si un service a une version obsolète"""
        # Liste simplifiée - en production, utiliser une base de données
        outdated = {
            'openssh': ['5.', '6.', '7.0', '7.1', '7.2'],
            'apache': ['2.2.', '2.4.0', '2.4.1', '2.4.2'],
            'nginx': ['1.0.', '1.1.', '1.2.', '1.3.'],
            'mysql': ['5.5.', '5.6.'],
        }

        if not service.product or not service.version:
            return None

        product_lower = service.product.lower()

        for product_name, old_versions in outdated.items():
            if product_name in product_lower:
                for old_ver in old_versions:
                    if service.version.startswith(old_ver):
                        return Finding(
                            id=f"NET-OUTDATED-{host.ip}-{service.port}",
                            title=f"Service obsolète: {service.product}",
                            description=f"{service.product} version {service.version} est obsolète et peut contenir des vulnérabilités connues",
                            severity=Severity.MEDIUM,
                            category="network",
                            target=host.ip,
                            port=service.port,
                            service=service.service_name,
                            remediation=f"Mettre à jour {service.product} vers la dernière version stable",
                            discovered_by="network_scanner",
                        )

        return None
