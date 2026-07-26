"""Modèles ORM SQLAlchemy pour Petrix — entités métier principales.

Consolide le modèle de données issu du prototype SIEM SecOP et du moteur de scan
Petrix Agent en une source unique : User, Asset, Vulnerability, Scan et AuditLog.
Les clés primaires sont des UUID v4 ; les colonnes JSONB stockent les données
flexibles ou de type liste.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.core.permissions import UserRole


# =============================================================================
# ÉNUMÉRATIONS
# =============================================================================

class AssetType(str, PyEnum):
    """Catégorie d'inventaire d'un actif réseau."""

    SERVER = "server"
    WORKSTATION = "workstation"
    NETWORK = "network"
    CLOUD_INSTANCE = "cloud_instance"
    CONTAINER = "container"
    DATABASE = "database"
    APPLICATION = "application"
    IOT = "iot"
    OTHER = "other"


class AssetStatus(str, PyEnum):
    """État du cycle de vie opérationnel d'un actif."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Severity(str, PyEnum):
    """Échelle de criticité unifiée, partagée par les vulnérabilités et les actifs."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnStatus(str, PyEnum):
    """État du workflow de remédiation d'une vulnérabilité."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class ScanStatus(str, PyEnum):
    """État d'exécution d'une campagne de scan."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, PyEnum):
    """Périmètre fonctionnel d'une campagne de scan."""

    DISCOVERY = "discovery"
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"
    FULL = "full"


# =============================================================================
# MODÈLES ORM
# =============================================================================

class User(Base):
    """Utilisateur de la plateforme avec mot de passe bcrypt, rôle RBAC et verrouillage de compte.

    Attributs notables :
        role: Rôle RBAC (ADMIN, ANALYST, VIEWER) — contrôle les permissions sur les routes API.
        must_change_password: Impose une réinitialisation du mot de passe à la prochaine connexion.
        failed_login_attempts: Incrémenté à chaque mauvais mot de passe ; déclenche le verrouillage.
        locked_until: Le compte est verrouillé tant que cet horodatage est dans le futur.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Sécurité du compte
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Profil
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Horodatages
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relations
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="created_by", foreign_keys="Scan.created_by_id")

    @property
    def full_name(self) -> str:
        """Retourne ``'Prénom Nom'`` si les deux champs sont renseignés, sinon l'adresse e-mail."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


class Asset(Base):
    """Actif réseau découvert automatiquement ou enregistré manuellement dans l'inventaire.

    Attributs notables :
        services: Liste JSONB des services ouverts rapportés par le Petrix Agent (port, nom, version).
        tags: Étiquettes libres (ex. ``["agent", "production"]``).
        custom_fields: Métadonnées arbitraires clé-valeur pour l'enrichissement spécifique au site.
        last_scan_id: FK vers le dernier scan ayant découvert ou mis à jour cet actif.
    """

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identification de l'actif
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus), default=AssetStatus.ACTIVE
    )
    criticality: Mapped[Severity] = mapped_column(
        Enum(Severity), default=Severity.MEDIUM
    )

    # Informations réseau — issues du HostInfo du Petrix Agent
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fqdn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Informations système
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Organisation
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Données flexibles (JSONB)
    services: Mapped[dict] = mapped_column(JSONB, default=list)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Association au dernier scan ayant découvert ou mis à jour cet actif
    last_scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Métadonnées
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relations
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="asset", cascade="all, delete-orphan"
    )
    last_scan: Mapped[Optional["Scan"]] = relationship("Scan", foreign_keys=[last_scan_id], back_populates="discovered_assets")

    __table_args__ = (
        Index("idx_assets_type_status", "asset_type", "status"),
    )


class Vulnerability(Base):
    """Finding de sécurité rattaché à un actif et optionnellement à une campagne de scan.

    Supporte la création manuelle et l'ingestion automatisée depuis le Petrix Agent.
    Le score CVSS 3.x, les identifiants CVE/CWE et la remédiation IA sont des champs
    optionnels enrichis progressivement au cours du cycle de vie du finding.

    Attributs notables :
        discovered_by: Origine du finding (``"manual"``, ``"agent"``, ``"scanner"``).
        ai_priority_score: Priorité 0–100 calculée par le pipeline d'enrichissement IA.
        ai_remediation: Suggestion de remédiation générée par LLM (peut être None).
    """

    __tablename__ = "vulnerabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="SET NULL"), nullable=True
    )

    # Identification
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    status: Mapped[VulnStatus] = mapped_column(
        Enum(VulnStatus), default=VulnStatus.OPEN
    )

    # Scores CVSS issus du Petrix Agent
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cve_ids: Mapped[List[str]] = mapped_column(JSONB, default=list)
    cwe_ids: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Contexte du finding
    affected_component: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    service: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Remédiation
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_effort: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    references: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Attribution du finding à un analyste
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Enrichissement IA
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Horodatages
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    discovered_by: Mapped[str] = mapped_column(String(50), default="manual")
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relations
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="vulnerabilities")
    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="vulnerabilities")
    assignee: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_vulns_severity_status", "severity", "status"),
        Index("idx_vulns_asset_id", "asset_id"),
    )


class Scan(Base):
    """Campagne de scan lancée par un utilisateur, issue du moteur Petrix Agent.

    Attributs notables :
        targets: Liste JSONB des cibles (adresses IP, plages CIDR, etc.).
        config: Paramètres de configuration du scan (modules activés, profil, etc.).
        score / grade: Résultat agrégé de l'audit (score 0–100, grade A–F).
        findings_summary: Compteurs par sévérité ``{critical, high, medium, low, info}``.
        phases_completed: Liste ordonnée des phases terminées (discovery, vuln_scan, etc.).
    """

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Informations générales
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType), nullable=False)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), default=ScanStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Cibles du scan (adresses IP, plages CIDR…)
    targets: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Paramètres de configuration du scan
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Résultats agrégés issus de l'AuditScore du Petrix Agent
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    findings_summary: Mapped[dict] = mapped_column(
        JSONB,
        default={"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    )

    # Suivi des phases d'exécution
    current_phase: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    phases_completed: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Horodatages du cycle de vie du scan
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Journalisation des erreurs
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    errors: Mapped[List[str]] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    created_by: Mapped[Optional["User"]] = relationship("User", back_populates="scans", foreign_keys=[created_by_id])
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="scan"
    )
    discovered_assets: Mapped[List["Asset"]] = relationship(
        "Asset", foreign_keys="Asset.last_scan_id", back_populates="last_scan"
    )

    __table_args__ = (
        Index("idx_scans_status_created", "status", "created_at"),
    )


class AuditLog(Base):
    """Piste d'audit immuable enregistrant toutes les actions significatives de la plateforme.

    Attributs notables :
        action: Verbe de l'action (``"login"``, ``"logout"``, ``"create"``, ``"delete"``…).
        resource_type: Type de ressource concernée (``"auth"``, ``"asset"``, ``"scan"``…).
        details: Contexte JSONB libre (paramètres, valeurs avant/après, etc.).
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Relations
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
    )
