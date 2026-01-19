"""
Web Scanner Module
Scan des applications web avec intégration Nuclei
"""

import asyncio
import json
import re
import subprocess
from urllib.parse import urlparse, urljoin
from typing import Any
import aiohttp
from rich.console import Console

from ..core.models import (
    AuditConfig,
    AuditTarget,
    Finding,
    Severity,
)


console = Console()


class WebScanner:
    """
    Scanner d'applications web
    Utilise Nuclei pour les vulnérabilités connues et des checks custom
    """

    def __init__(self, config: AuditConfig):
        self.config = config
        self._nuclei_path = self._find_nuclei()

    def _find_nuclei(self) -> str | None:
        """Trouve le chemin de Nuclei"""
        try:
            result = subprocess.run(
                ["which", "nuclei"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        common_paths = [
            "/usr/bin/nuclei",
            "/usr/local/bin/nuclei",
            "/opt/homebrew/bin/nuclei",
            os.path.expanduser("~/go/bin/nuclei"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    async def scan(self, targets: list[AuditTarget]) -> list[Finding]:
        """
        Scanne les applications web

        Args:
            targets: Liste de cibles web (URLs)

        Returns:
            Liste des findings web
        """
        findings = []

        urls = [t.value for t in targets if t.value.startswith(('http://', 'https://'))]

        if not urls:
            return findings

        # Scan avec Nuclei si disponible
        if self._nuclei_path:
            nuclei_findings = await self._scan_with_nuclei(urls)
            findings.extend(nuclei_findings)
        else:
            console.print("  [yellow]Nuclei not found, using built-in scanner[/]")

        # Scans custom en parallèle
        custom_findings = await self._run_custom_checks(urls)
        findings.extend(custom_findings)

        return findings

    async def _scan_with_nuclei(self, urls: list[str]) -> list[Finding]:
        """Scan avec Nuclei"""
        findings = []

        # Créer un fichier temporaire avec les URLs
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(urls))
            targets_file = f.name

        try:
            console.print(f"  [dim]Running Nuclei on {len(urls)} targets...[/]")

            cmd = [
                self._nuclei_path,
                "-l", targets_file,
                "-json",
                "-silent",
                "-severity", "critical,high,medium,low",
                "-rate-limit", "50",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.timeout_total
            )

            # Parser les résultats JSON (une ligne par résultat)
            for line in stdout.decode().strip().split('\n'):
                if line:
                    try:
                        result = json.loads(line)
                        finding = self._nuclei_result_to_finding(result)
                        if finding:
                            findings.append(finding)
                    except json.JSONDecodeError:
                        continue

            console.print(f"  [dim]Nuclei found {len(findings)} issues[/]")

        except asyncio.TimeoutError:
            console.print("  [yellow]Nuclei scan timed out[/]")
        except Exception as e:
            console.print(f"  [red]Nuclei error: {e}[/]")
        finally:
            import os
            os.unlink(targets_file)

        return findings

    def _nuclei_result_to_finding(self, result: dict) -> Finding | None:
        """Convertit un résultat Nuclei en Finding"""
        try:
            # Mapper la sévérité Nuclei
            severity_map = {
                'critical': Severity.CRITICAL,
                'high': Severity.HIGH,
                'medium': Severity.MEDIUM,
                'low': Severity.LOW,
                'info': Severity.INFO,
            }

            info = result.get('info', {})
            severity_str = info.get('severity', 'info').lower()
            severity = severity_map.get(severity_str, Severity.INFO)

            # Extraire les CVE
            cve_ids = []
            classification = info.get('classification', {})
            if 'cve-id' in classification:
                cve_ids = classification['cve-id'] if isinstance(classification['cve-id'], list) else [classification['cve-id']]

            return Finding(
                id=f"WEB-NUCLEI-{result.get('template-id', 'unknown')}",
                title=info.get('name', 'Unknown vulnerability'),
                description=info.get('description', 'Vulnerability detected by Nuclei'),
                severity=severity,
                category="web",
                target=result.get('host', result.get('matched-at', '')),
                cve_ids=cve_ids,
                cvss_score=classification.get('cvss-score'),
                evidence=result.get('matched-at', ''),
                remediation=info.get('remediation', 'See references for remediation guidance'),
                references=info.get('reference', []),
                discovered_by="nuclei",
            )
        except Exception:
            return None

    async def _run_custom_checks(self, urls: list[str]) -> list[Finding]:
        """Exécute des vérifications custom"""
        findings = []

        checks = [
            self._check_security_headers,
            self._check_ssl_tls,
            self._check_common_files,
            self._check_directory_listing,
            self._check_http_methods,
            self._check_cookies,
        ]

        for url in urls:
            for check in checks:
                try:
                    result = await check(url)
                    if result:
                        findings.extend(result)
                except Exception as e:
                    console.print(f"  [dim]Check failed for {url}: {e}[/]")

        return findings

    async def _check_security_headers(self, url: str) -> list[Finding]:
        """Vérifie les en-têtes de sécurité"""
        findings = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), ssl=False) as response:
                    headers = response.headers

                    # Headers de sécurité à vérifier
                    security_headers = {
                        'X-Content-Type-Options': {
                            'expected': 'nosniff',
                            'severity': Severity.LOW,
                            'title': 'X-Content-Type-Options manquant',
                            'desc': 'Protège contre les attaques MIME-sniffing',
                        },
                        'X-Frame-Options': {
                            'expected': ['DENY', 'SAMEORIGIN'],
                            'severity': Severity.MEDIUM,
                            'title': 'X-Frame-Options manquant',
                            'desc': 'Protège contre le clickjacking',
                        },
                        'Strict-Transport-Security': {
                            'expected': None,  # Juste vérifier la présence
                            'severity': Severity.MEDIUM,
                            'title': 'HSTS non configuré',
                            'desc': 'Force les connexions HTTPS',
                        },
                        'Content-Security-Policy': {
                            'expected': None,
                            'severity': Severity.MEDIUM,
                            'title': 'Content-Security-Policy manquant',
                            'desc': 'Protège contre XSS et injection de contenu',
                        },
                        'X-XSS-Protection': {
                            'expected': '1; mode=block',
                            'severity': Severity.LOW,
                            'title': 'X-XSS-Protection manquant',
                            'desc': 'Protection XSS du navigateur (obsolète mais encore utile)',
                        },
                    }

                    for header, config in security_headers.items():
                        value = headers.get(header)

                        if value is None:
                            findings.append(Finding(
                                id=f"WEB-HEADER-{header.upper().replace('-', '')}",
                                title=config['title'],
                                description=config['desc'],
                                severity=config['severity'],
                                category="web",
                                target=url,
                                remediation=f"Ajouter l'en-tête {header}",
                                discovered_by="web_scanner",
                            ))

        except Exception:
            pass

        return findings

    async def _check_ssl_tls(self, url: str) -> list[Finding]:
        """Vérifie la configuration SSL/TLS"""
        findings = []

        if not url.startswith('https://'):
            # HTTP sans HTTPS
            findings.append(Finding(
                id="WEB-SSL-001",
                title="Site accessible en HTTP",
                description="Le site est accessible en HTTP non chiffré",
                severity=Severity.MEDIUM,
                category="web",
                target=url,
                remediation="Forcer HTTPS et rediriger HTTP vers HTTPS",
                discovered_by="web_scanner",
            ))
            return findings

        try:
            import ssl
            import socket
            from urllib.parse import urlparse

            parsed = urlparse(url)
            hostname = parsed.netloc.split(':')[0]
            port = parsed.port or 443

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Vérifier la version TLS
                    version = ssock.version()

                    if version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                        findings.append(Finding(
                            id="WEB-SSL-002",
                            title=f"Version TLS obsolète: {version}",
                            description=f"Le serveur utilise {version} qui est obsolète et vulnérable",
                            severity=Severity.HIGH,
                            category="web",
                            target=url,
                            remediation="Configurer le serveur pour utiliser TLSv1.2 ou TLSv1.3 minimum",
                            discovered_by="web_scanner",
                        ))

        except Exception:
            pass

        return findings

    async def _check_common_files(self, url: str) -> list[Finding]:
        """Vérifie les fichiers sensibles exposés"""
        findings = []

        sensitive_files = [
            ('.git/config', 'Repository Git exposé', Severity.HIGH),
            ('.env', 'Fichier .env exposé', Severity.CRITICAL),
            ('wp-config.php.bak', 'Backup WordPress exposé', Severity.CRITICAL),
            ('phpinfo.php', 'phpinfo() exposé', Severity.MEDIUM),
            ('.htaccess', 'Fichier .htaccess exposé', Severity.LOW),
            ('web.config', 'Configuration IIS exposée', Severity.MEDIUM),
            ('robots.txt', 'robots.txt présent', Severity.INFO),
            ('.DS_Store', 'Fichier macOS exposé', Severity.LOW),
            ('backup.sql', 'Backup SQL exposé', Severity.CRITICAL),
            ('dump.sql', 'Dump SQL exposé', Severity.CRITICAL),
            ('config.php', 'Config PHP exposée', Severity.HIGH),
            ('database.yml', 'Config DB Rails exposée', Severity.CRITICAL),
        ]

        async with aiohttp.ClientSession() as session:
            for file_path, title, severity in sensitive_files:
                try:
                    test_url = urljoin(url, file_path)
                    async with session.get(
                        test_url,
                        timeout=aiohttp.ClientTimeout(total=5),
                        ssl=False,
                        allow_redirects=False
                    ) as response:
                        if response.status == 200:
                            # Vérifier que c'est bien le fichier et pas une page d'erreur
                            content_type = response.headers.get('Content-Type', '')
                            content = await response.text()

                            # Ignorer les pages HTML d'erreur
                            if 'text/html' in content_type and len(content) > 1000:
                                continue

                            if severity != Severity.INFO:
                                findings.append(Finding(
                                    id=f"WEB-FILE-{file_path.replace('.', '').replace('/', '').upper()}",
                                    title=title,
                                    description=f"Le fichier {file_path} est accessible publiquement",
                                    severity=severity,
                                    category="web",
                                    target=test_url,
                                    remediation=f"Bloquer l'accès au fichier {file_path}",
                                    discovered_by="web_scanner",
                                ))

                except Exception:
                    continue

        return findings

    async def _check_directory_listing(self, url: str) -> list[Finding]:
        """Vérifie si le directory listing est activé"""
        findings = []

        test_paths = ['/', '/images/', '/uploads/', '/assets/', '/static/', '/css/', '/js/']

        async with aiohttp.ClientSession() as session:
            for path in test_paths:
                try:
                    test_url = urljoin(url, path)
                    async with session.get(
                        test_url,
                        timeout=aiohttp.ClientTimeout(total=5),
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            content = await response.text()

                            # Patterns de directory listing
                            listing_patterns = [
                                'Index of',
                                '<title>Directory listing',
                                'Parent Directory',
                                '[To Parent Directory]',
                            ]

                            if any(p in content for p in listing_patterns):
                                findings.append(Finding(
                                    id=f"WEB-DIRLIST-{path.replace('/', '')}",
                                    title="Directory listing activé",
                                    description=f"Le listing de répertoire est activé sur {path}",
                                    severity=Severity.LOW,
                                    category="web",
                                    target=test_url,
                                    remediation="Désactiver le directory listing dans la configuration du serveur",
                                    discovered_by="web_scanner",
                                ))
                                break  # Un seul finding suffit

                except Exception:
                    continue

        return findings

    async def _check_http_methods(self, url: str) -> list[Finding]:
        """Vérifie les méthodes HTTP dangereuses"""
        findings = []

        dangerous_methods = ['PUT', 'DELETE', 'TRACE', 'CONNECT']

        async with aiohttp.ClientSession() as session:
            for method in dangerous_methods:
                try:
                    async with session.request(
                        method,
                        url,
                        timeout=aiohttp.ClientTimeout(total=5),
                        ssl=False
                    ) as response:
                        # Si la méthode n'est pas rejetée (405)
                        if response.status not in [405, 501]:
                            findings.append(Finding(
                                id=f"WEB-METHOD-{method}",
                                title=f"Méthode HTTP {method} autorisée",
                                description=f"La méthode {method} est autorisée sur le serveur",
                                severity=Severity.MEDIUM if method == 'TRACE' else Severity.LOW,
                                category="web",
                                target=url,
                                remediation=f"Désactiver la méthode {method} si non nécessaire",
                                discovered_by="web_scanner",
                            ))

                except Exception:
                    continue

        return findings

    async def _check_cookies(self, url: str) -> list[Finding]:
        """Vérifie la sécurité des cookies"""
        findings = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    cookies = response.cookies

                    for cookie in cookies.values():
                        issues = []

                        # Vérifier les flags de sécurité
                        if not cookie.get('secure') and url.startswith('https://'):
                            issues.append("Secure flag manquant")

                        if not cookie.get('httponly'):
                            issues.append("HttpOnly flag manquant")

                        samesite = cookie.get('samesite', '').lower()
                        if samesite not in ['strict', 'lax']:
                            issues.append("SameSite non défini ou trop permissif")

                        if issues and cookie.key.lower() in ['session', 'sessionid', 'phpsessid', 'jsessionid', 'auth', 'token']:
                            findings.append(Finding(
                                id=f"WEB-COOKIE-{cookie.key.upper()}",
                                title=f"Cookie de session mal configuré: {cookie.key}",
                                description=f"Problèmes détectés: {', '.join(issues)}",
                                severity=Severity.MEDIUM,
                                category="web",
                                target=url,
                                remediation="Ajouter les flags Secure, HttpOnly et SameSite=Strict",
                                discovered_by="web_scanner",
                            ))

        except Exception:
            pass

        return findings


# Import manquant
import os
