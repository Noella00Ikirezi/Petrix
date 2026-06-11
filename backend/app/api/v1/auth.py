"""Authentication endpoints with MFA via email OTP."""
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


# Schemas
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    mfa_token: str
    message: str = "OTP sent to your email"


class VerifyOtpRequest(BaseModel):
    mfa_token: str
    code: str


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


def _generate_otp() -> str:
    """Generate a random OTP code."""
    digits = settings.otp_length
    return "".join(str(secrets.randbelow(10)) for _ in range(digits))


def _get_client_ip(request: Request) -> str:
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
    """Step 1: Verify credentials and send OTP via email."""
    ip = _get_client_ip(request)

    # Rate limit: 10 attempts per minute per IP
    if not check_rate_limit(f"login:{ip}", 10, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            # Lock account after max attempts
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

    # Check lockout
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

    # Generate and store OTP
    otp_code = _generate_otp()
    otp_ttl = settings.mfa_token_expire_minutes * 60
    store_otp(str(user.id), otp_code, otp_ttl)

    # Send OTP via Celery
    user_name = user.first_name or user.email.split("@")[0]
    send_otp_email_task.delay(user.email, otp_code, user_name)

    # Create MFA pending token
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
    """Step 2: Verify OTP and return access + refresh tokens."""
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    # Decode MFA token
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

    # Verify OTP
    if not verify_otp(user_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP code",
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Reset failed attempts, update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token = create_token(data={"sub": str(user.id)}, token_type="access")
    refresh_token = create_token(data={"sub": str(user.id)}, token_type="refresh")

    # Store refresh token in Redis
    refresh_payload = decode_token(refresh_token)
    if refresh_payload and refresh_payload.get("jti"):
        store_refresh_token(
            refresh_payload["jti"],
            str(user.id),
            settings.refresh_token_expire_days * 86400,
        )

    # Audit log
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
    """Refresh access token using refresh token."""
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

    # Revoke old refresh token
    revoke_refresh_token(jti)

    # Create new tokens
    new_access = create_token(data={"sub": str(user.id)}, token_type="access")
    new_refresh = create_token(data={"sub": str(user.id)}, token_type="refresh")

    # Store new refresh token
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
    """Logout: blacklist access token and revoke refresh token."""
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    # Get token from header and blacklist it
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

    # Audit log
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
    db: Session = Depends(get_db),
):
    """Register a new user (creates VIEWER by default)."""
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
    """Change password. Si must_change_password=True, current_password n'est pas requis."""
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
    """Get current authenticated user."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )
