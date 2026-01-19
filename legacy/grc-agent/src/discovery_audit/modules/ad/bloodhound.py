"""
BloodHound Integration
Integration with BloodHound for AD attack path analysis
"""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Optional, Any
from dataclasses import dataclass
from rich.console import Console

from ...core.models import AuditConfig, Finding, Severity
from ...platform.executor import CommandExecutor, LocalExecutor


console = Console()


@dataclass
class BloodHoundConfig:
    """BloodHound configuration"""
    sharphound_path: Optional[str] = None
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "bloodhound"
    output_dir: str = "./bloodhound"


class BloodHoundIntegration:
    """
    BloodHound integration for AD attack path analysis
    Can run SharpHound collection and analyze results
    """

    def __init__(
        self,
        config: AuditConfig,
        bh_config: Optional[BloodHoundConfig] = None,
        executor: Optional[CommandExecutor] = None
    ):
        self.config = config
        self.bh_config = bh_config or BloodHoundConfig()
        self.executor = executor or LocalExecutor()
        self._sharphound_path = self._find_sharphound()

    def _find_sharphound(self) -> Optional[str]:
        """Find SharpHound executable"""
        search_paths = [
            self.bh_config.sharphound_path,
            "./SharpHound.exe",
            "./tools/SharpHound.exe",
            "C:\\Tools\\SharpHound.exe",
        ]

        for path in search_paths:
            if path and os.path.exists(path):
                return path

        return None

    async def collect(self, collection_method: str = "All") -> Optional[str]:
        """
        Run SharpHound collection

        Args:
            collection_method: Collection method (All, DCOnly, Session, etc.)

        Returns:
            Path to collected zip file or None
        """
        if not self._sharphound_path:
            console.print("  [yellow]SharpHound not found. Skipping collection.[/]")
            return None

        console.print(f"  [dim]Running SharpHound with method: {collection_method}...[/]")

        output_dir = self.bh_config.output_dir
        os.makedirs(output_dir, exist_ok=True)

        result = await self.executor.execute(
            f'"{self._sharphound_path}" --CollectionMethods {collection_method} --OutputDirectory "{output_dir}"',
            timeout=600  # 10 minutes
        )

        if not result.success:
            console.print(f"  [red]SharpHound failed: {result.stderr}[/]")
            return None

        # Find the output zip
        for file in os.listdir(output_dir):
            if file.endswith(".zip"):
                return os.path.join(output_dir, file)

        return None

    async def analyze_json(self, json_path: str) -> list[Finding]:
        """
        Analyze BloodHound JSON data for security issues

        Args:
            json_path: Path to BloodHound JSON file or directory

        Returns:
            List of findings
        """
        findings = []

        if os.path.isdir(json_path):
            # Process all JSON files in directory
            for file in os.listdir(json_path):
                if file.endswith(".json"):
                    file_findings = await self._analyze_single_json(os.path.join(json_path, file))
                    findings.extend(file_findings)
        else:
            findings = await self._analyze_single_json(json_path)

        return findings

    async def _analyze_single_json(self, json_file: str) -> list[Finding]:
        """Analyze a single BloodHound JSON file"""
        findings = []

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Determine file type and analyze accordingly
            if "users" in data:
                findings.extend(self._analyze_users(data["users"]))
            elif "computers" in data:
                findings.extend(self._analyze_computers(data["computers"]))
            elif "groups" in data:
                findings.extend(self._analyze_groups(data["groups"]))

        except (json.JSONDecodeError, IOError) as e:
            console.print(f"  [yellow]Failed to parse {json_file}: {e}[/]")

        return findings

    def _analyze_users(self, users: list[dict]) -> list[Finding]:
        """Analyze user data from BloodHound"""
        findings = []

        # Count high-value targets
        high_value = [u for u in users if u.get("Properties", {}).get("highvalue", False)]
        if high_value:
            findings.append(Finding(
                id="BH-USERS-HIGHVALUE",
                title=f"High-value user accounts: {len(high_value)}",
                description="BloodHound identified these users as high-value targets",
                severity=Severity.MEDIUM,
                category="ad",
                target="Active Directory",
                evidence=", ".join([u.get("Properties", {}).get("name", "") for u in high_value[:10]]),
                remediation="Apply additional protections to high-value accounts",
                discovered_by="bloodhound",
            ))

        # Check for password not required
        pwd_not_required = [
            u for u in users
            if u.get("Properties", {}).get("passwordnotreqd", False)
        ]
        if pwd_not_required:
            findings.append(Finding(
                id="BH-USERS-NOPWD",
                title=f"Accounts with password not required: {len(pwd_not_required)}",
                description="These accounts can have empty passwords",
                severity=Severity.HIGH,
                category="ad",
                target="Active Directory",
                evidence=", ".join([u.get("Properties", {}).get("name", "") for u in pwd_not_required[:10]]),
                remediation="Remove 'Password not required' flag from these accounts",
                discovered_by="bloodhound",
            ))

        # Check for sensitive accounts with SPN (Kerberoastable)
        kerberoastable = [
            u for u in users
            if u.get("Properties", {}).get("serviceprincipalnames", []) and
               u.get("Properties", {}).get("enabled", True)
        ]

        admin_kerberoastable = [
            u for u in kerberoastable
            if u.get("Properties", {}).get("admincount", False)
        ]

        if admin_kerberoastable:
            findings.append(Finding(
                id="BH-USERS-ADMINSPN",
                title=f"Admin accounts vulnerable to Kerberoasting: {len(admin_kerberoastable)}",
                description="Privileged accounts with SPNs can be Kerberoasted",
                severity=Severity.CRITICAL,
                category="ad",
                target="Active Directory",
                evidence=", ".join([u.get("Properties", {}).get("name", "") for u in admin_kerberoastable]),
                remediation="Remove SPNs or use managed service accounts",
                discovered_by="bloodhound",
            ))

        return findings

    def _analyze_computers(self, computers: list[dict]) -> list[Finding]:
        """Analyze computer data from BloodHound"""
        findings = []

        # Check for unconstrained delegation
        unconstrained = [
            c for c in computers
            if c.get("Properties", {}).get("unconstraineddelegation", False) and
               not c.get("Properties", {}).get("isdc", False)
        ]

        if unconstrained:
            findings.append(Finding(
                id="BH-COMPUTERS-UNCONST",
                title=f"Non-DC computers with unconstrained delegation: {len(unconstrained)}",
                description="These computers can impersonate any user to any service",
                severity=Severity.HIGH,
                category="ad",
                target="Active Directory",
                evidence=", ".join([c.get("Properties", {}).get("name", "") for c in unconstrained]),
                remediation="Replace unconstrained with constrained delegation",
                discovered_by="bloodhound",
            ))

        # Check for outdated OS
        old_os_patterns = ["2003", "2008", "XP", "Vista", "7"]
        old_computers = [
            c for c in computers
            if any(pattern in c.get("Properties", {}).get("operatingsystem", "") for pattern in old_os_patterns)
        ]

        if old_computers:
            findings.append(Finding(
                id="BH-COMPUTERS-OLDOS",
                title=f"Computers with outdated OS: {len(old_computers)}",
                description="These computers are running outdated operating systems",
                severity=Severity.HIGH,
                category="ad",
                target="Active Directory",
                evidence=", ".join([f"{c.get('Properties', {}).get('name', '')}: {c.get('Properties', {}).get('operatingsystem', '')}" for c in old_computers[:5]]),
                remediation="Upgrade or decommission outdated systems",
                discovered_by="bloodhound",
            ))

        return findings

    def _analyze_groups(self, groups: list[dict]) -> list[Finding]:
        """Analyze group data from BloodHound"""
        findings = []

        # Check for large privileged groups
        privileged_groups = ["domain admins", "enterprise admins", "administrators"]

        for group in groups:
            name = group.get("Properties", {}).get("name", "").lower()
            members = len(group.get("Members", []))

            for priv_group in privileged_groups:
                if priv_group in name and members > 10:
                    findings.append(Finding(
                        id=f"BH-GROUP-LARGE-{name.upper().replace(' ', '')}",
                        title=f"Large privileged group: {name} ({members} members)",
                        description=f"The {name} group has {members} members",
                        severity=Severity.MEDIUM,
                        category="ad",
                        target="Active Directory",
                        remediation=f"Review and reduce membership of {name}",
                        discovered_by="bloodhound",
                    ))

        return findings

    async def find_attack_paths(self) -> list[Finding]:
        """
        Query BloodHound Neo4j database for attack paths
        Requires BloodHound to be running with imported data
        """
        findings = []

        try:
            from neo4j import GraphDatabase
        except ImportError:
            console.print("  [yellow]neo4j driver not installed. Skipping attack path analysis.[/]")
            return findings

        try:
            driver = GraphDatabase.driver(
                self.bh_config.neo4j_url,
                auth=(self.bh_config.neo4j_user, self.bh_config.neo4j_password)
            )

            with driver.session() as session:
                # Query for paths to Domain Admins
                result = session.run("""
                    MATCH p=shortestPath((u:User)-[*1..]->(g:Group))
                    WHERE g.name =~ '(?i)domain admins@.*'
                    AND NOT u.name =~ '(?i)administrator@.*'
                    RETURN u.name AS user, length(p) AS path_length
                    ORDER BY path_length
                    LIMIT 20
                """)

                paths = list(result)
                if paths:
                    short_paths = [p for p in paths if p["path_length"] <= 3]
                    if short_paths:
                        findings.append(Finding(
                            id="BH-PATHS-DA",
                            title=f"Short attack paths to Domain Admins: {len(short_paths)}",
                            description="Users with short attack paths to Domain Admins",
                            severity=Severity.CRITICAL,
                            category="ad",
                            target="Active Directory",
                            evidence=", ".join([f"{p['user']} ({p['path_length']} hops)" for p in short_paths[:5]]),
                            remediation="Review and break attack paths identified by BloodHound",
                            discovered_by="bloodhound",
                        ))

                # Query for Kerberoastable paths
                result = session.run("""
                    MATCH (u:User {hasspn:true})
                    WHERE u.admincount = true
                    RETURN u.name AS user
                """)

                kerberoastable_admins = list(result)
                if kerberoastable_admins:
                    findings.append(Finding(
                        id="BH-PATHS-KERBEROAST",
                        title=f"Kerberoastable admin accounts: {len(kerberoastable_admins)}",
                        description="Admin accounts vulnerable to Kerberoasting",
                        severity=Severity.CRITICAL,
                        category="ad",
                        target="Active Directory",
                        evidence=", ".join([u["user"] for u in kerberoastable_admins]),
                        remediation="Remove SPNs from admin accounts or use gMSA",
                        discovered_by="bloodhound",
                    ))

            driver.close()

        except Exception as e:
            console.print(f"  [yellow]BloodHound query failed: {e}[/]")

        return findings
