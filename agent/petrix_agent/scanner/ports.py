"""
Port scanner — uses nmap if available, falls back to socket.
Works on Windows, Linux, macOS.
"""

import platform
import socket
import subprocess
from dataclasses import dataclass, field
from typing import Optional

OS = platform.system()

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
    161, 389, 443, 445, 465, 587, 993, 995,
    1433, 1521, 3000, 3306, 3389, 5432, 5900,
    6379, 8080, 8443, 8888, 27017,
]


@dataclass
class PortResult:
    port: int
    protocol: str = "tcp"
    state: str = "open"
    service: str = ""
    product: str = ""
    version: str = ""
    banner: Optional[str] = None
    http_title: Optional[str] = None
    ssl_subject: Optional[str] = None
    extra: list[str] = field(default_factory=list)


def scan_host(ip: str, ports: Optional[list[int]] = None, callback=None) -> list[PortResult]:
    """Scan ports on a host. Uses nmap if available, else socket."""
    if ports is None:
        ports = COMMON_PORTS

    results = _nmap_scan(ip, ports, callback)
    if results is not None:
        return results

    # Fallback: socket scan
    if callback:
        callback(f"nmap non disponible — scan socket sur {ip}...")
    return _socket_scan(ip, ports, callback)


def _nmap_scan(ip: str, ports: list[int], callback=None) -> Optional[list[PortResult]]:
    try:
        import nmap
        nm = nmap.PortScanner()
    except Exception:
        return None

    port_str = ",".join(str(p) for p in ports)
    if callback:
        callback(f"nmap -sV sur {ip} ({len(ports)} ports)...")

    scripts = "banner,http-title,http-headers,http-server-header,ssh-hostkey,ssl-cert,ftp-anon,smtp-commands"

    try:
        nm.scan(
            ip, port_str,
            arguments=f"-sV --version-intensity 5 -O --osscan-limit --script {scripts} -T4",
        )
    except Exception as e:
        # Try without OS detection if it fails (needs root)
        try:
            nm.scan(ip, port_str, arguments=f"-sV --version-intensity 5 --script {scripts} -T4")
        except Exception:
            return None

    if ip not in nm.all_hosts():
        return []

    results = []
    host_data = nm[ip]

    for proto in ["tcp", "udp"]:
        if proto not in host_data:
            continue
        for port_num, info in host_data[proto].items():
            if info.get("state") != "open":
                continue

            result = PortResult(
                port=port_num,
                protocol=proto,
                service=info.get("name", ""),
                product=info.get("product", ""),
                version=info.get("version", ""),
            )

            # Parse NSE script output
            scripts_out = info.get("script", {})
            if "banner" in scripts_out:
                result.banner = scripts_out["banner"][:100]
            if "http-title" in scripts_out:
                result.http_title = scripts_out["http-title"]
            if "ssl-cert" in scripts_out:
                cert_raw = scripts_out["ssl-cert"]
                for line in cert_raw.splitlines():
                    if "Subject:" in line:
                        result.ssl_subject = line.split("Subject:", 1)[-1].strip()
                        break
            if "ftp-anon" in scripts_out and "allowed" in scripts_out["ftp-anon"].lower():
                result.extra.append("FTP anonyme autorisé")
            if "redis-info" in scripts_out:
                result.extra.append("Redis accessible sans auth")

            results.append(result)

    if callback:
        callback(f"{len(results)} ports ouverts sur {ip}")
    return results


def _socket_scan(ip: str, ports: list[int], callback=None) -> list[PortResult]:
    results = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, port)) == 0:
                service = _guess_service(port)
                banner = _grab_banner(s, port)
                results.append(PortResult(
                    port=port, service=service, banner=banner, method="socket"
                ))
            s.close()
        except Exception:
            pass
    if callback:
        callback(f"{len(results)} ports ouverts sur {ip} (socket fallback)")
    return results


def _grab_banner(sock: socket.socket, port: int) -> Optional[str]:
    try:
        if port in (80, 8080, 8443, 443):
            sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
        else:
            sock.send(b"\r\n")
        data = sock.recv(256)
        return data.decode(errors="ignore").strip()[:80]
    except Exception:
        return None


SERVICE_MAP = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 135: "msrpc", 139: "netbios", 143: "imap",
    161: "snmp", 389: "ldap", 443: "https", 445: "smb", 465: "smtps",
    587: "smtp", 993: "imaps", 995: "pop3s", 1433: "mssql", 1521: "oracle",
    3000: "http-alt", 3306: "mysql", 3389: "rdp", 5432: "postgres",
    5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
    8888: "http-alt", 27017: "mongodb",
}


def _guess_service(port: int) -> str:
    return SERVICE_MAP.get(port, f"port-{port}")
