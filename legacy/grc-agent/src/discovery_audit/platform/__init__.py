"""
Platform Detection and Abstraction Layer
Cross-platform support for Windows and Linux
"""

from .detector import PlatformDetector, PlatformInfo, OSType
from .executor import CommandExecutor, LocalExecutor, SSHExecutor, WinRMExecutor

__all__ = [
    "PlatformDetector",
    "PlatformInfo",
    "OSType",
    "CommandExecutor",
    "LocalExecutor",
    "SSHExecutor",
    "WinRMExecutor",
]
