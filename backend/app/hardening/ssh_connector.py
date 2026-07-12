"""Connecteur SSH synchrone basé sur Paramiko pour le moteur HCO.

Fournit une interface unifiée execute_command() utilisée par tous les modules
d'audit ; supporte l'authentification par clé privée ou par mot de passe.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


class SSHConnector:
    """Abstraction Paramiko pour les commandes distantes des modules d'audit.

    Attributes:
        host: Adresse IP ou nom DNS de la cible.
        port: Port SSH (défaut 22).
        username: Compte SSH utilisé pour la connexion.
        key_file: Chemin vers la clé privée (Path) ; prioritaire sur password.
        password: Mot de passe SSH si aucune clé n'est fournie.
        timeout: Délai d'expiration en secondes pour la connexion et les commandes.
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str = "",
        key_file: Optional[Path] = None,
        password: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.key_file = key_file
        self.password = password
        self.timeout = timeout
        self._client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        """Établit la connexion SSH vers la cible.

        Utilise la clé privée si ``key_file`` est défini, sinon le mot de passe.
        La politique AutoAddPolicy accepte automatiquement les clés hôtes inconnues
        (acceptable en contexte d'audit contrôlé, à ne pas utiliser en production
        avec des cibles non maîtrisées).

        Returns:
            True si la connexion est établie, False en cas d'échec.

        Raises:
            ValueError: Si ni clé privée ni mot de passe ne sont fournis.
        """
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs: dict = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "timeout": self.timeout,
        }
        if self.key_file:
            kwargs["key_filename"] = str(self.key_file)
        elif self.password:
            kwargs["password"] = self.password
        else:
            raise ValueError(f"No auth method provided for {self.host}")

        try:
            self._client.connect(**kwargs)
            logger.info("SSH connected to %s", self.host)
            return True
        except Exception as exc:
            logger.error("SSH connection failed to %s: %s", self.host, exc)
            return False

    def execute_command(self, command: str) -> Tuple[str, str]:
        """Exécute une commande shell sur la cible et retourne (stdout, stderr).

        Args:
            command: Commande shell à exécuter.

        Returns:
            Tuple (stdout, stderr) décodés en UTF-8 (erreurs remplacées).

        Raises:
            RuntimeError: Si ``connect()`` n'a pas été appelé au préalable.
        """
        if not self._client:
            raise RuntimeError("Appeler connect() avant execute_command()")
        _, stdout, stderr = self._client.exec_command(command, timeout=self.timeout)
        return (
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )

    def disconnect(self) -> None:
        """Ferme la connexion SSH et libère les ressources Paramiko."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SSHConnector":
        """Ouvre la connexion SSH lors d'une utilisation en context manager."""
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        """Ferme la connexion SSH en sortie de context manager."""
        self.disconnect()
