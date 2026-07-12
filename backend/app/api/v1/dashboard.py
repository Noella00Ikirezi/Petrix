"""Endpoint unique du tableau de bord — agrège les métriques assets, vulnérabilités et hardening.
Les sessions de hardening sont scopées au compte courant (sauf ADMIN) ; assets et vulnérabilités restent globaux.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.permissions import Permission, UserRole
from app.infrastructure.database import get_db
from app.infrastructure.database.models import (
    Asset,
    AssetStatus,
    Vulnerability,
    VulnStatus,
    Severity,
    User,
)
from app.infrastructure.database.hardening_models import (
    HardeningSession,
    HardeningSessionStatus,
)
from app.api.v1.deps import require_permission

router = APIRouter()


def _is_admin(user: User) -> bool:
    """Retourne True si l'utilisateur possède le rôle ADMIN."""
    return user.role == UserRole.ADMIN


def _hs_base(db: Session, user: User):
    """Retourne la requête de base sur HardeningSession, restreinte au compte courant sauf pour un ADMIN."""
    q = db.query(HardeningSession)
    if not _is_admin(user):
        q = q.filter(HardeningSession.created_by_id == user.id)
    return q


class DashboardStats(BaseModel):
    """Compteurs agrégés affichés dans la vue principale du tableau de bord."""

    total_assets: int
    active_assets: int
    total_vulnerabilities: int
    open_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    total_hardening_sessions: int
    completed_hardening_sessions: int
    running_hardening_sessions: int
    average_hardening_score: float | None
    last_audit_date: str | None


class VulnTrend(BaseModel):
    """Point de données journalier pour le graphique d'évolution des vulnérabilités (7 derniers jours)."""

    date: str
    critical: int
    high: int
    medium: int
    low: int


class DashboardResponse(BaseModel):
    """Réponse complète du tableau de bord : métriques agrégées, tendances, audits récents et contexte de scope."""

    stats: DashboardStats
    vuln_by_severity: dict
    vuln_by_status: dict
    assets_by_type: dict
    recent_audits: list
    vuln_trends: list[VulnTrend]
    # Contexte de scope pour le frontend
    scope: str          # "own" | "global"
    user_role: str


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ASSET_VIEW)),
):
    """Retourne les métriques du tableau de bord ; sessions de hardening scopées à l'utilisateur sauf pour un ADMIN — requiert ASSET_VIEW."""
    is_admin = _is_admin(current_user)

    # ── Assets (global — modèle sans owner) ──────────────────────────────────
    total_assets  = db.query(Asset).count()
    active_assets = db.query(Asset).filter(Asset.status == AssetStatus.ACTIVE).count()

    # ── Vulnérabilités (global) ───────────────────────────────────────────────
    total_vulns    = db.query(Vulnerability).count()
    open_vulns     = db.query(Vulnerability).filter(Vulnerability.status == VulnStatus.OPEN).count()
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == Severity.CRITICAL, Vulnerability.status == VulnStatus.OPEN
    ).count()
    high_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == Severity.HIGH, Vulnerability.status == VulnStatus.OPEN
    ).count()

    # ── Hardening (scoped) ────────────────────────────────────────────────────
    hs_q = _hs_base(db, current_user)

    total_sessions     = hs_q.count()
    completed_sessions = hs_q.filter(HardeningSession.status == HardeningSessionStatus.COMPLETED).count()
    running_sessions   = _hs_base(db, current_user).filter(
        HardeningSession.status.in_([HardeningSessionStatus.CONNECTING, HardeningSessionStatus.AUDITING])
    ).count()

    avg_score_result = (
        _hs_base(db, current_user)
        .filter(
            HardeningSession.status == HardeningSessionStatus.COMPLETED,
            HardeningSession.score.isnot(None),
        )
        .with_entities(func.avg(HardeningSession.score))
        .scalar()
    )
    average_score = round(float(avg_score_result), 1) if avg_score_result else None

    last_session = (
        _hs_base(db, current_user)
        .filter(HardeningSession.status == HardeningSessionStatus.COMPLETED)
        .order_by(HardeningSession.completed_at.desc())
        .first()
    )
    last_audit_date = (
        last_session.completed_at.isoformat()
        if last_session and last_session.completed_at
        else None
    )

    # ── Vulns par sévérité (global) ───────────────────────────────────────────
    vuln_by_severity = {
        sev.value: db.query(Vulnerability).filter(Vulnerability.severity == sev).count()
        for sev in Severity
    }

    vuln_by_status = {
        st.value: db.query(Vulnerability).filter(Vulnerability.status == st).count()
        for st in VulnStatus
    }

    # ── Assets par type (global) ──────────────────────────────────────────────
    from app.infrastructure.database.models import AssetType
    assets_by_type = {
        at.value: c
        for at in AssetType
        if (c := db.query(Asset).filter(Asset.asset_type == at).count()) > 0
    }

    # ── Derniers audits (scoped) ──────────────────────────────────────────────
    recent_sessions = (
        _hs_base(db, current_user)
        .filter(HardeningSession.status == HardeningSessionStatus.COMPLETED)
        .order_by(HardeningSession.completed_at.desc())
        .limit(5)
        .all()
    )
    recent_audits_data = [
        {
            "id":          str(s.id),
            "target_name": s.target.name if s.target else "Unknown",
            "target_host": s.target.host if s.target else "",
            "status":      s.status if isinstance(s.status, str) else s.status.value,
            "grade":       s.grade,
            "score":       s.score,
            "findings_summary": s.findings_summary,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in recent_sessions
    ]

    # ── Tendances vulns (global, 7 jours seulement — 30 était inutilement lourd) ──
    vuln_trends = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        d     = today - timedelta(days=i)
        d_end = datetime.combine(d, datetime.max.time())
        vuln_trends.append(VulnTrend(
            date=d.isoformat(),
            critical=db.query(Vulnerability).filter(
                Vulnerability.severity == Severity.CRITICAL,
                Vulnerability.discovered_at <= d_end,
            ).count(),
            high=db.query(Vulnerability).filter(
                Vulnerability.severity == Severity.HIGH,
                Vulnerability.discovered_at <= d_end,
            ).count(),
            medium=db.query(Vulnerability).filter(
                Vulnerability.severity == Severity.MEDIUM,
                Vulnerability.discovered_at <= d_end,
            ).count(),
            low=db.query(Vulnerability).filter(
                Vulnerability.severity == Severity.LOW,
                Vulnerability.discovered_at <= d_end,
            ).count(),
        ))

    return DashboardResponse(
        stats=DashboardStats(
            total_assets=total_assets,
            active_assets=active_assets,
            total_vulnerabilities=total_vulns,
            open_vulnerabilities=open_vulns,
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            total_hardening_sessions=total_sessions,
            completed_hardening_sessions=completed_sessions,
            running_hardening_sessions=running_sessions,
            average_hardening_score=average_score,
            last_audit_date=last_audit_date,
        ),
        vuln_by_severity=vuln_by_severity,
        vuln_by_status=vuln_by_status,
        assets_by_type=assets_by_type,
        recent_audits=recent_audits_data,
        vuln_trends=vuln_trends,
        scope="global" if is_admin else "own",
        user_role=current_user.role.value,
    )
