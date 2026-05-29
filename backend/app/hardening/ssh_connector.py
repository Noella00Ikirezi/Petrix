"""SSH connector for HCO hardening module — synchronous Paramiko-based."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


class SSHConnector:
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
        if not self._client:
            raise RuntimeError("Call connect() before execute_command()")
        _, stdout, stderr = self._client.exec_command(command, timeout=self.timeout)
        return (
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SSHConnector":
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()
