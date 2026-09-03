"""Endpoints d'authentification Petrix — flux MFA à deux étapes via OTP par e-mail.

Le flux de connexion se déroule en deux appels : POST /login (vérification des
identifiants + envoi OTP via Celery) puis POST /verify-otp (validation de l'OTP et
émission des tokens JWT access + refresh stockés dans Redis).
"""
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    create_token,
    decode_token,
    verify_password,
    get_password_hash,
)
from app.core.redis import (
    store_otp,
    verify_otp,
    blacklist_token,
    store_refresh_token,
    revoke_refresh_token,
    is_refresh_token_valid,
    check_rate_limit,
)
from app.core.audit import log_audit_event
from app.core.permissions import UserRole
from app.infrastructure.database import get_db
from app.infrastructure.database.models import User
from app.api.v1.deps import get_current_active_user
from app.workers.email_tasks import send_otp_email_task

router = APIRouter()


# Schémas Pydantic — requêtes et réponses de l'API d'authentification

class LoginRequest(BaseModel):
    """Corps de la requête POST /login : identifiants de l'utilisateur."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Réponse à POST /login : token MFA temporaire transmis à POST /verify-otp."""

    mfa_token: str
    message: str = "OTP sent to your email"


class VerifyOtpRequest(BaseModel):
    """Corps de la requête POST /verify-otp : token MFA + code OTP reçu par e-mail."""

    mfa_token: str
    code: str


class AuthTokens(BaseModel):
    """Paire de tokens JWT retournée après authentification complète.

    Attributs :
        access_token: JWT de courte durée à inclure dans l'en-tête ``Authorization: Bearer``.
        refresh_token: JWT longue durée stocké côté client pour renouveler l'access token.
        must_change_password: Indique que l'utilisateur doit changer son mot de passe immédiatement.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    """Corps de la requête POST /refresh : refresh token à rotation."""

    refresh_token: str


class UserResponse(BaseModel):
    """Représentation publique d'un utilisateur retournée par les endpoints auth."""

    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    """Corps de la requête POST /register : création d'un compte avec rôle VIEWER par défaut."""

    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


def _generate_otp() -> str:
    """Génère un code OTP numérique aléatoire de longueur ``settings.otp_length``."""
    digits = settings.otp_length
    return "".join(str(secrets.randbelow(10)) for _ in range(digits))


def _get_client_ip(request: Request) -> str:
    """Extrait l'adresse IP réelle du client en tenant compte du proxy inverse (X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Endpoints
@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Étape 1 du flux MFA : vérifie les identifiants et envoie l'OTP par e-mail.

    Args:
        data: E-mail et mot de passe de l'utilisateur.
        request: Objet requête FastAPI (extraction IP pour le rate-limit).
        db: Session de base de données synchrone.

    Returns:
        LoginResponse contenant le token MFA temporaire à passer à /verify-otp.

    Raises:
        HTTPException 429: Trop de tentatives depuis cette IP (rate-limit).
        HTTPException 401: Identifiants incorrects.
        HTTPException 403: Compte désactivé.
        HTTPException 423: Compte temporairement verrouillé.
    """
    ip = _get_client_ip(request)

    # Limite de débit : 10 tentatives de connexion par minute par adresse IP
    if not check_rate_limit(f"login:{ip}", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            # Verrouillage temporaire du compte après dépassement du seuil d'échecs
            if user.failed_login_attempts >= settings.max_failed_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.account_lockout_minutes
                )
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Try again in {remaining} minutes.",
        )

    # Si MFA désactivé → retourner les tokens directement
    if not settings.mfa_enabled:
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.commit()
        access_token = create_token(data={"sub": str(user.id)}, token_type="access")
        refresh_token = create_token(data={"sub": str(user.id)}, token_type="refresh")
        refresh_payload = decode_token(refresh_token)
        if refresh_payload and refresh_payload.get("jti"):
            store_refresh_token(
                refresh_payload["jti"],
                str(user.id),
                settings.refresh_token_expire_days * 86400,
            )
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "mfa_bypass": True,
        })

    # Génération du code OTP et stockage temporaire dans Redis (TTL = mfa_token_expire_minutes)
    otp_code = _generate_otp()
    otp_ttl = settings.mfa_token_expire_minutes * 60
    store_otp(str(user.id), otp_code, otp_ttl)

    user_name = user.first_name or user.email.split("@")[0]
    send_otp_email_task.delay(user.email, otp_code, user_name)

    mfa_token = create_token(
        data={"sub": str(user.id)},
        token_type="mfa_pending",
    )

    return LoginResponse(mfa_token=mfa_token)


@router.post("/verify-otp", response_model=AuthTokens)
async def verify_otp_endpoint(
    data: VerifyOtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Étape 2 du flux MFA : valide l'OTP et retourne la paire de tokens JWT.

    Args:
        data: Token MFA issu de /login et code OTP reçu par e-mail.
        request: Objet requête FastAPI (extraction IP/UA pour l'audit log).
        db: Session de base de données synchrone.

    Returns:
        AuthTokens contenant access_token, refresh_token et le flag must_change_password.

    Raises:
        HTTPException 401: Token MFA invalide ou expiré, ou code OTP incorrect.
    """
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    if not check_rate_limit(f"verify-otp:{ip}", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )

    payload = decode_token(data.mfa_token, expected_type="mfa_pending")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA token",
        )

    if not verify_otp(user_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP code",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Réinitialisation du compteur d'échecs et mise à jour de la date de dernière connexion
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_token(data={"sub": str(user.id)}, token_type="access")
    refresh_token = create_token(data={"sub": str(user.id)}, token_type="refresh")

    # Enregistrement du jti du refresh token dans Redis pour permettre la révocation ultérieure
    refresh_payload = decode_token(refresh_token)
    if refresh_payload and refresh_payload.get("jti"):
        store_refresh_token(
            refresh_payload["jti"],
            str(user.id),
            settings.refresh_token_expire_days * 86400,
        )

    log_audit_event(
        db=db,
        action="login",
        resource_type="auth",
        user_id=user.id,
        details={"method": "email_otp"},
        ip_address=ip,
        user_agent=ua[:255] if ua else None,
    )

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=user.must_change_password,
    )


@router.post("/refresh", response_model=AuthTokens)
async def refresh_tokens(
    data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Renouvelle l'access token via le refresh token (rotation : l'ancien est révoqué).

    Args:
        data: Refresh token JWT valide.
        request: Objet requête FastAPI (non utilisé directement, requis par signature).
        db: Session de base de données synchrone.

    Returns:
        AuthTokens avec un nouvel access_token et un nouveau refresh_token.

    Raises:
        HTTPException 401: Token invalide, expiré ou déjà révoqué dans Redis.
    """
    payload = decode_token(data.refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    jti = payload.get("jti")
    if not jti or not is_refresh_token_valid(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Révocation de l'ancien refresh token (politique de rotation à usage unique)
    revoke_refresh_token(jti)

    new_access = create_token(data={"sub": str(user.id)}, token_type="access")
    new_refresh = create_token(data={"sub": str(user.id)}, token_type="refresh")

    new_payload = decode_token(new_refresh)
    if new_payload and new_payload.get("jti"):
        store_refresh_token(
            new_payload["jti"],
            str(user.id),
            settings.refresh_token_expire_days * 86400,
        )

    return AuthTokens(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Déconnecte l'utilisateur : inscrit l'access token sur liste noire Redis et révoque le refresh token."""
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    # Inscription du jti de l'access token courant sur liste noire Redis pour invalider immédiatement la session
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            jti = payload.get("jti")
            if jti:
                exp = payload.get("exp", 0)
                ttl = max(int(exp - datetime.utcnow().timestamp()), 0)
                blacklist_token(jti, ttl + 60)

    log_audit_event(
        db=db,
        action="logout",
        resource_type="auth",
        user_id=current_user.id,
        ip_address=ip,
        user_agent=ua[:255] if ua else None,
    )

    return {"message": "Logged out successfully"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Crée un nouveau compte utilisateur avec le rôle VIEWER par défaut."""
    ip = _get_client_ip(request)
    if not check_rate_limit(f"register:{ip}", 5, 300):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.VIEWER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        is_active=user.is_active,
    )


@router.post("/change-password")
async def change_password(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Modifie le mot de passe de l'utilisateur connecté.

    Si ``must_change_password`` est vrai (première connexion), l'ancien mot de passe
    n'est pas vérifié afin de permettre la réinitialisation forcée.
    """
    new_password = data.get("new_password", "")
    current_password = data.get("current_password", "")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 8 caractères")

    # Vérifier l'ancien mot de passe sauf lors du changement forcé (première connexion)
    if not current_user.must_change_password:
        if not current_password:
            raise HTTPException(status_code=400, detail="Le mot de passe actuel est requis")
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    current_user.password_hash = get_password_hash(new_password)
    current_user.must_change_password = False
    db.commit()
    return {"message": "Mot de passe mis à jour"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Retourne le profil de l'utilisateur actuellement authentifié."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


# ── Mot de passe oublié ───────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    reset_token: str
    message: str = "Si cet email existe, un code a été envoyé"


class ResetPasswordRequest(BaseModel):
    reset_token: str
    code: str
    new_password: str


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Envoie un OTP de réinitialisation si l'email existe en base.

    Retourne toujours la même réponse pour éviter l'énumération d'emails.
    """
    ip = _get_client_ip(request)
    if not check_rate_limit(f"forgot:{ip}", 5, 300):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Trop de tentatives. Réessayez dans 5 minutes.")

    user = db.query(User).filter(User.email == data.email).first()

    # Générer un reset_token systématiquement pour éviter le timing attack
    reset_token = create_token(
        data={"sub": str(user.id) if user else "unknown", "purpose": "password_reset"},
        token_type="mfa_pending",
    )

    if user and user.is_active:
        otp_code = _generate_otp()
        store_otp(f"reset:{str(user.id)}", otp_code, settings.mfa_token_expire_minutes * 60)
        user_name = user.first_name or user.email.split("@")[0]
        send_otp_email_task.delay(user.email, otp_code, user_name)

    return ForgotPasswordResponse(reset_token=reset_token)


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Valide le code OTP et réinitialise le mot de passe."""
    ip = _get_client_ip(request)
    if not check_rate_limit(f"reset-password:{ip}", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )

    payload = decode_token(data.reset_token, expected_type="mfa_pending")
    if not payload or payload.get("purpose") != "password_reset":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")

    user_id = payload.get("sub")
    if not user_id or user_id == "unknown":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

    if not verify_otp(f"reset:{user_id}", data.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Code invalide ou expiré")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit faire au moins 8 caractères")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    user.password_hash = get_password_hash(data.new_password)
    user.must_change_password = False
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}
