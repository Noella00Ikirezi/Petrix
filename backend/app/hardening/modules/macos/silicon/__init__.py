"""Modules d'audit HCO pour macOS Apple Silicon (arm64, M-series).

Exporte les cinq modules disponibles (ssh, users, firewall, services,
filesystem) pour une utilisation directe par le moteur HCO via OS_MODULE_MAP.
"""
from app.hardening.modules.macos.silicon import (
    audit_ssh,
    audit_users,
    audit_firewall,
    audit_services,
    audit_filesystem,
)
