"""Security utilities - JWT, password hashing."""
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt
import bcrypt

from app.config import settings


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


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None
