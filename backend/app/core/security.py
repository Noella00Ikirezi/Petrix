"""Security utilities - JWT with token types, password hashing."""
import uuid
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from jose import JWTError, jwt
import bcrypt

from app.config import settings
from app.core.redis import is_token_blacklisted

TokenType = Literal["access", "refresh", "mfa_pending"]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8')[:72],
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(
        password.encode('utf-8')[:72],
        bcrypt.gensalt()
    ).decode('utf-8')


def create_token(
    data: dict,
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT token with type and JTI."""
    to_encode = data.copy()

    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
        elif token_type == "refresh":
            expires_delta = timedelta(days=settings.refresh_token_expire_days)
        elif token_type == "mfa_pending":
            expires_delta = timedelta(minutes=settings.mfa_token_expire_minutes)

    expire = datetime.utcnow() + expires_delta
    jti = str(uuid.uuid4())

    to_encode.update({
        "exp": expire,
        "type": token_type,
        "jti": jti,
    })

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(
    token: str,
    expected_type: Optional[TokenType] = None,
) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT token, checking type and blacklist."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    # Check token type if specified
    if expected_type and payload.get("type") != expected_type:
        return None

    # Check blacklist
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        return None

    return payload


# Backward-compatible alias
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token (backward-compatible alias)."""
    return create_token(data, "access", expires_delta)
