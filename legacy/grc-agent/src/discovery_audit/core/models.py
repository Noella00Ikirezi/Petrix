"""
Modèles de données pour Discovery Audit
Définit les structures de données utilisées dans tout le système
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Niveaux de sévérité des findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditPhase(str, Enum):
    """Phases d'un audit discovery"""
    RECONNAISSANCE = "reconnaissance"
    NETWORK_SCAN = "network_scan"
    SERVICE_ENUM = "service_enumeration"
    VULN_SCAN = "vulnerability_scan"
    SYSTEM_AUDIT = "system_audit"
    WEB_AUDIT = "web_audit"
    ANALYSIS = "analysis"
    REPORTING = "reporting"


class TargetType(str, Enum):
    """Types de cibles d'audit"""
    IP = "ip"
    IP_RANGE = "ip_range"
    HOSTNAME = "hostname"
    URL = "url"
    NETWORK = "network"


class AuditTarget(BaseModel):
    """Représente une cible d'audit"""
    value: str = Field(..., description="IP, hostname, URL ou range")
    target_type: TargetType = Field(..., description="Type de cible")
    description: str | None = Field(None, description="Description optionnelle")
    tags: list[str] = Field(default_factory=list, description="Tags pour catégorisation")

    class Config:
        use_enum_values = True


class Finding(BaseModel):
    """Représente une découverte/vulnérabilité"""
    id: str = Field(..., description="Identifiant unique du finding")
    title: str = Field(..., description="Titre du finding")
    description: str = Field(..., description="Description détaillée")
    severity: Severity = Field(..., description="Niveau de sévérité")
    category: str = Field(..., description="Catégorie (network, system, web, etc.)")

    # Détails techniques
    target: str = Field(..., description="Cible affectée")
    port: int | None = Field(None, description="Port concerné si applicable")
    service: str | None = Field(None, description="Service concerné")
    protocol: str | None = Field(None, description="Protocole (tcp/udp)")

    # CVSS et scoring
    cvss_score: float | None = Field(None, ge=0.0, le=10.0, description="Score CVSS")
    cvss_vector: str | None = Field(None, description="Vecteur CVSS")
    cve_ids: list[str] = Field(default_factory=list, description="CVE associés")

    # Contexte
    evidence: str | None = Field(None, description="Preuve/Output")
    remediation: str | None = Field(None, description="Recommandation de correction")
    references: list[str] = Field(default_factory=list, description="Références externes")

    # Métadonnées
    discovered_at: datetime = Field(default_factory=datetime.now)
    discovered_by: str = Field(..., description="Module qui a découvert")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Niveau de confiance")
    false_positive: bool = Field(False, description="Marqué comme faux positif")

    class Config:
        use_enum_values = True


class ServiceInfo(BaseModel):
    """Information sur un service découvert"""
    port: int
    protocol: str = "tcp"
    state: str = "open"
    service_name: str | None = None
    version: str | None = None
    product: str | None = None
    extra_info: str | None = None
    banner: str | None = None
    cpe: list[str] = Field(default_factory=list)


class HostInfo(BaseModel):
    """Information sur un hôte découvert"""
    ip: str
    hostname: str | None = None
    mac_address: str | None = None
    os_guess: str | None = None
    os_accuracy: int | None = None
    state: str = "up"
    services: list[ServiceInfo] = Field(default_factory=list)

    # Informations supplémentaires
    traceroute: list[str] = Field(default_factory=list)
    scripts_output: dict[str, str] = Field(default_factory=dict)


class AuditScore(BaseModel):
    """Score d'audit détaillé"""
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Score global 0-100")
    grade: str = Field(..., description="Note A-F")

    # Scores par catégorie
    network_score: float = Field(0.0, ge=0.0, le=100.0)
    system_score: float = Field(0.0, ge=0.0, le=100.0)
    web_score: float = Field(0.0, ge=0.0, le=100.0)

    # Compteurs
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

    # Détails
    risk_level: str = Field("unknown", description="Niveau de risque global")
    summary: str = Field("", description="Résumé du score")


class AuditResult(BaseModel):
    """Résultat complet d'un audit"""
    id: str = Field(..., description="Identifiant unique de l'audit")
    name: str = Field(..., description="Nom de l'audit")

    # Cibles
    targets: list[AuditTarget] = Field(default_factory=list)

    # Découvertes
    hosts: list[HostInfo] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)

    # Score
    score: AuditScore | None = None

    # Métadonnées
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    # État
    current_phase: AuditPhase = AuditPhase.RECONNAISSANCE
    phases_completed: list[AuditPhase] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    # Configuration utilisée
    config: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def add_finding(self, finding: Finding) -> None:
        """Ajoute un finding à l'audit"""
        self.findings.append(finding)

    def add_host(self, host: HostInfo) -> None:
        """Ajoute un hôte découvert"""
        # Éviter les doublons
        existing_ips = {h.ip for h in self.hosts}
        if host.ip not in existing_ips:
            self.hosts.append(host)

    def get_findings_by_severity(self, severity: Severity) -> list[Finding]:
        """Retourne les findings d'une sévérité donnée"""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_category(self, category: str) -> list[Finding]:
        """Retourne les findings d'une catégorie donnée"""
        return [f for f in self.findings if f.category == category]


@dataclass
class AuditConfig:
    """Configuration d'un audit"""
    # Général
    name: str = "Discovery Audit"
    output_dir: str = "./reports"

    # Phases à exécuter
    enable_network_scan: bool = True
    enable_system_audit: bool = True
    enable_web_audit: bool = True
    enable_vuln_scan: bool = True

    # Network scan
    scan_ports: str = "1-1000"  # ou "full" pour 1-65535
    scan_udp: bool = False
    scan_aggressive: bool = False

    # Timeouts
    timeout_per_host: int = 300  # 5 minutes
    timeout_total: int = 3600  # 1 heure

    # Parallélisme
    max_concurrent_hosts: int = 10
    max_concurrent_checks: int = 50

    # Output
    generate_pdf: bool = True
    generate_html: bool = True
    generate_json: bool = True

    # Credentials pour audit système (optionnel)
    ssh_user: str | None = None
    ssh_key_path: str | None = None
    ssh_password: str | None = None

    # Options avancées
    custom_scripts: list[str] = field(default_factory=list)
    exclude_hosts: list[str] = field(default_factory=list)
    exclude_ports: list[int] = field(default_factory=list)
