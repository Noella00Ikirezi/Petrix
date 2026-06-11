"""
Rich host scanner — extracts maximum information from a target.
Uses nmap with NSE scripts for banners, SSL, HTTP headers, SSH keys, OS detection.
"""

import socket
import subprocess
from typing import Callable, Optional

import httpx
from loguru import logger


PUBLIC_TEST_TARGETS = [
    {"value": "scanme.nmap.org",       "label": "scanme.nmap.org (nmap official)"},
    {"value": "testphp.vulnweb.com",   "label": "testphp.vulnweb.com (Acunetix)"},
    {"value": "testasp.vulnweb.com",   "label": "testasp.vulnweb.com (Acunetix)"},
    {"value": "testaspnet.vulnweb.com","label": "testaspnet.vulnweb.com (Acunetix)"},
]

# Ports à scanner — couvre les services les plus courants
RICH_PORTS = (
    "21,22,23,25,53,80,110,111,135,139,143,161,"
    "389,443,445,465,587,993,995,1433,1521,"
    "3000,3306,3389,5432,5900,6379,8080,8443,8888,27017"
)

# NSE scripts pour extraction maximale d'info
NSE_SCRIPTS = ",".join([
    "banner",
    "http-title",
    "http-headers",
    "http-methods",
    "http-server-header",
    "ssh-hostkey",
    "ssl-cert",
    "ftp-anon",
    "smtp-commands",
    "rdp-enum-encryption",
    "snmp-info",
    "mysql-info",
    "redis-info",
    "mongodb-info",
])


def get_server_public_ip() -> Optional[str]:
    """Get the server's own public IP for blackbox self-scan."""
    for url in ["https://api.ipify.org", "https://ifconfig.me/ip"]:
        try:
            resp = httpx.get(url, timeout=5)
            ip = resp.text.strip()
            if ip:
                return ip
        except Exception:
            continue
    return None


def resolve_hostname(target: str) -> Optional[str]:
    """Reverse DNS or forward DNS resolution."""
    try:
        if all(c.isdigit() or c == "." for c in target):
            return socket.gethostbyaddr(target)[0]
        else:
            return socket.gethostbyname(target)
    except Exception:
        return None


def rich_scan_host(
    target: str,
    ports: str = RICH_PORTS,
    callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Deep scan of a single host. Returns structured dict with:
    - open_ports with service, version, banner, SSL info, HTTP info
    - os_guess
    - hostname (DNS)
    - raw_scripts output
    """
    if callback:
        callback(f"Deep scan: {target} — ports + banners + SSL + OS...")

    # DNS resolution
    dns_name = resolve_hostname(target)

    try:
        result = subprocess.run(
            [
                "nmap",
                "-sV", "--version-intensity", "7",
                "-O", "--osscan-limit",
                "--script", NSE_SCRIPTS,
                "-p", ports,
                target,
                "-T4", "--open",
                "--host-timeout", "120s",
            ],
            capture_output=True, text=True, timeout=180,
        )
        output = result.stdout
    except subprocess.TimeoutExpired:
        logger.warning(f"Rich scan timed out on {target}")
        output = ""
    except Exception as e:
        logger.error(f"Rich scan error on {target}: {e}")
        output = ""

    return _parse_nmap_rich_output(output, target, dns_name, callback)


def _parse_nmap_rich_output(output: str, target: str, dns_name: Optional[str], callback=None) -> dict:
    """Parse nmap verbose output into structured data."""
    lines = output.splitlines()

    os_guess = None
    open_ports = []
    current_port = None
    script_buffer: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # OS detection
        if "OS details:" in line or "Aggressive OS guesses:" in line:
            os_guess = line.split(":", 1)[-1].strip().split(",")[0].strip()

        # Open port line: "80/tcp   open  http    Apache httpd 2.4.41"
        if "/tcp" in line or "/udp" in line:
            parts = line.split()
            if len(parts) >= 3 and parts[1] == "open":
                # Save previous port with accumulated scripts
                if current_port:
                    _attach_scripts(current_port, script_buffer)
                    open_ports.append(current_port)
                    script_buffer = []

                port_proto = parts[0]  # e.g. "80/tcp"
                port_num, proto = port_proto.split("/")
                service = parts[2] if len(parts) > 2 else ""
                product = " ".join(parts[3:]) if len(parts) > 3 else ""

                current_port = {
                    "port": int(port_num),
                    "protocol": proto,
                    "service": service,
                    "product": product.strip(),
                    "banner": None,
                    "http_title": None,
                    "http_headers": {},
                    "ssl_subject": None,
                    "ssl_expiry": None,
                    "ssh_keys": [],
                    "extra": [],
                }

        # Collect script output lines (indented with |)
        elif line.startswith("|") and current_port is not None:
            script_buffer.append(line)

        i += 1

    # Last port
    if current_port:
        _attach_scripts(current_port, script_buffer)
        open_ports.append(current_port)

    if callback:
        callback(f"Found {len(open_ports)} open ports on {target}" + (f" ({os_guess})" if os_guess else ""))

    return {
        "ip": target,
        "hostname": dns_name,
        "os": os_guess,
        "open_ports": open_ports,
        "raw_output": output[:2000] if output else "",
    }


def _attach_scripts(port: dict, script_lines: list[str]):
    """Parse NSE script output lines and attach to port dict."""
    joined = "\n".join(script_lines)

    for line in script_lines:
        clean = line.lstrip("| ").strip()

        # Banner
        if "banner:" in line.lower() or line.startswith("|_banner"):
            port["banner"] = clean.replace("banner:", "").replace("_banner:", "").strip()

        # HTTP title
        elif "http-title:" in line.lower() or "_http-title:" in line.lower():
            port["http_title"] = clean.replace("http-title:", "").replace("_http-title:", "").strip()

        # HTTP server header
        elif "Server:" in line:
            port["http_headers"]["Server"] = clean.split("Server:", 1)[-1].strip()

        # HTTP methods
        elif "http-methods:" in line.lower() or ("Supported Methods:" in line):
            port["http_headers"]["Methods"] = clean.split(":", 1)[-1].strip() if ":" in clean else clean

        # SSL subject
        elif "Subject:" in line and "ssl" in joined.lower():
            port["ssl_subject"] = clean.replace("Subject:", "").strip()

        # SSL expiry
        elif "Not valid after" in line:
            port["ssl_expiry"] = clean.replace("Not valid after:", "").strip()

        # SSH host key
        elif "ssh-hostkey" not in line.lower() and any(k in line for k in ["rsa", "ecdsa", "ed25519"]):
            key_type = next((k for k in ["rsa", "ecdsa", "ed25519"] if k in line.lower()), None)
            if key_type and len(clean) > 10:
                port["ssh_keys"].append({"type": key_type, "key": clean})

        # FTP anon
        elif "ftp-anon" in line.lower() and "allowed" in line.lower():
            port["extra"].append("FTP anonymous login allowed")

        # Redis auth
        elif "redis" in line.lower() and ("no auth" in line.lower() or "unauthenticated" in line.lower()):
            port["extra"].append("Redis: no authentication required")
