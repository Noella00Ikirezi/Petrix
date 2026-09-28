"""WebSocket temps réel du module de durcissement : connexion persistante des agents
de surveillance continue et relai des événements live vers les dashboards connectés.

Deux endpoints :
  WS /hardening/ws/agent?target_id=...&token=...   — utilisé par petrix_daemon.py
  WS /hardening/ws/dashboard?token=<jwt>            — utilisé par le frontend (React)

Architecture agent-initiated uniquement, cohérente avec la suppression des audits SSH
orchestrés côté serveur (voir hardening.py) : aucune connexion entrante n'est jamais
établie vers une machine surveillée. Les événements (heartbeat, connexion/déconnexion,
nouvelle session) sont diffusés via Redis pub/sub (voir core/redis.py) car le backend
tourne avec plusieurs workers Uvicorn qui ne partagent pas d'état WebSocket en mémoire :
un agent connecté au worker A doit pouvoir notifier un dashboard connecté au worker B.
"""
import datetime
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.v1.hardening import _ingest_xml_report
from app.config import settings
from app.core.permissions import UserRole
from app.core.redis import HARDENING_LIVE_CHANNEL, check_rate_limit, publish_live_event
from app.core.security import decode_token, verify_password
from app.infrastructure.database import SessionLocal
from app.infrastructure.database.hardening_models import HardeningTarget
from app.infrastructure.database.models import User

router = APIRouter()


def _client_ip(websocket: WebSocket) -> str:
    """Retourne l'adresse IP du client WS, ou ``"unknown"`` si indisponible (tests, proxy)."""
    return websocket.client.host if websocket.client else "unknown"


def _publish_target_event(event_type: str, target: HardeningTarget, **extra) -> None:
    """Publie un événement lié à une cible, avec ``owner_id`` pour le filtrage côté dashboard."""
    publish_live_event({
        "type": event_type,
        "target_id": str(target.id),
        "owner_id": str(target.created_by_id),
        "at": datetime.datetime.utcnow().isoformat(),
        **extra,
    })


@router.websocket("/ws/agent")
async def agent_socket(websocket: WebSocket, target_id: str, token: str):
    """Connexion persistante d'un agent de surveillance continue (``petrix_daemon.py``).

    Authentification par token opaque (haché en base, jamais par JWT utilisateur) :
    l'agent tourne sur une machine tierce et ne doit jamais détenir de credentials
    utilisateur, seulement le token d'enrôlement généré par ``POST /agent-enroll``.
    """
    ip = _client_ip(websocket)
    if not check_rate_limit(f"agent-auth:{ip}", max_requests=10, window_seconds=60):
        await websocket.close(code=4029)
        return

    db: Session = SessionLocal()
    try:
        target = db.query(HardeningTarget).filter(HardeningTarget.id == target_id).first()
        if not target or not target.agent_token_hash or not verify_password(token, target.agent_token_hash):
            await websocket.close(code=4001)
            return

        await websocket.accept()
        target.last_heartbeat_at = datetime.datetime.utcnow()
        db.commit()
        _publish_target_event("agent_online", target)

        try:
            while True:
                message = await websocket.receive_json()
                msg_type = message.get("type")

                if msg_type == "heartbeat":
                    target.last_heartbeat_at = datetime.datetime.utcnow()
                    db.commit()
                    _publish_target_event("heartbeat", target)

                elif msg_type == "report":
                    xml_content = message.get("xml", "")
                    user = db.query(User).filter(User.id == target.created_by_id).first()
                    if user is None:
                        continue
                    session = await _ingest_xml_report(xml_content.encode("utf-8"), user, db)
                    target.last_heartbeat_at = datetime.datetime.utcnow()
                    db.commit()
                    _publish_target_event(
                        "new_session", target,
                        session_id=str(session.id),
                        score=session.score,
                        grade=session.grade,
                        findings_summary=session.findings_summary,
                    )
        except WebSocketDisconnect:
            pass
        finally:
            _publish_target_event("agent_offline", target)
    finally:
        db.close()


@router.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket, token: str):
    """Relai temps réel vers un client dashboard authentifié (frontend React).

    Authentification par JWT ``access`` classique (même token que les requêtes HTTP).
    Un admin reçoit tous les événements ; un utilisateur standard ne reçoit que ceux
    de ses propres cibles (même logique de scoping que ``_scope_query`` côté REST).
    """
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub") if payload else None
    if not user_id:
        await websocket.close(code=4001)
        return

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            await websocket.close(code=4001)
            return
        is_admin = user.role == UserRole.ADMIN
    finally:
        db.close()

    await websocket.accept()

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(HARDENING_LIVE_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            event = json.loads(message["data"])
            if not is_admin and event.get("owner_id") != str(user_id):
                continue
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(HARDENING_LIVE_CHANNEL)
        await pubsub.close()
        await redis_client.aclose()
