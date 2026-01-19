"""
Metasploit Integration
Integration with Metasploit Framework for vulnerability validation
"""

import asyncio
import json
from typing import Optional, Any
from dataclasses import dataclass
from rich.console import Console

from ..core.models import Finding, Severity, HostInfo


console = Console()


@dataclass
class MetasploitConfig:
    """Metasploit RPC configuration"""
    host: str = "127.0.0.1"
    port: int = 55553
    username: str = "msf"
    password: str = "msf"
    ssl: bool = True


class MetasploitIntegration:
    """
    Integration with Metasploit Framework via RPC API

    Used for:
    - Vulnerability validation
    - Safe exploit checking
    - Auxiliary module scanning
    """

    def __init__(self, config: Optional[MetasploitConfig] = None):
        self.config = config or MetasploitConfig()
        self._client: Any = None
        self._token: Optional[str] = None

    async def connect(self) -> bool:
        """
        Connect to Metasploit RPC server

        Returns:
            True if connection successful
        """
        try:
            from pymetasploit3.msfrpc import MsfRpcClient
        except ImportError:
            console.print("[yellow]pymetasploit3 not installed. Install with: pip install pymetasploit3[/]")
            return False

        try:
            self._client = MsfRpcClient(
                self.config.password,
                server=self.config.host,
                port=self.config.port,
                ssl=self.config.ssl,
            )

            console.print(f"[green]Connected to Metasploit RPC at {self.config.host}:{self.config.port}[/]")
            return True

        except Exception as e:
            console.print(f"[red]Failed to connect to Metasploit: {e}[/]")
            return False

    async def disconnect(self):
        """Disconnect from Metasploit"""
        if self._client:
            try:
                self._client.logout()
            except Exception:
                pass
            self._client = None

    async def search_modules(
        self,
        search_term: str,
        module_type: str = "exploit"
    ) -> list[dict]:
        """
        Search for Metasploit modules

        Args:
            search_term: Search query (e.g., "apache", "smb")
            module_type: Module type (exploit, auxiliary, post)

        Returns:
            List of matching modules
        """
        if not self._client:
            return []

        try:
            modules = self._client.modules.search(search_term)
            return [
                m for m in modules
                if m.get("type") == module_type
            ]
        except Exception as e:
            console.print(f"[yellow]Module search failed: {e}[/]")
            return []

    async def validate_vulnerability(
        self,
        host: str,
        port: int,
        module_name: str,
        options: dict = None
    ) -> dict:
        """
        Validate a vulnerability using a Metasploit module

        Args:
            host: Target host
            port: Target port
            module_name: Module name (e.g., "auxiliary/scanner/smb/smb_ms17_010")
            options: Additional module options

        Returns:
            Validation result
        """
        if not self._client:
            return {"success": False, "error": "Not connected"}

        try:
            # Get the module
            module = self._client.modules.use("auxiliary", module_name)

            # Set options
            module["RHOSTS"] = host
            module["RPORT"] = port

            if options:
                for key, value in options.items():
                    module[key] = value

            # Run the module
            console.print(f"[dim]Running {module_name} against {host}:{port}...[/]")

            job_id = module.execute()

            # Wait for completion (with timeout)
            await asyncio.sleep(10)  # Give it time to run

            # Get results from console
            console_id = self._client.consoles.console().cid
            output = self._client.consoles.console(console_id).read()

            return {
                "success": True,
                "job_id": job_id,
                "output": output.get("data", ""),
                "vulnerable": self._check_vuln_output(output.get("data", "")),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _check_vuln_output(self, output: str) -> bool:
        """Check if output indicates vulnerability"""
        vuln_indicators = [
            "is vulnerable",
            "VULNERABLE",
            "vulnerable to",
            "exploitable",
            "[+]",
        ]

        return any(indicator in output for indicator in vuln_indicators)

    async def run_auxiliary_scan(
        self,
        hosts: list[str],
        module_name: str,
        options: dict = None
    ) -> list[Finding]:
        """
        Run an auxiliary scanner module against multiple hosts

        Args:
            hosts: List of target hosts
            module_name: Auxiliary module name
            options: Additional options

        Returns:
            List of findings
        """
        findings = []

        if not self._client:
            return findings

        try:
            module = self._client.modules.use("auxiliary", module_name)

            # Set hosts
            module["RHOSTS"] = " ".join(hosts)

            if options:
                for key, value in options.items():
                    module[key] = value

            # Execute
            job_id = module.execute()

            # Wait and collect results
            await asyncio.sleep(30)

            # Parse output for findings
            # This is simplified - real implementation would parse module output

        except Exception as e:
            console.print(f"[yellow]Auxiliary scan failed: {e}[/]")

        return findings

    async def check_eternalblue(self, host: str) -> Optional[Finding]:
        """
        Check for MS17-010 (EternalBlue) vulnerability

        Args:
            host: Target host

        Returns:
            Finding if vulnerable, None otherwise
        """
        result = await self.validate_vulnerability(
            host=host,
            port=445,
            module_name="auxiliary/scanner/smb/smb_ms17_010",
        )

        if result.get("vulnerable"):
            return Finding(
                id=f"MSF-MS17-010-{host}",
                title="MS17-010 EternalBlue Vulnerability",
                description="Host is vulnerable to MS17-010 (EternalBlue). This vulnerability allows remote code execution.",
                severity=Severity.CRITICAL,
                category="vulnerability",
                target=host,
                port=445,
                service="smb",
                cve_ids=["CVE-2017-0143", "CVE-2017-0144", "CVE-2017-0145"],
                cvss_score=9.8,
                evidence=result.get("output", "")[:500],
                remediation="Apply MS17-010 security update and disable SMBv1",
                discovered_by="metasploit",
            )

        return None

    async def check_bluekeep(self, host: str) -> Optional[Finding]:
        """
        Check for BlueKeep (CVE-2019-0708) vulnerability

        Args:
            host: Target host

        Returns:
            Finding if vulnerable, None otherwise
        """
        result = await self.validate_vulnerability(
            host=host,
            port=3389,
            module_name="auxiliary/scanner/rdp/cve_2019_0708_bluekeep",
        )

        if result.get("vulnerable"):
            return Finding(
                id=f"MSF-BLUEKEEP-{host}",
                title="BlueKeep (CVE-2019-0708) Vulnerability",
                description="Host is vulnerable to BlueKeep. This RDP vulnerability allows remote code execution.",
                severity=Severity.CRITICAL,
                category="vulnerability",
                target=host,
                port=3389,
                service="rdp",
                cve_ids=["CVE-2019-0708"],
                cvss_score=9.8,
                evidence=result.get("output", "")[:500],
                remediation="Apply security update or disable RDP if not needed",
                discovered_by="metasploit",
            )

        return None

    async def validate_findings(
        self,
        findings: list[Finding],
        hosts: list[HostInfo]
    ) -> list[Finding]:
        """
        Validate existing findings using Metasploit

        Args:
            findings: List of findings to validate
            hosts: List of hosts with services

        Returns:
            Updated findings list with validation results
        """
        if not self._client:
            return findings

        # Map CVEs to Metasploit modules
        cve_modules = {
            "CVE-2017-0143": "auxiliary/scanner/smb/smb_ms17_010",
            "CVE-2019-0708": "auxiliary/scanner/rdp/cve_2019_0708_bluekeep",
            "CVE-2021-41773": "auxiliary/scanner/http/apache_normalize_path",
            "CVE-2021-44228": "auxiliary/scanner/http/log4shell_scanner",
        }

        for finding in findings:
            for cve_id in finding.cve_ids:
                if cve_id in cve_modules:
                    result = await self.validate_vulnerability(
                        host=finding.target,
                        port=finding.port or 0,
                        module_name=cve_modules[cve_id],
                    )

                    if result.get("vulnerable"):
                        finding.confidence = 1.0
                        finding.evidence += f"\n\nValidated by Metasploit: {result.get('output', '')[:200]}"
                    elif result.get("success"):
                        finding.confidence = 0.5

        return findings

    def get_available_modules(self, module_type: str = "auxiliary") -> list[str]:
        """
        Get list of available modules

        Args:
            module_type: Type of modules to list

        Returns:
            List of module names
        """
        if not self._client:
            return []

        try:
            return self._client.modules.list.get(module_type, [])
        except Exception:
            return []

    @staticmethod
    def cve_to_module(cve_id: str) -> Optional[str]:
        """
        Map a CVE ID to a Metasploit module

        Args:
            cve_id: CVE identifier

        Returns:
            Module name if found
        """
        # This would ideally query Metasploit's database
        # For now, maintain a static mapping of common CVEs
        mappings = {
            "CVE-2017-0143": "exploit/windows/smb/ms17_010_eternalblue",
            "CVE-2017-0144": "exploit/windows/smb/ms17_010_eternalblue",
            "CVE-2019-0708": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
            "CVE-2021-44228": "exploit/multi/http/log4shell_header_injection",
            "CVE-2021-41773": "exploit/multi/http/apache_normalize_path_rce",
            "CVE-2021-42013": "exploit/multi/http/apache_normalize_path_rce",
            "CVE-2020-1472": "exploit/windows/smb/zerologon",
            "CVE-2014-6271": "exploit/multi/http/apache_mod_cgi_bash_env_exec",
            "CVE-2017-5638": "exploit/multi/http/struts2_content_type_ognl",
        }

        return mappings.get(cve_id)
