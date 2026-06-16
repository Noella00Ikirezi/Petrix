"""Agent download endpoints — generate tokens and serve install scripts."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.security import create_token
from app.infrastructure.database.models import User
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
    """Generate an agent token — requires login only."""
    token = create_token(data={"sub": str(current_user.id)}, token_type="access")
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

    # Shell scripts for Linux / macOS
    scripts = {
        "linux": ("install-linux.sh",  "text/x-sh", "petrix-agent-install-linux.sh"),
        "macos": ("install-macos.sh",  "text/x-sh", "petrix-agent-install-macos.sh"),
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
            .replace('PETRIX_SERVER=""', f'PETRIX_SERVER="{server_url}"')
            .replace('PETRIX_TOKEN=""',  f'PETRIX_TOKEN="{token}"')
        )

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
