"""
External Tool Integrations
Integration with security tools like Metasploit, Nuclei, etc.
"""

from .metasploit import MetasploitIntegration
from .nuclei import NucleiScanner
from .nmap import NmapWrapper

__all__ = [
    "MetasploitIntegration",
    "NucleiScanner",
    "NmapWrapper",
]
