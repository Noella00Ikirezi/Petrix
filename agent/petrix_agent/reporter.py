"""
Reporter — sends scan results to the Petrix server API.
"""

import platform
import socket
from typing import Optional

import httpx


class PetrixReporter:
    def __init__(self, server_url: str, token: str):
        self.base = server_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate and return JWT token."""
        try:
            r = httpx.post(
                f"{self.base}/api/v1/auth/login",
                json={"email": email, "password": password},
                timeout=10,
            )
            data = r.json()
            # MFA disabled: direct token response
            token = data.get("access_token")
            if token:
                self.headers["Authorization"] = f"Bearer {token}"
                return token
            # MFA enabled: would need OTP flow
            return None
        except Exception as e:
            return None

    def create_scan(self, name: str, scan_type: str = "full") -> Optional[str]:
        """Create a scan entry on the server, return scan_id."""
        try:
            machine = socket.gethostname()
            r = httpx.post(
                f"{self.base}/api/v1/scans",
                headers=self.headers,
                json={
                    "name": name,
                    "scan_type": scan_type,
                    "targets": [],
                    "config": {"ports": "top1000", "agent": True, "machine": machine, "os": platform.system()},
                },
                timeout=10,
            )
            if r.status_code in (200, 201):
                return r.json().get("id")
        except Exception:
            pass
        return None

    def push_results(self, scan_id: str, hosts: list[dict], findings: list[dict]) -> bool:
        """Push agent scan results to the server."""
        try:
            r = httpx.post(
                f"{self.base}/api/v1/scans/{scan_id}/agent-results",
                headers=self.headers,
                json={"hosts": hosts, "findings": findings},
                timeout=30,
            )
            return r.status_code in (200, 201, 204)
        except Exception:
            return False

    def complete_scan(self, scan_id: str, summary: dict, score: float, grade: str) -> bool:
        """Mark scan as completed with final summary."""
        try:
            r = httpx.patch(
                f"{self.base}/api/v1/scans/{scan_id}/agent-complete",
                headers=self.headers,
                json={"summary": summary, "score": score, "grade": grade},
                timeout=10,
            )
            return r.status_code in (200, 204)
        except Exception:
            return False

    def get_pending_jobs(self, ips: list[str]) -> list[dict]:
        """Poll server for scans assigned to this machine (matched by IP)."""
        try:
            r = httpx.get(
                f"{self.base}/api/v1/agent/jobs",
                headers=self.headers,
                params={"ips": ",".join(ips)},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json().get("jobs", [])
        except Exception:
            pass
        return []

    def claim_job(self, scan_id: str) -> bool:
        """Claim a pending job so no other agent picks it up."""
        try:
            r = httpx.post(
                f"{self.base}/api/v1/agent/jobs/{scan_id}/claim",
                headers=self.headers,
                timeout=10,
            )
            return r.status_code in (200, 201)
        except Exception:
            return False

    def register_self(self) -> Optional[str]:
        """Register/update this machine as an asset in Petrix. Returns asset id or None."""
        import platform
        import socket

        # Collect all non-loopback IPv4 addresses
        ips: list[str] = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None):
                ip = info[4][0]
                if ":" not in ip and not ip.startswith("127."):
                    if ip not in ips:
                        ips.append(ip)
        except Exception:
            pass
        if not ips:
            try:
                ip = socket.gethostbyname(socket.gethostname())
                if not ip.startswith("127."):
                    ips = [ip]
            except Exception:
                pass

        payload = {
            "hostname": platform.node(),
            "ips": ips,
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
        }
        try:
            r = httpx.post(
                f"{self.base}/api/v1/assets/register-self",
                headers=self.headers,
                json=payload,
                timeout=10,
            )
            if r.status_code in (200, 201):
                return r.json().get("id")
        except Exception:
            pass
        return None
