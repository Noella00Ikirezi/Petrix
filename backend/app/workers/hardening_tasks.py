"""Tâches Celery pour le module HCO Hardening.

Expose la tâche ``run_hardening_session`` qui orchestre un audit complet
sur une cible distante : chargement de la session depuis la base de données,
connexion SSH, exécution des modules d'audit, persistance des findings et
mise à jour du score/grade dans la session.
"""
from datetime import datetime

from app.workers.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.database.hardening_models import (
    HardeningSession,
    HardeningSessionStatus,
    HardeningTarget,
    HardeningFinding,
)
from loguru import logger


def _get_db():
    """Retourne une session SQLAlchemy — à fermer explicitement dans un bloc finally."""
    return SessionLocal()


@celery_app.task(bind=True, name="hardening.run_session")
def run_hardening_session(self, session_id: str) -> dict:
    """Lance un audit HCO complet sur la cible associée à la session.

    Tâche Celery longue (jusqu'à 30 min par timeout Celery). Communique la
    progression via ``self.update_state`` et des commits intermédiaires
    en base pour permettre un suivi temps réel depuis l'API.

    Phases d'exécution :
        1. Chargement de la session et de la cible depuis la base.
        2. CONNECTING — ouverture de la connexion SSH.
        3. AUDITING — exécution module par module avec callback de progression.
        4. Persistance des ``HardeningFinding`` en base.
        5. COMPLETED — mise à jour du score, grade et statistiques de la session.

    Args:
        self: Référence Celery à la tâche courante (bind=True).
        session_id: UUID de la ``HardeningSession`` à exécuter.

    Returns:
        dict avec clés :
            ``session_id``, ``status``, ``score``, ``grade``,
            ``total_findings`` en cas de succès.
            ``error`` (str) en cas d'échec.
    """
    db = _get_db()
    try:
        session = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
        if not session:
            return {"error": f"Session {session_id} not found"}

        target = db.query(HardeningTarget).filter(HardeningTarget.id == session.target_id).first()
        if not target:
            session.status = HardeningSessionStatus.FAILED
            session.error_message = "Target not found"
            db.commit()
            return {"error": "Target not found"}

        session.status = HardeningSessionStatus.CONNECTING
        session.started_at = datetime.utcnow()
        db.commit()
        self.update_state(state="CONNECTING", meta={"progress": 5})

        creds = target.credentials or {}
        modules = session.modules_requested or None

        def _progress(module_name: str, pct: int) -> None:
            session.current_module = module_name
            session.progress = pct
            session.status = HardeningSessionStatus.AUDITING
            db.commit()
            self.update_state(state="AUDITING", meta={"progress": pct, "module": module_name})

        from app.hardening.engine import run_hardening_audit

        result = run_hardening_audit(
            host=target.host,
            port=target.port,
            username=target.username,
            password=creds.get("password"),
            key_path=creds.get("key_path"),
            os_type=target.os_type,
            modules=modules,
            progress_callback=_progress,
        )

        if result.get("error"):
            session.status = HardeningSessionStatus.FAILED
            session.error_message = result["error"]
            session.completed_at = datetime.utcnow()
            db.commit()
            return {"error": result["error"]}

        # Persist findings
        for f in result.get("all_findings", []):
            finding = HardeningFinding(
                session_id=session.id,
                check_id=f.get("check", "UNKNOWN"),
                check_name=f.get("check_name", f.get("check", "")),
                module=f.get("module", "unknown"),
                description=f.get("description", ""),
                severity=f.get("severity", "INFO"),
                found=str(f.get("found", "")),
                expected=str(f.get("expected", "")),
                remediation=f.get("remediation"),
                status="FAIL",
            )
            db.add(finding)

        session.status = HardeningSessionStatus.COMPLETED
        session.current_module = None
        session.progress = 100
        session.score = result["score"]
        session.grade = result["grade"]
        session.findings_summary = result["findings_summary"]
        session.total_findings = len(result["all_findings"])
        session.total_checks = result["total_checks"]
        session.passed_checks = result["passed_checks"]
        session.modules_completed = result["modules_completed"]
        session.completed_at = datetime.utcnow()
        if session.started_at:
            session.duration_seconds = (
                session.completed_at - session.started_at
            ).total_seconds()

        db.commit()

        logger.info(
            "Hardening session {} completed: score={} grade={} findings={}",
            session_id,
            result["score"],
            result["grade"],
            len(result["all_findings"]),
        )

        return {
            "session_id": session_id,
            "status": "completed",
            "score": result["score"],
            "grade": result["grade"],
            "total_findings": len(result["all_findings"]),
        }

    except Exception as exc:
        logger.error("Hardening session {} failed: {}", session_id, exc)
        try:
            session = db.query(HardeningSession).filter(HardeningSession.id == session_id).first()
            if session:
                session.status = HardeningSessionStatus.FAILED
                session.error_message = str(exc)
                session.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
        return {"error": str(exc)}
    finally:
        db.close()
