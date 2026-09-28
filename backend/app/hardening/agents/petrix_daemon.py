#!/usr/bin/env python3
"""Agent démon Petrix — surveillance continue d'un host homelab (Linux ou Proxmox VE).

Installé et lancé via le service systemd généré par GET /agent-script/install
(voir hardening.py). Contrairement aux scripts petrix_agent_*.sh (exécution
ponctuelle manuelle), ce démon tourne en continu et maintient une connexion
WebSocket SORTANTE vers Petrix — jamais l'inverse, aucun accès entrant (SSH ou
autre) n'est requis sur la machine surveillée, cohérent avec la suppression des
audits SSH orchestrés côté serveur.

Deux tâches concurrentes une fois connecté :
  - heartbeat_loop  : signale la présence en ligne toutes les HEARTBEAT_SECONDS
  - audit_loop      : relance le script d'audit local toutes les INTERVAL secondes
                       et pousse chaque rapport XML généré

Variables d'environnement requises (fournies par /etc/petrix-agent.env, écrit par
le script d'installation) : PETRIX_URL, TARGET_ID, AGENT_TOKEN, AUDIT_SCRIPT.
Optionnelle : INTERVAL (secondes, défaut 300).

Dépendance externe unique : le paquet ``websockets`` (installé par le script
d'installation via pip).
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time

import websockets

PETRIX_URL = os.environ["PETRIX_URL"].rstrip("/")
TARGET_ID = os.environ["TARGET_ID"]
AGENT_TOKEN = os.environ["AGENT_TOKEN"]
AUDIT_SCRIPT = os.environ["AUDIT_SCRIPT"]
INTERVAL = int(os.environ.get("INTERVAL", "300"))

HEARTBEAT_SECONDS = 30
MIN_BACKOFF = 5
MAX_BACKOFF = 60

WS_URL = (
    PETRIX_URL.replace("https://", "wss://").replace("http://", "ws://")
    + f"/api/v1/hardening/ws/agent?target_id={TARGET_ID}&token={AGENT_TOKEN}"
)


def _log(msg: str, *, err: bool = False) -> None:
    """Journalise un message horodaté sur stdout/stderr (capturé par journald via systemd)."""
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, file=sys.stderr if err else sys.stdout, flush=True)


def run_audit() -> str:
    """Exécute le script d'audit local (subprocess bloquant) et retourne le XML généré.

    Appelé via ``asyncio.to_thread`` depuis la boucle asyncio pour ne pas bloquer le
    heartbeat pendant les ~10-30s que peut prendre un audit complet.
    """
    fd, outfile = tempfile.mkstemp(suffix=".xml", prefix="petrix_audit_")
    os.close(fd)
    try:
        env = {**os.environ, "OUTFILE": outfile}
        subprocess.run(
            ["bash", AUDIT_SCRIPT], env=env, check=True, timeout=600,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        with open(outfile, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.unlink(outfile)
        except OSError:
            pass


async def audit_loop(ws) -> None:
    """Relance l'audit toutes les INTERVAL secondes et pousse chaque rapport XML."""
    while True:
        try:
            xml = await asyncio.to_thread(run_audit)
            await ws.send(json.dumps({"type": "report", "xml": xml}))
            _log(f"Rapport envoyé ({len(xml)} octets)")
        except Exception as exc:
            _log(f"Erreur pendant l'audit : {exc}", err=True)
        await asyncio.sleep(INTERVAL)


async def heartbeat_loop(ws) -> None:
    """Envoie un heartbeat régulier — Petrix marque la cible hors ligne après 2 cycles manqués."""
    while True:
        await ws.send(json.dumps({"type": "heartbeat"}))
        await asyncio.sleep(HEARTBEAT_SECONDS)


async def run_once() -> None:
    """Ouvre une connexion WebSocket et fait tourner heartbeat + audit jusqu'à déconnexion."""
    async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=20) as ws:
        _log("Connecté à Petrix — surveillance active")
        await asyncio.gather(heartbeat_loop(ws), audit_loop(ws))


async def main() -> None:
    """Boucle de connexion avec reconnexion à backoff exponentiel (5s → 60s max).

    Le backoff est réinitialisé après toute connexion ayant tenu plus de 30s, pour
    ne pénaliser que les échecs de reconnexion répétés (serveur injoignable), pas
    les coupures réseau occasionnelles d'une connexion par ailleurs stable.
    """
    backoff = MIN_BACKOFF
    while True:
        connected_at = time.monotonic()
        try:
            await run_once()
        except Exception as exc:
            _log(f"Connexion perdue : {exc}", err=True)
        duration = time.monotonic() - connected_at
        backoff = MIN_BACKOFF if duration > 30 else min(backoff * 2, MAX_BACKOFF)
        _log(f"Reconnexion dans {backoff}s...")
        await asyncio.sleep(backoff)


if __name__ == "__main__":
    asyncio.run(main())
