"""Moteur principal HCO (Hardening Configuration Operator).

Orchestre l'exécution des modules d'audit sur une cible distante via SSH,
aggrège les findings, calcule le score ANSSI-BP-028 (0–100) et la note A–F.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from app.hardening.ssh_connector import SSHConnector
from app.hardening.modules.linux import (
    audit_ssh,
    audit_users,
    audit_kernel,
    audit_firewall,
    audit_services,
    audit_filesystem,
    audit_network,
    audit_packages,
    audit_pam,
    audit_logging,
)
from app.hardening.modules.macos import intel as macos_intel_mods, silicon as macos_silicon_mods

logger = logging.getLogger(__name__)

LINUX_MODULES: dict = {
    "ssh":        audit_ssh,
    "users":      audit_users,
    "kernel":     audit_kernel,
    "firewall":   audit_firewall,
    "services":   audit_services,
    "filesystem": audit_filesystem,
    "network":    audit_network,
    "packages":   audit_packages,
    "pam":        audit_pam,
    "logging":    audit_logging,
}

MACOS_INTEL_MODULES: dict = {
    "ssh":        macos_intel_mods.audit_ssh,
    "users":      macos_intel_mods.audit_users,
    "firewall":   macos_intel_mods.audit_firewall,
    "services":   macos_intel_mods.audit_services,
    "filesystem": macos_intel_mods.audit_filesystem,
}

MACOS_SILICON_MODULES: dict = {
    "ssh":        macos_silicon_mods.audit_ssh,
    "users":      macos_silicon_mods.audit_users,
    "firewall":   macos_silicon_mods.audit_firewall,
    "services":   macos_silicon_mods.audit_services,
    "filesystem": macos_silicon_mods.audit_filesystem,
}

OS_MODULE_MAP: dict = {
    "linux":         LINUX_MODULES,
    "macos_intel":   MACOS_INTEL_MODULES,
    "macos_silicon": MACOS_SILICON_MODULES,
}

SUPPORTED_OS_TYPES = list(OS_MODULE_MAP.keys())

DEFAULT_MODULES_BY_OS: dict = {
    "linux":         list(LINUX_MODULES.keys()),
    "macos_intel":   list(MACOS_INTEL_MODULES.keys()),
    "macos_silicon": list(MACOS_SILICON_MODULES.keys()),
}

DEFAULT_RULES = {
    "root_login": "no",
    "password_auth": "no",
    "permit_empty_passwords": "no",
    "x11_forwarding": "no",
    "max_auth_tries": 4,
}

_SEVERITY_WEIGHTS = {"CRITICAL": 15, "HIGH": 8, "MEDIUM": 3, "LOW": 1, "INFO": 0}
_GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]


def _compute_score(findings: list[dict]) -> tuple[float, str]:
    """Calcule le score HCO (0–100) et la note A–F à partir des findings.

    Chaque finding réduit le score selon son niveau de sévérité :
    CRITICAL –15, HIGH –8, MEDIUM –3, LOW –1, INFO 0.
    Le score est borné à [0, 100].

    Args:
        findings: liste de dicts de findings, chacun contenant au moins
                  la clé ``severity`` (CRITICAL/HIGH/MEDIUM/LOW/INFO).

    Returns:
        Tuple (score, grade) où score est un float arrondi à 1 décimale
        et grade est une lettre parmi A, B, C, D, F.
    """
    counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "INFO").upper()
        counts[sev] = counts.get(sev, 0) + 1
    deduction = sum(_SEVERITY_WEIGHTS.get(s, 0) * n for s, n in counts.items())
    score = max(0.0, min(100.0, 100.0 - deduction))
    grade = next(g for threshold, g in _GRADE_THRESHOLDS if score >= threshold)
    return round(score, 1), grade


def run_hardening_audit(
    host: str,
    port: int = 22,
    username: str = "root",
    password: Optional[str] = None,
    key_path: Optional[str] = None,
    os_type: str = "linux",
    modules: Optional[list[str]] = None,
    rules: Optional[dict] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> dict:
    """Lance un audit HCO complet via SSH et retourne les résultats agrégés.

    Se connecte à la cible, exécute chaque module d'audit demandé dans l'ordre,
    puis calcule le score global et la note A–F selon la grille de sévérité HCO.
    La connexion SSH est fermée dans un bloc ``finally`` même en cas d'erreur.

    Args:
        host: Adresse IP ou nom DNS de la cible.
        port: Port SSH (défaut : 22).
        username: Compte SSH à utiliser (défaut : root).
        password: Mot de passe SSH (mutuellement exclusif avec key_path).
        key_path: Chemin vers la clé privée SSH (prend la priorité sur password).
        os_type: Type de système cible — ``"linux"``, ``"macos_intel"``
                 ou ``"macos_silicon"``.
        modules: Liste de noms de modules à exécuter ; ``None`` = tous les modules
                 disponibles pour l'os_type.
        rules: Surcharge des règles par défaut (ex. ``{"max_auth_tries": 3}``).
        progress_callback: Callable optionnel ``(module_name, percent)`` appelé
                           après chaque module pour signaler l'avancement.

    Returns:
        dict avec les clés :
            host (str), os_type (str), modules_completed (list[str]),
            all_findings (list[dict]), all_passed (list[dict]),
            score (float), grade (str), findings_summary (dict),
            total_checks (int), passed_checks (int),
            module_results (dict), error (str | None).
        En cas d'erreur précoce (os_type inconnu, échec SSH), seul ``error``
        est renseigné.
    """
    available = OS_MODULE_MAP.get(os_type)
    if available is None:
        return {
            "error": f"OS type '{os_type}' not supported. Supported: {SUPPORTED_OS_TYPES}"
        }

    default_mods = DEFAULT_MODULES_BY_OS[os_type]
    active_modules = [m for m in (modules or default_mods) if m in available]
    effective_rules = {**DEFAULT_RULES, **(rules or {})}

    connector = SSHConnector(
        host=host,
        port=port,
        username=username,
        password=password,
        key_file=Path(key_path) if key_path else None,
    )

    if not connector.connect():
        return {"error": f"SSH connection to {host}:{port} failed — check host, port, credentials."}

    all_findings: list[dict] = []
    all_passed: list[dict] = []
    module_results: dict = {}
    completed: list[str] = []

    try:
        for i, module_name in enumerate(active_modules):
            if progress_callback:
                progress_callback(module_name, int((i / len(active_modules)) * 90) + 5)

            audit_mod = available[module_name]
            try:
                result = audit_mod.run_audit(connector, effective_rules)
            except Exception as exc:
                logger.error("Module %s failed on %s: %s", module_name, host, exc)
                result = {
                    "findings": [],
                    "passed": [],
                    "summary": {"total_checks": 0, "passed": 0, "failed": 0, "error": str(exc)},
                }

            for item in result.get("findings", []):
                item["module"] = module_name
            for item in result.get("passed", []):
                item["module"] = module_name

            module_results[module_name] = result
            all_findings.extend(result.get("findings", []))
            all_passed.extend(result.get("passed", []))
            completed.append(module_name)

    finally:
        connector.disconnect()

    score, grade = _compute_score(all_findings)

    findings_summary: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in all_findings:
        sev = f.get("severity", "INFO").upper()
        findings_summary[sev] = findings_summary.get(sev, 0) + 1

    return {
        "host": host,
        "os_type": os_type,
        "modules_completed": completed,
        "all_findings": all_findings,
        "all_passed": all_passed,
        "score": score,
        "grade": grade,
        "findings_summary": findings_summary,
        "total_checks": len(all_findings) + len(all_passed),
        "passed_checks": len(all_passed),
        "module_results": module_results,
        "error": None,
    }
