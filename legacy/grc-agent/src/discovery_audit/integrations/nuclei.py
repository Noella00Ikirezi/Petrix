"""
Nuclei Integration
High-performance vulnerability scanner integration
"""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Optional, Any
from dataclasses import dataclass, field
from rich.console import Console

from ..core.models import Finding, Severity


console = Console()


@dataclass
class NucleiConfig:
    """Nuclei scanner configuration"""
    binary_path: Optional[str] = None
    templates_path: Optional[str] = None
    rate_limit: int = 150
    bulk_size: int = 25
    concurrency: int = 25
    timeout: int = 10
    retries: int = 1
    severity_filter: list[str] = field(default_factory=lambda: ["critical", "high", "medium", "low"])
    exclude_tags: list[str] = field(default_factory=list)
    include_tags: list[str] = field(default_factory=list)


class NucleiScanner:
    """
    Nuclei vulnerability scanner integration

    Nuclei is a fast and customizable vulnerability scanner based on
    simple YAML templates.
    """

    def __init__(self, config: Optional[NucleiConfig] = None):
        self.config = config or NucleiConfig()
        self._binary_path = self._find_nuclei()

    def _find_nuclei(self) -> Optional[str]:
        """Find Nuclei binary"""
        if self.config.binary_path and os.path.exists(self.config.binary_path):
            return self.config.binary_path

        # Check common paths
        search_paths = [
            "/usr/bin/nuclei",
            "/usr/local/bin/nuclei",
            "/opt/homebrew/bin/nuclei",
            os.path.expanduser("~/go/bin/nuclei"),
            os.path.expanduser("~/.local/bin/nuclei"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        # Try which
        try:
            result = subprocess.run(
                ["which", "nuclei"],
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
        """Check if Nuclei is available"""
        return self._binary_path is not None

    async def update_templates(self) -> bool:
        """
        Update Nuclei templates

        Returns:
            True if successful
        """
        if not self._binary_path:
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                self._binary_path, "-update-templates",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()
            return process.returncode == 0

        except Exception as e:
            console.print(f"[yellow]Template update failed: {e}[/]")
            return False

    async def scan(
        self,
        targets: list[str],
        templates: list[str] = None,
        tags: list[str] = None,
        severity: list[str] = None,
    ) -> list[Finding]:
        """
        Run Nuclei scan against targets

        Args:
            targets: List of target URLs/hosts
            templates: Specific templates to use
            tags: Template tags to filter
            severity: Severity levels to include

        Returns:
            List of findings
        """
        if not self._binary_path:
            console.print("[yellow]Nuclei not found. Skipping scan.[/]")
            return []

        findings = []

        # Create temporary file with targets
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(targets))
            targets_file = f.name

        # Create temporary file for output
        output_file = tempfile.mktemp(suffix='.json')

        try:
            # Build command
            cmd = [
                self._binary_path,
                "-l", targets_file,
                "-json-export", output_file,
                "-silent",
                "-rate-limit", str(self.config.rate_limit),
                "-bulk-size", str(self.config.bulk_size),
                "-c", str(self.config.concurrency),
                "-timeout", str(self.config.timeout),
                "-retries", str(self.config.retries),
            ]

            # Add severity filter
            severities = severity or self.config.severity_filter
            if severities:
                cmd.extend(["-severity", ",".join(severities)])

            # Add template filters
            if templates:
                for template in templates:
                    cmd.extend(["-t", template])
            elif self.config.templates_path:
                cmd.extend(["-t", self.config.templates_path])

            if tags:
                cmd.extend(["-tags", ",".join(tags)])
            elif self.config.include_tags:
                cmd.extend(["-tags", ",".join(self.config.include_tags)])

            if self.config.exclude_tags:
                cmd.extend(["-exclude-tags", ",".join(self.config.exclude_tags)])

            console.print(f"[dim]Running Nuclei scan on {len(targets)} targets...[/]")

            # Execute
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=3600  # 1 hour timeout
            )

            # Parse results
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                result = json.loads(line)
                                finding = self._parse_result(result)
                                if finding:
                                    findings.append(finding)
                            except json.JSONDecodeError:
                                continue

            console.print(f"[dim]Nuclei found {len(findings)} issues[/]")

        except asyncio.TimeoutError:
            console.print("[yellow]Nuclei scan timed out[/]")
        except Exception as e:
            console.print(f"[red]Nuclei scan failed: {e}[/]")
        finally:
            # Cleanup
            if os.path.exists(targets_file):
                os.unlink(targets_file)
            if os.path.exists(output_file):
                os.unlink(output_file)

        return findings

    def _parse_result(self, result: dict) -> Optional[Finding]:
        """Parse a Nuclei result into a Finding"""
        try:
            info = result.get("info", {})
            classification = info.get("classification", {})

            # Map severity
            severity_map = {
                "critical": Severity.CRITICAL,
                "high": Severity.HIGH,
                "medium": Severity.MEDIUM,
                "low": Severity.LOW,
                "info": Severity.INFO,
            }

            severity_str = info.get("severity", "info").lower()
            severity = severity_map.get(severity_str, Severity.INFO)

            # Extract CVEs
            cve_ids = []
            cve_id = classification.get("cve-id")
            if cve_id:
                if isinstance(cve_id, list):
                    cve_ids = cve_id
                else:
                    cve_ids = [cve_id]

            # Get CVSS score
            cvss_score = None
            cvss_metrics = classification.get("cvss-metrics")
            if cvss_metrics:
                try:
                    cvss_score = float(classification.get("cvss-score", 0))
                except (ValueError, TypeError):
                    pass

            return Finding(
                id=f"NUCLEI-{result.get('template-id', 'unknown')}-{result.get('matched-at', '')[:50]}",
                title=info.get("name", "Unknown vulnerability"),
                description=info.get("description", result.get("template-id", "")),
                severity=severity,
                category="web",
                target=result.get("host", result.get("matched-at", "")),
                cve_ids=cve_ids,
                cvss_score=cvss_score,
                evidence=result.get("matched-at", ""),
                remediation=info.get("remediation", "See references"),
                references=info.get("reference", []),
                discovered_by="nuclei",
            )

        except Exception:
            return None

    async def scan_cves(
        self,
        targets: list[str],
        cve_ids: list[str]
    ) -> list[Finding]:
        """
        Scan for specific CVEs

        Args:
            targets: List of targets
            cve_ids: List of CVE IDs to check

        Returns:
            List of findings
        """
        # Nuclei has CVE tags for templates
        cve_tags = [f"cve-{cve.lower().replace('cve-', '')}" for cve in cve_ids]

        return await self.scan(
            targets=targets,
            tags=cve_tags,
        )

    async def scan_technologies(
        self,
        targets: list[str],
        technologies: list[str]
    ) -> list[Finding]:
        """
        Scan based on detected technologies

        Args:
            targets: List of targets
            technologies: List of technology names (e.g., ["apache", "nginx", "wordpress"])

        Returns:
            List of findings
        """
        return await self.scan(
            targets=targets,
            tags=technologies,
        )

    async def run_template(
        self,
        targets: list[str],
        template_path: str
    ) -> list[Finding]:
        """
        Run a specific Nuclei template

        Args:
            targets: List of targets
            template_path: Path to template file

        Returns:
            List of findings
        """
        return await self.scan(
            targets=targets,
            templates=[template_path],
        )

    def get_template_count(self) -> int:
        """Get count of installed templates"""
        if not self._binary_path:
            return 0

        try:
            result = subprocess.run(
                [self._binary_path, "-tl"],
                capture_output=True,
                text=True,
                timeout=30
            )

            return len(result.stdout.strip().split('\n'))

        except Exception:
            return 0

    async def scan_exposed_panels(self, targets: list[str]) -> list[Finding]:
        """Scan for exposed admin panels and login pages"""
        return await self.scan(
            targets=targets,
            tags=["panel", "login", "admin"],
            severity=["info", "low", "medium", "high", "critical"],
        )

    async def scan_misconfigurations(self, targets: list[str]) -> list[Finding]:
        """Scan for security misconfigurations"""
        return await self.scan(
            targets=targets,
            tags=["misconfig", "misconfiguration", "exposure"],
        )

    async def scan_takeovers(self, targets: list[str]) -> list[Finding]:
        """Scan for subdomain takeover vulnerabilities"""
        return await self.scan(
            targets=targets,
            tags=["takeover"],
        )
