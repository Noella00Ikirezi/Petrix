"""
CIS Linux Benchmark
Security configuration checks based on CIS Benchmarks for Linux
"""

import os
from typing import Optional

from .base import (
    ComplianceBenchmark,
    ComplianceCheck,
    ComplianceResult,
    ComplianceStatus,
    ComplianceLevel,
)
from ...platform.executor import CommandExecutor, LocalExecutor


class CISLinuxBenchmark(ComplianceBenchmark):
    """
    CIS Benchmark for Linux systems
    Based on CIS Benchmark for Ubuntu/Debian and RHEL/CentOS
    """

    def __init__(self, executor: Optional[CommandExecutor] = None):
        super().__init__(executor)

    @property
    def benchmark_name(self) -> str:
        return "CIS Linux Benchmark"

    @property
    def benchmark_version(self) -> str:
        return "1.0.0"

    def _register_checks(self):
        """Register all CIS Linux checks"""

        # === 1. Initial Setup ===

        # 1.1 Filesystem Configuration
        self.checks.append(ComplianceCheck(
            id="1.1.1.1",
            title="Ensure mounting of cramfs is disabled",
            description="The cramfs filesystem type is a compressed read-only Linux filesystem",
            level=ComplianceLevel.LEVEL_1,
            category="Filesystem",
            check_func=self._check_cramfs_disabled,
            remediation="Add 'install cramfs /bin/true' to /etc/modprobe.d/cramfs.conf",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.1.2",
            title="Ensure mounting of squashfs is disabled",
            description="The squashfs filesystem type is a compressed read-only Linux filesystem",
            level=ComplianceLevel.LEVEL_2,
            category="Filesystem",
            check_func=self._check_squashfs_disabled,
            remediation="Add 'install squashfs /bin/true' to /etc/modprobe.d/squashfs.conf",
        ))

        self.checks.append(ComplianceCheck(
            id="1.1.1.3",
            title="Ensure mounting of udf is disabled",
            description="The udf filesystem type is the universal disk format",
            level=ComplianceLevel.LEVEL_1,
            category="Filesystem",
            check_func=self._check_udf_disabled,
            remediation="Add 'install udf /bin/true' to /etc/modprobe.d/udf.conf",
        ))

        # 1.4 Secure Boot Settings
        self.checks.append(ComplianceCheck(
            id="1.4.1",
            title="Ensure bootloader password is set",
            description="Setting the boot loader password will require that anyone rebooting must enter a password",
            level=ComplianceLevel.LEVEL_1,
            category="Boot",
            check_func=self._check_bootloader_password,
            remediation="Set GRUB bootloader password",
        ))

        # === 2. Services ===

        self.checks.append(ComplianceCheck(
            id="2.1.1",
            title="Ensure xinetd is not installed",
            description="xinetd is a super-server daemon that was historically used to manage network services",
            level=ComplianceLevel.LEVEL_1,
            category="Services",
            check_func=self._check_xinetd_not_installed,
            remediation="Remove xinetd: apt remove xinetd or yum remove xinetd",
        ))

        self.checks.append(ComplianceCheck(
            id="2.2.1",
            title="Ensure time synchronization is in use",
            description="System time should be synchronized between all systems",
            level=ComplianceLevel.LEVEL_1,
            category="Services",
            check_func=self._check_time_sync,
            remediation="Install and configure chrony or ntp",
        ))

        # === 3. Network Configuration ===

        self.checks.append(ComplianceCheck(
            id="3.1.1",
            title="Ensure IP forwarding is disabled",
            description="IP forwarding allows the system to forward packets from one network to another",
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            check_func=self._check_ip_forwarding_disabled,
            remediation="Set net.ipv4.ip_forward = 0 in /etc/sysctl.conf",
        ))

        self.checks.append(ComplianceCheck(
            id="3.1.2",
            title="Ensure packet redirect sending is disabled",
            description="ICMP Redirects are used to send routing information to other hosts",
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            check_func=self._check_send_redirects_disabled,
            remediation="Set net.ipv4.conf.all.send_redirects = 0",
        ))

        self.checks.append(ComplianceCheck(
            id="3.2.1",
            title="Ensure source routed packets are not accepted",
            description="Source routed packets allow the source to specify the route for the packet",
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            check_func=self._check_source_route_disabled,
            remediation="Set net.ipv4.conf.all.accept_source_route = 0",
        ))

        self.checks.append(ComplianceCheck(
            id="3.2.2",
            title="Ensure ICMP redirects are not accepted",
            description="ICMP redirect messages are packets that convey routing information",
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            check_func=self._check_icmp_redirects_disabled,
            remediation="Set net.ipv4.conf.all.accept_redirects = 0",
        ))

        # === 4. Logging and Auditing ===

        self.checks.append(ComplianceCheck(
            id="4.1.1",
            title="Ensure auditd is installed",
            description="auditd is the userspace component to the Linux Auditing System",
            level=ComplianceLevel.LEVEL_2,
            category="Logging",
            check_func=self._check_auditd_installed,
            remediation="Install auditd: apt install auditd or yum install audit",
        ))

        self.checks.append(ComplianceCheck(
            id="4.1.2",
            title="Ensure auditd service is enabled",
            description="Enable and start the auditd daemon to record system events",
            level=ComplianceLevel.LEVEL_2,
            category="Logging",
            check_func=self._check_auditd_enabled,
            remediation="Enable auditd: systemctl enable auditd",
        ))

        self.checks.append(ComplianceCheck(
            id="4.2.1",
            title="Ensure rsyslog is installed",
            description="rsyslog provides a system utility providing support for message logging",
            level=ComplianceLevel.LEVEL_1,
            category="Logging",
            check_func=self._check_rsyslog_installed,
            remediation="Install rsyslog: apt install rsyslog",
        ))

        # === 5. Access, Authentication and Authorization ===

        self.checks.append(ComplianceCheck(
            id="5.1.1",
            title="Ensure cron daemon is enabled",
            description="The cron daemon is used to execute batch jobs",
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            check_func=self._check_cron_enabled,
            remediation="Enable cron: systemctl enable cron",
        ))

        self.checks.append(ComplianceCheck(
            id="5.2.1",
            title="Ensure permissions on /etc/ssh/sshd_config are configured",
            description="The /etc/ssh/sshd_config file contains configuration specifications for sshd",
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            check_func=self._check_sshd_config_permissions,
            remediation="chmod 600 /etc/ssh/sshd_config",
        ))

        self.checks.append(ComplianceCheck(
            id="5.2.4",
            title="Ensure SSH Protocol is set to 2",
            description="SSH Protocol 1 has known vulnerabilities",
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            check_func=self._check_ssh_protocol,
            remediation="Set 'Protocol 2' in /etc/ssh/sshd_config",
        ))

        self.checks.append(ComplianceCheck(
            id="5.2.5",
            title="Ensure SSH LogLevel is appropriate",
            description="INFO level is the basic level that only records login activity",
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            check_func=self._check_ssh_loglevel,
            remediation="Set 'LogLevel INFO' or 'LogLevel VERBOSE' in /etc/ssh/sshd_config",
        ))

        self.checks.append(ComplianceCheck(
            id="5.2.8",
            title="Ensure SSH root login is disabled",
            description="Disallowing root logins over SSH requires system admins to authenticate using their own credentials",
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            check_func=self._check_ssh_root_login,
            remediation="Set 'PermitRootLogin no' in /etc/ssh/sshd_config",
        ))

        self.checks.append(ComplianceCheck(
            id="5.2.9",
            title="Ensure SSH PermitEmptyPasswords is disabled",
            description="Disallowing remote shell access to accounts that have an empty password",
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            check_func=self._check_ssh_empty_passwords,
            remediation="Set 'PermitEmptyPasswords no' in /etc/ssh/sshd_config",
        ))

        self.checks.append(ComplianceCheck(
            id="5.3.1",
            title="Ensure password creation requirements are configured",
            description="Strong passwords protect systems from being hacked through brute force methods",
            level=ComplianceLevel.LEVEL_1,
            category="Password",
            check_func=self._check_password_requirements,
            remediation="Configure password requirements in /etc/security/pwquality.conf",
        ))

        self.checks.append(ComplianceCheck(
            id="5.4.1.1",
            title="Ensure password expiration is 365 days or less",
            description="Password expiration should be set to 365 days or less",
            level=ComplianceLevel.LEVEL_1,
            category="Password",
            check_func=self._check_password_expiration,
            remediation="Set PASS_MAX_DAYS 365 in /etc/login.defs",
        ))

        self.checks.append(ComplianceCheck(
            id="5.4.2",
            title="Ensure system accounts are secured",
            description="System accounts should be non-login accounts",
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            check_func=self._check_system_accounts,
            remediation="Set shell to /usr/sbin/nologin for system accounts",
        ))

        self.checks.append(ComplianceCheck(
            id="5.4.4",
            title="Ensure default user umask is 027 or more restrictive",
            description="The umask controls the default permissions given to files",
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            check_func=self._check_umask,
            remediation="Set umask 027 in /etc/profile and /etc/bashrc",
        ))

        # === 6. System Maintenance ===

        self.checks.append(ComplianceCheck(
            id="6.1.1",
            title="Ensure permissions on /etc/passwd are configured",
            description="/etc/passwd should be readable by all users but only writable by root",
            level=ComplianceLevel.LEVEL_1,
            category="Permissions",
            check_func=self._check_passwd_permissions,
            remediation="chmod 644 /etc/passwd",
        ))

        self.checks.append(ComplianceCheck(
            id="6.1.2",
            title="Ensure permissions on /etc/shadow are configured",
            description="/etc/shadow should only be readable by root",
            level=ComplianceLevel.LEVEL_1,
            category="Permissions",
            check_func=self._check_shadow_permissions,
            remediation="chmod 640 /etc/shadow",
        ))

        self.checks.append(ComplianceCheck(
            id="6.2.1",
            title="Ensure password fields are not empty",
            description="All accounts must have a password or be locked",
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            check_func=self._check_empty_passwords,
            remediation="Set passwords for all accounts or lock unused accounts",
        ))

        self.checks.append(ComplianceCheck(
            id="6.2.2",
            title="Ensure no legacy '+' entries exist in /etc/passwd",
            description="Legacy NIS '+' entries allow blank passwords",
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            check_func=self._check_legacy_entries,
            remediation="Remove '+' entries from /etc/passwd",
        ))

        self.checks.append(ComplianceCheck(
            id="6.2.5",
            title="Ensure root is the only UID 0 account",
            description="Any account with UID 0 has superuser privileges",
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            check_func=self._check_uid_zero,
            remediation="Remove or change UID of unauthorized UID 0 accounts",
        ))

    # === Check Implementations ===

    async def _check_cramfs_disabled(self) -> ComplianceResult:
        """Check if cramfs is disabled"""
        result = await self.executor.execute("modprobe -n -v cramfs 2>&1")

        status = ComplianceStatus.PASS if "install /bin/true" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="1.1.1.1",
            title="Ensure mounting of cramfs is disabled",
            description="The cramfs filesystem type is a compressed read-only Linux filesystem",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Filesystem",
            expected="install /bin/true",
            actual=result.stdout.strip(),
            remediation="Add 'install cramfs /bin/true' to /etc/modprobe.d/cramfs.conf",
        )

    async def _check_squashfs_disabled(self) -> ComplianceResult:
        """Check if squashfs is disabled"""
        result = await self.executor.execute("modprobe -n -v squashfs 2>&1")

        status = ComplianceStatus.PASS if "install /bin/true" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="1.1.1.2",
            title="Ensure mounting of squashfs is disabled",
            description="The squashfs filesystem type is a compressed read-only Linux filesystem",
            status=status,
            level=ComplianceLevel.LEVEL_2,
            category="Filesystem",
            expected="install /bin/true",
            actual=result.stdout.strip(),
            remediation="Add 'install squashfs /bin/true' to /etc/modprobe.d/squashfs.conf",
        )

    async def _check_udf_disabled(self) -> ComplianceResult:
        """Check if udf is disabled"""
        result = await self.executor.execute("modprobe -n -v udf 2>&1")

        status = ComplianceStatus.PASS if "install /bin/true" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="1.1.1.3",
            title="Ensure mounting of udf is disabled",
            description="The udf filesystem type is the universal disk format",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Filesystem",
            expected="install /bin/true",
            actual=result.stdout.strip(),
            remediation="Add 'install udf /bin/true' to /etc/modprobe.d/udf.conf",
        )

    async def _check_bootloader_password(self) -> ComplianceResult:
        """Check if bootloader password is set"""
        result = await self.executor.execute("grep '^GRUB2_PASSWORD' /boot/grub2/user.cfg 2>/dev/null || grep '^password' /boot/grub/grub.cfg 2>/dev/null")

        status = ComplianceStatus.PASS if result.stdout.strip() else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="1.4.1",
            title="Ensure bootloader password is set",
            description="Setting the boot loader password protects against unauthorized modifications",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Boot",
            expected="GRUB password configured",
            actual="Password set" if result.stdout.strip() else "No password set",
            remediation="Set GRUB bootloader password using grub2-setpassword",
        )

    async def _check_xinetd_not_installed(self) -> ComplianceResult:
        """Check if xinetd is not installed"""
        result = await self.executor.execute("dpkg -s xinetd 2>/dev/null || rpm -q xinetd 2>/dev/null")

        status = ComplianceStatus.PASS if result.return_code != 0 else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.1.1",
            title="Ensure xinetd is not installed",
            description="xinetd is a super-server daemon that was historically used",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Services",
            expected="Not installed",
            actual="Installed" if result.return_code == 0 else "Not installed",
            remediation="Remove xinetd: apt remove xinetd or yum remove xinetd",
        )

    async def _check_time_sync(self) -> ComplianceResult:
        """Check if time synchronization is configured"""
        chrony = await self.executor.execute("systemctl is-active chronyd 2>/dev/null")
        ntp = await self.executor.execute("systemctl is-active ntpd 2>/dev/null")
        timesyncd = await self.executor.execute("systemctl is-active systemd-timesyncd 2>/dev/null")

        sync_active = any(
            "active" in r.stdout
            for r in [chrony, ntp, timesyncd]
        )

        status = ComplianceStatus.PASS if sync_active else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="2.2.1",
            title="Ensure time synchronization is in use",
            description="System time should be synchronized",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Services",
            expected="Time sync service active",
            actual="Active" if sync_active else "No time sync service",
            remediation="Install and enable chrony: apt install chrony && systemctl enable chronyd",
        )

    async def _check_ip_forwarding_disabled(self) -> ComplianceResult:
        """Check if IP forwarding is disabled"""
        result = await self.executor.execute("sysctl net.ipv4.ip_forward")

        value = result.stdout.strip().split("=")[-1].strip() if result.success else "unknown"
        status = ComplianceStatus.PASS if value == "0" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="3.1.1",
            title="Ensure IP forwarding is disabled",
            description="IP forwarding allows packet routing between networks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            expected="net.ipv4.ip_forward = 0",
            actual=result.stdout.strip(),
            remediation="Set net.ipv4.ip_forward = 0 in /etc/sysctl.conf",
        )

    async def _check_send_redirects_disabled(self) -> ComplianceResult:
        """Check if sending ICMP redirects is disabled"""
        result = await self.executor.execute("sysctl net.ipv4.conf.all.send_redirects")

        value = result.stdout.strip().split("=")[-1].strip() if result.success else "unknown"
        status = ComplianceStatus.PASS if value == "0" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="3.1.2",
            title="Ensure packet redirect sending is disabled",
            description="ICMP Redirects can be used in routing attacks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            expected="net.ipv4.conf.all.send_redirects = 0",
            actual=result.stdout.strip(),
            remediation="Set net.ipv4.conf.all.send_redirects = 0",
        )

    async def _check_source_route_disabled(self) -> ComplianceResult:
        """Check if source routed packets are rejected"""
        result = await self.executor.execute("sysctl net.ipv4.conf.all.accept_source_route")

        value = result.stdout.strip().split("=")[-1].strip() if result.success else "unknown"
        status = ComplianceStatus.PASS if value == "0" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="3.2.1",
            title="Ensure source routed packets are not accepted",
            description="Source routed packets can be used in attacks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            expected="net.ipv4.conf.all.accept_source_route = 0",
            actual=result.stdout.strip(),
            remediation="Set net.ipv4.conf.all.accept_source_route = 0",
        )

    async def _check_icmp_redirects_disabled(self) -> ComplianceResult:
        """Check if ICMP redirects are disabled"""
        result = await self.executor.execute("sysctl net.ipv4.conf.all.accept_redirects")

        value = result.stdout.strip().split("=")[-1].strip() if result.success else "unknown"
        status = ComplianceStatus.PASS if value == "0" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="3.2.2",
            title="Ensure ICMP redirects are not accepted",
            description="ICMP redirects can be used in man-in-the-middle attacks",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Network",
            expected="net.ipv4.conf.all.accept_redirects = 0",
            actual=result.stdout.strip(),
            remediation="Set net.ipv4.conf.all.accept_redirects = 0",
        )

    async def _check_auditd_installed(self) -> ComplianceResult:
        """Check if auditd is installed"""
        result = await self.executor.execute("dpkg -s auditd 2>/dev/null || rpm -q audit 2>/dev/null")

        status = ComplianceStatus.PASS if result.return_code == 0 else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="4.1.1",
            title="Ensure auditd is installed",
            description="auditd provides system auditing capabilities",
            status=status,
            level=ComplianceLevel.LEVEL_2,
            category="Logging",
            expected="Installed",
            actual="Installed" if result.return_code == 0 else "Not installed",
            remediation="Install auditd: apt install auditd",
        )

    async def _check_auditd_enabled(self) -> ComplianceResult:
        """Check if auditd is enabled"""
        result = await self.executor.execute("systemctl is-enabled auditd 2>/dev/null")

        status = ComplianceStatus.PASS if "enabled" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="4.1.2",
            title="Ensure auditd service is enabled",
            description="auditd should be enabled to capture security events",
            status=status,
            level=ComplianceLevel.LEVEL_2,
            category="Logging",
            expected="enabled",
            actual=result.stdout.strip(),
            remediation="Enable auditd: systemctl enable auditd",
        )

    async def _check_rsyslog_installed(self) -> ComplianceResult:
        """Check if rsyslog is installed"""
        result = await self.executor.execute("dpkg -s rsyslog 2>/dev/null || rpm -q rsyslog 2>/dev/null")

        status = ComplianceStatus.PASS if result.return_code == 0 else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="4.2.1",
            title="Ensure rsyslog is installed",
            description="rsyslog provides system logging capabilities",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Logging",
            expected="Installed",
            actual="Installed" if result.return_code == 0 else "Not installed",
            remediation="Install rsyslog: apt install rsyslog",
        )

    async def _check_cron_enabled(self) -> ComplianceResult:
        """Check if cron is enabled"""
        result = await self.executor.execute("systemctl is-enabled cron 2>/dev/null || systemctl is-enabled crond 2>/dev/null")

        status = ComplianceStatus.PASS if "enabled" in result.stdout else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.1.1",
            title="Ensure cron daemon is enabled",
            description="cron is used for scheduled jobs",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            expected="enabled",
            actual=result.stdout.strip(),
            remediation="Enable cron: systemctl enable cron",
        )

    async def _check_sshd_config_permissions(self) -> ComplianceResult:
        """Check sshd_config permissions"""
        result = await self.executor.execute("stat -c '%a' /etc/ssh/sshd_config 2>/dev/null")

        perms = result.stdout.strip()
        status = ComplianceStatus.PASS if perms in ["600", "400"] else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.2.1",
            title="Ensure permissions on /etc/ssh/sshd_config are configured",
            description="sshd_config should be restricted to root only",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            expected="600 or 400",
            actual=perms,
            remediation="chmod 600 /etc/ssh/sshd_config",
        )

    async def _check_ssh_protocol(self) -> ComplianceResult:
        """Check SSH protocol version"""
        # Protocol 2 is default in modern SSH, so we check it's not set to 1
        result = await self.executor.execute("grep -i '^Protocol' /etc/ssh/sshd_config 2>/dev/null")

        if not result.stdout.strip():
            status = ComplianceStatus.PASS  # Default is 2
        elif "1" in result.stdout and "2" not in result.stdout:
            status = ComplianceStatus.FAIL
        else:
            status = ComplianceStatus.PASS

        return ComplianceResult(
            check_id="5.2.4",
            title="Ensure SSH Protocol is set to 2",
            description="SSH Protocol 1 has known vulnerabilities",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            expected="Protocol 2 (or not set)",
            actual=result.stdout.strip() or "Not set (default: 2)",
            remediation="Set 'Protocol 2' in /etc/ssh/sshd_config",
        )

    async def _check_ssh_loglevel(self) -> ComplianceResult:
        """Check SSH log level"""
        result = await self.executor.execute("grep -i '^LogLevel' /etc/ssh/sshd_config 2>/dev/null")

        log_level = result.stdout.strip().split()[-1] if result.stdout.strip() else "INFO"
        acceptable = ["INFO", "VERBOSE"]

        status = ComplianceStatus.PASS if log_level.upper() in acceptable else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.2.5",
            title="Ensure SSH LogLevel is appropriate",
            description="SSH should log authentication events",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            expected="INFO or VERBOSE",
            actual=log_level,
            remediation="Set 'LogLevel INFO' in /etc/ssh/sshd_config",
        )

    async def _check_ssh_root_login(self) -> ComplianceResult:
        """Check if SSH root login is disabled"""
        result = await self.executor.execute("grep -i '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null")

        setting = result.stdout.strip().lower()
        status = ComplianceStatus.PASS if "no" in setting else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.2.8",
            title="Ensure SSH root login is disabled",
            description="Direct root login should be disabled",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            expected="PermitRootLogin no",
            actual=result.stdout.strip() or "Not set",
            remediation="Set 'PermitRootLogin no' in /etc/ssh/sshd_config",
        )

    async def _check_ssh_empty_passwords(self) -> ComplianceResult:
        """Check if empty passwords are disabled"""
        result = await self.executor.execute("grep -i '^PermitEmptyPasswords' /etc/ssh/sshd_config 2>/dev/null")

        setting = result.stdout.strip().lower()
        # Default is no, so pass if not set or set to no
        status = ComplianceStatus.PASS if not setting or "no" in setting else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.2.9",
            title="Ensure SSH PermitEmptyPasswords is disabled",
            description="Empty passwords should not be allowed",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="SSH",
            expected="PermitEmptyPasswords no",
            actual=result.stdout.strip() or "Not set (default: no)",
            remediation="Set 'PermitEmptyPasswords no' in /etc/ssh/sshd_config",
        )

    async def _check_password_requirements(self) -> ComplianceResult:
        """Check password complexity requirements"""
        result = await self.executor.execute("grep -E '^minlen|^minclass|^dcredit|^ucredit|^lcredit|^ocredit' /etc/security/pwquality.conf 2>/dev/null")

        has_requirements = bool(result.stdout.strip())
        status = ComplianceStatus.PASS if has_requirements else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.3.1",
            title="Ensure password creation requirements are configured",
            description="Strong passwords protect against brute force",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password",
            expected="Password requirements configured",
            actual=result.stdout.strip() or "No requirements set",
            remediation="Configure password requirements in /etc/security/pwquality.conf",
        )

    async def _check_password_expiration(self) -> ComplianceResult:
        """Check password expiration settings"""
        result = await self.executor.execute("grep '^PASS_MAX_DAYS' /etc/login.defs")

        try:
            max_days = int(result.stdout.strip().split()[-1])
            status = ComplianceStatus.PASS if 0 < max_days <= 365 else ComplianceStatus.FAIL
        except (ValueError, IndexError):
            status = ComplianceStatus.FAIL
            max_days = "Not set"

        return ComplianceResult(
            check_id="5.4.1.1",
            title="Ensure password expiration is 365 days or less",
            description="Passwords should expire within a year",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Password",
            expected="PASS_MAX_DAYS <= 365",
            actual=str(max_days),
            remediation="Set PASS_MAX_DAYS 365 in /etc/login.defs",
        )

    async def _check_system_accounts(self) -> ComplianceResult:
        """Check if system accounts are secured"""
        result = await self.executor.execute(
            "awk -F: '($1!=\"root\" && $1!=\"sync\" && $1!=\"shutdown\" && $1!=\"halt\" && $3<1000 && $7!=\"/usr/sbin/nologin\" && $7!=\"/bin/false\" && $7!=\"/sbin/nologin\") {print $1}' /etc/passwd"
        )

        accounts = result.stdout.strip()
        status = ComplianceStatus.PASS if not accounts else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.4.2",
            title="Ensure system accounts are secured",
            description="System accounts should not have login shells",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            expected="No system accounts with login shells",
            actual=accounts or "All secured",
            remediation="Set shell to /usr/sbin/nologin for system accounts",
        )

    async def _check_umask(self) -> ComplianceResult:
        """Check default umask setting"""
        result = await self.executor.execute("grep -E '^umask' /etc/profile /etc/bashrc /etc/bash.bashrc 2>/dev/null")

        # Look for 027 or more restrictive (022 is less restrictive)
        umask_good = "027" in result.stdout or "077" in result.stdout

        status = ComplianceStatus.PASS if umask_good else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="5.4.4",
            title="Ensure default user umask is 027 or more restrictive",
            description="Restrictive umask limits default file permissions",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Access",
            expected="umask 027 or 077",
            actual=result.stdout.strip() or "Not set",
            remediation="Set umask 027 in /etc/profile and /etc/bashrc",
        )

    async def _check_passwd_permissions(self) -> ComplianceResult:
        """Check /etc/passwd permissions"""
        result = await self.executor.execute("stat -c '%a' /etc/passwd")

        perms = result.stdout.strip()
        status = ComplianceStatus.PASS if perms == "644" else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="6.1.1",
            title="Ensure permissions on /etc/passwd are configured",
            description="/etc/passwd should be readable but not writable",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Permissions",
            expected="644",
            actual=perms,
            remediation="chmod 644 /etc/passwd",
        )

    async def _check_shadow_permissions(self) -> ComplianceResult:
        """Check /etc/shadow permissions"""
        result = await self.executor.execute("stat -c '%a' /etc/shadow")

        perms = result.stdout.strip()
        status = ComplianceStatus.PASS if perms in ["640", "600", "400", "000"] else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="6.1.2",
            title="Ensure permissions on /etc/shadow are configured",
            description="/etc/shadow should be restricted to root",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Permissions",
            expected="640 or more restrictive",
            actual=perms,
            remediation="chmod 640 /etc/shadow",
        )

    async def _check_empty_passwords(self) -> ComplianceResult:
        """Check for accounts with empty passwords"""
        result = await self.executor.execute("awk -F: '($2 == \"\") {print $1}' /etc/shadow 2>/dev/null")

        accounts = result.stdout.strip()
        status = ComplianceStatus.PASS if not accounts else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="6.2.1",
            title="Ensure password fields are not empty",
            description="All accounts must have a password or be locked",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            expected="No empty password fields",
            actual=accounts or "None found",
            remediation="Set passwords or lock accounts with empty passwords",
        )

    async def _check_legacy_entries(self) -> ComplianceResult:
        """Check for legacy NIS entries"""
        result = await self.executor.execute("grep '^+:' /etc/passwd /etc/shadow /etc/group 2>/dev/null")

        entries = result.stdout.strip()
        status = ComplianceStatus.PASS if not entries else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="6.2.2",
            title="Ensure no legacy '+' entries exist in /etc/passwd",
            description="Legacy NIS entries can allow blank passwords",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            expected="No '+' entries",
            actual=entries or "None found",
            remediation="Remove '+' entries from password files",
        )

    async def _check_uid_zero(self) -> ComplianceResult:
        """Check for multiple UID 0 accounts"""
        result = await self.executor.execute("awk -F: '($3 == 0 && $1 != \"root\") {print $1}' /etc/passwd")

        accounts = result.stdout.strip()
        status = ComplianceStatus.PASS if not accounts else ComplianceStatus.FAIL

        return ComplianceResult(
            check_id="6.2.5",
            title="Ensure root is the only UID 0 account",
            description="Only root should have UID 0",
            status=status,
            level=ComplianceLevel.LEVEL_1,
            category="Accounts",
            expected="No non-root UID 0 accounts",
            actual=accounts or "Only root",
            remediation="Remove or change UID of unauthorized UID 0 accounts",
        )
