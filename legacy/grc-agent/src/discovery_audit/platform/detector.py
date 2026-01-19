"""
Platform Detector - Detects OS type and gathers system information
"""

import os
import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OSType(str, Enum):
    """Operating System Types"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


class LinuxDistro(str, Enum):
    """Linux Distribution Types"""
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    CENTOS = "centos"
    RHEL = "rhel"
    FEDORA = "fedora"
    ARCH = "arch"
    ALPINE = "alpine"
    SUSE = "suse"
    UNKNOWN = "unknown"


class WindowsVersion(str, Enum):
    """Windows Version Types"""
    SERVER_2022 = "server_2022"
    SERVER_2019 = "server_2019"
    SERVER_2016 = "server_2016"
    SERVER_2012 = "server_2012"
    WINDOWS_11 = "windows_11"
    WINDOWS_10 = "windows_10"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Platform information container"""
    os_type: OSType
    os_name: str
    os_version: str
    kernel_version: str = ""
    architecture: str = ""
    hostname: str = ""
    fqdn: str = ""

    # Linux specific
    distro: LinuxDistro = LinuxDistro.UNKNOWN
    distro_version: str = ""
    package_manager: str = ""
    init_system: str = ""

    # Windows specific
    windows_version: WindowsVersion = WindowsVersion.UNKNOWN
    is_domain_joined: bool = False
    domain_name: str = ""
    is_domain_controller: bool = False

    # Privileges
    is_elevated: bool = False
    current_user: str = ""

    # Additional info
    cpu_count: int = 0
    memory_total_gb: float = 0.0

    # Raw data for debugging
    raw_data: dict = field(default_factory=dict)


class PlatformDetector:
    """
    Detects platform information for local and remote systems
    """

    @classmethod
    def detect_local(cls) -> PlatformInfo:
        """Detect local system platform information"""
        os_type = cls._detect_os_type()

        if os_type == OSType.WINDOWS:
            return cls._detect_windows_local()
        elif os_type == OSType.LINUX:
            return cls._detect_linux_local()
        elif os_type == OSType.MACOS:
            return cls._detect_macos_local()
        else:
            return PlatformInfo(
                os_type=OSType.UNKNOWN,
                os_name=platform.system(),
                os_version=platform.version(),
            )

    @classmethod
    def _detect_os_type(cls) -> OSType:
        """Detect the operating system type"""
        system = platform.system().lower()

        if system == "windows":
            return OSType.WINDOWS
        elif system == "linux":
            return OSType.LINUX
        elif system == "darwin":
            return OSType.MACOS
        else:
            return OSType.UNKNOWN

    @classmethod
    def _detect_linux_local(cls) -> PlatformInfo:
        """Detect Linux platform information"""
        import pwd

        info = PlatformInfo(
            os_type=OSType.LINUX,
            os_name=platform.system(),
            os_version=platform.release(),
            kernel_version=platform.release(),
            architecture=platform.machine(),
            hostname=platform.node(),
        )

        # Get current user
        info.current_user = pwd.getpwuid(os.getuid()).pw_name

        # Check if root
        info.is_elevated = os.getuid() == 0

        # Detect distribution
        info.distro, info.distro_version = cls._detect_linux_distro()

        # Detect package manager
        info.package_manager = cls._detect_package_manager()

        # Detect init system
        info.init_system = cls._detect_init_system()

        # Get FQDN
        try:
            import socket
            info.fqdn = socket.getfqdn()
        except Exception:
            info.fqdn = info.hostname

        # Get hardware info
        info.cpu_count = os.cpu_count() or 0
        info.memory_total_gb = cls._get_linux_memory_gb()

        return info

    @classmethod
    def _detect_linux_distro(cls) -> tuple[LinuxDistro, str]:
        """Detect Linux distribution"""
        distro = LinuxDistro.UNKNOWN
        version = ""

        # Try /etc/os-release first (modern standard)
        if os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release") as f:
                    os_release = {}
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            os_release[key] = value.strip('"')

                    distro_id = os_release.get("ID", "").lower()
                    version = os_release.get("VERSION_ID", "")

                    distro_map = {
                        "debian": LinuxDistro.DEBIAN,
                        "ubuntu": LinuxDistro.UBUNTU,
                        "centos": LinuxDistro.CENTOS,
                        "rhel": LinuxDistro.RHEL,
                        "fedora": LinuxDistro.FEDORA,
                        "arch": LinuxDistro.ARCH,
                        "alpine": LinuxDistro.ALPINE,
                        "opensuse": LinuxDistro.SUSE,
                        "sles": LinuxDistro.SUSE,
                    }

                    distro = distro_map.get(distro_id, LinuxDistro.UNKNOWN)

            except Exception:
                pass

        # Fallback to specific files
        if distro == LinuxDistro.UNKNOWN:
            if os.path.exists("/etc/debian_version"):
                distro = LinuxDistro.DEBIAN
            elif os.path.exists("/etc/redhat-release"):
                distro = LinuxDistro.RHEL
            elif os.path.exists("/etc/arch-release"):
                distro = LinuxDistro.ARCH
            elif os.path.exists("/etc/alpine-release"):
                distro = LinuxDistro.ALPINE

        return distro, version

    @classmethod
    def _detect_package_manager(cls) -> str:
        """Detect the system package manager"""
        package_managers = [
            ("apt", "/usr/bin/apt"),
            ("apt-get", "/usr/bin/apt-get"),
            ("yum", "/usr/bin/yum"),
            ("dnf", "/usr/bin/dnf"),
            ("pacman", "/usr/bin/pacman"),
            ("apk", "/sbin/apk"),
            ("zypper", "/usr/bin/zypper"),
        ]

        for name, path in package_managers:
            if os.path.exists(path):
                return name

        return "unknown"

    @classmethod
    def _detect_init_system(cls) -> str:
        """Detect the init system (systemd, sysvinit, etc.)"""
        if os.path.exists("/run/systemd/system"):
            return "systemd"
        elif os.path.exists("/etc/init.d"):
            return "sysvinit"
        elif os.path.exists("/sbin/openrc"):
            return "openrc"
        else:
            return "unknown"

    @classmethod
    def _get_linux_memory_gb(cls) -> float:
        """Get total memory in GB on Linux"""
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / 1024 / 1024, 2)
        except Exception:
            pass
        return 0.0

    @classmethod
    def _detect_windows_local(cls) -> PlatformInfo:
        """Detect Windows platform information"""
        info = PlatformInfo(
            os_type=OSType.WINDOWS,
            os_name=platform.system(),
            os_version=platform.version(),
            architecture=platform.machine(),
            hostname=platform.node(),
        )

        # Get current user
        info.current_user = os.environ.get("USERNAME", "unknown")

        # Check if elevated (admin)
        info.is_elevated = cls._check_windows_admin()

        # Detect Windows version
        info.windows_version = cls._detect_windows_version()

        # Check domain membership
        info.is_domain_joined, info.domain_name = cls._check_windows_domain()

        # Check if Domain Controller
        info.is_domain_controller = cls._check_is_domain_controller()

        # Get FQDN
        try:
            import socket
            info.fqdn = socket.getfqdn()
        except Exception:
            info.fqdn = info.hostname

        # Get hardware info
        info.cpu_count = os.cpu_count() or 0
        info.memory_total_gb = cls._get_windows_memory_gb()

        return info

    @classmethod
    def _check_windows_admin(cls) -> bool:
        """Check if running with admin privileges on Windows"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @classmethod
    def _detect_windows_version(cls) -> WindowsVersion:
        """Detect Windows version"""
        try:
            # Use PowerShell to get OS caption
            result = subprocess.run(
                ["powershell", "-Command", "(Get-WmiObject Win32_OperatingSystem).Caption"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                caption = result.stdout.strip().lower()

                if "server 2022" in caption:
                    return WindowsVersion.SERVER_2022
                elif "server 2019" in caption:
                    return WindowsVersion.SERVER_2019
                elif "server 2016" in caption:
                    return WindowsVersion.SERVER_2016
                elif "server 2012" in caption:
                    return WindowsVersion.SERVER_2012
                elif "windows 11" in caption:
                    return WindowsVersion.WINDOWS_11
                elif "windows 10" in caption:
                    return WindowsVersion.WINDOWS_10

        except Exception:
            pass

        return WindowsVersion.UNKNOWN

    @classmethod
    def _check_windows_domain(cls) -> tuple[bool, str]:
        """Check if Windows is domain joined"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "(Get-WmiObject Win32_ComputerSystem).PartOfDomain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            is_domain = result.stdout.strip().lower() == "true"

            if is_domain:
                result = subprocess.run(
                    ["powershell", "-Command", "(Get-WmiObject Win32_ComputerSystem).Domain"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                domain = result.stdout.strip()
                return True, domain

        except Exception:
            pass

        return False, ""

    @classmethod
    def _check_is_domain_controller(cls) -> bool:
        """Check if this Windows server is a Domain Controller"""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_ComputerSystem).DomainRole"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # DomainRole: 4 = Backup DC, 5 = Primary DC
            role = int(result.stdout.strip())
            return role in [4, 5]

        except Exception:
            pass

        return False

    @classmethod
    def _get_windows_memory_gb(cls) -> float:
        """Get total memory in GB on Windows"""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                bytes_total = int(result.stdout.strip())
                return round(bytes_total / 1024 / 1024 / 1024, 2)

        except Exception:
            pass

        return 0.0

    @classmethod
    def _detect_macos_local(cls) -> PlatformInfo:
        """Detect macOS platform information"""
        import pwd

        info = PlatformInfo(
            os_type=OSType.MACOS,
            os_name="macOS",
            os_version=platform.mac_ver()[0],
            kernel_version=platform.release(),
            architecture=platform.machine(),
            hostname=platform.node(),
        )

        info.current_user = pwd.getpwuid(os.getuid()).pw_name
        info.is_elevated = os.getuid() == 0
        info.cpu_count = os.cpu_count() or 0

        # Get memory
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info.memory_total_gb = round(int(result.stdout.strip()) / 1024 / 1024 / 1024, 2)
        except Exception:
            pass

        return info
