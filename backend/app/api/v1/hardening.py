"""Router API du module de durcissement HCO (Hardening Compliance Officer).

Expose la gestion des cibles d'audit (HardeningTarget), des sessions d'analyse
(HardeningSession) et des constats (HardeningFinding), l'import de rapports XML
générés par l'agent local Petrix, l'analyse IA via Mistral, la corrélation avec
les alertes CERT-FR et le téléchargement des scripts d'audit locaux.
"""
import asyncio
import datetime
import json
import os
import re
import defusedxml.ElementTree as ET
from xml.etree.ElementTree import Element as _XMLElement
from typing import Optional
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import URLError

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_permission
from app.core.permissions import Permission, UserRole
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User, Vulnerability, VulnStatus, Severity
from app.infrastructure.database.hardening_models import (
    HardeningTarget,
    HardeningSession,
    HardeningSessionStatus,
    HardeningFinding,
)
from app.hardening.engine import DEFAULT_MODULES_BY_OS, SUPPORTED_OS_TYPES
from app.hardening.cve_mapping import get_cves_for_check

router = APIRouter()

# Points déduits du score par sévérité de finding (formule identique aux agents bash/PS1)
SEVERITY_DEDUCTIONS: dict[str, int] = {
    "CRITICAL": 15, "HIGH": 8, "MEDIUM": 3, "LOW": 1, "INFO": 0
}


# =============================================================================
# Helpers de contrôle d'accès
# =============================================================================

def _is_admin(user: User) -> bool:
    """Retourne True si l'utilisateur possède le rôle ADMIN."""
    return user.role == UserRole.ADMIN


def _scope_query(query, model, user: User):
    """Restreint une requête aux enregistrements appartenant à l'utilisateur, sauf pour les admins."""
    if not _is_admin(user):
        return query.filter(model.created_by_id == user.id)
    return query


def _check_access(resource, user: User) -> None:
    """Lève une HTTPException 403 si la ressource n'appartient pas à l'utilisateur (non-admin).

    Args:
        resource: Instance ORM possédant un attribut ``created_by_id``.
        user: Utilisateur authentifié courant.

    Raises:
        HTTPException 403: Accès refusé si l'utilisateur n'est pas propriétaire ni admin.
    """
    if not _is_admin(user) and resource.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")


# =============================================================================
# Schémas Pydantic — requêtes et réponses de l'API de durcissement
# =============================================================================

class TargetCreate(BaseModel):
    """Corps de la requête POST /targets : enregistrement d'une nouvelle cible d'audit."""

    name: str
    os_type: str = "linux"
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class LatestSessionSummary(BaseModel):
    """Résumé de la dernière session d'audit d'une cible, inclus dans TargetResponse."""

    session_id: str
    status: str
    score: Optional[float]
    grade: Optional[str]
    completed_at: Optional[str]
    total_checks: int
    passed_checks: int
    total_findings: int
    findings_summary: Optional[dict]


class TargetResponse(BaseModel):
    """Représentation complète d'une cible de durcissement retournée par l'API.

    Attributs notables :
        latest_session: Résumé de la dernière session exécutée sur cette cible (ou None).
        session_count: Nombre total de sessions d'audit enregistrées pour cette cible.
    """

    id: str
    name: str
    host: str
    port: int
    username: str
    os_type: str
    description: Optional[str]
    tags: Optional[list[str]]
    created_at: str
    latest_session: Optional[LatestSessionSummary] = None
    session_count: int = 0

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Corps de la requête POST /sessions (dépréciée — utiliser POST /import-xml à la place)."""

    target_id: str
    modules: Optional[list[str]] = None


class FindingResponse(BaseModel):
    """Représentation d'un constat individuel de durcissement.

    Attributs notables :
        found / expected: Valeur observée vs valeur attendue selon le référentiel.
        cve_ids: CVE associés via la table de correspondance ``cve_mapping.py``.
    """

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
    cve_ids: list[str] = []
    point_deduction: int = 0


class SessionResponse(BaseModel):
    """Représentation complète d'une session de durcissement retournée par l'API."""

    id: str
    target_id: str
    target_name: str
    target_host: str
    target_os_type: Optional[str] = None
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


class FullReportResponse(BaseModel):
    """Rapport complet d'une session d'audit : session + liste des constats + analyse IA."""

    session: SessionResponse
    findings: list[FindingResponse]
    target_description: Optional[str] = None
    target_tags: Optional[list[str]] = None
    ai_analysis: Optional[dict] = None


class AiChatRequest(BaseModel):
    """Corps de la requête POST /sessions/{id}/ai-chat : question posée à l'IA Mistral."""

    question: str


class AiChatResponse(BaseModel):
    """Réponse de l'IA Mistral à une question contextualisée sur les findings d'une session."""

    answer: str


# =============================================================================
# Fonctions de conversion ORM → schéma
# =============================================================================

def _target_to_response(t: HardeningTarget, db: Optional[Session] = None) -> TargetResponse:
    """Convertit un ORM HardeningTarget en TargetResponse avec résumé de la dernière session.

    Args:
        t: Instance ORM de la cible à convertir.
        db: Session de base de données optionnelle ; si fournie, charge le nombre de sessions
            et le résumé de la plus récente.

    Returns:
        TargetResponse prête à être sérialisée par FastAPI.
    """
    latest_session = None
    session_count = 0

    if db is not None:
        session_count = db.query(HardeningSession).filter(
            HardeningSession.target_id == t.id
        ).count()
        last = (
            db.query(HardeningSession)
            .filter(HardeningSession.target_id == t.id)
            .order_by(HardeningSession.started_at.desc())
            .first()
        )
        if last:
            latest_session = LatestSessionSummary(
                session_id=str(last.id),
                status=last.status if isinstance(last.status, str) else last.status.value,
                score=last.score,
                grade=last.grade,
                completed_at=last.completed_at.isoformat() if last.completed_at else None,
                total_checks=last.total_checks or 0,
                passed_checks=last.passed_checks or 0,
                total_findings=last.total_findings or 0,
                findings_summary=last.findings_summary,
            )

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
        latest_session=latest_session,
        session_count=session_count,
    )


def _session_to_response(s: HardeningSession) -> SessionResponse:
    """Convertit un ORM HardeningSession en SessionResponse avec les infos de sa cible."""
    target = s.target
    return SessionResponse(
        id=str(s.id),
        target_id=str(s.target_id),
        target_name=target.name if target else "",
        target_host=target.host if target else "",
        target_os_type=target.os_type if target else None,
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
    """Crée une nouvelle cible d'audit de durcissement pour l'utilisateur courant."""
    target = HardeningTarget(
        created_by_id=current_user.id,
        name=body.name,
        host=body.name,
        port=0,
        username="local",
        os_type=body.os_type,
        description=body.description,
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
    """Liste les cibles de durcissement accessibles à l'utilisateur (toutes pour un admin)."""
    q = _scope_query(db.query(HardeningTarget), HardeningTarget, current_user)
    targets = q.order_by(HardeningTarget.created_at.desc()).all()
    return [_target_to_response(t, db) for t in targets]


@router.get("/targets/{target_id}", response_model=TargetResponse)
def get_target(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le détail d'une cible de durcissement par son UUID."""
    t = db.query(HardeningTarget).filter(HardeningTarget.id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    _check_access(t, current_user)
    return _target_to_response(t, db)


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Supprime une cible de durcissement et toutes ses sessions associées (cascade)."""
    t = db.query(HardeningTarget).filter(HardeningTarget.id == target_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Target not found")
    _check_access(t, current_user)
    db.delete(t)
    db.commit()


# =============================================================================
# Sessions
# =============================================================================

@router.post("/sessions", status_code=status.HTTP_410_GONE)
def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
):
    """SSH-based audit sessions have been removed.
    Use the local agent scripts and POST /import-xml instead."""
    raise HTTPException(
        status_code=410,
        detail=(
            "Les audits SSH ont été supprimés. "
            "Téléchargez l'agent local (GET /agent-script/{linux|macos|windows}) "
            "et importez le rapport XML via POST /import-xml."
        ),
    )


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Liste les 50 sessions de durcissement les plus récentes accessibles à l'utilisateur."""
    q = _scope_query(db.query(HardeningSession), HardeningSession, current_user)
    sessions = q.order_by(HardeningSession.started_at.desc()).limit(50).all()
    return [_session_to_response(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le détail d'une session de durcissement par son UUID."""
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_access(s, current_user)
    return _session_to_response(s)


@router.get("/sessions/{session_id}/findings", response_model=list[FindingResponse])
def get_session_findings(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne la liste des constats d'une session, triés par sévérité décroissante."""
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_access(s, current_user)

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
            cve_ids=get_cves_for_check(f.check_id),
            point_deduction=SEVERITY_DEDUCTIONS.get(f.severity, 0) if f.status != "PASS" else 0,
        )
        for f in findings
    ]


@router.get("/sessions/{session_id}/report", response_model=FullReportResponse)
def get_full_report(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne le rapport complet d'une session : métadonnées, constats triés et analyse IA."""
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_access(s, current_user)

    findings = (
        db.query(HardeningFinding)
        .filter(HardeningFinding.session_id == session_id)
        .order_by(HardeningFinding.severity)
        .all()
    )
    finding_list = [
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
            cve_ids=get_cves_for_check(f.check_id),
            point_deduction=SEVERITY_DEDUCTIONS.get(f.severity, 0) if f.status != "PASS" else 0,
        )
        for f in findings
    ]
    target = s.target
    return FullReportResponse(
        session=_session_to_response(s),
        findings=finding_list,
        target_description=target.description if target else None,
        target_tags=target.tags if target else None,
        ai_analysis=s.ai_analysis,
    )


# =============================================================================
# AI Chat — Mistral (questions contextualisées sur une session)
# =============================================================================

def _mistral_chat(hostname: str, os_label: str, score: float, grade: str,
                  findings: list, question: str) -> str:
    """Envoie une question contextuelle à Mistral API et retourne la réponse en texte libre.

    Args:
        hostname: Nom de la machine auditée (affiché dans le contexte du prompt).
        os_label: Libellé de l'OS (macOS, Linux…) pour enrichir le contexte IA.
        score: Score global de l'audit (0–100).
        grade: Grade alphabétique (A–F).
        findings: Liste de dicts ``{status, severity, name, found, expected}`` (max 30).
        question: Question posée par l'utilisateur (max 500 caractères).

    Returns:
        Réponse textuelle de Mistral (max ~300 mots), ou message d'erreur lisible.
    """
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return "L'analyse IA n'est pas disponible (clé API Mistral non configurée). Contactez votre administrateur."

    fails = [f for f in findings if f.get("status") != "PASS"]
    context_lines = [
        f"- [{f.get('severity','?')}] {f.get('name','')}: trouvé={f.get('found','')}, attendu={f.get('expected','')}"
        for f in findings[:30]
    ]
    context = "\n".join(context_lines)

    prompt = f"""Tu es un expert en cybersécurité ANSSI-BP-028 intégré à la plateforme Petrix.
Contexte de l'audit :
  Système : {hostname} ({os_label}) — Score : {score}/100 — Grade : {grade}
  {len(fails)} findings FAIL sur {len(findings)} contrôles totaux

Findings principaux :
{context}

L'utilisateur pose cette question : {question}

Réponds en français de manière claire, concise et pratique (maximum 300 mots).
Si la question porte sur un finding spécifique, inclus la remédiation concrète."""

    payload = json.dumps({
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3,
    }).encode("utf-8")

    req = UrlRequest(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return f"L'analyse IA est temporairement indisponible. Réessayez dans quelques instants. ({type(e).__name__})"


@router.post("/sessions/{session_id}/ai-chat", response_model=AiChatResponse)
async def ai_chat(
    session_id: str,
    body: AiChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Répond à une question sur un audit en utilisant Mistral avec les findings comme contexte.

    Délègue l'appel HTTP bloquant à Mistral dans un thread séparé via asyncio.to_thread
    pour ne pas bloquer la boucle d'événements FastAPI.
    """
    if not body.question or not body.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    if len(body.question) > 500:
        raise HTTPException(status_code=400, detail="Question trop longue (max 500 caractères)")

    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_access(s, current_user)

    findings_db = (
        db.query(HardeningFinding)
        .filter(HardeningFinding.session_id == session_id)
        .all()
    )
    findings_for_ai = [
        {
            "status":   f.status,
            "severity": f.severity,
            "name":     f.check_name,
            "found":    f.found,
            "expected": f.expected,
        }
        for f in findings_db
    ]

    target = s.target
    hostname  = target.name if target else "inconnu"
    os_label  = target.os_type if target else "unknown"

    answer = await asyncio.to_thread(
        _mistral_chat,
        hostname, os_label,
        s.score or 0, s.grade or "?",
        findings_for_ai, body.question.strip()
    )
    return AiChatResponse(answer=answer)


# =============================================================================
# Analyse IA — Mistral
# =============================================================================

def _mistral_analyze(hostname: str, os_label: str, score: float, grade: str,
                     findings: list) -> Optional[dict]:
    """Génère une analyse structurée des findings via Mistral et retourne un dict JSON.

    Args:
        hostname: Nom de la machine auditée.
        os_label: Libellé de l'OS pour enrichir le contexte IA.
        score: Score global de l'audit (0–100).
        grade: Grade alphabétique (A–F).
        findings: Liste complète de dicts ``{status, severity, name, found, expected}``.

    Returns:
        Dict avec clés ``resume_executif``, ``top_priorites``, ``evaluation_anssi``,
        ``plan_remediation``, ``risque_global`` ; ou None en cas d'erreur API/parsing.
    """
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        return None

    fails = [f for f in findings if f.get("status") != "PASS"]
    if not fails:
        return {
            "resume_executif": f"Le système {hostname} présente une excellente posture de sécurité avec un score de {score}/100 (grade {grade}). Aucun écart de conformité détecté.",
            "top_priorites": ["Maintenir ce niveau de conformité", "Planifier un re-audit dans 3 mois", "Documenter la configuration comme référence"],
            "evaluation_anssi": "Conforme aux recommandations ANSSI-BP-028.",
            "plan_remediation": "Aucune action corrective requise.",
            "risque_global": "FAIBLE",
        }

    crit_count = sum(1 for f in fails if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in fails if f.get("severity") == "HIGH")
    med_count  = sum(1 for f in fails if f.get("severity") == "MEDIUM")
    low_count  = sum(1 for f in fails if f.get("severity") == "LOW")

    findings_text = "\n".join([
        f"- [{f.get('severity','?')}] {f.get('name','')}: valeur={f.get('found','')}, attendu={f.get('expected','')}"
        for f in fails[:25]
    ])

    prompt = f"""Tu es un auditeur senior en cybersécurité. Voici les resultats d'un audit de durcissement automatise. Genere une synthese de conclusion en JSON valide uniquement (sans markdown, sans code block).

Systeme audite: {hostname} ({os_label})
Score: {score}/100 — Grade: {grade}
Ecarts: {len(fails)} au total ({crit_count} critiques x15pts, {high_count} eleves x8pts, {med_count} moyens x3pts, {low_count} faibles x1pt)

Ecarts detectes:
{findings_text}

Reponds UNIQUEMENT avec ce JSON (sans aucun texte autour):
{{
  "resume_executif": "Synthese en 3 phrases max de la posture securite du systeme",
  "niveau_risque": "CRITIQUE|ELEVE|MODERE|FAIBLE",
  "top_priorites": ["Action 1 urgente concrete", "Action 2 concrete", "Action 3 concrete"],
  "quick_wins": ["Correctif rapide 1 (moins de 5 min)", "Correctif rapide 2 (1 commande)"],
  "plan_remediation": "Court terme (48h): ... Moyen terme (2 semaines): ... Long terme: ...",
  "evaluation_conformite": "Evaluation de la conformite aux normes applicables (ANSSI-BP-028 pour Linux, CIS macOS pour Mac, CIS WS2019 pour Windows)"
}}"""

    payload = json.dumps({
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.2,
    }).encode("utf-8")

    req = UrlRequest(
        "https://api.mistral.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        # Nettoyer si markdown ```json ... ```
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S).strip()
        return json.loads(content)
    except (URLError, KeyError, json.JSONDecodeError):
        return None


# =============================================================================
# Import XML (rapport local Petrix Audit Agent)
# =============================================================================

def _txt(el: Optional[_XMLElement], tag: str, default: str = "") -> str:
    """Extrait le texte d'un sous-élément XML, en retournant ``default`` si absent ou vide."""
    child = el.find(tag) if el is not None else None
    return (child.text or default).strip() if child is not None else default


@router.post("/import-xml", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def import_xml_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.SCAN_CREATE)),
):
    """Importe un rapport XML généré par l'agent local ``petrix_audit_local.py``.

    Crée automatiquement la cible (upsert par hostname + os_type) et la session
    dans la base de données, puis lance l'analyse IA Mistral en arrière-plan.
    Taille maximale acceptée : 5 Mo. Format attendu : ``<PetrixAuditReport>``.
    """
    if not file.filename or not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Fichier XML requis (.xml)")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 5 Mo)")

    try:
        root = ET.fromstring(content.decode("utf-8", errors="replace"))
    except ET.ParseError as exc:
        raise HTTPException(status_code=422, detail=f"XML invalide : {exc}")

    if root.tag != "PetrixAuditReport":
        raise HTTPException(status_code=422, detail="Format non reconnu — utiliser petrix_audit_local.py")

    # ── Métadonnées ──────────────────────────────────────────────────────────
    meta      = root.find("Metadata")
    hostname  = _txt(meta, "Hostname", "unknown")
    os_label  = _txt(meta, "OS", "macOS")
    os_type   = _txt(meta, "OSType", "macos_silicon")
    arch      = _txt(meta, "Architecture", "arm64")
    gen_date  = _txt(meta, "GenerationDate", "")
    referential = root.attrib.get("Referential", "CIS_macOS_L1")

    # ── Scores ───────────────────────────────────────────────────────────────
    scores_el = root.find("Scores")
    global_score = float(_txt(scores_el, "GlobalScore", "0"))
    global_grade = _txt(scores_el, "GlobalGrade", "F")
    total_checks  = int(_txt(scores_el, "TotalChecks", "0"))
    passed_checks = int(_txt(scores_el, "PassedChecks", "0"))
    crit_count    = int(_txt(scores_el, "CriticalCount", "0"))
    high_count    = int(_txt(scores_el, "HighCount", "0"))
    med_count     = int(_txt(scores_el, "MediumCount", "0"))
    low_count     = int(_txt(scores_el, "LowCount", "0"))

    findings_summary = {
        "CRITICAL": crit_count,
        "HIGH":     high_count,
        "MEDIUM":   med_count,
        "LOW":      low_count,
    }

    modules_completed = []
    ms_el = scores_el.find("ModuleScores") if scores_el is not None else None
    if ms_el is not None:
        modules_completed = [m.attrib.get("name", "") for m in ms_el.findall("Module")]

    # ── Findings ─────────────────────────────────────────────────────────────
    findings_el = root.find("Findings")
    raw_findings = findings_el.findall("Finding") if findings_el is not None else []
    fail_count   = len([f for f in raw_findings if f.attrib.get("status") == "FAIL"])

    # ── Trouver ou créer la cible (scoped au compte courant) ──────────────────
    target = (
        db.query(HardeningTarget)
        .filter(
            HardeningTarget.host == hostname,
            HardeningTarget.os_type == os_type,
            HardeningTarget.created_by_id == current_user.id,
        )
        .first()
    )
    if not target:
        target = HardeningTarget(
            created_by_id=current_user.id,
            name=hostname,
            host=hostname,
            port=0,
            username="local",
            os_type=os_type,
            description=f"Import XML local — {os_label} {arch} — {referential}",
            tags=["xml-import", arch, referential],
        )
        db.add(target)
        db.flush()

    # ── Créer la session ──────────────────────────────────────────────────────
    try:
        completed_at = datetime.datetime.fromisoformat(gen_date) if gen_date else datetime.datetime.utcnow()
    except ValueError:
        completed_at = datetime.datetime.utcnow()

    session = HardeningSession(
        target_id=target.id,
        created_by_id=current_user.id,
        status=HardeningSessionStatus.COMPLETED,
        progress=100,
        modules_requested=modules_completed,
        modules_completed=modules_completed,
        score=global_score,
        grade=global_grade,
        findings_summary=findings_summary,
        total_findings=fail_count,
        total_checks=total_checks,
        passed_checks=passed_checks,
        started_at=completed_at,
        completed_at=completed_at,
    )
    db.add(session)
    db.flush()

    # ── Créer les findings ────────────────────────────────────────────────────
    sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    for f_el in sorted(raw_findings, key=lambda x: sev_order.get(x.attrib.get("severity", "INFO"), 4)):
        finding = HardeningFinding(
            session_id=session.id,
            check_id=f_el.attrib.get("id", ""),
            check_name=_txt(f_el, "Name"),
            module=f_el.attrib.get("module", ""),
            description=_txt(f_el, "Context") or _txt(f_el, "Name"),
            severity=f_el.attrib.get("severity", "MEDIUM"),
            found=_txt(f_el, "Found"),
            expected=_txt(f_el, "Expected"),
            remediation=_txt(f_el, "Remediation"),
            status=f_el.attrib.get("status", "FAIL"),
        )
        db.add(finding)

    db.commit()
    db.refresh(session)

    # ── Auto-sync CRITICAL/HIGH → tracker vulnérabilités ─────────────────────
    sev_vuln_map = {"CRITICAL": Severity.CRITICAL, "HIGH": Severity.HIGH}
    for f_el in raw_findings:
        sev_str = f_el.attrib.get("severity", "")
        if f_el.attrib.get("status") != "FAIL" or sev_str not in sev_vuln_map:
            continue
        title = f"[HCO] {_txt(f_el, 'Name')}"
        if not db.query(Vulnerability).filter(Vulnerability.title == title).first():
            db.add(Vulnerability(
                title=title,
                description=_txt(f_el, "Context") or _txt(f_el, "Name"),
                severity=sev_vuln_map[sev_str],
                status=VulnStatus.OPEN,
                discovered_by="agent",
            ))
    db.commit()

    # ── Analyse IA Mistral ────────────────────────────────────────────────────
    findings_for_ai = [
        {
            "status":   f_el.attrib.get("status", "FAIL"),
            "severity": f_el.attrib.get("severity", "MEDIUM"),
            "name":     _txt(f_el, "Name"),
            "found":    _txt(f_el, "Found"),
            "expected": _txt(f_el, "Expected"),
        }
        for f_el in raw_findings
    ]
    ai = await asyncio.to_thread(_mistral_analyze, hostname, os_label, global_score, global_grade, findings_for_ai)
    if ai:
        session.ai_analysis = ai
        db.commit()
        db.refresh(session)

    return _session_to_response(session)


# =============================================================================
# Agent scripts download
# =============================================================================

_AGENT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "hardening", "agents")

_AGENT_FILES = {
    "linux":   ("linux.sh",    "application/x-sh", "petrix_agent_linux.sh"),
    "macos":   ("macos.sh",    "application/x-sh", "petrix_agent_macos.sh"),
    "windows": ("windows.ps1", None,                "petrix_agent_windows.bat"),
}

# En-tête polyglotte BAT/PS1 — s'exécute dans CMD sans restriction ExecutionPolicy.
# CMD exécute les lignes 1-3 puis termine ; PowerShell les ignore et saute directement
# au contenu PS1 après le marqueur #--PETRIX_PS1_START--.
_WINDOWS_BAT_HEADER = """\
@echo off
setlocal
set "_pf=%~f0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$f=$env:_pf;$a=[IO.File]::ReadAllLines($f);$s=0;for($i=0;$i-lt$a.Count;$i++){if($a[$i]-eq'#--PETRIX_PS1_START--'){$s=$i+1;break}};$t=[IO.Path]::GetTempPath()+'petrix_'+[Guid]::NewGuid().ToString().Substring(0,8)+'.ps1';[IO.File]::WriteAllLines($t,$a[$s..($a.Count-1)]);& $t;Remove-Item $t -EA 0"
endlocal & exit /b %ERRORLEVEL%
#--PETRIX_PS1_START--
"""


@router.get("/agent-script/{os_type}")
def download_agent_script(os_type: str):
    """Télécharge le script d'audit local pour l'OS demandé (linux, macos, windows). Endpoint public.

    Pour Windows, retourne un fichier ``.bat`` polyglotte BAT/PS1 qui extrait et exécute
    le script PowerShell embarqué sans requérir de modification de la politique d'exécution.
    """
    entry = _AGENT_FILES.get(os_type.lower())
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"OS non supporte : {os_type}. Valeurs acceptees : linux, macos, windows",
        )
    filename, media_type, download_name = entry
    path = os.path.normpath(os.path.join(_AGENT_DIR, filename))
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Script d'agent introuvable sur le serveur")

    if os_type.lower() == "windows":
        ps1_content = open(path, encoding="ascii").read()
        bat_content = (_WINDOWS_BAT_HEADER + ps1_content).encode("ascii")
        return Response(
            content=bat_content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )

    return FileResponse(path, media_type=media_type, filename=download_name)


# =============================================================================
# CVE / CERT-FR correlation
# =============================================================================

# Mots-clés par module d'audit utilisés pour corréler les constats avec les alertes CERT-FR
_MODULE_CERT_KW: dict[str, list[str]] = {
    "ssh":        ["ssh", "openssh", "secure shell", "sftp"],
    "firewall":   ["pare-feu", "firewall", "iptables", "nftables", "netfilter", " pf "],
    "filesystem": ["chiffrement", "luks", "setuid", "permission", "droits", "privilege"],
    "system":     ["noyau", "kernel", "linux", "sudo", "polkit", "systemd"],
    "users":      ["authentification", "compte", "mot de passe", "password", "privilege", "ldap", "active directory"],
    "services":   ["smb", "samba", "ftp", "telnet", "rpc", "nfs", "cifs", "vnc", "rdp", "mssql", "mysql", "postgresql"],
    "updates":    ["mise à jour", "patch", "update", "paquet", "obsolète", "vulnérable"],
    "network":    ["réseau", "network", "netbios", "llmnr", "mdns", "snmp", "arp"],
    "packages":   ["paquet", "package", "dépôt", "repository", "apt", "yum", "dnf"],
    "pam":        ["pam", "authentification", "mot de passe", "password", "kerberos"],
    "logging":    ["journalisation", "audit", "log", "syslog", "auditd"],
    "kernel":     ["noyau", "kernel", "sysctl", "aslr", "débordement", "buffer overflow"],
    "winpolicies":["uac", "stratégie", "policy", "powershell", "windows defender", "applocker"],
    "winlogging": ["event log", "journalisation", "windows", "security audit"],
    "filevault":  ["chiffrement", "bitlocker", "filevault", "luks", "disk encryption"],
}


def _fetch_cert_fr_items() -> list[dict]:
    """Récupère et fusionne les flux RSS CERT-FR (alertes + avis) ; retourne une liste vide en cas d'erreur."""
    from app.api.v1.feed import _fetch_rss
    try:
        alertes = _fetch_rss("alerte")["items"]
    except Exception:
        alertes = []
    try:
        avis = _fetch_rss("avis")["items"]
    except Exception:
        avis = []
    return alertes + avis


def _correlate_finding_to_cert(finding_module: str, check_name: str, cert_items: list[dict]) -> list[dict]:
    """Retourne les alertes/avis CERT-FR correspondant à un constat par correspondance de mots-clés.

    Args:
        finding_module: Module d'audit source du constat (ssh, firewall, users…).
        check_name: Nom du contrôle (utilisé pour extraire des mots-clés supplémentaires).
        cert_items: Liste combinée des items CERT-FR (alertes + avis).

    Returns:
        Liste de au plus 3 dicts CERT-FR pertinents (cert_id, title, link, severity, cves, published).
    """
    kws = _MODULE_CERT_KW.get(finding_module, [])
    # Mots significatifs (≥ 4 caractères) extraits du nom du contrôle pour affiner le matching
    name_words = [w.lower() for w in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", check_name) if len(w) >= 4]
    all_kws = kws + name_words
    matched = []
    for item in cert_items:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        if any(kw in text for kw in all_kws):
            matched.append({
                "cert_id":  item.get("cert_id", ""),
                "title":    item.get("title", ""),
                "link":     item.get("link", ""),
                "severity": item.get("severity", "MEDIUM"),
                "cves":     item.get("cves", []),
                "published":item.get("published", ""),
            })
    return matched[:3]  # Limite à 3 correspondances par constat pour éviter le bruit


@router.get("/sessions/{session_id}/cert-correlations")
async def get_cert_correlations(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pour une session donnée, corrèle les constats FAIL avec les alertes/avis CERT-FR.

    Récupère les flux RSS CERT-FR en temps réel puis applique un matching par module
    et mots-clés sur les 40 premiers constats FAIL triés par sévérité.
    """
    s = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_access(s, current_user)

    fail_findings = (
        db.query(HardeningFinding)
        .filter(
            HardeningFinding.session_id == session_id,
            HardeningFinding.status == "FAIL",
        )
        .order_by(HardeningFinding.severity)
        .limit(40)
        .all()
    )

    cert_items = await asyncio.to_thread(_fetch_cert_fr_items)

    correlations = []
    for f in fail_findings:
        matched_alerts = _correlate_finding_to_cert(f.module, f.check_name, cert_items)
        if matched_alerts:
            correlations.append({
                "finding_id":   str(f.id),
                "check_id":     f.check_id,
                "check_name":   f.check_name,
                "module":       f.module,
                "severity":     f.severity,
                "cert_alerts":  matched_alerts,
            })

    return {
        "session_id":    session_id,
        "total_correlated": len(correlations),
        "cert_items_fetched": len(cert_items),
        "correlations":  correlations,
    }


# =============================================================================
# Misc
# =============================================================================

@router.get("/modules")
def list_available_modules(current_user: User = Depends(get_current_user)):
    """Retourne la liste des modules d'audit disponibles par OS, avec références ANSSI-BP-028."""
    return {
        "supported_os": SUPPORTED_OS_TYPES,
        "modules_by_os": {
            "linux": [
                {"id": "ssh",        "name": "SSH Configuration",    "description": "[ANSSI R4-R5] Configuration du serveur SSH", "anssi_refs": ["R4", "R5"]},
                {"id": "users",      "name": "Comptes utilisateurs", "description": "[ANSSI R30-R44] Comptes, sudo, politique de mots de passe", "anssi_refs": ["R30", "R31", "R32", "R33", "R34", "R36", "R37"]},
                {"id": "kernel",     "name": "Paramètres noyau",     "description": "[ANSSI R8-R13] Paramètres sysctl de sécurité (ASLR, SYN cookies…)", "anssi_refs": ["R8", "R9", "R10", "R11", "R12", "R13"]},
                {"id": "firewall",   "name": "Pare-feu",             "description": "[ANSSI R67] ufw / iptables / firewalld / nftables", "anssi_refs": ["R67"]},
                {"id": "services",   "name": "Services",             "description": "[ANSSI R62-R66] Détection des services dangereux ou obsolètes", "anssi_refs": ["R62", "R63", "R66"]},
                {"id": "filesystem", "name": "Système de fichiers",  "description": "[ANSSI R28-R57] Partitions, setuid/setgid, sticky bit, permissions", "anssi_refs": ["R28", "R29", "R49", "R52", "R53", "R54", "R56", "R57"]},
                {"id": "network",    "name": "Réseau",               "description": "[ANSSI R12] Ports en écoute, exposition réseau", "anssi_refs": ["R12"]},
                {"id": "packages",   "name": "Gestion des paquets",  "description": "[ANSSI R58-R61] Paquets inutiles, dépôts de confiance, mises à jour", "anssi_refs": ["R58", "R59", "R61"]},
                {"id": "pam",        "name": "Authentification PAM", "description": "[ANSSI R68-R70] PAM, hachage des mots de passe, bases distantes", "anssi_refs": ["R68", "R69", "R70"]},
                {"id": "logging",    "name": "Journalisation",       "description": "[ANSSI R71-R74] syslog, auditd, service mail, intégrité fichiers", "anssi_refs": ["R71", "R72", "R73", "R74"]},
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
