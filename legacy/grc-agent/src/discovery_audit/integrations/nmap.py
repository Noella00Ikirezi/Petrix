"""
Nmap Integration Wrapper
Enhanced Nmap integration with script support
"""

import asyncio
import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional, Any
from dataclasses import dataclass, field
from rich.console import Console

from ..core.models import HostInfo, ServiceInfo, Finding, Severity


console = Console()


@dataclass
class NmapConfig:
    """Nmap scanner configuration"""
    binary_path: Optional[str] = None
    timing: int = 4  # T0-T5
    default_scripts: list[str] = field(default_factory=lambda: ["default"])
    vuln_scripts: list[str] = field(default_factory=lambda: ["vuln", "vulners"])
    max_retries: int = 2
    host_timeout: int = 300
    min_rate: int = 100


class NmapWrapper:
    """
    Enhanced Nmap wrapper with vulnerability scanning
    """

    def __init__(self, config: Optional[NmapConfig] = None):
        self.config = config or NmapConfig()
        self._binary_path = self._find_nmap()

    def _find_nmap(self) -> Optional[str]:
        """Find Nmap binary"""
        if self.config.binary_path and os.path.exists(self.config.binary_path):
            return self.config.binary_path

        search_paths = [
            "/usr/bin/nmap",
            "/usr/local/bin/nmap",
            "/opt/homebrew/bin/nmap",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

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

        return None

    @property
    def is_available(self) -> bool:
        """Check if Nmap is available"""
        return self._binary_path is not None

    async def quick_scan(
        self,
        targets: list[str],
        ports: str = "22,80,443,445,3389,8080"
    ) -> list[HostInfo]:
        """
        Quick port scan

        Args:
            targets: List of targets
            ports: Ports to scan

        Returns:
            List of discovered hosts
        """
        return await self._run_scan(
            targets=targets,
            args=["-sT", "-p", ports, "-T4", "--open"],
        )

    async def full_scan(
        self,
        targets: list[str],
        with_scripts: bool = True
    ) -> list[HostInfo]:
        """
        Full port scan with service detection

        Args:
            targets: List of targets
            with_scripts: Run NSE scripts

        Returns:
            List of discovered hosts
        """
        args = [
            "-sS",  # SYN scan
            "-sV",  # Version detection
            "-p-",  # All ports
            f"-T{self.config.timing}",
            "--open",
            f"--host-timeout", str(self.config.host_timeout),
        ]

        if with_scripts:
            args.extend(["--script", ",".join(self.config.default_scripts)])

        return await self._run_scan(targets=targets, args=args)

    async def vuln_scan(
        self,
        targets: list[str],
        ports: str = None
    ) -> tuple[list[HostInfo], list[Finding]]:
        """
        Vulnerability scan using NSE scripts

        Args:
            targets: List of targets
            ports: Specific ports to scan

        Returns:
            Tuple of (hosts, findings)
        """
        args = [
            "-sV",
            f"-T{self.config.timing}",
            "--open",
            "--script", ",".join(self.config.vuln_scripts),
        ]

        if ports:
            args.extend(["-p", ports])
        else:
            args.extend(["-p", "21,22,23,25,80,110,143,443,445,993,995,1433,3306,3389,5432,5900,8080"])

        hosts = await self._run_scan(targets=targets, args=args)
        findings = self._extract_vuln_findings(hosts)

        return hosts, findings

    async def os_scan(self, targets: list[str]) -> list[HostInfo]:
        """
        OS detection scan

        Args:
            targets: List of targets

        Returns:
            List of hosts with OS info
        """
        return await self._run_scan(
            targets=targets,
            args=["-O", "-sV", f"-T{self.config.timing}", "--open"],
        )

    async def udp_scan(
        self,
        targets: list[str],
        ports: str = "53,67,123,161,500"
    ) -> list[HostInfo]:
        """
        UDP port scan

        Args:
            targets: List of targets
            ports: UDP ports to scan

        Returns:
            List of discovered hosts
        """
        return await self._run_scan(
            targets=targets,
            args=["-sU", "-p", ports, f"-T{self.config.timing}", "--open"],
        )

    async def _run_scan(
        self,
        targets: list[str],
        args: list[str]
    ) -> list[HostInfo]:
        """
        Run Nmap scan with specified arguments

        Args:
            targets: List of targets
            args: Nmap arguments

        Returns:
            List of discovered hosts
        """
        if not self._binary_path:
            console.print("[yellow]Nmap not found. Skipping scan.[/]")
            return []

        # Build command
        cmd = [self._binary_path, "-oX", "-"] + args + targets

        console.print(f"[dim]Running: {' '.join(cmd[:5])}...[/]")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.host_timeout * len(targets)
            )

            if process.returncode != 0:
                console.print(f"[yellow]Nmap warning: {stderr.decode()[:200]}[/]")

            return self._parse_xml(stdout.decode())

        except asyncio.TimeoutError:
            console.print("[yellow]Nmap scan timed out[/]")
            return []
        except Exception as e:
            console.print(f"[red]Nmap scan failed: {e}[/]")
            return []

    def _parse_xml(self, xml_output: str) -> list[HostInfo]:
        """Parse Nmap XML output"""
        hosts = []

        try:
            root = ET.fromstring(xml_output)

            for host_elem in root.findall('.//host'):
                host = self._parse_host(host_elem)
                if host:
                    hosts.append(host)

        except ET.ParseError as e:
            console.print(f"[yellow]XML parse error: {e}[/]")

        return hosts

    def _parse_host(self, host_elem: ET.Element) -> Optional[HostInfo]:
        """Parse a host element from Nmap XML"""
        # Check if host is up
        status = host_elem.find('status')
        if status is None or status.get('state') != 'up':
            return None

        # Get IP address
        address = host_elem.find("address[@addrtype='ipv4']")
        if address is None:
            address = host_elem.find("address[@addrtype='ipv6']")
        if address is None:
            return None

        ip = address.get('addr', '')

        # Get MAC
        mac_elem = host_elem.find("address[@addrtype='mac']")
        mac = mac_elem.get('addr') if mac_elem is not None else None

        # Get hostname
        hostname = None
        hostnames = host_elem.find('hostnames')
        if hostnames is not None:
            hostname_elem = hostnames.find('hostname')
            if hostname_elem is not None:
                hostname = hostname_elem.get('name')

        # Get OS
        os_guess = None
        os_accuracy = None
        os_elem = host_elem.find('.//osmatch')
        if os_elem is not None:
            os_guess = os_elem.get('name')
            os_accuracy = int(os_elem.get('accuracy', 0))

        # Get services
        services = []
        ports = host_elem.find('ports')
        if ports is not None:
            for port_elem in ports.findall('port'):
                service = self._parse_port(port_elem)
                if service:
                    services.append(service)

        # Get script output
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

    def _parse_port(self, port_elem: ET.Element) -> Optional[ServiceInfo]:
        """Parse a port element from Nmap XML"""
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

    def _extract_vuln_findings(self, hosts: list[HostInfo]) -> list[Finding]:
        """Extract vulnerability findings from NSE script output"""
        findings = []

        # Known vulnerability script patterns
        vuln_patterns = {
            "smb-vuln-ms17-010": {
                "title": "MS17-010 (EternalBlue)",
                "cves": ["CVE-2017-0143"],
                "severity": Severity.CRITICAL,
                "indicator": "VULNERABLE",
            },
            "smb-vuln-ms08-067": {
                "title": "MS08-067 (Conficker)",
                "cves": ["CVE-2008-4250"],
                "severity": Severity.CRITICAL,
                "indicator": "VULNERABLE",
            },
            "ssl-heartbleed": {
                "title": "Heartbleed",
                "cves": ["CVE-2014-0160"],
                "severity": Severity.CRITICAL,
                "indicator": "VULNERABLE",
            },
            "ssl-poodle": {
                "title": "POODLE SSL vulnerability",
                "cves": ["CVE-2014-3566"],
                "severity": Severity.MEDIUM,
                "indicator": "VULNERABLE",
            },
            "http-shellshock": {
                "title": "Shellshock",
                "cves": ["CVE-2014-6271"],
                "severity": Severity.CRITICAL,
                "indicator": "VULNERABLE",
            },
        }

        for host in hosts:
            for script_id, output in host.scripts_output.items():
                if script_id in vuln_patterns:
                    pattern = vuln_patterns[script_id]
                    if pattern["indicator"] in output.upper():
                        findings.append(Finding(
                            id=f"NMAP-{script_id.upper()}-{host.ip}",
                            title=pattern["title"],
                            description=f"Nmap NSE script detected {pattern['title']} vulnerability",
                            severity=pattern["severity"],
                            category="vulnerability",
                            target=host.ip,
                            cve_ids=pattern["cves"],
                            evidence=output[:500],
                            remediation="Apply vendor patches immediately",
                            discovered_by="nmap",
                        ))

                # Check vulners script output for CVEs
                if script_id == "vulners" and output:
                    vulners_findings = self._parse_vulners_output(host.ip, output)
                    findings.extend(vulners_findings)

        return findings

    def _parse_vulners_output(self, ip: str, output: str) -> list[Finding]:
        """Parse vulners script output for CVEs"""
        findings = []

        # Vulners output format:
        # CVE-XXXX-YYYY  CVSS_SCORE  URL

        for line in output.split('\n'):
            if 'CVE-' in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    cve_id = parts[0]
                    try:
                        cvss = float(parts[1])

                        if cvss >= 9.0:
                            severity = Severity.CRITICAL
                        elif cvss >= 7.0:
                            severity = Severity.HIGH
                        elif cvss >= 4.0:
                            severity = Severity.MEDIUM
                        else:
                            severity = Severity.LOW

                        # Only report high/critical for noise reduction
                        if cvss >= 7.0:
                            findings.append(Finding(
                                id=f"NMAP-VULNERS-{cve_id}-{ip}",
                                title=f"Potential vulnerability: {cve_id}",
                                description=f"Vulners database indicates potential {cve_id} vulnerability",
                                severity=severity,
                                category="vulnerability",
                                target=ip,
                                cve_ids=[cve_id],
                                cvss_score=cvss,
                                evidence=line,
                                remediation="Verify and apply vendor patches",
                                discovered_by="nmap-vulners",
                                confidence=0.7,  # Vulners results need verification
                            ))

                    except ValueError:
                        continue

        return findings
