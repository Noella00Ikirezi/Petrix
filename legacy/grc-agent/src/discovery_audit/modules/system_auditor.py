"""
System Auditor Module
Audit des configurations système Linux/Windows
"""

import asyncio
import os
from typing import Any
from rich.console import Console

from ..core.models import (
    AuditConfig,
    HostInfo,
    Finding,
    Severity,
)


console = Console()


class SystemAuditor:
    """
    Auditeur de configurations système
    Vérifie les bonnes pratiques de sécurité sur Linux et Windows
    """

    def __init__(self, config: AuditConfig):
        self.config = config

    async def audit(self, hosts: list[HostInfo]) -> list[Finding]:
        """
        Audite les configurations système des hôtes

        Pour les hôtes accessibles via SSH, effectue un audit approfondi
        Pour les hôtes locaux, audit direct
        """
        findings = []

        # Vérifier si on audite le système local
        local_findings = await self._audit_local_system()
        findings.extend(local_findings)

        # Auditer les hôtes distants via SSH si credentials disponibles
        if self.config.ssh_user:
            for host in hosts:
                # Vérifier si SSH est disponible
                ssh_service = next(
                    (s for s in host.services if s.service_name == 'ssh'),
                    None
                )
                if ssh_service:
                    try:
                        remote_findings = await self._audit_remote_system(host)
                        findings.extend(remote_findings)
                    except Exception as e:
                        console.print(f"  [yellow]Could not audit {host.ip}: {e}[/]")

        return findings

    async def _audit_local_system(self) -> list[Finding]:
        """Audite le système local"""
        findings = []

        # Détecter l'OS
        if os.name == 'posix':
            # Linux/macOS
            findings.extend(await self._audit_linux_local())
        elif os.name == 'nt':
            # Windows
            findings.extend(await self._audit_windows_local())

        return findings

    async def _audit_linux_local(self) -> list[Finding]:
        """Audit Linux local"""
        findings = []
        checks = [
            self._check_ssh_config,
            self._check_sudo_config,
            self._check_passwd_shadow,
            self._check_world_writable,
            self._check_suid_sgid,
            self._check_firewall,
            self._check_updates,
            self._check_services,
            self._check_users,
            self._check_logs,
        ]

        for check in checks:
            try:
                result = await check()
                if result:
                    findings.extend(result)
            except Exception as e:
                console.print(f"  [dim]Check failed: {e}[/]")

        return findings

    async def _run_command(self, cmd: str) -> tuple[int, str, str]:
        """Exécute une commande shell"""
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()

    async def _check_ssh_config(self) -> list[Finding]:
        """Vérifie la configuration SSH"""
        findings = []
        ssh_config = "/etc/ssh/sshd_config"

        if not os.path.exists(ssh_config):
            return findings

        try:
            with open(ssh_config, 'r') as f:
                config_content = f.read().lower()

            # Root login autorisé
            if 'permitrootlogin yes' in config_content:
                findings.append(Finding(
                    id="SYS-SSH-001",
                    title="SSH permet le login root",
                    description="La connexion SSH en tant que root est autorisée, ce qui augmente le risque en cas de compromission",
                    severity=Severity.HIGH,
                    category="system",
                    target="localhost",
                    service="ssh",
                    remediation="Modifier /etc/ssh/sshd_config : PermitRootLogin no",
                    discovered_by="system_auditor",
                ))

            # Authentification par mot de passe
            if 'passwordauthentication yes' in config_content:
                findings.append(Finding(
                    id="SYS-SSH-002",
                    title="SSH autorise l'authentification par mot de passe",
                    description="L'authentification par mot de passe est moins sécurisée que l'authentification par clé",
                    severity=Severity.MEDIUM,
                    category="system",
                    target="localhost",
                    service="ssh",
                    remediation="Utiliser l'authentification par clé et désactiver PasswordAuthentication",
                    discovered_by="system_auditor",
                ))

            # Protocole SSH v1
            if 'protocol 1' in config_content:
                findings.append(Finding(
                    id="SYS-SSH-003",
                    title="SSH Protocol v1 activé",
                    description="Le protocole SSH v1 est obsolète et vulnérable",
                    severity=Severity.CRITICAL,
                    category="system",
                    target="localhost",
                    service="ssh",
                    remediation="Utiliser uniquement Protocol 2",
                    discovered_by="system_auditor",
                ))

        except PermissionError:
            pass

        return findings

    async def _check_sudo_config(self) -> list[Finding]:
        """Vérifie la configuration sudo"""
        findings = []

        # Vérifier NOPASSWD
        code, stdout, _ = await self._run_command("grep -r 'NOPASSWD' /etc/sudoers /etc/sudoers.d/ 2>/dev/null")

        if code == 0 and stdout.strip():
            findings.append(Finding(
                id="SYS-SUDO-001",
                title="Sudo NOPASSWD détecté",
                description=f"Des règles sudo sans mot de passe existent:\n{stdout[:500]}",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                service="sudo",
                remediation="Revoir les règles NOPASSWD et les supprimer si non nécessaires",
                discovered_by="system_auditor",
            ))

        return findings

    async def _check_passwd_shadow(self) -> list[Finding]:
        """Vérifie les fichiers passwd et shadow"""
        findings = []

        # Vérifier les permissions de /etc/shadow
        if os.path.exists('/etc/shadow'):
            mode = os.stat('/etc/shadow').st_mode
            if mode & 0o044:  # Lisible par groupe ou autres
                findings.append(Finding(
                    id="SYS-AUTH-001",
                    title="Permissions /etc/shadow trop permissives",
                    description="Le fichier /etc/shadow est lisible par d'autres utilisateurs",
                    severity=Severity.CRITICAL,
                    category="system",
                    target="localhost",
                    remediation="chmod 600 /etc/shadow",
                    discovered_by="system_auditor",
                ))

        # Comptes sans mot de passe
        code, stdout, _ = await self._run_command("awk -F: '($2 == \"\") {print $1}' /etc/shadow 2>/dev/null")
        if code == 0 and stdout.strip():
            findings.append(Finding(
                id="SYS-AUTH-002",
                title="Comptes sans mot de passe",
                description=f"Les comptes suivants n'ont pas de mot de passe: {stdout.strip()}",
                severity=Severity.CRITICAL,
                category="system",
                target="localhost",
                remediation="Définir un mot de passe ou désactiver ces comptes",
                discovered_by="system_auditor",
            ))

        return findings

    async def _check_world_writable(self) -> list[Finding]:
        """Vérifie les fichiers world-writable dangereux"""
        findings = []

        # Fichiers world-writable dans /etc
        code, stdout, _ = await self._run_command("find /etc -type f -perm -002 2>/dev/null | head -20")

        if code == 0 and stdout.strip():
            findings.append(Finding(
                id="SYS-PERM-001",
                title="Fichiers world-writable dans /etc",
                description=f"Fichiers modifiables par tous dans /etc:\n{stdout}",
                severity=Severity.HIGH,
                category="system",
                target="localhost",
                remediation="Corriger les permissions avec chmod o-w",
                discovered_by="system_auditor",
            ))

        return findings

    async def _check_suid_sgid(self) -> list[Finding]:
        """Vérifie les binaires SUID/SGID suspects"""
        findings = []

        # Binaires SUID communs et légitimes
        known_suid = {
            '/usr/bin/sudo', '/usr/bin/su', '/usr/bin/passwd',
            '/usr/bin/chsh', '/usr/bin/chfn', '/usr/bin/newgrp',
            '/usr/bin/gpasswd', '/usr/sbin/unix_chkpwd',
            '/usr/bin/ping', '/usr/bin/mount', '/usr/bin/umount',
        }

        code, stdout, _ = await self._run_command(
            "find /usr -type f \\( -perm -4000 -o -perm -2000 \\) 2>/dev/null"
        )

        if code == 0 and stdout.strip():
            suid_files = set(stdout.strip().split('\n'))
            unknown_suid = suid_files - known_suid

            if unknown_suid:
                findings.append(Finding(
                    id="SYS-SUID-001",
                    title="Binaires SUID/SGID non standards",
                    description=f"Binaires SUID/SGID inhabituels détectés:\n" + "\n".join(list(unknown_suid)[:10]),
                    severity=Severity.MEDIUM,
                    category="system",
                    target="localhost",
                    remediation="Vérifier si ces binaires SUID sont nécessaires",
                    discovered_by="system_auditor",
                ))

        return findings

    async def _check_firewall(self) -> list[Finding]:
        """Vérifie la configuration du firewall"""
        findings = []

        # Vérifier iptables
        code, stdout, _ = await self._run_command("iptables -L -n 2>/dev/null")

        if code != 0:
            # iptables non disponible ou pas de droits
            pass
        elif "Chain INPUT (policy ACCEPT)" in stdout:
            findings.append(Finding(
                id="SYS-FW-001",
                title="Firewall en mode ACCEPT par défaut",
                description="La politique par défaut du firewall est ACCEPT, tous les paquets sont autorisés",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Configurer une politique DROP par défaut avec des règles explicites",
                discovered_by="system_auditor",
            ))

        # Vérifier UFW (Ubuntu)
        code, stdout, _ = await self._run_command("ufw status 2>/dev/null")
        if code == 0 and "inactive" in stdout.lower():
            findings.append(Finding(
                id="SYS-FW-002",
                title="UFW inactif",
                description="Le firewall UFW est installé mais inactif",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Activer UFW avec: sudo ufw enable",
                discovered_by="system_auditor",
            ))

        return findings

    async def _check_updates(self) -> list[Finding]:
        """Vérifie les mises à jour de sécurité"""
        findings = []

        # Debian/Ubuntu
        if os.path.exists('/usr/bin/apt'):
            code, stdout, _ = await self._run_command(
                "apt list --upgradable 2>/dev/null | grep -i security | wc -l"
            )
            if code == 0:
                try:
                    count = int(stdout.strip())
                    if count > 0:
                        severity = Severity.HIGH if count > 10 else Severity.MEDIUM
                        findings.append(Finding(
                            id="SYS-UPDATE-001",
                            title=f"{count} mises à jour de sécurité disponibles",
                            description="Des mises à jour de sécurité sont en attente d'installation",
                            severity=severity,
                            category="system",
                            target="localhost",
                            remediation="Appliquer les mises à jour avec: apt update && apt upgrade",
                            discovered_by="system_auditor",
                        ))
                except ValueError:
                    pass

        return findings

    async def _check_services(self) -> list[Finding]:
        """Vérifie les services potentiellement dangereux"""
        findings = []

        dangerous_services = ['telnet', 'rsh', 'rlogin', 'rexec', 'finger']

        for service in dangerous_services:
            code, _, _ = await self._run_command(f"systemctl is-active {service} 2>/dev/null")
            if code == 0:
                findings.append(Finding(
                    id=f"SYS-SVC-{service.upper()}",
                    title=f"Service dangereux actif: {service}",
                    description=f"Le service {service} est actif. Ce service est obsolète et non sécurisé.",
                    severity=Severity.HIGH,
                    category="system",
                    target="localhost",
                    service=service,
                    remediation=f"Désactiver le service: systemctl disable --now {service}",
                    discovered_by="system_auditor",
                ))

        return findings

    async def _check_users(self) -> list[Finding]:
        """Vérifie les utilisateurs et groupes"""
        findings = []

        # Utilisateurs avec UID 0 (autre que root)
        code, stdout, _ = await self._run_command("awk -F: '($3 == 0 && $1 != \"root\") {print $1}' /etc/passwd")
        if code == 0 and stdout.strip():
            findings.append(Finding(
                id="SYS-USER-001",
                title="Utilisateurs non-root avec UID 0",
                description=f"Les utilisateurs suivants ont UID 0: {stdout.strip()}",
                severity=Severity.CRITICAL,
                category="system",
                target="localhost",
                remediation="Un seul utilisateur devrait avoir UID 0 (root)",
                discovered_by="system_auditor",
            ))

        return findings

    async def _check_logs(self) -> list[Finding]:
        """Vérifie la configuration des logs"""
        findings = []

        # Vérifier si les logs sont actifs
        log_files = ['/var/log/auth.log', '/var/log/secure', '/var/log/syslog']
        log_exists = any(os.path.exists(f) for f in log_files)

        if not log_exists:
            findings.append(Finding(
                id="SYS-LOG-001",
                title="Logs système non trouvés",
                description="Les fichiers de logs standards ne sont pas présents",
                severity=Severity.MEDIUM,
                category="system",
                target="localhost",
                remediation="Vérifier la configuration de rsyslog/syslog-ng",
                discovered_by="system_auditor",
            ))

        return findings

    async def _audit_windows_local(self) -> list[Finding]:
        """Audit Windows local"""
        findings = []

        # TODO: Implémenter les vérifications Windows
        # - Vérification des politiques de sécurité
        # - Vérification de Windows Defender
        # - Vérification des mises à jour
        # - Vérification des utilisateurs/groupes
        # - Vérification des services

        console.print("  [dim]Windows audit not yet fully implemented[/]")

        return findings

    async def _audit_remote_system(self, host: HostInfo) -> list[Finding]:
        """Audite un système distant via SSH"""
        findings = []

        # TODO: Implémenter l'audit distant via Paramiko
        # - Connexion SSH
        # - Exécution des mêmes vérifications à distance
        # - Collecte des résultats

        console.print(f"  [dim]Remote audit of {host.ip} not yet implemented[/]")

        return findings
