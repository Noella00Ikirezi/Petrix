"""Redis helpers for OTP, token blacklist, refresh tokens, and rate limiting."""
import redis
from app.config import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)

# OTP
OTP_PREFIX = "otp:"
TOKEN_BLACKLIST_PREFIX = "bl:"
REFRESH_TOKEN_PREFIX = "rt:"
RATE_LIMIT_PREFIX = "rl:"


def store_otp(user_id: str, code: str, ttl_seconds: int = 300) -> None:
    _redis.setex(f"{OTP_PREFIX}{user_id}", ttl_seconds, code)


def verify_otp(user_id: str, code: str) -> bool:
    key = f"{OTP_PREFIX}{user_id}"
    stored = _redis.get(key)
    if stored and stored == code:
        _redis.delete(key)
        return True
    return False


# Token blacklist (for logout)
def blacklist_token(jti: str, ttl_seconds: int) -> None:
    _redis.setex(f"{TOKEN_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    return _redis.exists(f"{TOKEN_BLACKLIST_PREFIX}{jti}") > 0


# Refresh tokens
def store_refresh_token(jti: str, user_id: str, ttl_seconds: int) -> None:
    _redis.setex(f"{REFRESH_TOKEN_PREFIX}{jti}", ttl_seconds, user_id)


def revoke_refresh_token(jti: str) -> None:
    _redis.delete(f"{REFRESH_TOKEN_PREFIX}{jti}")


def is_refresh_token_valid(jti: str) -> bool:
    return _redis.exists(f"{REFRESH_TOKEN_PREFIX}{jti}") > 0


# Rate limiting
def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool:
    """Return True if request is allowed, False if rate limited."""
    full_key = f"{RATE_LIMIT_PREFIX}{key}"
    current = _redis.get(full_key)
    if current and int(current) >= max_requests:
        return False
    pipe = _redis.pipeline()
    pipe.incr(full_key)
    pipe.expire(full_key, window_seconds)
    pipe.execute()
    return True
