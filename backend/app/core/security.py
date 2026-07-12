"""Cycle de vie des tokens JWT et hachage bcrypt des mots de passe.

Centralise toutes les opérations cryptographiques afin que le reste de la base
de code ne manipule jamais directement les clés ou les noms d'algorithmes. Trois
types de tokens sont supportés : ``access`` (courte durée), ``refresh`` (longue
durée) et ``mfa_pending`` (état intermédiaire pendant la vérification OTP/TOTP).
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from jose import JWTError, jwt
import bcrypt

from app.config import settings
from app.core.redis import is_token_blacklisted

# Union discriminée servant de contrainte auto-documentée sur les paramètres token_type.
TokenType = Literal["access", "refresh", "mfa_pending"]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Retourne True si ``plain_password`` correspond au hash bcrypt stocké.

    La troncature à ``[:72]`` est intentionnelle : bcrypt tronque silencieusement
    l'entrée au-delà de 72 octets, ce qui ferait comparer comme égaux des mots de
    passe ne différant qu'après l'octet 72.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8')[:72],
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Retourne un hash bcrypt de ``password``, tronqué à 72 octets avant hachage.

    Voir ``verify_password`` pour le détail de la limite à 72 octets.
    """
    return bcrypt.hashpw(
        password.encode('utf-8')[:72],
        bcrypt.gensalt()
    ).decode('utf-8')


def create_token(
    data: dict,
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Encode un JWT avec une claim de type et un identifiant unique (JTI).

    Args:
        data: Claims arbitraires à intégrer (ex. ``{"sub": user_id}``).
        token_type: L'un des types ``"access"``, ``"refresh"`` ou ``"mfa_pending"``.
            Détermine l'expiration par défaut si ``expires_delta`` est absent.
        expires_delta: Surcharge la durée de vie par défaut pour ce type de token.

    Returns:
        Chaîne JWT signée.

    Le ``jti`` (JWT ID) permet une révocation ciblée via la liste noire Redis
    sans invalider la clé de signature.
    """
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
    """Décode un JWT et effectue deux validations supplémentaires au-delà de la signature.

    Args:
        token: Chaîne JWT brute issue de l'en-tête Authorization.
        expected_type: Si fourni, la claim ``type`` du token doit correspondre
            exactement. Empêche la réutilisation d'un access token comme refresh token.

    Returns:
        Dictionnaire du payload décodé, ou ``None`` si une étape de validation échoue.

    Ordre de validation : (1) signature + expiration via jose, (2) concordance du
    type de token, (3) consultation de la liste noire Redis via le JTI. Retourner
    ``None`` sur tous les chemins d'échec évite de révéler quelle vérification a échoué.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    if expected_type and payload.get("type") != expected_type:
        return None

    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        return None

    return payload


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Crée un token JWT de type accès.

    Alias rétrocompatible vers ``create_token(data, "access", expires_delta)``,
    conservé pour les appelants antérieurs au système multi-types.
    """
    return create_token(data, "access", expires_delta)
