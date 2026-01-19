"""
Vulnerability Scanner Module
Détection de vulnérabilités connues via CVE et bases de données
"""

import asyncio
import json
import re
from typing import Any
import aiohttp
from rich.console import Console

from ..core.models import (
    AuditConfig,
    HostInfo,
    ServiceInfo,
    Finding,
    Severity,
)


console = Console()


class VulnScanner:
    """
    Scanner de vulnérabilités
    Analyse les services découverts et recherche les CVE associées
    """

    # Base de vulnérabilités connues (simplifié - en production utiliser NVD API)
    KNOWN_VULNS = {
        # OpenSSH
        'openssh': {
            '7.4': [('CVE-2018-15473', 'User enumeration vulnerability', Severity.MEDIUM, 5.3)],
            '7.5': [('CVE-2018-15473', 'User enumeration vulnerability', Severity.MEDIUM, 5.3)],
            '7.6': [('CVE-2018-15473', 'User enumeration vulnerability', Severity.MEDIUM, 5.3)],
            '7.7': [('CVE-2018-15473', 'User enumeration vulnerability', Severity.MEDIUM, 5.3)],
            '8.0': [('CVE-2019-6111', 'SCP client vulnerability', Severity.MEDIUM, 5.9)],
            '8.1': [('CVE-2019-6111', 'SCP client vulnerability', Severity.MEDIUM, 5.9)],
        },
        # Apache
        'apache': {
            '2.4.49': [('CVE-2021-41773', 'Path traversal and RCE', Severity.CRITICAL, 9.8)],
            '2.4.50': [('CVE-2021-42013', 'Path traversal and RCE', Severity.CRITICAL, 9.8)],
            '2.4.46': [('CVE-2021-26691', 'Heap overflow', Severity.CRITICAL, 9.8)],
        },
        # nginx
        'nginx': {
            '1.16': [('CVE-2019-20372', 'HTTP request smuggling', Severity.MEDIUM, 5.3)],
            '1.17': [('CVE-2019-20372', 'HTTP request smuggling', Severity.MEDIUM, 5.3)],
        },
        # MySQL
        'mysql': {
            '5.7': [('CVE-2020-14812', 'Server: Locking vulnerability', Severity.MEDIUM, 4.9)],
            '8.0': [('CVE-2021-2471', 'MySQL Connector vulnerability', Severity.MEDIUM, 5.9)],
        },
        # PostgreSQL
        'postgresql': {
            '9.6': [('CVE-2019-10164', 'Stack buffer overflow', Severity.CRITICAL, 9.8)],
            '10': [('CVE-2019-10164', 'Stack buffer overflow', Severity.CRITICAL, 9.8)],
            '11': [('CVE-2019-10164', 'Stack buffer overflow', Severity.CRITICAL, 9.8)],
        },
        # vsftpd
        'vsftpd': {
            '2.3.4': [('CVE-2011-2523', 'Backdoor command execution', Severity.CRITICAL, 10.0)],
        },
        # ProFTPD
        'proftpd': {
            '1.3.5': [('CVE-2019-12815', 'Remote code execution', Severity.CRITICAL, 9.8)],
        },
        # Samba
        'samba': {
            '4.5': [('CVE-2017-7494', 'Remote code execution (SambaCry)', Severity.CRITICAL, 9.8)],
            '4.6': [('CVE-2017-7494', 'Remote code execution (SambaCry)', Severity.CRITICAL, 9.8)],
        },
        # Redis
        'redis': {
            '5.0': [('CVE-2020-14147', 'Integer overflow', Severity.HIGH, 7.5)],
            '6.0': [('CVE-2021-32761', 'Integer overflow', Severity.HIGH, 7.5)],
        },
        # Elasticsearch
        'elasticsearch': {
            '7.0': [('CVE-2019-7619', 'Information disclosure', Severity.MEDIUM, 5.3)],
            '7.1': [('CVE-2019-7619', 'Information disclosure', Severity.MEDIUM, 5.3)],
        },
    }

    # Configurations dangereuses par service
    DANGEROUS_CONFIGS = {
        'redis': {
            'no_auth': 'Redis sans authentification détecté',
            'protected_mode_off': 'Redis protected mode désactivé',
        },
        'mongodb': {
            'no_auth': 'MongoDB sans authentification détecté',
        },
        'elasticsearch': {
            'no_auth': 'Elasticsearch sans authentification détecté',
        },
        'memcached': {
            'exposed': 'Memcached exposé sur le réseau',
        },
    }

    def __init__(self, config: AuditConfig):
        self.config = config

    async def scan(self, hosts: list[HostInfo]) -> list[Finding]:
        """
        Scanne les hôtes pour détecter des vulnérabilités

        Args:
            hosts: Liste des hôtes avec leurs services

        Returns:
            Liste des findings de vulnérabilités
        """
        findings = []

        for host in hosts:
            for service in host.services:
                # Recherche CVE par version
                cve_findings = self._check_known_vulns(host, service)
                findings.extend(cve_findings)

                # Vérifications de configuration
                config_findings = await self._check_service_config(host, service)
                findings.extend(config_findings)

        # Rechercher des CVE via API (si disponible)
        # findings.extend(await self._search_nvd_api(hosts))

        return findings

    def _check_known_vulns(
        self,
        host: HostInfo,
        service: ServiceInfo
    ) -> list[Finding]:
        """Vérifie les vulnérabilités connues par version"""
        findings = []

        if not service.product or not service.version:
            return findings

        product = service.product.lower()
        version = service.version

        # Chercher le produit dans notre base
        for known_product, versions in self.KNOWN_VULNS.items():
            if known_product in product:
                # Vérifier la version
                for known_version, vulns in versions.items():
                    if version.startswith(known_version):
                        for cve_id, desc, severity, cvss in vulns:
                            findings.append(Finding(
                                id=f"VULN-{cve_id}",
                                title=f"{cve_id}: {desc}",
                                description=f"La version {version} de {product} est vulnérable à {cve_id}",
                                severity=severity,
                                category="vulnerability",
                                target=host.ip,
                                port=service.port,
                                service=service.service_name,
                                protocol=service.protocol,
                                cve_ids=[cve_id],
                                cvss_score=cvss,
                                remediation=f"Mettre à jour {product} vers la dernière version stable",
                                references=[f"https://nvd.nist.gov/vuln/detail/{cve_id}"],
                                discovered_by="vuln_scanner",
                            ))

        return findings

    async def _check_service_config(
        self,
        host: HostInfo,
        service: ServiceInfo
    ) -> list[Finding]:
        """Vérifie les configurations dangereuses des services"""
        findings = []

        service_name = service.service_name or ''

        # Redis
        if 'redis' in service_name.lower():
            result = await self._check_redis(host.ip, service.port)
            if result:
                findings.append(result)

        # MongoDB
        elif 'mongodb' in service_name.lower():
            result = await self._check_mongodb(host.ip, service.port)
            if result:
                findings.append(result)

        # Elasticsearch
        elif 'elasticsearch' in service_name.lower() or service.port == 9200:
            result = await self._check_elasticsearch(host.ip, service.port)
            if result:
                findings.append(result)

        # Memcached
        elif 'memcached' in service_name.lower() or service.port == 11211:
            result = await self._check_memcached(host.ip, service.port)
            if result:
                findings.append(result)

        # MySQL
        elif 'mysql' in service_name.lower():
            result = await self._check_mysql(host.ip, service.port)
            if result:
                findings.append(result)

        return findings

    async def _check_redis(self, ip: str, port: int) -> Finding | None:
        """Vérifie si Redis est accessible sans auth"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5
            )

            # Envoyer une commande INFO
            writer.write(b"INFO\r\n")
            await writer.drain()

            response = await asyncio.wait_for(reader.read(1024), timeout=5)
            writer.close()
            await writer.wait_closed()

            # Si on reçoit une réponse sans erreur d'auth
            if b'redis_version' in response:
                return Finding(
                    id=f"VULN-REDIS-NOAUTH-{ip}",
                    title="Redis accessible sans authentification",
                    description="Redis est accessible sans mot de passe. Un attaquant peut lire/écrire des données.",
                    severity=Severity.CRITICAL,
                    category="vulnerability",
                    target=ip,
                    port=port,
                    service="redis",
                    evidence=response.decode('utf-8', errors='ignore')[:200],
                    remediation="Configurer l'authentification Redis avec 'requirepass'",
                    discovered_by="vuln_scanner",
                )

        except Exception:
            pass

        return None

    async def _check_mongodb(self, ip: str, port: int) -> Finding | None:
        """Vérifie si MongoDB est accessible sans auth"""
        try:
            # Utiliser pymongo ou une connexion brute
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5
            )

            # MongoDB wire protocol - query simple
            # C'est simplifié, en production utiliser pymongo
            writer.close()
            await writer.wait_closed()

            # Essayer via HTTP API (si exposée)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip}:{port}/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        if 'mongodb' in content.lower():
                            return Finding(
                                id=f"VULN-MONGO-NOAUTH-{ip}",
                                title="MongoDB accessible sans authentification",
                                description="MongoDB est accessible sans authentification",
                                severity=Severity.CRITICAL,
                                category="vulnerability",
                                target=ip,
                                port=port,
                                service="mongodb",
                                remediation="Activer l'authentification MongoDB",
                                discovered_by="vuln_scanner",
                            )

        except Exception:
            pass

        return None

    async def _check_elasticsearch(self, ip: str, port: int) -> Finding | None:
        """Vérifie si Elasticsearch est accessible sans auth"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{ip}:{port}/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        if 'cluster_name' in content or 'elasticsearch' in content.lower():
                            return Finding(
                                id=f"VULN-ELASTIC-NOAUTH-{ip}",
                                title="Elasticsearch accessible sans authentification",
                                description="Elasticsearch est accessible publiquement sans authentification",
                                severity=Severity.CRITICAL,
                                category="vulnerability",
                                target=ip,
                                port=port,
                                service="elasticsearch",
                                evidence=content[:300],
                                remediation="Activer X-Pack Security ou configurer un reverse proxy avec auth",
                                discovered_by="vuln_scanner",
                            )

        except Exception:
            pass

        return None

    async def _check_memcached(self, ip: str, port: int) -> Finding | None:
        """Vérifie si Memcached est exposé"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5
            )

            writer.write(b"stats\r\n")
            await writer.drain()

            response = await asyncio.wait_for(reader.read(1024), timeout=5)
            writer.close()
            await writer.wait_closed()

            if b'STAT' in response:
                return Finding(
                    id=f"VULN-MEMCACHED-EXPOSED-{ip}",
                    title="Memcached exposé sur le réseau",
                    description="Memcached est accessible depuis le réseau. Risque d'amplification DDoS et de fuite de données.",
                    severity=Severity.HIGH,
                    category="vulnerability",
                    target=ip,
                    port=port,
                    service="memcached",
                    evidence=response.decode('utf-8', errors='ignore')[:200],
                    remediation="Restreindre Memcached à localhost ou configurer une authentification",
                    discovered_by="vuln_scanner",
                )

        except Exception:
            pass

        return None

    async def _check_mysql(self, ip: str, port: int) -> Finding | None:
        """Vérifie les configurations MySQL dangereuses"""
        # Simplifié - vérifier si MySQL accepte les connexions sans SSL
        # En production, utiliser mysql-connector-python

        return None

    async def _search_nvd_api(self, hosts: list[HostInfo]) -> list[Finding]:
        """
        Recherche des CVE via l'API NVD

        Note: Nécessite une clé API NVD pour les requêtes fréquentes
        https://nvd.nist.gov/developers/request-an-api-key
        """
        findings = []

        # Collecter les CPE uniques
        cpes = set()
        for host in hosts:
            for service in host.services:
                cpes.update(service.cpe)

        if not cpes:
            return findings

        # L'API NVD est rate-limitée, donc on ne l'utilise pas en demo
        # En production:
        # async with aiohttp.ClientSession() as session:
        #     for cpe in cpes:
        #         url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cpeName={cpe}"
        #         async with session.get(url) as response:
        #             if response.status == 200:
        #                 data = await response.json()
        #                 # Parser les CVE

        return findings


class ExploitChecker:
    """
    Vérifie la disponibilité d'exploits publics pour les CVE détectées
    """

    # Mapping CVE -> disponibilité d'exploit
    KNOWN_EXPLOITS = {
        'CVE-2021-41773': {
            'available': True,
            'type': 'RCE',
            'metasploit': True,
            'public_poc': True,
        },
        'CVE-2021-42013': {
            'available': True,
            'type': 'RCE',
            'metasploit': True,
            'public_poc': True,
        },
        'CVE-2017-7494': {
            'available': True,
            'type': 'RCE',
            'metasploit': True,
            'public_poc': True,
        },
        'CVE-2019-12815': {
            'available': True,
            'type': 'RCE',
            'metasploit': True,
            'public_poc': True,
        },
        'CVE-2011-2523': {
            'available': True,
            'type': 'Backdoor',
            'metasploit': True,
            'public_poc': True,
        },
    }

    @classmethod
    def check_exploit(cls, cve_id: str) -> dict | None:
        """Vérifie si un exploit existe pour un CVE"""
        return cls.KNOWN_EXPLOITS.get(cve_id)

    @classmethod
    def enrich_finding(cls, finding: Finding) -> Finding:
        """Enrichit un finding avec les informations d'exploit"""
        for cve_id in finding.cve_ids:
            exploit_info = cls.check_exploit(cve_id)
            if exploit_info:
                # Augmenter la priorité si un exploit existe
                if exploit_info.get('available'):
                    finding.description += "\n\n⚠️ EXPLOIT PUBLIC DISPONIBLE"
                    if exploit_info.get('metasploit'):
                        finding.description += " (Metasploit module)"
                    if finding.severity == Severity.HIGH:
                        finding.severity = Severity.CRITICAL

        return finding
