"""Hardening (HCO) API router — targets, sessions, findings."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.infrastructure.database.hardening_models import (
    HardeningTarget,
    HardeningSession,
    HardeningSessionStatus,
    HardeningFinding,
)
from app.hardening.engine import DEFAULT_MODULES_BY_OS, SUPPORTED_OS_TYPES

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class TargetCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str = "root"
    os_type: str = "linux"
    description: Optional[str] = None
    password: Optional[str] = None
    key_path: Optional[str] = None
    tags: Optional[list[str]] = None


class TargetResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    username: str
    os_type: str
    description: Optional[str]
    tags: Optional[list[str]]
    created_at: str

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    target_id: str
    modules: Optional[list[str]] = None


class FindingResponse(BaseModel):
    id: str
    check_id: str
    check_name: str
    module: str
    description: str
    severity: str
    found: str
    expected: str
    remediation: Optional[str]
    status: str


class SessionResponse(BaseModel):
    id: str
    target_id: str
    target_name: str
    target_host: str
    status: str
    current_module: Optional[str]
    progress: int
    modules_requested: Optional[list[str]]
    modules_completed: Optional[list[str]]
    score: Optional[float]
    grade: Optional[str]
    findings_summary: Optional[dict]
    total_findings: int
    total_checks: int
    passed_checks: int
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]


# =============================================================================
# Helpers
# =============================================================================

def _target_to_response(t: HardeningTarget) -> TargetResponse:
    return TargetResponse(
        id=str(t.id),
        name=t.name,
        host=t.host,
        port=t.port,
        username=t.username,
        os_type=t.os_type,
        description=t.description,
        tags=t.tags or [],
        created_at=t.created_at.isoformat() if t.created_at else "",
    )


def _session_to_response(s: HardeningSession) -> SessionResponse:
    target = s.target
    return SessionResponse(
        id=str(s.id),
        target_id=str(s.target_id),
        target_name=target.name if target else "",
        target_host=target.host if target else "",
        status=s.status if isinstance(s.status, str) else s.status.value,
        current_module=s.current_module,
        progress=s.progress or 0,
        modules_requested=s.modules_requested,
        modules_completed=s.modules_completed,
        score=s.score,
        grade=s.grade,
        findings_summary=s.findings_summary,
        total_findings=s.total_findings or 0,
        total_checks=s.total_checks or 0,
        passed_checks=s.passed_checks or 0,
        error_message=s.error_message,
        started_at=s.started_at.isoformat() if s.started_at else None,
        completed_at=s.completed_at.isoformat() if s.completed_at else None,
        duration_seconds=s.duration_seconds,
    )


# =============================================================================
# Targets
# =============================================================================

@router.post("/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    body: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = HardeningTarget(
        created_by_id=current_user.id,
        name=body.name,
        host=body.host,
        port=body.port,
        username=body.username,
        os_type=body.os_type,
        description=body.description,
        credentials={
            "password": body.password,
            "key_path": body.key_path,
        } if (body.password or body.key_path) else None,
        tags=body.tags,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return _target_to_response(target)


@router.get("/targets", response_model=list[TargetResponse])
def list_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    targets = db.query(HardeningTarget).order_by(HardeningTarget.created_at.desc()).all()
    return [_target_to_response(t) for t in targets]


@router.get("/targets/{target_id}", response_model=TargetResponse)
def get_target(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(HardeningTarget).filter(HardeningTarget.id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    return _target_to_response(t)


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = db.query(HardeningTarget).filter(HardeningTarget.id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(t)
    db.commit()


# =============================================================================
# Sessions
# =============================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(HardeningTarget).filter(HardeningTarget.id == body.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    default_mods = DEFAULT_MODULES_BY_OS.get(target.os_type, DEFAULT_MODULES_BY_OS["linux"])
    session = HardeningSession(
        target_id=target.id,
        created_by_id=current_user.id,
        status=HardeningSessionStatus.PENDING,
        modules_requested=body.modules or default_mods,
        progress=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    from app.workers.hardening_tasks import run_hardening_session

    run_hardening_session.delay(str(session.id))

    return _session_to_response(session)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(HardeningSession)
        .order_by(HardeningSession.started_at.desc())
        .limit(50)
        .all()
    )
    return [_session_to_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_response(s)


@router.get("/sessions/{session_id}/findings", response_model=list[FindingResponse])
def get_session_findings(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    findings = (
        db.query(HardeningFinding)
        .filter(HardeningFinding.session_id == session_id)
        .order_by(HardeningFinding.severity)
        .all()
    )
    return [
        FindingResponse(
            id=str(f.id),
            check_id=f.check_id,
            check_name=f.check_name,
            module=f.module,
            description=f.description,
            severity=f.severity,
            found=f.found,
            expected=f.expected,
            remediation=f.remediation,
            status=f.status,
        )
        for f in findings
    ]


# =============================================================================
# Misc
# =============================================================================

@router.get("/modules")
def list_available_modules(current_user: User = Depends(get_current_user)):
    return {
        "supported_os": SUPPORTED_OS_TYPES,
        "modules_by_os": {
            "linux": [
                {"id": "ssh",        "name": "SSH Configuration",  "description": "CIS Benchmark SSH hardening checks"},
                {"id": "users",      "name": "User Accounts",      "description": "UID, password and shell audits"},
                {"id": "kernel",     "name": "Kernel Parameters",  "description": "sysctl security settings (ASLR, SYN cookies…)"},
                {"id": "firewall",   "name": "Firewall",           "description": "ufw / iptables / firewalld / nftables status"},
                {"id": "services",   "name": "Services",           "description": "Dangerous/obsolete services detection"},
                {"id": "filesystem", "name": "Filesystem",         "description": "Permissions et propriétaires des fichiers sensibles"},
                {"id": "network",    "name": "Network",            "description": "Ports en écoute, exposition réseau, ports à risque"},
            ],
            "macos_intel": [
                {"id": "ssh",        "name": "SSH Configuration",  "description": "macOS Intel SSH hardening"},
                {"id": "users",      "name": "User Accounts",      "description": "Comptes locaux macOS Intel"},
                {"id": "firewall",   "name": "Firewall",           "description": "pf / Application Firewall macOS Intel"},
                {"id": "services",   "name": "Services",           "description": "Services LaunchDaemon macOS Intel"},
                {"id": "filesystem", "name": "Filesystem",         "description": "Permissions fichiers sensibles macOS Intel"},
            ],
            "macos_silicon": [
                {"id": "ssh",        "name": "SSH Configuration",  "description": "macOS Silicon SSH hardening"},
                {"id": "users",      "name": "User Accounts",      "description": "Comptes locaux macOS Silicon"},
                {"id": "firewall",   "name": "Firewall",           "description": "pf / Application Firewall macOS Silicon"},
                {"id": "services",   "name": "Services",           "description": "Services LaunchDaemon macOS Silicon"},
                {"id": "filesystem", "name": "Filesystem",         "description": "Permissions fichiers sensibles macOS Silicon"},
            ],
        },
    }
