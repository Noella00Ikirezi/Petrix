"""Tâches Celery pour l'envoi d'e-mails transactionnels Petrix.

Délègue les appels bloquants SMTP à Celery afin de ne pas pénaliser
les endpoints API : OTP d'authentification et invitation de nouvel utilisateur.
"""
from app.workers.celery_app import celery_app
from app.core.email import send_otp_email, send_invitation_email


@celery_app.task(name="send_otp_email")
def send_otp_email_task(to: str, code: str, name: str = "") -> dict:
    """Envoie un e-mail OTP de manière asynchrone via Celery.

    Args:
        to: Adresse e-mail du destinataire.
        code: Code OTP à inclure dans le message.
        name: Prénom ou nom de l'utilisateur (optionnel, pour la personnalisation).

    Returns:
        dict ``{"status": "sent", "to": to}``.
    """
    send_otp_email(to, code, name)
    return {"status": "sent", "to": to}


@celery_app.task(name="send_invitation_email")
def send_invitation_email_task(to: str, name: str, temp_password: str, role: str, login_url: str) -> dict:
    """Envoie un e-mail d'invitation avec mot de passe temporaire via Celery.

    Args:
        to: Adresse e-mail du destinataire.
        name: Nom affiché dans l'e-mail.
        temp_password: Mot de passe temporaire généré pour la première connexion.
        role: Rôle attribué à l'utilisateur invité (ex. ``"admin"``, ``"user"``).
        login_url: URL de connexion à inclure dans l'e-mail.

    Returns:
        dict ``{"status": "sent", "to": to}``.
    """
    send_invitation_email(to, name, temp_password, role, login_url)
    return {"status": "sent", "to": to}
