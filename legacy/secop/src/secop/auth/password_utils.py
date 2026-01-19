"""Password hashing and verification utilities."""

import bcrypt
import secrets
import string
from typing import Tuple

from secop.config.settings import get_settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    settings = get_settings()
    salt = bcrypt.gensalt(rounds=settings.security.bcrypt_rounds)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_session_token() -> str:
    """
    Generate a secure random session token.

    Returns:
        64-character hex token
    """
    return secrets.token_hex(32)


def generate_password(length: int = 16) -> str:
    """
    Generate a random secure password.

    Args:
        length: Password length (minimum 12)

    Returns:
        Random password string
    """
    length = max(length, 12)

    # Ensure at least one of each type
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")

    # Fill remaining with random choices
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = "".join(secrets.choice(all_chars) for _ in range(length - 4))

    # Combine and shuffle
    password_chars = list(lowercase + uppercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def check_password_strength(password: str) -> Tuple[bool, list[str]]:
    """
    Check password strength against security requirements.

    Args:
        password: Password to check

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters")
    if len(password) > 128:
        issues.append("Password must be less than 128 characters")
    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one digit")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")

    # Check for common weak patterns
    weak_patterns = ["password", "123456", "qwerty", "admin", "letmein"]
    if any(pattern in password.lower() for pattern in weak_patterns):
        issues.append("Password contains common weak pattern")

    return len(issues) == 0, issues
