"""Couche d'accès Redis pour l'état transitoire de l'authentification.

Regroupe les opérations Redis qui ne doivent pas polluer la base relationnelle :
OTP à usage unique, liste noire de tokens JWT, suivi des refresh tokens et
limitation de débit. Chaque famille de clés est isolée par un préfixe dédié
pour éviter les collisions dans une instance Redis partagée.
"""
import redis
from app.config import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)

# Préfixes de clés — permettent une inspection/suppression ciblée en production
OTP_PREFIX = "otp:"
TOKEN_BLACKLIST_PREFIX = "bl:"
REFRESH_TOKEN_PREFIX = "rt:"
RATE_LIMIT_PREFIX = "rl:"


def store_otp(user_id: str, code: str, ttl_seconds: int = 300) -> None:
    """Stocke un OTP en Redis avec expiration automatique.

    Le TTL par défaut de 300 s correspond à la fenêtre de validité configurée
    dans ``settings.mfa_token_expire_minutes``.
    """
    _redis.setex(f"{OTP_PREFIX}{user_id}", ttl_seconds, code)


def verify_otp(user_id: str, code: str) -> bool:
    """Vérifie un OTP et le supprime immédiatement s'il est valide.

    La suppression atomique après validation garantit le caractère à usage unique
    de l'OTP : une seconde soumission identique sera rejetée même dans la fenêtre TTL.
    """
    key = f"{OTP_PREFIX}{user_id}"
    stored = _redis.get(key)
    if stored and stored == code:
        _redis.delete(key)
        return True
    return False


def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Ajoute le JTI d'un token à la liste noire pour la durée de sa validité restante.

    Le TTL doit correspondre au temps restant avant l'expiration du token afin
    que la clé Redis soit supprimée automatiquement sans accumulation indéfinie.
    """
    _redis.setex(f"{TOKEN_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    """Retourne True si le JTI figure dans la liste noire (token révoqué)."""
    return _redis.exists(f"{TOKEN_BLACKLIST_PREFIX}{jti}") > 0


def store_refresh_token(jti: str, user_id: str, ttl_seconds: int) -> None:
    """Enregistre un refresh token en liant son JTI à l'identifiant utilisateur.

    La valeur stockée (``user_id``) permet de retrouver l'utilisateur lors du
    renouvellement de token sans consulter la base de données.
    """
    _redis.setex(f"{REFRESH_TOKEN_PREFIX}{jti}", ttl_seconds, user_id)


def revoke_refresh_token(jti: str) -> None:
    """Supprime un refresh token du registre Redis (déconnexion / rotation)."""
    _redis.delete(f"{REFRESH_TOKEN_PREFIX}{jti}")


def is_refresh_token_valid(jti: str) -> bool:
    """Retourne True si le JTI correspond à un refresh token encore actif."""
    return _redis.exists(f"{REFRESH_TOKEN_PREFIX}{jti}") > 0


def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool:
    """Vérifie si la requête est autorisée selon la fenêtre glissante de limitation.

    Args:
        key: Clé discriminante (ex. ``"login:192.168.1.1"``).
        max_requests: Nombre maximum de requêtes autorisées sur la fenêtre.
        window_seconds: Durée de la fenêtre de comptage en secondes.

    Returns:
        True si la requête est autorisée, False si le quota est dépassé.

    Le pipeline Redis (INCR + EXPIRE) est exécuté en un seul aller-retour réseau,
    ce qui réduit la fenêtre de compétition entre processus concurrents sans
    nécessiter de verrou explicite.
    """
    full_key = f"{RATE_LIMIT_PREFIX}{key}"
    current = _redis.get(full_key)
    if current and int(current) >= max_requests:
        return False
    pipe = _redis.pipeline()
    pipe.incr(full_key)
    pipe.expire(full_key, window_seconds)
    pipe.execute()
    return True
