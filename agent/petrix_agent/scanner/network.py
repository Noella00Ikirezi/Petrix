"""
Network discovery — adapts to Windows / Linux / macOS automatically.
"""

import platform
import socket
import subprocess
from dataclasses import dataclass, field
from typing import Optional

OS = platform.system()  # "Windows", "Linux", "Darwin"


@dataclass
class LocalNetwork:
    interface: str
    ip: str
    cidr: str


@dataclass
class DiscoveredHost:
    ip: str
    hostname: Optional[str] = None
    mac: Optional[str] = None
    method: str = "unknown"


def get_local_networks() -> list[LocalNetwork]:
    """Detect local subnets on all active network interfaces."""
    try:
        import netifaces
        networks = []
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            af_inet = addrs.get(netifaces.AF_INET, [])
            for addr in af_inet:
                ip = addr.get("addr", "")
                netmask = addr.get("netmask", "")
                if not ip or ip.startswith("127.") or ip.startswith("169.254."):
                    continue
                cidr = _netmask_to_cidr(ip, netmask)
                networks.append(LocalNetwork(interface=iface, ip=ip, cidr=cidr))
        return networks
    except Exception:
        return _fallback_network_detect()


def _netmask_to_cidr(ip: str, netmask: str) -> str:
    """Convert IP + netmask to CIDR notation."""
    try:
        import ipaddress
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network)
    except Exception:
        return f"{ip}/24"


def _fallback_network_detect() -> list[LocalNetwork]:
    """Fallback using socket if netifaces fails."""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127."):
            return [LocalNetwork(interface="default", ip=ip, cidr=f"{ip}/24")]
    except Exception:
        pass
    return []


def discover_hosts(cidr: str, callback=None) -> list[DiscoveredHost]:
    """
    Discover live hosts on a subnet.
    Tries ARP (root/admin only), then nmap ping, then socket connect.
    """
    # Try ARP first (needs root on Linux/macOS, admin on Windows)
    hosts = _try_arp(cidr, callback)
    if hosts:
        return hosts

    # Nmap ping scan (nmap must be installed)
    hosts = _try_nmap_ping(cidr, callback)
    if hosts:
        return hosts

    # Socket sweep fallback
    return _try_socket_sweep(cidr, callback)


def _try_arp(cidr: str, callback=None) -> list[DiscoveredHost]:
    try:
        from scapy.layers.l2 import ARP, Ether
        from scapy.sendrecv import srp
        import scapy.config
        scapy.config.conf.verb = 0

        if callback:
            callback(f"ARP scan sur {cidr}...")

        pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=cidr)
        answered, _ = srp(pkt, timeout=2, retry=1)

        hosts = []
        for _, recv in answered:
            name = _resolve(recv.psrc)
            hosts.append(DiscoveredHost(ip=recv.psrc, mac=recv.hwsrc, hostname=name, method="arp"))
        return hosts
    except Exception:
        return []


def _try_nmap_ping(cidr: str, callback=None) -> list[DiscoveredHost]:
    try:
        if callback:
            callback(f"Nmap ping scan sur {cidr}...")

        cmd = ["nmap", "-sn", "-T4", "--open", "-oG", "-", cidr]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        hosts = []
        for line in result.stdout.splitlines():
            if "Host:" in line and "Status: Up" in line:
                parts = line.split()
                ip = parts[1]
                hostname = parts[2].strip("()") if len(parts) > 2 else None
                hosts.append(DiscoveredHost(ip=ip, hostname=hostname or _resolve(ip), method="nmap_ping"))
        return hosts
    except Exception:
        return []


def _try_socket_sweep(cidr: str, callback=None) -> list[DiscoveredHost]:
    """Last resort: try connecting to port 80/22/445 on each IP."""
    try:
        import ipaddress
        net = ipaddress.ip_network(cidr, strict=False)
        ips = [str(h) for h in net.hosts()]
        if len(ips) > 254:
            ips = ips[:254]

        if callback:
            callback(f"Socket sweep sur {len(ips)} adresses...")

        hosts = []
        for ip in ips:
            for port in [80, 22, 445, 443, 3389]:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    if s.connect_ex((ip, port)) == 0:
                        hosts.append(DiscoveredHost(ip=ip, hostname=_resolve(ip), method="socket"))
                        s.close()
                        break
                    s.close()
                except Exception:
                    pass
        return hosts
    except Exception:
        return []


def _resolve(ip: str) -> Optional[str]:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None
