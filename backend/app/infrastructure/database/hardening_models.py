"""Modèles ORM SQLAlchemy pour le module de durcissement HCO (Hardening Compliance Officer).

Représente le cycle de vie complet d'un audit de durcissement : cible (HardeningTarget),
session d'audit (HardeningSession) et constats individuels (HardeningFinding).
Les rapports XML importés depuis l'agent local Petrix sont persistés via ces modèles.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class HardeningSessionStatus(str, PyEnum):
    """État d'avancement d'une session de durcissement."""

    PENDING = "pending"
    CONNECTING = "connecting"
    AUDITING = "auditing"
    COMPLETED = "completed"
    FAILED = "failed"


class HardeningTarget(Base):
    """Machine cible d'un audit de durcissement, identifiée par son nom d'hôte et son OS.

    Attributs notables :
        host: Nom d'hôte ou adresse IP de la cible (``"local"`` pour les imports XML locaux).
        os_type: Type d'OS audité (``"linux"``, ``"macos_silicon"``, ``"macos_intel"``).
        credentials: Données d'accès SSH chiffrées (JSONB) — vide pour les audits locaux.
        tags: Étiquettes libres (ex. ``["xml-import", "arm64", "CIS_macOS_L1"]``).
    """

    __tablename__ = "hardening_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22)
    username: Mapped[str] = mapped_column(String(100), default="root")
    os_type: Mapped[str] = mapped_column(String(30), default="linux")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credentials: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sessions = relationship(
        "HardeningSession", back_populates="target", cascade="all, delete-orphan"
    )


class HardeningSession(Base):
    """Exécution d'un audit de durcissement sur une cible, avec score, grade et analyse IA.

    Attributs notables :
        modules_requested: Liste des modules demandés (ssh, users, kernel, etc.).
        modules_completed: Liste des modules effectivement exécutés.
        score / grade: Résultat global (score 0–100, grade A–F).
        findings_summary: Compteurs par sévérité ``{CRITICAL, HIGH, MEDIUM, LOW}``.
        ai_analysis: Analyse structurée générée par Mistral (résumé exécutif, top priorités…).
    """

    __tablename__ = "hardening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hardening_targets.id"), nullable=False
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(30), default=HardeningSessionStatus.PENDING)
    current_module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    modules_requested: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    modules_completed: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    findings_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    passed_checks: Mapped[int] = mapped_column(Integer, default=0)

    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    target = relationship("HardeningTarget", back_populates="sessions")
    findings = relationship(
        "HardeningFinding", back_populates="session", cascade="all, delete-orphan"
    )


class HardeningFinding(Base):
    """Constat individuel issu d'un contrôle de durcissement (PASS ou FAIL).

    Attributs notables :
        check_id: Identifiant court du contrôle (ex. ``"SSH-001"``).
        module: Module d'audit source (ssh, users, firewall, etc.).
        found: Valeur observée sur le système audité.
        expected: Valeur attendue selon le référentiel (ANSSI-BP-028, CIS…).
        status: Résultat du contrôle (``"PASS"`` ou ``"FAIL"``).
    """

    __tablename__ = "hardening_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hardening_sessions.id"), nullable=False
    )

    check_id: Mapped[str] = mapped_column(String(20), nullable=False)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    found: Mapped[str] = mapped_column(Text, nullable=False)
    expected: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="FAIL")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("HardeningSession", back_populates="findings")
