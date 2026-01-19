"""
Command Executor - Execute commands locally or remotely
Supports SSH for Linux and WinRM for Windows
"""

import asyncio
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

from .detector import OSType, PlatformInfo


@dataclass
class CommandResult:
    """Result of a command execution"""
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out


class CommandExecutor(ABC):
    """Abstract base class for command execution"""

    @abstractmethod
    async def execute(
        self,
        command: str,
        timeout: int = 60,
        shell: bool = True
    ) -> CommandResult:
        """Execute a command and return the result"""
        pass

    @abstractmethod
    async def execute_powershell(
        self,
        script: str,
        timeout: int = 60
    ) -> CommandResult:
        """Execute a PowerShell script (Windows only)"""
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """Read a file and return its contents"""
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        pass

    @abstractmethod
    async def get_platform_info(self) -> PlatformInfo:
        """Get platform information for this executor"""
        pass


class LocalExecutor(CommandExecutor):
    """Execute commands on the local system"""

    def __init__(self):
        from .detector import PlatformDetector
        self._platform_info: Optional[PlatformInfo] = None
        self._detector = PlatformDetector

    async def execute(
        self,
        command: str,
        timeout: int = 60,
        shell: bool = True
    ) -> CommandResult:
        """Execute a local command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return CommandResult(
                return_code=process.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
            )

        except asyncio.TimeoutError:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="Command timed out",
                timed_out=True
            )
        except Exception as e:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr=str(e)
            )

    async def execute_powershell(
        self,
        script: str,
        timeout: int = 60
    ) -> CommandResult:
        """Execute a PowerShell script locally"""
        platform_info = await self.get_platform_info()

        if platform_info.os_type != OSType.WINDOWS:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="PowerShell is only available on Windows"
            )

        # Encode script for PowerShell
        cmd = f'powershell -NoProfile -NonInteractive -Command "{script}"'
        return await self.execute(cmd, timeout)

    async def read_file(self, path: str) -> str:
        """Read a local file"""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to read file {path}: {e}")

    async def file_exists(self, path: str) -> bool:
        """Check if a local file exists"""
        return os.path.exists(path)

    async def get_platform_info(self) -> PlatformInfo:
        """Get local platform information"""
        if self._platform_info is None:
            self._platform_info = self._detector.detect_local()
        return self._platform_info


class SSHExecutor(CommandExecutor):
    """Execute commands on remote Linux systems via SSH"""

    def __init__(
        self,
        hostname: str,
        username: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        port: int = 22,
        timeout: int = 30
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = key_path
        self.port = port
        self.timeout = timeout
        self._client: Any = None
        self._platform_info: Optional[PlatformInfo] = None

    async def _connect(self) -> None:
        """Establish SSH connection"""
        if self._client is not None:
            return

        try:
            import paramiko

            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.hostname,
                "port": self.port,
                "username": self.username,
                "timeout": self.timeout,
            }

            if self.key_path:
                connect_kwargs["key_filename"] = self.key_path
            elif self.password:
                connect_kwargs["password"] = self.password

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.connect(**connect_kwargs)
            )

        except ImportError:
            raise RuntimeError("paramiko is required for SSH connections")
        except Exception as e:
            self._client = None
            raise ConnectionError(f"SSH connection failed: {e}")

    async def execute(
        self,
        command: str,
        timeout: int = 60,
        shell: bool = True
    ) -> CommandResult:
        """Execute a command over SSH"""
        await self._connect()

        try:
            loop = asyncio.get_event_loop()

            def _exec():
                stdin, stdout, stderr = self._client.exec_command(
                    command,
                    timeout=timeout
                )
                return (
                    stdout.channel.recv_exit_status(),
                    stdout.read().decode("utf-8", errors="replace"),
                    stderr.read().decode("utf-8", errors="replace")
                )

            return_code, stdout, stderr = await asyncio.wait_for(
                loop.run_in_executor(None, _exec),
                timeout=timeout + 5
            )

            return CommandResult(
                return_code=return_code,
                stdout=stdout,
                stderr=stderr
            )

        except asyncio.TimeoutError:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="Command timed out",
                timed_out=True
            )
        except Exception as e:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr=str(e)
            )

    async def execute_powershell(
        self,
        script: str,
        timeout: int = 60
    ) -> CommandResult:
        """PowerShell not available over SSH"""
        return CommandResult(
            return_code=-1,
            stdout="",
            stderr="PowerShell not available over SSH"
        )

    async def read_file(self, path: str) -> str:
        """Read a remote file via SSH"""
        result = await self.execute(f"cat '{path}'")
        if result.success:
            return result.stdout
        raise IOError(f"Failed to read file {path}: {result.stderr}")

    async def file_exists(self, path: str) -> bool:
        """Check if a remote file exists"""
        result = await self.execute(f"test -e '{path}' && echo 'exists'")
        return "exists" in result.stdout

    async def get_platform_info(self) -> PlatformInfo:
        """Get remote platform information"""
        if self._platform_info is not None:
            return self._platform_info

        from .detector import PlatformInfo, OSType, LinuxDistro

        info = PlatformInfo(
            os_type=OSType.LINUX,
            os_name="Linux",
            os_version="",
            hostname=self.hostname
        )

        # Get OS info
        result = await self.execute("cat /etc/os-release")
        if result.success:
            for line in result.stdout.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip('"')
                    if key == "ID":
                        distro_map = {
                            "debian": LinuxDistro.DEBIAN,
                            "ubuntu": LinuxDistro.UBUNTU,
                            "centos": LinuxDistro.CENTOS,
                            "rhel": LinuxDistro.RHEL,
                            "fedora": LinuxDistro.FEDORA,
                        }
                        info.distro = distro_map.get(value.lower(), LinuxDistro.UNKNOWN)
                    elif key == "VERSION_ID":
                        info.distro_version = value
                    elif key == "PRETTY_NAME":
                        info.os_name = value

        # Get kernel version
        result = await self.execute("uname -r")
        if result.success:
            info.kernel_version = result.stdout.strip()
            info.os_version = info.kernel_version

        # Get architecture
        result = await self.execute("uname -m")
        if result.success:
            info.architecture = result.stdout.strip()

        # Check if root
        result = await self.execute("id -u")
        if result.success:
            info.is_elevated = result.stdout.strip() == "0"

        # Get current user
        result = await self.execute("whoami")
        if result.success:
            info.current_user = result.stdout.strip()

        self._platform_info = info
        return info

    def close(self) -> None:
        """Close the SSH connection"""
        if self._client:
            self._client.close()
            self._client = None


class WinRMExecutor(CommandExecutor):
    """Execute commands on remote Windows systems via WinRM"""

    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        port: int = 5985,
        use_ssl: bool = False,
        timeout: int = 30
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self._session: Any = None
        self._platform_info: Optional[PlatformInfo] = None

    async def _connect(self) -> None:
        """Establish WinRM connection"""
        if self._session is not None:
            return

        try:
            import winrm

            protocol = "https" if self.use_ssl else "http"
            endpoint = f"{protocol}://{self.hostname}:{self.port}/wsman"

            self._session = winrm.Session(
                endpoint,
                auth=(self.username, self.password),
                transport="ntlm"
            )

        except ImportError:
            raise RuntimeError("pywinrm is required for WinRM connections")
        except Exception as e:
            self._session = None
            raise ConnectionError(f"WinRM connection failed: {e}")

    async def execute(
        self,
        command: str,
        timeout: int = 60,
        shell: bool = True
    ) -> CommandResult:
        """Execute a command over WinRM"""
        await self._connect()

        try:
            loop = asyncio.get_event_loop()

            def _exec():
                return self._session.run_cmd(command)

            result = await asyncio.wait_for(
                loop.run_in_executor(None, _exec),
                timeout=timeout
            )

            return CommandResult(
                return_code=result.status_code,
                stdout=result.std_out.decode("utf-8", errors="replace"),
                stderr=result.std_err.decode("utf-8", errors="replace")
            )

        except asyncio.TimeoutError:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="Command timed out",
                timed_out=True
            )
        except Exception as e:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr=str(e)
            )

    async def execute_powershell(
        self,
        script: str,
        timeout: int = 60
    ) -> CommandResult:
        """Execute a PowerShell script over WinRM"""
        await self._connect()

        try:
            loop = asyncio.get_event_loop()

            def _exec():
                return self._session.run_ps(script)

            result = await asyncio.wait_for(
                loop.run_in_executor(None, _exec),
                timeout=timeout
            )

            return CommandResult(
                return_code=result.status_code,
                stdout=result.std_out.decode("utf-8", errors="replace"),
                stderr=result.std_err.decode("utf-8", errors="replace")
            )

        except asyncio.TimeoutError:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr="Command timed out",
                timed_out=True
            )
        except Exception as e:
            return CommandResult(
                return_code=-1,
                stdout="",
                stderr=str(e)
            )

    async def read_file(self, path: str) -> str:
        """Read a remote file via WinRM"""
        result = await self.execute_powershell(f"Get-Content -Path '{path}' -Raw")
        if result.success:
            return result.stdout
        raise IOError(f"Failed to read file {path}: {result.stderr}")

    async def file_exists(self, path: str) -> bool:
        """Check if a remote file exists"""
        result = await self.execute_powershell(f"Test-Path '{path}'")
        return "True" in result.stdout

    async def get_platform_info(self) -> PlatformInfo:
        """Get remote Windows platform information"""
        if self._platform_info is not None:
            return self._platform_info

        from .detector import PlatformInfo, OSType, WindowsVersion

        info = PlatformInfo(
            os_type=OSType.WINDOWS,
            os_name="Windows",
            os_version="",
            hostname=self.hostname
        )

        # Get OS info
        result = await self.execute_powershell(
            "(Get-WmiObject Win32_OperatingSystem).Caption"
        )
        if result.success:
            info.os_name = result.stdout.strip()

            caption_lower = info.os_name.lower()
            if "server 2022" in caption_lower:
                info.windows_version = WindowsVersion.SERVER_2022
            elif "server 2019" in caption_lower:
                info.windows_version = WindowsVersion.SERVER_2019
            elif "server 2016" in caption_lower:
                info.windows_version = WindowsVersion.SERVER_2016

        # Check domain
        result = await self.execute_powershell(
            "(Get-WmiObject Win32_ComputerSystem).PartOfDomain"
        )
        if result.success:
            info.is_domain_joined = "True" in result.stdout

        if info.is_domain_joined:
            result = await self.execute_powershell(
                "(Get-WmiObject Win32_ComputerSystem).Domain"
            )
            if result.success:
                info.domain_name = result.stdout.strip()

        # Check if DC
        result = await self.execute_powershell(
            "(Get-WmiObject Win32_ComputerSystem).DomainRole"
        )
        if result.success:
            try:
                role = int(result.stdout.strip())
                info.is_domain_controller = role in [4, 5]
            except ValueError:
                pass

        self._platform_info = info
        return info
