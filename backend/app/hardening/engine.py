"""Moteur principal HCO (Hardening Configuration Operator).

Agrège les findings issus de l'agent local, calcule le score ANSSI-BP-028 (0–100)
et la note A–F. L'audit s'exécute localement via les scripts agents (linux.sh,
macos.sh, windows.ps1) — aucune connexion SSH n'est établie par ce module.
"""
from __future__ import annotations

import logging

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


