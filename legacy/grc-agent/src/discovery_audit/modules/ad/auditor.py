"""
Active Directory Security Auditor
Comprehensive AD security assessment similar to PingCastle
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from rich.console import Console

from ...core.models import AuditConfig, Finding, Severity
from ...platform.executor import CommandExecutor, LocalExecutor


console = Console()


class ADRiskCategory(str, Enum):
    """AD Risk Categories (similar to PingCastle)"""
    STALE_OBJECTS = "Stale Objects"
    PRIVILEGED_ACCOUNTS = "Privileged Accounts"
    TRUSTS = "Trusts"
    ANOMALIES = "Anomalies"
    PASSWORDS = "Password Policies"
    KERBEROS = "Kerberos"
    VULNERABILITIES = "Vulnerabilities"
    CONFIGURATION = "Configuration"


@dataclass
class ADDomainInfo:
    """Active Directory Domain Information"""
    domain_name: str = ""
    domain_dns: str = ""
    domain_sid: str = ""
    forest_name: str = ""
    domain_functional_level: str = ""
    forest_functional_level: str = ""
    domain_controllers: list[str] = field(default_factory=list)
    fsmo_roles: dict[str, str] = field(default_factory=dict)
    schema_version: int = 0
    created_date: Optional[datetime] = None


class ADSecurityAuditor:
    """
    Active Directory Security Auditor
    Performs comprehensive security assessment of AD environments
    Similar to PingCastle functionality
    """

    def __init__(
        self,
        config: AuditConfig,
        executor: Optional[CommandExecutor] = None
    ):
        self.config = config
        self.executor = executor or LocalExecutor()
        self.domain_info: Optional[ADDomainInfo] = None

    async def audit(self) -> list[Finding]:
        """
        Run comprehensive AD security audit

        Returns:
            List of security findings
        """
        findings = []

        # First check if we're on a domain-joined machine
        platform_info = await self.executor.get_platform_info()

        if not platform_info.is_domain_joined:
            console.print("  [yellow]Machine is not domain-joined. Skipping AD audit.[/]")
            return findings

        console.print(f"  [dim]Domain detected: {platform_info.domain_name}[/]")

        # Gather domain information
        console.print("  [dim]Gathering domain information...[/]")
        self.domain_info = await self._gather_domain_info()

        if not self.domain_info.domain_name:
            console.print("  [yellow]Could not gather AD information. Check permissions.[/]")
            return findings

        # Run all AD audit modules
        audit_functions = [
            ("Domain Controllers", self._audit_domain_controllers),
            ("Privileged Accounts", self._audit_privileged_accounts),
            ("Kerberos Configuration", self._audit_kerberos),
            ("Password Policies", self._audit_password_policies),
            ("Stale Objects", self._audit_stale_objects),
            ("Trust Relationships", self._audit_trusts),
            ("GPO Security", self._audit_gpo_security),
            ("LDAP Security", self._audit_ldap_security),
            ("Delegation", self._audit_delegation),
            ("SPN Configuration", self._audit_spn),
            ("AdminSDHolder", self._audit_adminsdholder),
            ("Schema Security", self._audit_schema),
        ]

        for name, func in audit_functions:
            try:
                console.print(f"  [dim]Checking {name}...[/]")
                result = await func()
                findings.extend(result)
            except Exception as e:
                console.print(f"  [yellow]Failed to check {name}: {e}[/]")

        return findings

    async def _gather_domain_info(self) -> ADDomainInfo:
        """Gather Active Directory domain information"""
        info = ADDomainInfo()

        # Get domain information
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            $domain = Get-ADDomain
            @{
                DomainName = $domain.Name
                DomainDNS = $domain.DNSRoot
                DomainSID = $domain.DomainSID.Value
                Forest = $domain.Forest
                DomainMode = $domain.DomainMode.ToString()
                DCs = (Get-ADDomainController -Filter *).HostName
            } | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                data = json.loads(result.stdout)
                info.domain_name = data.get("DomainName", "")
                info.domain_dns = data.get("DomainDNS", "")
                info.domain_sid = data.get("DomainSID", "")
                info.forest_name = data.get("Forest", "")
                info.domain_functional_level = data.get("DomainMode", "")
                info.domain_controllers = data.get("DCs", [])
                if not isinstance(info.domain_controllers, list):
                    info.domain_controllers = [info.domain_controllers]
            except json.JSONDecodeError:
                pass

        # Get forest information
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            $forest = Get-ADForest
            @{
                ForestMode = $forest.ForestMode.ToString()
                SchemaVersion = (Get-ADObject (Get-ADRootDSE).schemaNamingContext -Property objectVersion).objectVersion
            } | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                data = json.loads(result.stdout)
                info.forest_functional_level = data.get("ForestMode", "")
                info.schema_version = data.get("SchemaVersion", 0)
            except json.JSONDecodeError:
                pass

        return info

    async def _audit_domain_controllers(self) -> list[Finding]:
        """Audit Domain Controller security"""
        findings = []

        # Check DC OS versions
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADDomainController -Filter * |
            Select-Object HostName, OperatingSystem, OperatingSystemVersion |
            ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                dcs = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(dcs, list):
                    dcs = [dcs]

                for dc in dcs:
                    os_name = dc.get("OperatingSystem", "").lower()

                    # Check for outdated DC OS
                    if any(old in os_name for old in ["2008", "2003", "2000"]):
                        findings.append(Finding(
                            id=f"AD-DC-OLDOS-{dc.get('HostName', 'UNKNOWN')}",
                            title=f"Outdated DC operating system: {dc.get('HostName')}",
                            description=f"Domain Controller running outdated OS: {dc.get('OperatingSystem')}",
                            severity=Severity.CRITICAL,
                            category="ad",
                            target=dc.get("HostName", ""),
                            remediation="Upgrade Domain Controller to Windows Server 2016 or newer",
                            discovered_by="ad_auditor",
                        ))

                    if "2012" in os_name and "r2" not in os_name:
                        findings.append(Finding(
                            id=f"AD-DC-OLDOS-{dc.get('HostName', 'UNKNOWN')}",
                            title=f"Aging DC operating system: {dc.get('HostName')}",
                            description=f"Domain Controller running Windows Server 2012 (non-R2)",
                            severity=Severity.HIGH,
                            category="ad",
                            target=dc.get("HostName", ""),
                            remediation="Plan upgrade to Windows Server 2016 or newer",
                            discovered_by="ad_auditor",
                        ))
            except json.JSONDecodeError:
                pass

        # Check functional levels
        if self.domain_info:
            old_levels = ["Windows2000", "Windows2003", "Windows2008"]
            if any(old in self.domain_info.domain_functional_level for old in old_levels):
                findings.append(Finding(
                    id="AD-FL-OLD",
                    title="Outdated domain functional level",
                    description=f"Domain functional level is {self.domain_info.domain_functional_level}",
                    severity=Severity.HIGH,
                    category="ad",
                    target=self.domain_info.domain_dns,
                    remediation="Raise domain functional level to Windows Server 2016 or higher",
                    discovered_by="ad_auditor",
                ))

        return findings

    async def _audit_privileged_accounts(self) -> list[Finding]:
        """Audit privileged accounts and groups"""
        findings = []

        # Count Domain Admins
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            @{
                DomainAdmins = (Get-ADGroupMember -Identity "Domain Admins" -Recursive).Count
                EnterpriseAdmins = (Get-ADGroupMember -Identity "Enterprise Admins" -Recursive -ErrorAction SilentlyContinue).Count
                SchemaAdmins = (Get-ADGroupMember -Identity "Schema Admins" -Recursive -ErrorAction SilentlyContinue).Count
                Administrators = (Get-ADGroupMember -Identity "Administrators" -Recursive).Count
            } | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                counts = json.loads(result.stdout)

                domain_admins = counts.get("DomainAdmins", 0)
                if domain_admins > 10:
                    findings.append(Finding(
                        id="AD-PRIV-DOMAINADMINS",
                        title=f"Too many Domain Admins: {domain_admins}",
                        description=f"There are {domain_admins} members in Domain Admins group",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Review and reduce Domain Admins membership. Use tiered admin model.",
                        discovered_by="ad_auditor",
                    ))

                enterprise_admins = counts.get("EnterpriseAdmins", 0)
                if enterprise_admins > 5:
                    findings.append(Finding(
                        id="AD-PRIV-ENTERPRISEADMINS",
                        title=f"Too many Enterprise Admins: {enterprise_admins}",
                        description=f"There are {enterprise_admins} members in Enterprise Admins group",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Enterprise Admins should be empty during normal operations",
                        discovered_by="ad_auditor",
                    ))

                schema_admins = counts.get("SchemaAdmins", 0)
                if schema_admins > 0:
                    findings.append(Finding(
                        id="AD-PRIV-SCHEMAADMINS",
                        title=f"Schema Admins group is not empty: {schema_admins}",
                        description="Schema Admins should be empty unless performing schema modifications",
                        severity=Severity.MEDIUM,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Remove all members from Schema Admins when not needed",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        # Check for accounts that can DCSync
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            $domain = Get-ADDomain
            $acl = Get-ACL "AD:\\$($domain.DistinguishedName)"
            $dcsync = $acl.Access | Where-Object {
                ($_.ActiveDirectoryRights -match 'ExtendedRight') -and
                ($_.ObjectType -eq '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2' -or  # DS-Replication-Get-Changes
                 $_.ObjectType -eq '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2')    # DS-Replication-Get-Changes-All
            }
            $dcsync | Select-Object IdentityReference | ConvertTo-Json
        """)

        if result.success and result.stdout.strip():
            try:
                import json
                dcsync_accounts = json.loads(result.stdout)
                if not isinstance(dcsync_accounts, list):
                    dcsync_accounts = [dcsync_accounts]

                # Filter out expected accounts
                expected = ["domain controllers", "enterprise domain controllers", "administrators"]
                suspicious = [
                    a for a in dcsync_accounts
                    if not any(e in a.get("IdentityReference", "").lower() for e in expected)
                ]

                if suspicious:
                    findings.append(Finding(
                        id="AD-PRIV-DCSYNC",
                        title="Non-standard accounts with DCSync rights",
                        description=f"Found {len(suspicious)} accounts with DCSync replication rights",
                        severity=Severity.CRITICAL,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join([a.get("IdentityReference", "") for a in suspicious[:5]]),
                        remediation="Review and remove unnecessary DCSync rights",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_kerberos(self) -> list[Finding]:
        """Audit Kerberos configuration"""
        findings = []

        # Check for Kerberoastable accounts (SPNs on user accounts)
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties ServicePrincipalName, PasswordLastSet, Enabled |
            Where-Object { $_.Enabled -eq $true } |
            Select-Object SamAccountName, ServicePrincipalName, PasswordLastSet |
            ConvertTo-Json
        """)

        if result.success and result.stdout.strip():
            try:
                import json
                kerberoastable = json.loads(result.stdout)
                if not isinstance(kerberoastable, list):
                    kerberoastable = [kerberoastable]

                if len(kerberoastable) > 0:
                    severity = Severity.HIGH if len(kerberoastable) > 5 else Severity.MEDIUM
                    findings.append(Finding(
                        id="AD-KERB-KERBEROAST",
                        title=f"Kerberoastable accounts found: {len(kerberoastable)}",
                        description="User accounts with SPNs are vulnerable to Kerberoasting",
                        severity=severity,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join([a.get("SamAccountName", "") for a in kerberoastable[:10]]),
                        remediation="Use managed service accounts (gMSA) or ensure strong passwords for SPN accounts",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        # Check for AS-REP roastable accounts (no pre-auth)
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true} -Properties DoesNotRequirePreAuth |
            Select-Object SamAccountName |
            ConvertTo-Json
        """)

        if result.success and result.stdout.strip() and result.stdout.strip() != "null":
            try:
                import json
                asrep = json.loads(result.stdout)
                if not isinstance(asrep, list):
                    asrep = [asrep]

                if len(asrep) > 0:
                    findings.append(Finding(
                        id="AD-KERB-ASREP",
                        title=f"AS-REP Roastable accounts: {len(asrep)}",
                        description="Accounts with 'Do not require Kerberos preauthentication' enabled",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join([a.get("SamAccountName", "") for a in asrep[:10]]),
                        remediation="Enable Kerberos pre-authentication for all accounts",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        # Check krbtgt password age
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADUser krbtgt -Properties PasswordLastSet | Select-Object PasswordLastSet | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                krbtgt = json.loads(result.stdout)
                if krbtgt.get("PasswordLastSet"):
                    # Parse the date
                    pwd_date_str = krbtgt["PasswordLastSet"]
                    if "/Date(" in pwd_date_str:
                        timestamp = int(pwd_date_str.replace("/Date(", "").replace(")/", "")) / 1000
                        pwd_date = datetime.fromtimestamp(timestamp)
                        days_old = (datetime.now() - pwd_date).days

                        if days_old > 365:
                            findings.append(Finding(
                                id="AD-KERB-KRBTGT",
                                title=f"krbtgt password is {days_old} days old",
                                description="The krbtgt account password should be rotated periodically",
                                severity=Severity.HIGH if days_old > 730 else Severity.MEDIUM,
                                category="ad",
                                target=self.domain_info.domain_dns if self.domain_info else "",
                                remediation="Rotate the krbtgt password twice (with time between resets)",
                                discovered_by="ad_auditor",
                            ))
            except (json.JSONDecodeError, ValueError):
                pass

        return findings

    async def _audit_password_policies(self) -> list[Finding]:
        """Audit password policies"""
        findings = []

        # Get default domain password policy
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADDefaultDomainPasswordPolicy | Select-Object
                MinPasswordLength, PasswordHistoryCount, MaxPasswordAge,
                MinPasswordAge, ComplexityEnabled, ReversibleEncryptionEnabled,
                LockoutThreshold, LockoutDuration, LockoutObservationWindow |
            ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                policy = json.loads(result.stdout)

                # Check minimum password length
                min_len = policy.get("MinPasswordLength", 0)
                if min_len < 14:
                    findings.append(Finding(
                        id="AD-PWD-MINLEN",
                        title=f"Weak minimum password length: {min_len}",
                        description="Minimum password length should be at least 14 characters",
                        severity=Severity.MEDIUM if min_len >= 8 else Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Increase minimum password length to 14 characters",
                        discovered_by="ad_auditor",
                    ))

                # Check password history
                history = policy.get("PasswordHistoryCount", 0)
                if history < 24:
                    findings.append(Finding(
                        id="AD-PWD-HISTORY",
                        title=f"Low password history: {history}",
                        description="Password history should remember at least 24 passwords",
                        severity=Severity.LOW,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Set password history to 24 or more",
                        discovered_by="ad_auditor",
                    ))

                # Check complexity
                if not policy.get("ComplexityEnabled", True):
                    findings.append(Finding(
                        id="AD-PWD-COMPLEXITY",
                        title="Password complexity not enforced",
                        description="Password complexity requirements are disabled",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Enable password complexity requirements",
                        discovered_by="ad_auditor",
                    ))

                # Check reversible encryption
                if policy.get("ReversibleEncryptionEnabled", False):
                    findings.append(Finding(
                        id="AD-PWD-REVERSIBLE",
                        title="Reversible encryption enabled",
                        description="Passwords are stored with reversible encryption",
                        severity=Severity.CRITICAL,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Disable reversible encryption storage",
                        discovered_by="ad_auditor",
                    ))

                # Check lockout
                lockout = policy.get("LockoutThreshold", 0)
                if lockout == 0:
                    findings.append(Finding(
                        id="AD-PWD-LOCKOUT",
                        title="Account lockout not configured",
                        description="No account lockout threshold is set",
                        severity=Severity.MEDIUM,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Configure account lockout threshold (recommended: 5 attempts)",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_stale_objects(self) -> list[Finding]:
        """Audit stale AD objects"""
        findings = []

        # Check for stale computer accounts (not logged in for 90+ days)
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            $90DaysAgo = (Get-Date).AddDays(-90)
            (Get-ADComputer -Filter {LastLogonDate -lt $90DaysAgo} -Properties LastLogonDate |
            Where-Object { $_.Enabled -eq $true }).Count
        """)

        if result.success:
            try:
                stale_computers = int(result.stdout.strip())
                if stale_computers > 0:
                    findings.append(Finding(
                        id="AD-STALE-COMPUTERS",
                        title=f"Stale computer accounts: {stale_computers}",
                        description=f"Found {stale_computers} enabled computer accounts inactive for 90+ days",
                        severity=Severity.LOW if stale_computers < 50 else Severity.MEDIUM,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Review and disable/delete stale computer accounts",
                        discovered_by="ad_auditor",
                    ))
            except ValueError:
                pass

        # Check for stale user accounts
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            $90DaysAgo = (Get-Date).AddDays(-90)
            (Get-ADUser -Filter {LastLogonDate -lt $90DaysAgo -and Enabled -eq $true} -Properties LastLogonDate).Count
        """)

        if result.success:
            try:
                stale_users = int(result.stdout.strip())
                if stale_users > 0:
                    findings.append(Finding(
                        id="AD-STALE-USERS",
                        title=f"Stale user accounts: {stale_users}",
                        description=f"Found {stale_users} enabled user accounts inactive for 90+ days",
                        severity=Severity.LOW if stale_users < 100 else Severity.MEDIUM,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Review and disable stale user accounts",
                        discovered_by="ad_auditor",
                    ))
            except ValueError:
                pass

        return findings

    async def _audit_trusts(self) -> list[Finding]:
        """Audit AD trust relationships"""
        findings = []

        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADTrust -Filter * | Select-Object Name, Direction, TrustType,
                DisallowTransivity, SelectiveAuthentication, SIDFilteringQuarantined,
                SIDFilteringForestAware | ConvertTo-Json
        """)

        if result.success and result.stdout.strip() and result.stdout.strip() != "null":
            try:
                import json
                trusts = json.loads(result.stdout)
                if not isinstance(trusts, list):
                    trusts = [trusts]

                for trust in trusts:
                    # Check for trusts without SID filtering
                    if not trust.get("SIDFilteringQuarantined", True):
                        findings.append(Finding(
                            id=f"AD-TRUST-SIDFILTER-{trust.get('Name', 'UNKNOWN')}",
                            title=f"SID filtering disabled on trust: {trust.get('Name')}",
                            description="Trust without SID filtering is vulnerable to SID history attacks",
                            severity=Severity.HIGH,
                            category="ad",
                            target=trust.get("Name", ""),
                            remediation="Enable SID filtering on the trust",
                            discovered_by="ad_auditor",
                        ))

                    # Check for trusts without selective authentication
                    if not trust.get("SelectiveAuthentication", True) and trust.get("Direction") != "Inbound":
                        findings.append(Finding(
                            id=f"AD-TRUST-SELECTAUTH-{trust.get('Name', 'UNKNOWN')}",
                            title=f"Selective authentication not enabled: {trust.get('Name')}",
                            description="Trust allows forest-wide authentication instead of selective",
                            severity=Severity.MEDIUM,
                            category="ad",
                            target=trust.get("Name", ""),
                            remediation="Enable selective authentication on the trust",
                            discovered_by="ad_auditor",
                        ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_gpo_security(self) -> list[Finding]:
        """Audit Group Policy security"""
        findings = []

        # Check for GPOs with weak permissions
        result = await self.executor.execute_powershell("""
            Import-Module GroupPolicy -ErrorAction SilentlyContinue
            Get-GPO -All | ForEach-Object {
                $gpo = $_
                $acl = Get-GPPermission -Guid $gpo.Id -All
                $dangerous = $acl | Where-Object {
                    $_.Permission -eq 'GpoEditDeleteModifySecurity' -and
                    $_.Trustee.SidType -eq 'User'
                }
                if ($dangerous) {
                    [PSCustomObject]@{
                        Name = $gpo.DisplayName
                        Users = ($dangerous | Select-Object -ExpandProperty Trustee | Select-Object -ExpandProperty Name) -join ','
                    }
                }
            } | ConvertTo-Json
        """)

        if result.success and result.stdout.strip() and result.stdout.strip() != "null":
            try:
                import json
                gpos = json.loads(result.stdout)
                if not isinstance(gpos, list):
                    gpos = [gpos]

                if len(gpos) > 0:
                    findings.append(Finding(
                        id="AD-GPO-PERMISSIONS",
                        title=f"GPOs with dangerous user permissions: {len(gpos)}",
                        description="GPOs that can be modified by non-admin users",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join([g.get("Name", "") for g in gpos[:5]]),
                        remediation="Review and restrict GPO modification permissions",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_ldap_security(self) -> list[Finding]:
        """Audit LDAP security settings"""
        findings = []

        # Check LDAP signing requirement
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\NTDS\\Parameters' -Name 'LDAPServerIntegrity' -ErrorAction SilentlyContinue
        """)

        if result.success:
            try:
                value = int(result.stdout.strip())
                if value < 2:
                    findings.append(Finding(
                        id="AD-LDAP-SIGNING",
                        title="LDAP signing not required",
                        description="LDAP server does not require signing",
                        severity=Severity.MEDIUM,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        remediation="Set LDAP server signing to 'Require signing'",
                        discovered_by="ad_auditor",
                    ))
            except ValueError:
                pass

        # Check LDAP channel binding
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\NTDS\\Parameters' -Name 'LdapEnforceChannelBinding' -ErrorAction SilentlyContinue
        """)

        if not result.success or result.stdout.strip() == "" or result.stdout.strip() == "0":
            findings.append(Finding(
                id="AD-LDAP-CHANNELBIND",
                title="LDAP channel binding not enforced",
                description="LDAP channel binding is not configured or not enforced",
                severity=Severity.MEDIUM,
                category="ad",
                target=self.domain_info.domain_dns if self.domain_info else "",
                remediation="Enable LDAP channel binding token requirements",
                discovered_by="ad_auditor",
            ))

        return findings

    async def _audit_delegation(self) -> list[Finding]:
        """Audit Kerberos delegation settings"""
        findings = []

        # Check for unconstrained delegation
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation |
            Where-Object { $_.Name -notlike '*DC*' } |
            Select-Object Name | ConvertTo-Json
        """)

        if result.success and result.stdout.strip() and result.stdout.strip() != "null":
            try:
                import json
                unconstrained = json.loads(result.stdout)
                if not isinstance(unconstrained, list):
                    unconstrained = [unconstrained]

                if len(unconstrained) > 0:
                    findings.append(Finding(
                        id="AD-DELEG-UNCONSTRAINED",
                        title=f"Unconstrained delegation found: {len(unconstrained)} computers",
                        description="Computers with unconstrained delegation can impersonate any user",
                        severity=Severity.HIGH,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join([c.get("Name", "") for c in unconstrained]),
                        remediation="Replace unconstrained delegation with constrained or resource-based delegation",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_spn(self) -> list[Finding]:
        """Audit SPN configuration"""
        # Covered in Kerberos audit
        return []

    async def _audit_adminsdholder(self) -> list[Finding]:
        """Audit AdminSDHolder protected accounts"""
        findings = []

        # Check for accounts with adminCount=1 that shouldn't have it
        result = await self.executor.execute_powershell("""
            Import-Module ActiveDirectory -ErrorAction SilentlyContinue
            Get-ADUser -Filter {adminCount -eq 1} -Properties adminCount, MemberOf |
            Select-Object SamAccountName, @{N='Groups';E={($_.MemberOf | ForEach-Object { (Get-ADGroup $_).Name }) -join ','}} |
            ConvertTo-Json
        """)

        if result.success and result.stdout.strip():
            try:
                import json
                admin_count_users = json.loads(result.stdout)
                if not isinstance(admin_count_users, list):
                    admin_count_users = [admin_count_users]

                # Check for orphaned adminCount (not actually in privileged groups)
                privileged_groups = ["domain admins", "enterprise admins", "schema admins", "administrators", "account operators", "backup operators"]

                orphaned = []
                for user in admin_count_users:
                    groups = user.get("Groups", "").lower()
                    if not any(pg in groups for pg in privileged_groups):
                        orphaned.append(user.get("SamAccountName", ""))

                if len(orphaned) > 0:
                    findings.append(Finding(
                        id="AD-ADMINSDHOLDER-ORPHANED",
                        title=f"Orphaned adminCount attributes: {len(orphaned)}",
                        description="Accounts with adminCount=1 but not in protected groups",
                        severity=Severity.LOW,
                        category="ad",
                        target=self.domain_info.domain_dns if self.domain_info else "",
                        evidence=", ".join(orphaned[:10]),
                        remediation="Clear adminCount attribute for accounts not in protected groups",
                        discovered_by="ad_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_schema(self) -> list[Finding]:
        """Audit AD schema security"""
        findings = []

        if self.domain_info and self.domain_info.schema_version:
            # Schema versions: https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/schema-updates
            # 87 = 2016, 88 = 2019, 89 = 2022
            if self.domain_info.schema_version < 87:
                findings.append(Finding(
                    id="AD-SCHEMA-OLD",
                    title=f"Outdated AD schema version: {self.domain_info.schema_version}",
                    description="AD schema is outdated and missing security improvements",
                    severity=Severity.MEDIUM,
                    category="ad",
                    target=self.domain_info.domain_dns if self.domain_info else "",
                    remediation="Upgrade schema to latest version during DC upgrades",
                    discovered_by="ad_auditor",
                ))

        return findings
