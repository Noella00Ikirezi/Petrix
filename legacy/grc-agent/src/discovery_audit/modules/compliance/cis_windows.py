"""
CIS Windows Benchmark
Security configuration checks based on CIS Benchmarks for Windows
"""

from typing import Optional

from .base import (
    ComplianceBenchmark,
    ComplianceCheck,
    ComplianceResult,
    ComplianceStatus,
    ComplianceLevel,
)
from ...platform.executor import CommandExecutor, LocalExecutor


class CISWindowsBenchmark(ComplianceBenchmark):
    """
    CIS Benchmark for Windows systems
    Based on CIS Benchmark for Windows Server 2016/2019/2022
    """

    def __init__(self, executor: Optional[CommandExecutor] = None):
        super().__init__(executor)

    @property
    def benchmark_name(self) -> str:
        return "CIS Windows Benchmark"

    @property
    def benchmark_version(self) -> str:
        return "1.0.0"

    def _register_checks(self):
        """Register all CIS Windows checks"""

        # === 1. Account Policies ===

        self.checks.append(ComplianceCheck(
            id="1.1.1",
            title="Ensure 'Enforce password history' is set to '24 or more'",
            description="Password history prevents users from reusing recent passwords",
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            check_func=self._check_password_history,
            remediation="Set password history to 24 via Group Policy",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.2",
            title="Ensure 'Maximum password age' is set to '365 or fewer days'",
            description="Passwords should expire within a year",
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            check_func=self._check_max_password_age,
            remediation="Set maximum password age to 365 days or less",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.3",
            title="Ensure 'Minimum password age' is set to '1 or more'",
            description="Prevents immediate password changes to bypass history",
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            check_func=self._check_min_password_age,
            remediation="Set minimum password age to at least 1 day",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.4",
            title="Ensure 'Minimum password length' is set to '14 or more'",
            description="Longer passwords are more secure",
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            check_func=self._check_min_password_length,
            remediation="Set minimum password length to 14 characters",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.5",
            title="Ensure 'Password must meet complexity requirements' is Enabled",
            description="Complex passwords resist brute force attacks",
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            check_func=self._check_password_complexity,
            remediation="Enable password complexity requirements",
        ))

        self.checks.append(ComplianceCheck(
            id="1.2.1",
            title="Ensure 'Account lockout duration' is set to '15 or more minutes'",
            description="Slows down brute force attacks",
            level=ComplianceLevel.LEVEL_1,
            category="Account Lockout",
            check_func=self._check_lockout_duration,
            remediation="Set account lockout duration to 15 minutes or more",
        ))

        self.checks.append(ComplianceCheck(
            id="1.2.2",
            title="Ensure 'Account lockout threshold' is set to '5 or fewer'",
            description="Limits failed login attempts before lockout",
            level=ComplianceLevel.LEVEL_1,
            category="Account Lockout",
            check_func=self._check_lockout_threshold,
            remediation="Set account lockout threshold to 5 or fewer attempts",
        ))

        # === 2. Local Policies ===

        self.checks.append(ComplianceCheck(
            id="2.2.1",
            title="Ensure 'Access this computer from the network' is configured",
            description="Controls network access to the computer",
            level=ComplianceLevel.LEVEL_1,
            category="User Rights",
            check_func=self._check_network_access,
            remediation="Configure network access rights appropriately",
        ))

        self.checks.append(ComplianceCheck(
            id="2.2.2",
            title="Ensure 'Deny access to this computer from the network' includes Guests",
            description="Prevents Guest account network access",
            level=ComplianceLevel.LEVEL_1,
            category="User Rights",
            check_func=self._check_deny_network_access,
            remediation="Add Guests to 'Deny access to this computer from the network'",
        ))

        self.checks.append(ComplianceCheck(
            id="2.3.1.1",
            title="Ensure 'Accounts: Administrator account status' is Disabled",
            description="Built-in Administrator should be disabled",
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            check_func=self._check_admin_disabled,
            remediation="Disable the built-in Administrator account",
        ))

        self.checks.append(ComplianceCheck(
            id="2.3.1.2",
            title="Ensure 'Accounts: Guest account status' is Disabled",
            description="Guest account provides anonymous access",
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            check_func=self._check_guest_disabled,
            remediation="Disable the Guest account",
        ))

        self.checks.append(ComplianceCheck(
            id="2.3.7.1",
            title="Ensure 'Interactive logon: Do not display last user name' is Enabled",
            description="Prevents username enumeration",
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            check_func=self._check_no_last_username,
            remediation="Enable 'Do not display last user name'",
        ))

        self.checks.append(ComplianceCheck(
            id="2.3.10.1",
            title="Ensure 'Network access: Do not allow anonymous enumeration of SAM accounts' is Enabled",
            description="Prevents anonymous enumeration of accounts",
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            check_func=self._check_restrict_anonymous_sam,
            remediation="Enable restriction of anonymous SAM enumeration",
        ))

        self.checks.append(ComplianceCheck(
            id="2.3.11.1",
            title="Ensure 'Network security: LAN Manager authentication level' is configured",
            description="Controls NTLM authentication level",
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            check_func=self._check_lm_auth_level,
            remediation="Set LAN Manager authentication to 'Send NTLMv2 response only'",
        ))

        # === 9. Windows Firewall ===

        self.checks.append(ComplianceCheck(
            id="9.1.1",
            title="Ensure 'Windows Firewall: Domain: Firewall state' is On",
            description="Domain profile firewall should be enabled",
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            check_func=self._check_firewall_domain,
            remediation="Enable Windows Firewall for Domain profile",
        ))

        self.checks.append(ComplianceCheck(
            id="9.2.1",
            title="Ensure 'Windows Firewall: Private: Firewall state' is On",
            description="Private profile firewall should be enabled",
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            check_func=self._check_firewall_private,
            remediation="Enable Windows Firewall for Private profile",
        ))

        self.checks.append(ComplianceCheck(
            id="9.3.1",
            title="Ensure 'Windows Firewall: Public: Firewall state' is On",
            description="Public profile firewall should be enabled",
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            check_func=self._check_firewall_public,
            remediation="Enable Windows Firewall for Public profile",
        ))

        # === 17. Advanced Audit Policy ===

        self.checks.append(ComplianceCheck(
            id="17.1.1",
            title="Ensure 'Audit Credential Validation' is set to Success and Failure",
            description="Audits credential validation events",
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            check_func=self._check_audit_credential_validation,
            remediation="Enable auditing for Credential Validation",
        ))

        self.checks.append(ComplianceCheck(
            id="17.2.1",
            title="Ensure 'Audit Application Group Management' is set",
            description="Audits application group management events",
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            check_func=self._check_audit_app_group,
            remediation="Enable auditing for Application Group Management",
        ))

        self.checks.append(ComplianceCheck(
            id="17.5.1",
            title="Ensure 'Audit Account Lockout' is set to include Failure",
            description="Audits account lockout events",
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            check_func=self._check_audit_lockout,
            remediation="Enable failure auditing for Account Lockout",
        ))

        # === 18. Administrative Templates ===

        self.checks.append(ComplianceCheck(
            id="18.3.1",
            title="Ensure 'LAPS AdmPwd GPO Extension / CSE' is installed",
            description="Local Administrator Password Solution provides secure password management",
            level=ComplianceLevel.LEVEL_1,
            category="LAPS",
            check_func=self._check_laps_installed,
            remediation="Install LAPS from Microsoft",
        ))

        self.checks.append(ComplianceCheck(
            id="18.4.1",
            title="Ensure 'MSS: (AutoAdminLogon) is disabled'",
            description="Auto-admin logon is a security risk",
            level=ComplianceLevel.LEVEL_1,
            category="MSS",
            check_func=self._check_auto_admin_logon,
            remediation="Disable automatic admin logon",
        ))

        self.checks.append(ComplianceCheck(
            id="18.9.1",
            title="Ensure 'Turn off Windows Error Reporting' is Enabled",
            description="Error reporting may leak sensitive information",
            level=ComplianceLevel.LEVEL_2,
            category="Windows Components",
            check_func=self._check_error_reporting,
            remediation="Disable Windows Error Reporting",
        ))

    # === Check Implementations ===

    async def _check_password_history(self) -> ComplianceResult:
        """Check password history policy"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Length of password history'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if value >= 24 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.1.1",
            title="Ensure 'Enforce password history' is set to '24 or more'",
            description="Password history prevents users from reusing recent passwords",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            expected="24 or more",
            actual=str(value),
            remediation="Set password history to 24 via Group Policy",
        )

    async def _check_max_password_age(self) -> ComplianceResult:
        """Check maximum password age"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Maximum password age'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if 0 < value <= 365 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.1.2",
            title="Ensure 'Maximum password age' is set to '365 or fewer days'",
            description="Passwords should expire within a year",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            expected="1-365 days",
            actual=str(value),
            remediation="Set maximum password age to 365 days or less",
        )

    async def _check_min_password_age(self) -> ComplianceResult:
        """Check minimum password age"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Minimum password age'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if value >= 1 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.1.3",
            title="Ensure 'Minimum password age' is set to '1 or more'",
            description="Prevents immediate password changes",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            expected="1 or more days",
            actual=str(value),
            remediation="Set minimum password age to at least 1 day",
        )

    async def _check_min_password_length(self) -> ComplianceResult:
        """Check minimum password length"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Minimum password length'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if value >= 14 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.1.4",
            title="Ensure 'Minimum password length' is set to '14 or more'",
            description="Longer passwords are more secure",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            expected="14 or more",
            actual=str(value),
            remediation="Set minimum password length to 14 characters",
        )

    async def _check_password_complexity(self) -> ComplianceResult:
        """Check password complexity requirement"""
        result = await self.executor.execute_powershell("""
            $tempFile = [System.IO.Path]::GetTempFileName()
            secedit /export /cfg $tempFile /quiet
            $content = Get-Content $tempFile
            Remove-Item $tempFile
            $content | Select-String 'PasswordComplexity'
        """)

        status = ComplianceStatus.PASS if "= 1" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="1.1.5",
            title="Ensure 'Password must meet complexity requirements' is Enabled",
            description="Complex passwords resist brute force attacks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password Policy",
            expected="PasswordComplexity = 1",
            actual=result.stdout.strip() or "Not configured",
            remediation="Enable password complexity requirements",
        )

    async def _check_lockout_duration(self) -> ComplianceResult:
        """Check account lockout duration"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Lockout duration'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if value >= 15 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.2.1",
            title="Ensure 'Account lockout duration' is set to '15 or more minutes'",
            description="Slows down brute force attacks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Account Lockout",
            expected="15 or more minutes",
            actual=str(value),
            remediation="Set account lockout duration to 15 minutes or more",
        )

    async def _check_lockout_threshold(self) -> ComplianceResult:
        """Check account lockout threshold"""
        result = await self.executor.execute_powershell(
            "net accounts | Select-String 'Lockout threshold'"
        )

        try:
            value = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if 0 < value <= 5 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.ERROR
            value = "Unable to determine"

        return ComplianceResult(
            check_id="1.2.2",
            title="Ensure 'Account lockout threshold' is set to '5 or fewer'",
            description="Limits failed login attempts before lockout",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Account Lockout",
            expected="1-5 attempts",
            actual=str(value),
            remediation="Set account lockout threshold to 5 or fewer attempts",
        )

    async def _check_network_access(self) -> ComplianceResult:
        """Check network access rights"""
        # This is a manual review check
        return ComplianceResult(
            check_id="2.2.1",
            title="Ensure 'Access this computer from the network' is configured",
            description="Controls network access to the computer",
            status=ComplianceStatus.MANUAL,
            level=ComplianceLevel.LEVEL_1,
            category="User Rights",
            expected="Administrators, Authenticated Users (varies by role)",
            actual="Manual review required",
            remediation="Configure network access rights appropriately",
        )

    async def _check_deny_network_access(self) -> ComplianceResult:
        """Check deny network access includes Guests"""
        result = await self.executor.execute_powershell("""
            $tempFile = [System.IO.Path]::GetTempFileName()
            secedit /export /cfg $tempFile /quiet
            $content = Get-Content $tempFile
            Remove-Item $tempFile
            $content | Select-String 'SeDenyNetworkLogonRight'
        """)

        status = ComplianceStatus.PASS if "Guest" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.2.2",
            title="Ensure 'Deny access to this computer from the network' includes Guests",
            description="Prevents Guest account network access",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="User Rights",
            expected="Guests included",
            actual=result.stdout.strip() or "Not configured",
            remediation="Add Guests to 'Deny access to this computer from the network'",
        )

    async def _check_admin_disabled(self) -> ComplianceResult:
        """Check if built-in Administrator is disabled"""
        result = await self.executor.execute_powershell(
            "Get-LocalUser -Name Administrator | Select-Object Enabled"
        )

        status = ComplianceStatus.PASS if "False" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.3.1.1",
            title="Ensure 'Accounts: Administrator account status' is Disabled",
            description="Built-in Administrator should be disabled",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            expected="Enabled: False",
            actual=result.stdout.strip(),
            remediation="Disable the built-in Administrator account",
        )

    async def _check_guest_disabled(self) -> ComplianceResult:
        """Check if Guest account is disabled"""
        result = await self.executor.execute_powershell(
            "Get-LocalUser -Name Guest | Select-Object Enabled"
        )

        status = ComplianceStatus.PASS if "False" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.3.1.2",
            title="Ensure 'Accounts: Guest account status' is Disabled",
            description="Guest account provides anonymous access",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            expected="Enabled: False",
            actual=result.stdout.strip(),
            remediation="Disable the Guest account",
        )

    async def _check_no_last_username(self) -> ComplianceResult:
        """Check if last username display is disabled"""
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'DontDisplayLastUserName' -ErrorAction SilentlyContinue
        """)

        status = ComplianceStatus.PASS if result.stdout.strip() == "1" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.3.7.1",
            title="Ensure 'Interactive logon: Do not display last user name' is Enabled",
            description="Prevents username enumeration",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            expected="1 (Enabled)",
            actual=result.stdout.strip() or "Not configured",
            remediation="Enable 'Do not display last user name'",
        )

    async def _check_restrict_anonymous_sam(self) -> ComplianceResult:
        """Check anonymous SAM enumeration restriction"""
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name 'RestrictAnonymousSAM' -ErrorAction SilentlyContinue
        """)

        status = ComplianceStatus.PASS if result.stdout.strip() == "1" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.3.10.1",
            title="Ensure 'Network access: Do not allow anonymous enumeration of SAM accounts' is Enabled",
            description="Prevents anonymous enumeration of accounts",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            expected="1 (Enabled)",
            actual=result.stdout.strip() or "Not configured",
            remediation="Enable restriction of anonymous SAM enumeration",
        )

    async def _check_lm_auth_level(self) -> ComplianceResult:
        """Check LAN Manager authentication level"""
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name 'LmCompatibilityLevel' -ErrorAction SilentlyContinue
        """)

        try:
            value = int(result.stdout.strip())
            # 3 = Send NTLMv2 only, refuse LM & NTLM
            # 5 = Send NTLMv2 only, refuse LM & NTLM (DC)
            status = ComplianceStatus.PASS if value >= 3 else ComplianceStatus.FAIL
        except ValueError:
            status = ComplianceStatus.FAIL
            value = "Not configured"

        return ComplianceResult(
            check_id="2.3.11.1",
            title="Ensure 'Network security: LAN Manager authentication level' is configured",
            description="Controls NTLM authentication level",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Security Options",
            expected="3 or higher (NTLMv2 only)",
            actual=str(value),
            remediation="Set LAN Manager authentication to 'Send NTLMv2 response only'",
        )

    async def _check_firewall_domain(self) -> ComplianceResult:
        """Check Domain profile firewall"""
        result = await self.executor.execute_powershell(
            "Get-NetFirewallProfile -Name Domain | Select-Object Enabled"
        )

        status = ComplianceStatus.PASS if "True" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="9.1.1",
            title="Ensure 'Windows Firewall: Domain: Firewall state' is On",
            description="Domain profile firewall should be enabled",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            expected="Enabled: True",
            actual=result.stdout.strip(),
            remediation="Enable Windows Firewall for Domain profile",
        )

    async def _check_firewall_private(self) -> ComplianceResult:
        """Check Private profile firewall"""
        result = await self.executor.execute_powershell(
            "Get-NetFirewallProfile -Name Private | Select-Object Enabled"
        )

        status = ComplianceStatus.PASS if "True" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="9.2.1",
            title="Ensure 'Windows Firewall: Private: Firewall state' is On",
            description="Private profile firewall should be enabled",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            expected="Enabled: True",
            actual=result.stdout.strip(),
            remediation="Enable Windows Firewall for Private profile",
        )

    async def _check_firewall_public(self) -> ComplianceResult:
        """Check Public profile firewall"""
        result = await self.executor.execute_powershell(
            "Get-NetFirewallProfile -Name Public | Select-Object Enabled"
        )

        status = ComplianceStatus.PASS if "True" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="9.3.1",
            title="Ensure 'Windows Firewall: Public: Firewall state' is On",
            description="Public profile firewall should be enabled",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Firewall",
            expected="Enabled: True",
            actual=result.stdout.strip(),
            remediation="Enable Windows Firewall for Public profile",
        )

    async def _check_audit_credential_validation(self) -> ComplianceResult:
        """Check Credential Validation auditing"""
        result = await self.executor.execute_powershell(
            "auditpol /get /subcategory:'Credential Validation'"
        )

        has_success = "Success" in result.stdout
        has_failure = "Failure" in result.stdout

        status = ComplianceStatus.PASS if has_success and has_failure else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="17.1.1",
            title="Ensure 'Audit Credential Validation' is set to Success and Failure",
            description="Audits credential validation events",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            expected="Success and Failure",
            actual=result.stdout.strip(),
            remediation="Enable auditing for Credential Validation",
        )

    async def _check_audit_app_group(self) -> ComplianceResult:
        """Check Application Group Management auditing"""
        result = await self.executor.execute_powershell(
            "auditpol /get /subcategory:'Application Group Management'"
        )

        has_auditing = "Success" in result.stdout or "Failure" in result.stdout

        status = ComplianceStatus.PASS if has_auditing else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="17.2.1",
            title="Ensure 'Audit Application Group Management' is set",
            description="Audits application group management events",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            expected="Success and/or Failure",
            actual=result.stdout.strip(),
            remediation="Enable auditing for Application Group Management",
        )

    async def _check_audit_lockout(self) -> ComplianceResult:
        """Check Account Lockout auditing"""
        result = await self.executor.execute_powershell(
            "auditpol /get /subcategory:'Account Lockout'"
        )

        has_failure = "Failure" in result.stdout

        status = ComplianceStatus.PASS if has_failure else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="17.5.1",
            title="Ensure 'Audit Account Lockout' is set to include Failure",
            description="Audits account lockout events",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Audit Policy",
            expected="Failure enabled",
            actual=result.stdout.strip(),
            remediation="Enable failure auditing for Account Lockout",
        )

    async def _check_laps_installed(self) -> ComplianceResult:
        """Check if LAPS is installed"""
        result = await self.executor.execute_powershell(
            "Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' | Where-Object { $_.DisplayName -like '*LAPS*' }"
        )

        status = ComplianceStatus.PASS if result.stdout.strip() else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="18.3.1",
            title="Ensure 'LAPS AdmPwd GPO Extension / CSE' is installed",
            description="LAPS provides secure local admin password management",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="LAPS",
            expected="LAPS installed",
            actual="Installed" if result.stdout.strip() else "Not installed",
            remediation="Install LAPS from Microsoft",
        )

    async def _check_auto_admin_logon(self) -> ComplianceResult:
        """Check if auto admin logon is disabled"""
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon' -Name 'AutoAdminLogon' -ErrorAction SilentlyContinue
        """)

        # Should be 0 or not exist
        status = ComplianceStatus.PASS if not result.stdout.strip() or result.stdout.strip() == "0" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="18.4.1",
            title="Ensure 'MSS: (AutoAdminLogon) is disabled'",
            description="Auto-admin logon is a security risk",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="MSS",
            expected="0 or not configured",
            actual=result.stdout.strip() or "Not configured",
            remediation="Disable automatic admin logon",
        )

    async def _check_error_reporting(self) -> ComplianceResult:
        """Check if Windows Error Reporting is disabled"""
        result = await self.executor.execute_powershell("""
            Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Error Reporting' -Name 'Disabled' -ErrorAction SilentlyContinue
        """)

        status = ComplianceStatus.PASS if result.stdout.strip() == "1" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="18.9.1",
            title="Ensure 'Turn off Windows Error Reporting' is Enabled",
            description="Error reporting may leak sensitive information",
            status=status,
            level=ComplianceLevel.LEVEL_2,
            category="Windows Components",
            expected="1 (Disabled)",
            actual=result.stdout.strip() or "Not configured",
            remediation="Disable Windows Error Reporting via Group Policy",
        )
