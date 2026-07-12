"""Sous-package des modules d'audit HCO pour macOS.

Contient deux variantes : ``intel`` (x86_64) et ``silicon`` (arm64 Apple M-series),
chacune exposant les mêmes cinq modules d'audit (ssh, users, firewall,
services, filesystem) avec des adaptations spécifiques à l'architecture.
"""
