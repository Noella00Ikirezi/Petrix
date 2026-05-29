"""Celery tasks for HCO Hardening module."""
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
    return SessionLocal()


@celery_app.task(bind=True, name="hardening.run_session")
def run_hardening_session(self, session_id: str) -> dict:
    """
    Run a full HCO hardening audit on a target via SSH.

    Phases:
    1. Load session + target from DB
    2. CONNECTING: establish SSH
    3. AUDITING: run each requested module
    4. Persist HardeningFinding records
    5. COMPLETED: update session with score/grade
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
            "Hardening session %s completed: score=%s grade=%s findings=%s",
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
        logger.error("Hardening session %s failed: %s", session_id, exc)
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
