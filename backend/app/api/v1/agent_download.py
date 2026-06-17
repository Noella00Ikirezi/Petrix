"""Agent download endpoints — generate tokens, serve install scripts, and manage agent jobs."""
import uuid as _uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.infrastructure.database import get_db
from app.infrastructure.database.models import Scan, ScanStatus, User
from app.api.v1.deps import get_current_active_user

router = APIRouter()

INSTALL_DIR = Path(__file__).parent.parent.parent.parent / "agent" / "install"

# Magic markers in the pre-compiled Windows .exe — patched at download time
_MAGIC_SRV = b"PTXSRV1!"
_MAGIC_TKN = b"PTXTKN1!"
_SRV_LEN   = 128   # bytes reserved after magic for server URL
_TKN_LEN   = 2048  # bytes reserved after magic for token


def _patch_exe(data: bytes, server_url: str, token: str) -> bytes:
    buf = bytearray(data)

    idx = buf.find(_MAGIC_SRV)
    if idx != -1:
        srv = server_url.encode("utf-8")[:_SRV_LEN]
        buf[idx + 8 : idx + 8 + _SRV_LEN] = srv + bytes(_SRV_LEN - len(srv))

    idx = buf.find(_MAGIC_TKN)
    if idx != -1:
        tok = token.encode("utf-8")[:_TKN_LEN]
        buf[idx + 8 : idx + 8 + _TKN_LEN] = tok + bytes(_TKN_LEN - len(tok))

    return bytes(buf)


@router.post("/token")
async def generate_agent_token(
    current_user: User = Depends(get_current_active_user),
):
    """Generate a long-lived agent token (30 days) — requires login only."""
    token = create_token(
        data={"sub": str(current_user.id), "agent": True},
        token_type="access",
        expires_delta=timedelta(days=30),
    )
    return {"token": token, "user": current_user.email}


@router.get("/download/{os_name}")
async def download_installer(
    os_name: str,
    server_url: str = "https://petrix.noellahome.org",
    token: str = "",
):
    """Serve the OS-specific installer — no auth required, the embedded token protects access."""

    # Windows EXE — binary patching
    if os_name == "windows":
        exe_path = INSTALL_DIR / "petrix-installer-base.exe"
        if not exe_path.exists():
            raise HTTPException(status_code=503, detail="Installeur Windows non disponible")
        data = exe_path.read_bytes()
        if token:
            data = _patch_exe(data, server_url, token)
        return Response(
            content=data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": 'attachment; filename="petrix-agent-installer.exe"'},
        )

    # PowerShell script for Windows (fallback when no EXE, or explicit request)
    scripts = {
        "linux":      ("install-linux.sh",      "text/x-sh",          "petrix-agent-install-linux.sh"),
        "macos":      ("install-macos.sh",       "text/x-sh",          "petrix-agent-install-macos.sh"),
        "windows-ps": ("install-windows.ps1",    "text/plain",         "petrix-agent-install-windows.ps1"),
    }
    if os_name not in scripts:
        raise HTTPException(status_code=404, detail=f"OS non supporté: {os_name}")

    filename, content_type, download_name = scripts[os_name]
    script_path = INSTALL_DIR / filename
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script d'installation non trouvé")

    content = script_path.read_text().replace("\r\n", "\n")
    if token:
        content = (
            content
            # bash / sh scripts: PETRIX_SERVER=""
            .replace('PETRIX_SERVER=""', f'PETRIX_SERVER="{server_url}"')
            .replace('PETRIX_TOKEN=""',  f'PETRIX_TOKEN="{token}"')
            # PowerShell scripts: $PETRIX_SERVER = ""
            .replace('$PETRIX_SERVER = ""', f'$PETRIX_SERVER = "{server_url}"')
            .replace('$PETRIX_TOKEN = ""',  f'$PETRIX_TOKEN = "{token}"')
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agent job polling — market-standard pull model
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/jobs")
async def get_agent_jobs(
    ips: str = Query("", description="Comma-separated list of agent IPs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agent polls this every N minutes to discover scans assigned to it.
    A scan is 'assigned' when config.agent_ip matches one of the agent's IPs.
    Returns PENDING scans only — agent claims them via /jobs/{id}/claim.
    """
    agent_ips = {ip.strip() for ip in ips.split(",") if ip.strip()}
    if not agent_ips:
        return {"jobs": []}

    pending = (
        db.query(Scan)
        .filter(Scan.status == ScanStatus.PENDING)
        .order_by(Scan.created_at.asc())
        .all()
    )

    jobs = []
    for scan in pending:
        cfg = scan.config or {}
        if cfg.get("agent_ip") in agent_ips:
            jobs.append({
                "id":        str(scan.id),
                "name":      scan.name,
                "scan_type": scan.scan_type.value,
                "targets":   scan.targets,
                "config":    cfg,
            })

    return {"jobs": jobs}


@router.post("/jobs/{scan_id}/claim")
async def claim_agent_job(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agent claims a pending job — sets it RUNNING without triggering Celery.
    Only works on PENDING scans; returns 409 if already claimed by another agent.
    """
    try:
        uid = _uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    scan = db.query(Scan).filter(Scan.id == uid).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Job not found")
    if scan.status != ScanStatus.PENDING:
        raise HTTPException(status_code=409, detail="Job already claimed or completed")

    scan.status       = ScanStatus.RUNNING
    scan.started_at   = datetime.utcnow()
    scan.current_phase = "agent_scanning"
    db.commit()

    return {"ok": True, "scan_id": scan_id, "name": scan.name}
