"""Agent download endpoints — generate tokens and serve install scripts."""
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import create_token
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.v1.deps import get_current_active_user

router = APIRouter()

INSTALL_DIR = Path(__file__).parent.parent.parent.parent.parent / "agent" / "install"


@router.post("/token")
async def generate_agent_token(
    current_user: User = Depends(get_current_active_user),
):
    """Generate a short-lived token for the local agent — requires login only."""
    token = create_token(data={"sub": str(current_user.id)}, token_type="access")
    return {"token": token, "user": current_user.email}


@router.get("/download/{os_name}")
async def download_installer(
    os_name: str,
    server_url: str = "https://petrix.noellahome.org",
    token: str = "",
    current_user: User = Depends(get_current_active_user),
):
    """Serve the OS-specific installer script with server URL and token embedded."""
    scripts = {
        "linux":   ("install-linux.sh",   "text/x-sh",          "petrix-agent-install-linux.sh"),
        "macos":   ("install-macos.sh",    "text/x-sh",          "petrix-agent-install-macos.sh"),
        "windows": ("install-windows.ps1", "text/x-powershell",  "petrix-agent-install-windows.ps1"),
    }

    if os_name not in scripts:
        raise HTTPException(status_code=404, detail=f"OS non supporté: {os_name}")

    filename, content_type, download_name = scripts[os_name]
    script_path = INSTALL_DIR / filename

    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Script d'installation non trouvé")

    content = script_path.read_text()

    # Inject server URL and token if provided
    if token:
        if os_name == "windows":
            content = content.replace(
                "param(\n    [Parameter(Mandatory=$true)]  [string]$Server,\n    [Parameter(Mandatory=$true)]  [string]$Token\n)",
                f'$Server = "{server_url}"\n$Token = "{token}"',
            )
        else:
            content = content.replace(
                'PETRIX_SERVER=""', f'PETRIX_SERVER="{server_url}"'
            ).replace(
                'PETRIX_TOKEN=""', f'PETRIX_TOKEN="{token}"'
            )

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
