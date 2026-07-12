"""Source de vérité unique pour l'ensemble des paramètres de l'application.

Les valeurs sont lues depuis les variables d'environnement et un fichier `.env`
(via pydantic-settings). Le singleton ``settings`` au niveau du module est importé
dans toute la base de code afin que chaque sous-système partage le même objet de
configuration validé.
"""
import secrets as _secrets
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs validés, alimentés par les variables d'environnement.

    Tous les champs peuvent être surchargés via des variables d'env (insensibles
    à la casse) ou un fichier `.env`. Les valeurs sensibles par défaut (ex.
    ``secret_key``) sont générées aléatoirement au démarrage du processus — un
    déploiement en production **doit** les fixer explicitement.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Petrix"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Base de données
    database_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Sécurité
    # secret_key généré par processus si absent — les tokens deviennent invalides
    # au redémarrage ; à fixer impérativement en production.
    secret_key: str = _secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    # Stocké en chaîne CSV car les variables d'env ne supportent pas les listes
    # nativement.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit la chaîne CSV des origines CORS en liste pour le middleware FastAPI."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@petrix.local"
    smtp_from_name: str = "Petrix"
    smtp_tls: bool = False

    # Authentification étendue
    refresh_token_expire_days: int = 7
    mfa_token_expire_minutes: int = 5   # Fenêtre courte : l'OTP est à usage unique
    otp_length: int = 6
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30
    mfa_enabled: bool = True

    # Utilisateur admin (créé au premier démarrage)
    admin_email: str = "nikirezi@outlook.fr"
    admin_password: str = ""


@lru_cache
def get_settings() -> Settings:
    """Retourne le singleton des paramètres applicatifs.

    ``lru_cache`` garantit que le fichier `.env` n'est parsé qu'une seule fois
    par processus, rendant la fonction sûre à appeler depuis le code de niveau
    module.
    """
    return Settings()


settings = get_settings()
