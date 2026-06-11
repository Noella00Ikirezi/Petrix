"""
Network host discovery using Scapy (ARP / ICMP) with nmap fallback.

Requires: NET_RAW + NET_ADMIN capabilities (celery container has both).
"""

import ipaddress
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Optional

from loguru import logger


@dataclass
class DiscoveredHost:
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    latency_ms: Optional[float] = None
    method: str = "unknown"


@dataclass
class DiscoveryResult:
    target: str
    hosts: list[DiscoveredHost] = field(default_factory=list)
    method_used: str = "none"
    error: Optional[str] = None


def _try_arp_scan(network: str, callback: Optional[Callable] = None) -> list[DiscoveredHost]:
    """ARP scan — works only on local Layer-2 networks (same subnet)."""
    try:
        from scapy.layers.l2 import ARP, Ether
        from scapy.sendrecv import srp
        import scapy.config
        scapy.config.conf.verb = 0  # silent

        if callback:
            callback(f"ARP scan on {network}...")

        arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
        answered, _ = srp(arp_request, timeout=2, retry=1)

        hosts = []
        for _, recv in answered:
            hosts.append(DiscoveredHost(
                ip=recv.psrc,
                mac=recv.hwsrc,
                method="arp",
            ))

        if callback:
            callback(f"ARP found {len(hosts)} hosts")
        return hosts

    except Exception as e:
        logger.debug(f"ARP scan failed: {e}")
        return []


def _try_icmp_scan(targets: list[str], callback: Optional[Callable] = None) -> list[DiscoveredHost]:
    """ICMP echo ping sweep — works across subnets, needs NET_RAW."""
    try:
        from scapy.layers.inet import IP, ICMP
        from scapy.sendrecv import sr1
        import scapy.config
        scapy.config.conf.verb = 0

        if callback:
            callback(f"ICMP ping sweep on {len(targets)} hosts...")

        hosts = []
        for ip in targets:
            try:
                pkt = IP(dst=ip) / ICMP()
                reply = sr1(pkt, timeout=1, verbose=0)
                if reply is not None:
                    hosts.append(DiscoveredHost(ip=ip, method="icmp"))
            except Exception:
                continue

        if callback:
            callback(f"ICMP found {len(hosts)} live hosts")
        return hosts

    except Exception as e:
        logger.debug(f"ICMP scan failed: {e}")
        return []


def _nmap_ping_scan(network: str, callback: Optional[Callable] = None) -> list[DiscoveredHost]:
    """Fallback: nmap -sn ping scan (no port scan)."""
    try:
        if callback:
            callback(f"nmap ping scan on {network} (fallback)...")

        result = subprocess.run(
            ["nmap", "-sn", "-T4", "--open", "-oG", "-", network],
            capture_output=True, text=True, timeout=60
        )

        hosts = []
        for line in result.stdout.splitlines():
            if "Host:" in line and "Status: Up" in line:
                parts = line.split()
                ip = parts[1]
                hosts.append(DiscoveredHost(ip=ip, method="nmap_ping"))

        if callback:
            callback(f"nmap found {len(hosts)} hosts")
        return hosts

    except Exception as e:
        logger.error(f"nmap ping scan failed: {e}")
        return []


def _single_host_alive(ip: str) -> bool:
    """Quick check: is a single host reachable?"""
    try:
        from scapy.layers.inet import IP, ICMP
        from scapy.sendrecv import sr1
        import scapy.config
        scapy.config.conf.verb = 0
        reply = sr1(IP(dst=ip) / ICMP(), timeout=2, verbose=0)
        return reply is not None
    except Exception:
        # Fallback: nmap single host
        try:
            r = subprocess.run(
                ["nmap", "-sn", "-T4", ip], capture_output=True, text=True, timeout=10
            )
            return "1 host up" in r.stdout
        except Exception:
            return True  # assume up if we can't check


def discover_network(
    target: str,
    callback: Optional[Callable[[str], None]] = None,
) -> DiscoveryResult:
    """
    Discover live hosts on a target.

    Args:
        target: Single IP, hostname, or CIDR range (e.g. 192.168.1.0/24)
        callback: Optional progress callback

    Returns:
        DiscoveryResult with discovered hosts
    """
    result = DiscoveryResult(target=target)

    # Single host
    if "/" not in target and not _is_range(target):
        alive = _single_host_alive(target)
        if alive:
            result.hosts = [DiscoveredHost(ip=target, method="direct")]
        result.method_used = "direct"
        return result

    # Network range — try ARP first (fast, LAN only), then ICMP, then nmap fallback
    try:
        net = ipaddress.ip_network(target, strict=False)
        all_ips = [str(h) for h in net.hosts()]
    except ValueError as e:
        result.error = str(e)
        return result

    # ARP is best for /24 and smaller on local network
    if net.prefixlen >= 16:
        hosts = _try_arp_scan(target, callback)
        if hosts:
            result.hosts = hosts
            result.method_used = "scapy_arp"
            return result

    # ICMP sweep (cross-subnet)
    if len(all_ips) <= 512:
        hosts = _try_icmp_scan(all_ips, callback)
        if hosts:
            result.hosts = hosts
            result.method_used = "scapy_icmp"
            return result

    # nmap fallback
    hosts = _nmap_ping_scan(target, callback)
    result.hosts = hosts
    result.method_used = "nmap_ping"

    return result


def _is_range(target: str) -> bool:
    return "-" in target or target.endswith(".*")
