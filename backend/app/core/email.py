"""Email sending via stdlib smtplib."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings


def send_email(to: str, subject: str, html: str, text: str = "") -> None:
    """Send an email via SMTP."""
    if not settings.smtp_host:
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to
    msg["Subject"] = subject

    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def send_otp_email(to: str, code: str, name: str = "") -> None:
    """Send OTP verification code email."""
    display_name = name or to.split("@")[0]
    subject = f"Petrix - Code de verification: {code}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h2 style="color: #0f172a; margin: 0;">Petrix</h2>
            <p style="color: #64748b; margin: 4px 0 0;">Security &amp; Compliance Platform</p>
        </div>
        <div style="background: #f8fafc; border-radius: 8px; padding: 24px; text-align: center;">
            <p style="color: #334155; margin: 0 0 16px;">Bonjour {display_name},</p>
            <p style="color: #334155; margin: 0 0 16px;">Votre code de verification :</p>
            <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #0f172a; background: white; border-radius: 8px; padding: 16px; margin: 16px 0;">
                {code}
            </div>
            <p style="color: #94a3b8; font-size: 13px; margin: 16px 0 0;">
                Ce code expire dans 5 minutes.<br>
                Si vous n'avez pas demande cette connexion, ignorez cet email.
            </p>
        </div>
    </div>
    """

    text = f"Petrix - Code de verification: {code}\n\nCe code expire dans 5 minutes."

    send_email(to, subject, html, text)
