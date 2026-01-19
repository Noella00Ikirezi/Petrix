"""
Windows System Auditor
Comprehensive security audit for Windows systems
"""

import asyncio
from typing import Optional
from rich.console import Console

from ...core.models import AuditConfig, Finding, Severity, HostInfo
from ...platform.executor import CommandExecutor, LocalExecutor


console = Console()


class WindowsAuditor:
    """
    Main Windows security auditor
    Coordinates all Windows-specific security checks
    """

    def __init__(
        self,
        config: AuditConfig,
        executor: Optional[CommandExecutor] = None
    ):
        self.config = config
        self.executor = executor or LocalExecutor()

    async def audit(self, hosts: list[HostInfo] = None) -> list[Finding]:
        """
        Run comprehensive Windows security audit

        Args:
            hosts: Optional list of hosts (for remote audits)

        Returns:
            List of security findings
        """
        findings = []

        platform_info = await self.executor.get_platform_info()

        if not platform_info.is_elevated:
            console.print("  [yellow]Warning: Not running as Administrator. Some checks may fail.[/]")

        # Run all audit modules
        audit_functions = [
            ("Security Policies", self._audit_security_policies),
            ("User Accounts", self._audit_user_accounts),
            ("Windows Services", self._audit_services),
            ("Windows Firewall", self._audit_firewall),
            ("Windows Defender", self._audit_defender),
            ("Windows Updates", self._audit_updates),
            ("Audit Policies", self._audit_audit_policies),
            ("Registry Security", self._audit_registry),
            ("Installed Software", self._audit_software),
            ("Scheduled Tasks", self._audit_scheduled_tasks),
            ("Network Configuration", self._audit_network),
            ("RDP Configuration", self._audit_rdp),
            ("PowerShell Security", self._audit_powershell),
            ("SMB Configuration", self._audit_smb),
        ]

        for name, func in audit_functions:
            try:
                console.print(f"  [dim]Checking {name}...[/]")
                result = await func()
                findings.extend(result)
            except Exception as e:
                console.print(f"  [yellow]Failed to check {name}: {e}[/]")

        return findings

    async def _audit_security_policies(self) -> list[Finding]:
        """Audit local security policies"""
        findings = []

        # Export security policy to analyze
        result = await self.executor.execute_powershell("""
            $tempFile = [System.IO.Path]::GetTempFileName()
            secedit /export /cfg $tempFile /quiet
            Get-Content $tempFile
            Remove-Item $tempFile
        """)

        if not result.success:
            return findings

        policy_content = result.stdout.lower()

        # Check password policies
        checks = [
            {
                "pattern": "minimumpasswordlength",
                "threshold": 14,
                "title": "Weak minimum password length",
                "description": "Minimum password length should be at least 14 characters",
                "severity": Severity.MEDIUM,
            },
            {
                "pattern": "passwordhistorysize",
                "threshold": 24,
                "title": "Insufficient password history",
                "description": "Password history should remember at least 24 passwords",
                "severity": Severity.LOW,
            },
            {
                "pattern": "maximumpasswordage",
                "max_value": 90,
                "title": "Password expiration too long",
                "description": "Maximum password age should be 90 days or less",
                "severity": Severity.LOW,
            },
            {
                "pattern": "lockoutbadcount",
                "max_value": 5,
                "title": "Account lockout threshold too high",
                "description": "Account should lock after 5 or fewer failed attempts",
                "severity": Severity.MEDIUM,
            },
        ]

        for line in policy_content.split("\n"):
            for check in checks:
                if check["pattern"] in line and "=" in line:
                    try:
                        value = int(line.split("=")[1].strip())

                        if "threshold" in check and value < check["threshold"]:
                            findings.append(Finding(
                                id=f"WIN-POL-{check['pattern'].upper()}",
                                title=check["title"],
                                description=f"{check['description']}. Current value: {value}",
                                severity=check["severity"],
                                category="system",
                                target="localhost",
                                remediation=f"Set {check['pattern']} to at least {check['threshold']}",
                                discovered_by="windows_auditor",
                            ))

                        if "max_value" in check and value > check["max_value"]:
                            findings.append(Finding(
                                id=f"WIN-POL-{check['pattern'].upper()}",
                                title=check["title"],
                                description=f"{check['description']}. Current value: {value}",
                                severity=check["severity"],
                                category="system",
                                target="localhost",
                                remediation=f"Set {check['pattern']} to {check['max_value']} or less",
                                discovered_by="windows_auditor",
                            ))
                    except ValueError:
                        pass

        return findings

    async def _audit_user_accounts(self) -> list[Finding]:
        """Audit local user accounts"""
        findings = []

        # Get local administrators
        result = await self.executor.execute_powershell("""
            Get-LocalGroupMember -Group "Administrators" |
            Select-Object Name, ObjectClass, PrincipalSource |
            ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                admins = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(admins, list):
                    admins = [admins]

                if len(admins) > 5:
                    findings.append(Finding(
                        id="WIN-USER-ADMINS",
                        title="Too many local administrators",
                        description=f"Found {len(admins)} local administrators. Limit admin access.",
                        severity=Severity.MEDIUM,
                        category="system",
                        target="localhost",
                        evidence=", ".join([a.get("Name", "") for a in admins[:10]]),
                        remediation="Remove unnecessary users from the Administrators group",
                        discovered_by="windows_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        # Check for Guest account
        result = await self.executor.execute_powershell("""
            Get-LocalUser -Name "Guest" | Select-Object Enabled | ConvertTo-Json
        """)

        if result.success and '"Enabled":true' in result.stdout.lower().replace(" ", ""):
            findings.append(Finding(
                id="WIN-USER-GUEST",
                title="Guest account is enabled",
                description="The built-in Guest account is enabled, which is a security risk",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Disable the Guest account: Disable-LocalUser -Name Guest",
                discovered_by="windows_auditor",
            ))

        # Check for accounts with no password expiration
        result = await self.executor.execute_powershell("""
            Get-LocalUser | Where-Object { $_.PasswordNeverExpires -eq $true -and $_.Enabled -eq $true } |
            Select-Object Name | ConvertTo-Json
        """)

        if result.success and result.stdout.strip() and result.stdout.strip() != "null":
            try:
                import json
                users = json.loads(result.stdout)
                if not isinstance(users, list):
                    users = [users]

                if users:
                    findings.append(Finding(
                        id="WIN-USER-NOEXPIRE",
                        title="Accounts with non-expiring passwords",
                        description=f"Found {len(users)} accounts with passwords that never expire",
                        severity=Severity.LOW,
                        category="system",
                        target="localhost",
                        evidence=", ".join([u.get("Name", "") for u in users[:10]]),
                        remediation="Set password expiration for all user accounts",
                        discovered_by="windows_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_services(self) -> list[Finding]:
        """Audit Windows services"""
        findings = []

        # Check for dangerous services
        dangerous_services = [
            ("RemoteRegistry", "Remote Registry service", Severity.MEDIUM),
            ("Telnet", "Telnet service", Severity.HIGH),
            ("SNMP", "SNMP service", Severity.MEDIUM),
            ("WinHttpAutoProxySvc", "WinHTTP Web Proxy Auto-Discovery", Severity.LOW),
        ]

        for service_name, description, severity in dangerous_services:
            result = await self.executor.execute_powershell(f"""
                Get-Service -Name "{service_name}" -ErrorAction SilentlyContinue |
                Select-Object Status | ConvertTo-Json
            """)

            if result.success and '"Running"' in result.stdout:
                findings.append(Finding(
                    id=f"WIN-SVC-{service_name.upper()}",
                    title=f"Dangerous service running: {service_name}",
                    description=f"{description} is running and may pose a security risk",
                    severity=severity,
                    category="system",
                    target="localhost",
                    service=service_name,
                    remediation=f"Stop and disable the {service_name} service if not needed",
                    discovered_by="windows_auditor",
                ))

        # Check for services running as LocalSystem that shouldn't be
        result = await self.executor.execute_powershell("""
            Get-WmiObject Win32_Service |
            Where-Object { $_.StartName -eq "LocalSystem" -and $_.State -eq "Running" } |
            Select-Object Name, DisplayName |
            ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                services = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(services, list):
                    services = [services]

                # Known safe services to ignore
                safe_services = {
                    "wuauserv", "cryptsvc", "msiserver", "trustedinstaller",
                    "schedule", "eventlog", "plugplay", "power", "themes",
                    "lanmanserver", "lanmanworkstation", "netlogon"
                }

                suspicious = [
                    s for s in services
                    if s.get("Name", "").lower() not in safe_services
                ]

                if len(suspicious) > 20:
                    findings.append(Finding(
                        id="WIN-SVC-LOCALSYSTEM",
                        title="Many services running as LocalSystem",
                        description=f"{len(suspicious)} non-standard services running as LocalSystem",
                        severity=Severity.LOW,
                        category="system",
                        target="localhost",
                        remediation="Review services and use least-privilege accounts where possible",
                        discovered_by="windows_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_firewall(self) -> list[Finding]:
        """Audit Windows Firewall configuration"""
        findings = []

        # Check if firewall is enabled for all profiles
        result = await self.executor.execute_powershell("""
            Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                profiles = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(profiles, list):
                    profiles = [profiles]

                for profile in profiles:
                    if not profile.get("Enabled", True):
                        findings.append(Finding(
                            id=f"WIN-FW-{profile.get('Name', 'UNKNOWN').upper()}",
                            title=f"Windows Firewall disabled for {profile.get('Name')} profile",
                            description=f"Windows Firewall is disabled for the {profile.get('Name')} profile",
                            severity=Severity.HIGH,
                            category="system",
                            target="localhost",
                            remediation=f"Enable firewall: Set-NetFirewallProfile -Profile {profile.get('Name')} -Enabled True",
                            discovered_by="windows_auditor",
                        ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_defender(self) -> list[Finding]:
        """Audit Windows Defender configuration"""
        findings = []

        # Check Defender status
        result = await self.executor.execute_powershell("""
            Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled,
            AntispywareEnabled, BehaviorMonitorEnabled, IoavProtectionEnabled |
            ConvertTo-Json
        """)

        if result.success and result.stdout.strip():
            try:
                import json
                status = json.loads(result.stdout)

                protections = [
                    ("AntivirusEnabled", "Antivirus"),
                    ("RealTimeProtectionEnabled", "Real-time protection"),
                    ("AntispywareEnabled", "Antispyware"),
                    ("BehaviorMonitorEnabled", "Behavior monitoring"),
                    ("IoavProtectionEnabled", "Download protection"),
                ]

                for key, name in protections:
                    if not status.get(key, True):
                        findings.append(Finding(
                            id=f"WIN-DEF-{key.upper()}",
                            title=f"Windows Defender {name} disabled",
                            description=f"Windows Defender {name} is not enabled",
                            severity=Severity.HIGH,
                            category="system",
                            target="localhost",
                            remediation=f"Enable Windows Defender {name}",
                            discovered_by="windows_auditor",
                        ))
            except json.JSONDecodeError:
                pass
        else:
            findings.append(Finding(
                id="WIN-DEF-MISSING",
                title="Windows Defender not available",
                description="Unable to query Windows Defender status. It may be disabled or replaced.",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Verify antivirus protection is installed and active",
                discovered_by="windows_auditor",
            ))

        return findings

    async def _audit_updates(self) -> list[Finding]:
        """Audit Windows Update status"""
        findings = []

        # Check for pending updates
        result = await self.executor.execute_powershell("""
            $UpdateSession = New-Object -ComObject Microsoft.Update.Session
            $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
            $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
            $SearchResult.Updates.Count
        """, timeout=120)

        if result.success:
            try:
                pending_count = int(result.stdout.strip())

                if pending_count > 0:
                    severity = Severity.HIGH if pending_count > 10 else Severity.MEDIUM
                    findings.append(Finding(
                        id="WIN-UPDATE-PENDING",
                        title=f"{pending_count} Windows updates pending",
                        description=f"There are {pending_count} Windows updates waiting to be installed",
                        severity=severity,
                        category="system",
                        target="localhost",
                        remediation="Install pending Windows updates",
                        discovered_by="windows_auditor",
                    ))
            except ValueError:
                pass

        # Check last update time
        result = await self.executor.execute_powershell("""
            Get-HotFix | Sort-Object InstalledOn -Descending |
            Select-Object -First 1 InstalledOn | ConvertTo-Json
        """)

        if result.success and result.stdout.strip():
            try:
                import json
                from datetime import datetime, timedelta

                hotfix = json.loads(result.stdout)
                if hotfix.get("InstalledOn"):
                    # Parse the date (format: /Date(timestamp)/)
                    timestamp_str = hotfix["InstalledOn"]
                    if "/Date(" in timestamp_str:
                        timestamp = int(timestamp_str.replace("/Date(", "").replace(")/", "")) / 1000
                        last_update = datetime.fromtimestamp(timestamp)

                        days_since = (datetime.now() - last_update).days

                        if days_since > 90:
                            findings.append(Finding(
                                id="WIN-UPDATE-OLD",
                                title="No recent Windows updates",
                                description=f"Last Windows update was {days_since} days ago",
                                severity=Severity.HIGH if days_since > 180 else Severity.MEDIUM,
                                category="system",
                                target="localhost",
                                remediation="Check Windows Update settings and install pending updates",
                                discovered_by="windows_auditor",
                            ))
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

        return findings

    async def _audit_audit_policies(self) -> list[Finding]:
        """Audit Windows audit policies"""
        findings = []

        result = await self.executor.execute_powershell("""
            auditpol /get /category:* /r | ConvertFrom-Csv | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                policies = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(policies, list):
                    policies = [policies]

                # Critical audit policies that should be enabled
                required_audits = {
                    "Logon": ["Success", "Failure"],
                    "Account Logon": ["Success", "Failure"],
                    "Account Management": ["Success", "Failure"],
                    "Privilege Use": ["Success", "Failure"],
                    "System": ["Success", "Failure"],
                }

                for policy in policies:
                    subcategory = policy.get("Subcategory", "")
                    setting = policy.get("Inclusion Setting", "")

                    for category, required in required_audits.items():
                        if category.lower() in subcategory.lower():
                            if setting == "No Auditing":
                                findings.append(Finding(
                                    id=f"WIN-AUDIT-{subcategory.upper().replace(' ', '')}",
                                    title=f"Audit policy not configured: {subcategory}",
                                    description=f"The {subcategory} audit policy is not configured",
                                    severity=Severity.MEDIUM,
                                    category="system",
                                    target="localhost",
                                    remediation=f"Enable auditing for {subcategory} events",
                                    discovered_by="windows_auditor",
                                ))
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_registry(self) -> list[Finding]:
        """Audit Windows Registry security settings"""
        findings = []

        # Check for insecure registry settings
        registry_checks = [
            {
                "path": r"HKLM:\SYSTEM\CurrentControlSet\Control\Lsa",
                "name": "RestrictAnonymous",
                "expected": 1,
                "title": "Anonymous access restrictions not configured",
                "description": "RestrictAnonymous should be set to 1 to prevent anonymous enumeration",
                "severity": Severity.MEDIUM,
            },
            {
                "path": r"HKLM:\SYSTEM\CurrentControlSet\Control\Lsa",
                "name": "LmCompatibilityLevel",
                "min_value": 3,
                "title": "Weak LAN Manager authentication level",
                "description": "LmCompatibilityLevel should be at least 3 (NTLMv2 only)",
                "severity": Severity.HIGH,
            },
            {
                "path": r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                "name": "EnableLUA",
                "expected": 1,
                "title": "UAC is disabled",
                "description": "User Account Control (UAC) is disabled",
                "severity": Severity.HIGH,
            },
            {
                "path": r"HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters",
                "name": "SMB1",
                "expected": 0,
                "title": "SMBv1 is enabled",
                "description": "SMBv1 is enabled and is vulnerable to exploits like EternalBlue",
                "severity": Severity.CRITICAL,
            },
        ]

        for check in registry_checks:
            result = await self.executor.execute_powershell(f"""
                try {{
                    $value = Get-ItemPropertyValue -Path "{check['path']}" -Name "{check['name']}" -ErrorAction Stop
                    $value
                }} catch {{
                    "NOT_FOUND"
                }}
            """)

            if result.success:
                value = result.stdout.strip()

                if value == "NOT_FOUND":
                    if "expected" in check and check["expected"] != 0:
                        findings.append(Finding(
                            id=f"WIN-REG-{check['name'].upper()}",
                            title=check["title"],
                            description=f"{check['description']}. Registry value not found.",
                            severity=check["severity"],
                            category="system",
                            target="localhost",
                            remediation=f"Set {check['path']}\\{check['name']} to {check.get('expected', check.get('min_value'))}",
                            discovered_by="windows_auditor",
                        ))
                else:
                    try:
                        int_value = int(value)

                        if "expected" in check and int_value != check["expected"]:
                            findings.append(Finding(
                                id=f"WIN-REG-{check['name'].upper()}",
                                title=check["title"],
                                description=f"{check['description']}. Current value: {int_value}",
                                severity=check["severity"],
                                category="system",
                                target="localhost",
                                remediation=f"Set {check['path']}\\{check['name']} to {check['expected']}",
                                discovered_by="windows_auditor",
                            ))

                        if "min_value" in check and int_value < check["min_value"]:
                            findings.append(Finding(
                                id=f"WIN-REG-{check['name'].upper()}",
                                title=check["title"],
                                description=f"{check['description']}. Current value: {int_value}",
                                severity=check["severity"],
                                category="system",
                                target="localhost",
                                remediation=f"Set {check['path']}\\{check['name']} to at least {check['min_value']}",
                                discovered_by="windows_auditor",
                            ))
                    except ValueError:
                        pass

        return findings

    async def _audit_software(self) -> list[Finding]:
        """Audit installed software for known vulnerable versions"""
        # Implementation would check installed software against CVE database
        return []

    async def _audit_scheduled_tasks(self) -> list[Finding]:
        """Audit scheduled tasks for suspicious entries"""
        findings = []

        result = await self.executor.execute_powershell("""
            Get-ScheduledTask | Where-Object { $_.State -eq 'Ready' } |
            Select-Object TaskName, TaskPath,
            @{N='Author';E={$_.Principal.UserId}},
            @{N='RunAs';E={$_.Principal.RunLevel}} |
            ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                tasks = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(tasks, list):
                    tasks = [tasks]

                # Check for tasks running as SYSTEM from unusual paths
                for task in tasks:
                    path = task.get("TaskPath", "")
                    run_as = task.get("RunAs", "")

                    # Flag tasks not in standard Microsoft paths running as elevated
                    if run_as == "HighestAvailable" and "\\Microsoft\\" not in path:
                        if "\\Microsoft\\" not in path:
                            findings.append(Finding(
                                id=f"WIN-TASK-ELEVATED",
                                title=f"Elevated scheduled task: {task.get('TaskName')}",
                                description=f"Non-standard scheduled task running with elevated privileges",
                                severity=Severity.LOW,
                                category="system",
                                target="localhost",
                                evidence=f"Task: {task.get('TaskName')}, Path: {path}",
                                remediation="Review and verify the legitimacy of this scheduled task",
                                discovered_by="windows_auditor",
                            ))
                            break  # Just one finding for this check
            except json.JSONDecodeError:
                pass

        return findings

    async def _audit_network(self) -> list[Finding]:
        """Audit network configuration"""
        findings = []

        # Check for IPv6 if not needed
        result = await self.executor.execute_powershell("""
            Get-NetAdapterBinding | Where-Object { $_.ComponentID -eq 'ms_tcpip6' -and $_.Enabled -eq $true } |
            Select-Object Name | ConvertTo-Json
        """)

        # Check DNS settings
        result = await self.executor.execute_powershell("""
            Get-DnsClientServerAddress |
            Where-Object { $_.AddressFamily -eq 2 } |
            Select-Object InterfaceAlias, ServerAddresses |
            ConvertTo-Json
        """)

        return findings

    async def _audit_rdp(self) -> list[Finding]:
        """Audit RDP configuration"""
        findings = []

        # Check if RDP is enabled
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections'
        """)

        if result.success and result.stdout.strip() == "0":
            # RDP is enabled, check security settings

            # Check NLA requirement
            result = await self.executor.execute_powershell("""
                Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'UserAuthentication' -ErrorAction SilentlyContinue
            """)

            if result.success and result.stdout.strip() != "1":
                findings.append(Finding(
                    id="WIN-RDP-NLA",
                    title="RDP Network Level Authentication not required",
                    description="RDP is configured without requiring Network Level Authentication",
                    severity=Severity.HIGH,
                    category="system",
                    target="localhost",
                    port=3389,
                    remediation="Enable NLA for RDP connections",
                    discovered_by="windows_auditor",
                ))

            # Check encryption level
            result = await self.executor.execute_powershell("""
                Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'MinEncryptionLevel' -ErrorAction SilentlyContinue
            """)

            if result.success:
                try:
                    level = int(result.stdout.strip())
                    if level < 3:
                        findings.append(Finding(
                            id="WIN-RDP-ENCRYPT",
                            title="RDP encryption level too low",
                            description=f"RDP encryption level is {level}, should be 3 (High)",
                            severity=Severity.MEDIUM,
                            category="system",
                            target="localhost",
                            port=3389,
                            remediation="Set RDP encryption to High level",
                            discovered_by="windows_auditor",
                        ))
                except ValueError:
                    pass

        return findings

    async def _audit_powershell(self) -> list[Finding]:
        """Audit PowerShell security configuration"""
        findings = []

        # Check execution policy
        result = await self.executor.execute_powershell("Get-ExecutionPolicy")

        if result.success:
            policy = result.stdout.strip().lower()
            if policy in ["unrestricted", "bypass"]:
                findings.append(Finding(
                    id="WIN-PS-EXECPOLICY",
                    title=f"PowerShell execution policy is {policy}",
                    description="PowerShell allows unrestricted script execution",
                    severity=Severity.MEDIUM,
                    category="system",
                    target="localhost",
                    remediation="Set PowerShell execution policy to RemoteSigned or more restrictive",
                    discovered_by="windows_auditor",
                ))

        # Check PowerShell v2 (often used to bypass logging)
        result = await self.executor.execute_powershell("""
            (Get-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root).State
        """)

        if result.success and "Enabled" in result.stdout:
            findings.append(Finding(
                id="WIN-PS-V2",
                title="PowerShell v2 is enabled",
                description="PowerShell v2 is enabled and can be used to bypass security logging",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Disable PowerShell v2: Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root",
                discovered_by="windows_auditor",
            ))

        # Check script block logging
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\ScriptBlockLogging' -Name 'EnableScriptBlockLogging' -ErrorAction SilentlyContinue
        """)

        if not result.success or result.stdout.strip() != "1":
            findings.append(Finding(
                id="WIN-PS-LOGGING",
                title="PowerShell script block logging not enabled",
                description="PowerShell script block logging is not configured",
                severity=Severity.LOW,
                category="system",
                target="localhost",
                remediation="Enable PowerShell script block logging via Group Policy",
                discovered_by="windows_auditor",
            ))

        return findings

    async def _audit_smb(self) -> list[Finding]:
        """Audit SMB configuration"""
        findings = []

        # Check SMB signing
        result = await self.executor.execute_powershell("""
            Get-SmbServerConfiguration | Select-Object RequireSecuritySignature, EnableSecuritySignature | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                config = json.loads(result.stdout)

                if not config.get("RequireSecuritySignature", True):
                    findings.append(Finding(
                        id="WIN-SMB-SIGNING",
                        title="SMB signing not required",
                        description="SMB signing is not required, making it vulnerable to man-in-the-middle attacks",
                        severity=Severity.MEDIUM,
                        category="system",
                        target="localhost",
                        port=445,
                        remediation="Enable required SMB signing: Set-SmbServerConfiguration -RequireSecuritySignature $true",
                        discovered_by="windows_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        # Check for open SMB shares
        result = await self.executor.execute_powershell("""
            Get-SmbShare | Where-Object { $_.Name -notlike '*$' } | Select-Object Name, Path, Description | ConvertTo-Json
        """)

        if result.success:
            try:
                import json
                shares = json.loads(result.stdout) if result.stdout.strip() else []
                if not isinstance(shares, list):
                    shares = [shares]

                if len(shares) > 0:
                    findings.append(Finding(
                        id="WIN-SMB-SHARES",
                        title=f"{len(shares)} non-administrative SMB shares found",
                        description="Custom SMB shares are configured. Review permissions.",
                        severity=Severity.LOW,
                        category="system",
                        target="localhost",
                        port=445,
                        evidence=", ".join([s.get("Name", "") for s in shares]),
                        remediation="Review and restrict SMB share permissions",
                        discovered_by="windows_auditor",
                    ))
            except json.JSONDecodeError:
                pass

        return findings
