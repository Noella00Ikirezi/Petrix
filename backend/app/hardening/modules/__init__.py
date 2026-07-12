"""Sous-package des modules d'audit HCO par système d'exploitation.

Chaque sous-package (linux, macos/intel, macos/silicon) expose des modules
``audit_*.py`` implémentant l'interface ``run_audit(ssh, rules) -> dict``.
"""
