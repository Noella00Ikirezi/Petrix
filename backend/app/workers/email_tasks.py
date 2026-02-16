"""Celery tasks for email sending."""
from app.workers.celery_app import celery_app
from app.core.email import send_otp_email


@celery_app.task(name="send_otp_email")
def send_otp_email_task(to: str, code: str, name: str = "") -> dict:
    """Send OTP email asynchronously via Celery."""
    send_otp_email(to, code, name)
    return {"status": "sent", "to": to}
