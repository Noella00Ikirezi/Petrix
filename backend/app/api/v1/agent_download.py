"""Router de téléchargement de l'agent Petrix : génération de tokens longue durée, distribution des scripts d'installation et modèle pull de jobs.

Ce module gère le cycle de vie côté serveur de l'agent Petrix : création du token JWT agent
(30 jours), téléchargement des installeurs paramétrés pour Linux/macOS/Windows et acquisition
des jobs de scan via le modèle pull (poll + claim) utilisé par les agents déployés.
"""
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

# Marqueurs magiques inscrits dans l'exécutable Windows pré-compilé et remplacés à la volée lors du téléchargement
_MAGIC_SRV = b"PTXSRV1!"
_MAGIC_TKN = b"PTXTKN1!"
_SRV_LEN   = 128   # octets réservés après le marqueur pour l'URL du serveur
_TKN_LEN   = 2048  # octets réservés après le marqueur pour le token JWT


def _patch_exe(data: bytes, server_url: str, token: str) -> bytes:
    """Injecte l'URL du serveur et le token JWT dans l'exécutable Windows pré-compilé.

    Localise les marqueurs magiques dans le binaire et écrase les zones réservées
    par les valeurs encodées en UTF-8, complétées à la bonne longueur par des octets nuls.

    Args:
        data: Contenu brut de l'exécutable Windows (bytes).
        server_url: URL du serveur Petrix à inscrire après ``_MAGIC_SRV`` (tronquée à 128 octets).
        token: Token JWT d'agent à inscrire après ``_MAGIC_TKN`` (tronqué à 2048 octets).

    Returns:
        Nouveau contenu binaire de l'exécutable avec les zones patchées.
    """
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
    """Génère un token JWT longue durée (30 jours) à configurer dans l'agent — tout utilisateur authentifié."""
    token = create_token(
        data={"sub": str(current_user.id), "agent": True},
        token_type="access",
        expires_delta=timedelta(days=30),
    )
    return {"token": token, "user": current_user.email}


@router.get("/download/wheel")
async def download_agent_wheel():
    """Sert le wheel Python ``petrix-agent`` le plus récent — sans authentification (le token dans config.env protège l'accès)."""
    import glob
    wheels = sorted(glob.glob(str(INSTALL_DIR / "petrix_agent-*.whl")))
    if not wheels:
        raise HTTPException(status_code=503, detail="Agent wheel non disponible sur ce serveur")
    wheel_path = Path(wheels[-1])  # latest version
    return Response(
        content=wheel_path.read_bytes(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{wheel_path.name}"'},
    )


@router.get("/download/{os_name}")
async def download_installer(
    os_name: str,
    server_url: str = "https://petrix.noellahome.org",
    token: str = "",
):
    """Sert l'installeur spécifique à l'OS avec token et URL pré-inscrits — sans authentification, le token embarqué protège l'accès."""

    # Installeur Windows EXE — injection binaire du token et de l'URL
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

    # Scripts shell/PowerShell (Linux, macOS, Windows PowerShell en fallback ou demande explicite)
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
            # Scripts bash/sh — variables sans guillemets internes
            .replace('PETRIX_SERVER=""', f'PETRIX_SERVER="{server_url}"')
            .replace('PETRIX_TOKEN=""',  f'PETRIX_TOKEN="{token}"')
            # Scripts PowerShell — variables avec espaces autour du signe égal
            .replace('$PETRIX_SERVER = ""', f'$PETRIX_SERVER = "{server_url}"')
            .replace('$PETRIX_TOKEN = ""',  f'$PETRIX_TOKEN = "{token}"')
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Polling de jobs agent — modèle pull (l'agent interroge puis acquiert ses scans)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/jobs")
async def get_agent_jobs(
    ips: str = Query("", description="Comma-separated list of agent IPs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retourne les scans PENDING assignés à cet agent (par correspondance d'IP) — l'agent appelle cet endpoint toutes les N minutes pour découvrir ses jobs."""
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
    """Acquiert un job PENDING et le passe en RUNNING sans déclencher Celery — retourne 409 si déjà acquis par un autre agent."""
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
