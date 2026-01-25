"""
Document packs configuration for SMSI generation.

Complete catalog of ~100 documents based on:
- Matrice-SMSI-Multi-Normes from 08-refonte-SMSI project
- ISO 27001:2022 Annexe A (A.5 to A.18)
- RGPD
- PCI-DSS v4.0
- NIS2
- ISO 22301

Each document includes compliance labels for all applicable standards.
"""
from typing import Dict, List, Any
from enum import Enum


class PackType(str, Enum):
    """Types of document packs."""
    ESSENTIAL = "essential"      # Pack minimal - documents essentiels uniquement
    STANDARD = "standard"        # Pack standard - couverture complète
    ADVANCED = "advanced"        # Pack avancé - avec annexes et outils


# =============================================================================
# COMPLETE DOCUMENT CATALOG (~100 documents)
# Based on ISO 27001 Annexe A + RGPD + PCI-DSS + NIS2 + ISO 22301
# =============================================================================

ALL_DOCUMENTS: List[Dict[str, Any]] = [
    # =========================================================================
    # DIRECTIVES STRATEGIQUES (Format PSSIG - La Poste) - 5 documents
    # =========================================================================
    {
        "code": "DIRSTRAT-001",
        "name": "Directive Stratégique - Organisation de la Sécurité",
        "type": "DIRECTIVE",
        "required_for": ["ISO27001", "NIS2", "DORA"],
        "iso_ref": "A.5.1, A.6.1",
        "priority": 1,
        "owner": "DG/RSSI",
        "description": "Définit l'organisation, la gouvernance et les rôles SSI"
    },
    {
        "code": "DIRSTRAT-002",
        "name": "Directive Stratégique - Gestion des Risques",
        "type": "DIRECTIVE",
        "required_for": ["ISO27001", "NIS2", "DORA"],
        "iso_ref": "6.1.2, 8.2",
        "priority": 1,
        "owner": "RSSI",
        "description": "Cadre méthodologique d'analyse et traitement des risques"
    },
    {
        "code": "DIRSTRAT-003",
        "name": "Directive Stratégique - Conformité et Audit",
        "type": "DIRECTIVE",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.18.1, A.18.2",
        "priority": 1,
        "owner": "RSSI/DPO",
        "description": "Cadre de conformité réglementaire et programme d'audit"
    },
    {
        "code": "DIRSTRAT-004",
        "name": "Directive Stratégique - Continuité d'Activité",
        "type": "DIRECTIVE",
        "required_for": ["ISO27001", "ISO22301", "NIS2", "DORA"],
        "iso_ref": "A.17.1, A.17.2",
        "priority": 1,
        "owner": "DG/RSSI",
        "description": "Stratégie de résilience et continuité des opérations"
    },
    {
        "code": "DIRSTRAT-005",
        "name": "Directive Stratégique - Sécurité des Tiers",
        "type": "DIRECTIVE",
        "required_for": ["ISO27001", "RGPD", "NIS2", "DORA"],
        "iso_ref": "A.15.1, A.15.2",
        "priority": 1,
        "owner": "RSSI/Achats",
        "description": "Exigences de sécurité pour la chaîne d'approvisionnement"
    },

    # =========================================================================
    # POLITIQUES - 22 documents
    # =========================================================================
    {
        "code": "POL-001",
        "name": "PSSI - Politique Générale de Sécurité des Systèmes d'Information",
        "type": "POLICY",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.5.1.1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Document chapeau définissant les principes de sécurité SI"
    },
    {
        "code": "POL-002",
        "name": "PSP - Politique de Sécurité Physique",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "ISO22301"],
        "iso_ref": "A.11.1.1",
        "priority": 2,
        "owner": "Services Généraux",
        "description": "Protection physique des locaux et équipements"
    },
    {
        "code": "POL-003",
        "name": "Politique de Classification de l'Information",
        "type": "POLICY",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS"],
        "iso_ref": "A.8.2.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Niveaux de classification et règles de protection"
    },
    {
        "code": "POL-004",
        "name": "PCA - Politique de Continuité d'Activité",
        "type": "POLICY",
        "required_for": ["ISO27001", "ISO22301", "NIS2", "DORA"],
        "iso_ref": "A.17.1.1",
        "priority": 1,
        "owner": "RSSI/DG",
        "description": "Principes de continuité et résilience"
    },
    {
        "code": "POL-005",
        "name": "Politique de Sécurité des Tiers (Third-Party)",
        "type": "POLICY",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.15.1.1",
        "priority": 2,
        "owner": "RSSI/Achats",
        "description": "Exigences de sécurité pour les fournisseurs"
    },
    {
        "code": "POL-006",
        "name": "Charte d'Utilisation du Système d'Information",
        "type": "POLICY",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.8.1.3",
        "priority": 2,
        "owner": "RSSI",
        "description": "Droits et devoirs des utilisateurs du SI"
    },
    {
        "code": "POL-007",
        "name": "Cadre de Conformité (Compliance Framework)",
        "type": "POLICY",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.18.1.1",
        "priority": 2,
        "owner": "Juridique/RSSI",
        "description": "Cadre de conformité réglementaire"
    },
    {
        "code": "POL-008",
        "name": "Politique de Gestion de Crise",
        "type": "POLICY",
        "required_for": ["ISO27001", "ISO22301", "NIS2"],
        "iso_ref": "A.16.1.1",
        "priority": 1,
        "owner": "RSSI/DG",
        "description": "Organisation et procédures de crise cyber"
    },
    {
        "code": "POL-009",
        "name": "Politique de Contrôle d'Accès",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.9.1.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Principes de gestion des accès logiques"
    },
    {
        "code": "POL-010",
        "name": "Politique de Cryptographie",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.10.1.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Standards de chiffrement et gestion des clés"
    },
    {
        "code": "POL-011",
        "name": "Politique des Appareils Mobiles",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.6.2.1",
        "priority": 2,
        "owner": "RSSI/DSI",
        "description": "Sécurité des terminaux mobiles"
    },
    {
        "code": "POL-012",
        "name": "Politique de Télétravail",
        "type": "POLICY",
        "required_for": ["ISO27001"],
        "iso_ref": "A.6.2.2",
        "priority": 2,
        "owner": "RSSI/DRH",
        "description": "Sécurité du travail à distance"
    },
    {
        "code": "POL-013",
        "name": "Politique de Sauvegarde",
        "type": "POLICY",
        "required_for": ["ISO27001", "ISO22301", "NIS2", "DORA"],
        "iso_ref": "A.12.3.1",
        "priority": 1,
        "owner": "DSI",
        "description": "Stratégie et règles de sauvegarde"
    },
    {
        "code": "POL-014",
        "name": "Politique de Journalisation",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.12.4.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Gestion des logs et traces"
    },
    {
        "code": "POL-015",
        "name": "Politique Anti-Malware",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.12.2.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Protection contre les logiciels malveillants"
    },
    {
        "code": "POL-016",
        "name": "Politique des Comptes à Privilèges (PAM)",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.9.2.3",
        "priority": 1,
        "owner": "RSSI/DSI",
        "description": "Gestion des accès privilégiés"
    },
    {
        "code": "POL-017",
        "name": "Politique de Gestion des Mots de Passe",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.2.4",
        "priority": 2,
        "owner": "RSSI",
        "description": "Règles de création et gestion des mots de passe"
    },
    {
        "code": "POL-018",
        "name": "Politique de Développement Sécurisé (SSDLC)",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.14.2.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Secure Software Development Lifecycle"
    },
    {
        "code": "POL-019",
        "name": "Politique de Protection des Données Personnelles",
        "type": "POLICY",
        "required_for": ["RGPD"],
        "iso_ref": "A.18.1.4",
        "priority": 1,
        "owner": "DPO",
        "description": "Protection des données à caractère personnel"
    },
    {
        "code": "POL-020",
        "name": "Politique de Sécurité Réseau",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.13.1.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Sécurité des réseaux et communications"
    },
    {
        "code": "POL-021",
        "name": "Politique Bureau Propre / Écran Verrouillé",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.11.2.9",
        "priority": 3,
        "owner": "RSSI",
        "description": "Clear Desk / Clear Screen Policy"
    },
    {
        "code": "POL-022",
        "name": "Politique des Supports Amovibles",
        "type": "POLICY",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.8.3.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Gestion des clés USB et supports amovibles"
    },

    # =========================================================================
    # PROCEDURES - 26 documents
    # =========================================================================
    {
        "code": "PROC-001",
        "name": "Procédure de Gestion des Incidents de Sécurité",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.16.1.1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Détection, qualification et traitement des incidents"
    },
    {
        "code": "PROC-002",
        "name": "Procédure de Signalement des Incidents",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.16.1.2",
        "priority": 1,
        "owner": "RSSI",
        "description": "Notification 24h/72h (NIS2/RGPD)"
    },
    {
        "code": "PROC-003",
        "name": "Plan de Réponse aux Incidents",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "ISO22301", "NIS2"],
        "iso_ref": "A.16.1.5",
        "priority": 1,
        "owner": "RSSI",
        "description": "Incident Response Plan"
    },
    {
        "code": "PROC-004",
        "name": "Plan de Continuité d'Activité (PCA)",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "ISO22301", "NIS2", "DORA"],
        "iso_ref": "A.17.1.2",
        "priority": 1,
        "owner": "RSSI/DSI",
        "description": "Business Continuity Plan"
    },
    {
        "code": "PROC-005",
        "name": "Plan de Reprise d'Activité (PRA)",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "ISO22301", "DORA"],
        "iso_ref": "A.17.2.1",
        "priority": 1,
        "owner": "DSI",
        "description": "Disaster Recovery Plan"
    },
    {
        "code": "PROC-006",
        "name": "Procédure de Gestion des Changements",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.12.1.2",
        "priority": 2,
        "owner": "DSI",
        "description": "Change Management"
    },
    {
        "code": "PROC-007",
        "name": "Procédure de Gestion des Vulnérabilités",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.12.6.1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Vulnerability Management"
    },
    {
        "code": "PROC-008",
        "name": "Procédure de Gestion des Comptes Utilisateurs",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.2.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Création/suppression des comptes"
    },
    {
        "code": "PROC-009",
        "name": "Procédure d'Attribution des Droits",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.2.2",
        "priority": 2,
        "owner": "DSI",
        "description": "Access Provisioning"
    },
    {
        "code": "PROC-010",
        "name": "Procédure de Revue des Droits d'Accès",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.2.5",
        "priority": 2,
        "owner": "RSSI",
        "description": "Access Review"
    },
    {
        "code": "PROC-011",
        "name": "Procédure de Départ (Off-boarding)",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS"],
        "iso_ref": "A.7.3.1",
        "priority": 2,
        "owner": "DRH/DSI",
        "description": "Processus de fin de contrat"
    },
    {
        "code": "PROC-012",
        "name": "Plan de Sensibilisation SSI",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.7.2.2",
        "priority": 2,
        "owner": "RSSI/RH",
        "description": "Security Awareness Program"
    },
    {
        "code": "PROC-013",
        "name": "Procédure de Gestion des Clés Cryptographiques",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.10.1.2",
        "priority": 1,
        "owner": "DSI",
        "description": "Key Management"
    },
    {
        "code": "PROC-014",
        "name": "Procédure de Contrôle d'Accès Physique",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.11.1.2",
        "priority": 2,
        "owner": "Services Généraux",
        "description": "Physical Access Control"
    },
    {
        "code": "PROC-015",
        "name": "Procédure de Destruction des Supports",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS"],
        "iso_ref": "A.8.3.2",
        "priority": 2,
        "owner": "DSI",
        "description": "Media Destruction"
    },
    {
        "code": "PROC-016",
        "name": "Procédure de Mise au Rebut Sécurisée",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.11.2.7",
        "priority": 2,
        "owner": "DSI",
        "description": "Secure Equipment Disposal"
    },
    {
        "code": "PROC-017",
        "name": "Procédure d'Audit Interne SSI",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.18.2.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Internal Security Audit"
    },
    {
        "code": "PROC-018",
        "name": "Procédure de Revue Documentaire",
        "type": "PROCEDURE",
        "required_for": ["ISO27001"],
        "iso_ref": "A.5.1.2",
        "priority": 3,
        "owner": "RSSI",
        "description": "Document Review Process"
    },
    {
        "code": "PROC-019",
        "name": "Procédure de Revue des Fournisseurs",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.15.2.1",
        "priority": 2,
        "owner": "RSSI/Achats",
        "description": "Supplier Review"
    },
    {
        "code": "PROC-020",
        "name": "Procédure de Collecte de Preuves (Forensic)",
        "type": "PROCEDURE",
        "required_for": ["ISO27001"],
        "iso_ref": "A.16.1.7",
        "priority": 2,
        "owner": "RSSI",
        "description": "Evidence Collection"
    },
    {
        "code": "PROC-021",
        "name": "Procédure de Retour d'Expérience (REX)",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "ISO22301"],
        "iso_ref": "A.16.1.6",
        "priority": 2,
        "owner": "RSSI",
        "description": "Lessons Learned"
    },
    {
        "code": "PROC-022",
        "name": "Procédure de Tests de Sécurité",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.14.2.8",
        "priority": 2,
        "owner": "RSSI",
        "description": "Security Testing"
    },
    {
        "code": "PROC-023",
        "name": "Plan de Tests PCA",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "ISO22301"],
        "iso_ref": "A.17.1.3",
        "priority": 2,
        "owner": "RSSI",
        "description": "BCP Testing Plan"
    },
    {
        "code": "PROC-024",
        "name": "Check-list Sécurité Projets",
        "type": "PROCEDURE",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.6.1.5",
        "priority": 3,
        "owner": "RSSI",
        "description": "Security by Design / Privacy by Design"
    },
    {
        "code": "PROC-025",
        "name": "Manuel d'Exploitation",
        "type": "PROCEDURE",
        "required_for": ["ISO27001"],
        "iso_ref": "A.12.1.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Operations Manual"
    },
    {
        "code": "PROC-026",
        "name": "Procédure AIPD (Analyse d'Impact)",
        "type": "PROCEDURE",
        "required_for": ["RGPD"],
        "iso_ref": "A.6.1.5",
        "priority": 1,
        "owner": "DPO",
        "description": "Data Protection Impact Assessment"
    },

    # =========================================================================
    # REGISTRES - 15 documents
    # =========================================================================
    {
        "code": "REG-001",
        "name": "Inventaire des Actifs SI",
        "type": "REGISTER",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.8.1.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Asset Inventory"
    },
    {
        "code": "REG-002",
        "name": "Registre des Traitements de Données Personnelles",
        "type": "REGISTER",
        "required_for": ["RGPD"],
        "iso_ref": "A.18.1.4",
        "priority": 1,
        "owner": "DPO",
        "description": "RGPD Article 30 - Record of Processing Activities"
    },
    {
        "code": "REG-003",
        "name": "Registre des Incidents de Sécurité",
        "type": "REGISTER",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.16.1.1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Security Incident Register"
    },
    {
        "code": "REG-004",
        "name": "Registre des Accès Privilégiés",
        "type": "REGISTER",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.2.3",
        "priority": 1,
        "owner": "RSSI/DSI",
        "description": "Privileged Access Register"
    },
    {
        "code": "REG-005",
        "name": "Registre des Fournisseurs",
        "type": "REGISTER",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.15.1.2",
        "priority": 2,
        "owner": "Achats/RSSI",
        "description": "Supplier Register"
    },
    {
        "code": "REG-006",
        "name": "Registre des Formations Sécurité",
        "type": "REGISTER",
        "required_for": ["ISO27001", "PCI-DSS", "NIS2"],
        "iso_ref": "A.7.2.2",
        "priority": 2,
        "owner": "RH/RSSI",
        "description": "Security Training Register"
    },
    {
        "code": "REG-007",
        "name": "Registre des Audits",
        "type": "REGISTER",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.18.2.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Audit Register"
    },
    {
        "code": "REG-008",
        "name": "Registre des Non-Conformités",
        "type": "REGISTER",
        "required_for": ["ISO27001"],
        "iso_ref": "A.18.2.2",
        "priority": 2,
        "owner": "RSSI",
        "description": "Non-Conformity Register"
    },
    {
        "code": "REG-009",
        "name": "Registre des Risques",
        "type": "REGISTER",
        "required_for": ["ISO27001", "NIS2", "DORA"],
        "iso_ref": "6.1.2",
        "priority": 1,
        "owner": "RSSI",
        "description": "Risk Register"
    },
    {
        "code": "REG-010",
        "name": "Registre des Exigences Légales",
        "type": "REGISTER",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.18.1.1",
        "priority": 2,
        "owner": "Juridique",
        "description": "Legal Requirements Register"
    },
    {
        "code": "REG-011",
        "name": "Registre des Violations de Données (RGPD)",
        "type": "REGISTER",
        "required_for": ["RGPD"],
        "iso_ref": "A.16.1.1",
        "priority": 1,
        "owner": "DPO",
        "description": "Data Breach Register"
    },
    {
        "code": "REG-012",
        "name": "Matrice des Propriétaires d'Actifs",
        "type": "REGISTER",
        "required_for": ["ISO27001"],
        "iso_ref": "A.8.1.2",
        "priority": 2,
        "owner": "DSI",
        "description": "Asset Owners Matrix"
    },
    {
        "code": "REG-013",
        "name": "Liste des Contacts Autorités",
        "type": "REGISTER",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.6.1.3",
        "priority": 2,
        "owner": "RSSI/DPO",
        "description": "Authorities Contact List"
    },
    {
        "code": "REG-014",
        "name": "Registre des Actions d'Amélioration",
        "type": "REGISTER",
        "required_for": ["ISO27001"],
        "iso_ref": "10.1",
        "priority": 3,
        "owner": "RSSI",
        "description": "Improvement Actions Register"
    },
    {
        "code": "REG-015",
        "name": "Registre PCI-DSS (SAQ)",
        "type": "REGISTER",
        "required_for": ["PCI-DSS"],
        "iso_ref": "Req. 12",
        "priority": 1,
        "owner": "RSSI",
        "description": "PCI-DSS Self-Assessment Questionnaire"
    },

    # =========================================================================
    # ANNEXES - 12 documents
    # =========================================================================
    {
        "code": "ANX-001",
        "name": "Matrice RACI SMSI",
        "type": "ANNEX",
        "required_for": ["ISO27001", "ISO22301"],
        "iso_ref": "A.6.1.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Roles and Responsibilities Matrix"
    },
    {
        "code": "ANX-002",
        "name": "Clauses Type DPA (Data Processing Agreement)",
        "type": "ANNEX",
        "required_for": ["RGPD"],
        "iso_ref": "A.15.1.2",
        "priority": 2,
        "owner": "DPO/Juridique",
        "description": "Standard Data Processing Clauses"
    },
    {
        "code": "ANX-003",
        "name": "Template PIA (Analyse d'Impact)",
        "type": "ANNEX",
        "required_for": ["RGPD"],
        "iso_ref": "A.6.1.5",
        "priority": 2,
        "owner": "DPO",
        "description": "Privacy Impact Assessment Template"
    },
    {
        "code": "ANX-004",
        "name": "Questionnaire Sécurité Fournisseur",
        "type": "ANNEX",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.15.1.1",
        "priority": 2,
        "owner": "RSSI/Achats",
        "description": "Supplier Security Questionnaire"
    },
    {
        "code": "ANX-005",
        "name": "Clauses de Confidentialité (NDA)",
        "type": "ANNEX",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.7.1.2",
        "priority": 2,
        "owner": "Juridique",
        "description": "Non-Disclosure Agreement Template"
    },
    {
        "code": "ANX-006",
        "name": "Engagement de Sécurité Salarié",
        "type": "ANNEX",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.7.1.2",
        "priority": 2,
        "owner": "DRH",
        "description": "Employee Security Commitment"
    },
    {
        "code": "ANX-007",
        "name": "Matrice de Séparation des Tâches",
        "type": "ANNEX",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.6.1.2",
        "priority": 2,
        "owner": "RSSI",
        "description": "Segregation of Duties Matrix"
    },
    {
        "code": "ANX-008",
        "name": "Matrice des Accès Réseau",
        "type": "ANNEX",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.9.1.2",
        "priority": 2,
        "owner": "DSI",
        "description": "Network Access Matrix"
    },
    {
        "code": "ANX-009",
        "name": "Glossaire SMSI",
        "type": "ANNEX",
        "required_for": ["ISO27001"],
        "iso_ref": "3",
        "priority": 4,
        "owner": "RSSI",
        "description": "ISMS Glossary"
    },
    {
        "code": "ANX-010",
        "name": "Liste des Contacts d'Urgence",
        "type": "ANNEX",
        "required_for": ["ISO27001", "ISO22301"],
        "iso_ref": "A.16.1.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Emergency Contacts List"
    },
    {
        "code": "ANX-011",
        "name": "Clauses SSI pour Contrats",
        "type": "ANNEX",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.15.1.2",
        "priority": 2,
        "owner": "Juridique/RSSI",
        "description": "Security Clauses for Contracts"
    },
    {
        "code": "ANX-012",
        "name": "Check-list Nouveau Projet",
        "type": "ANNEX",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.6.1.5",
        "priority": 3,
        "owner": "RSSI",
        "description": "New Project Security Checklist"
    },

    # =========================================================================
    # SCHEMAS - 8 documents
    # =========================================================================
    {
        "code": "SCH-001",
        "name": "Architecture SI Globale",
        "type": "SCHEMA",
        "required_for": ["ISO27001"],
        "iso_ref": "A.12.1.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Global IT Architecture Diagram"
    },
    {
        "code": "SCH-002",
        "name": "Flux de Données Inter-Entités",
        "type": "SCHEMA",
        "required_for": ["ISO27001", "RGPD"],
        "iso_ref": "A.13.2.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Data Flow Diagram"
    },
    {
        "code": "SCH-003",
        "name": "Zones de Sécurité (N1/N2/N3)",
        "type": "SCHEMA",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.13.1.3",
        "priority": 2,
        "owner": "RSSI",
        "description": "Security Zones Diagram"
    },
    {
        "code": "SCH-004",
        "name": "Architecture Cloud (Google Workspace)",
        "type": "SCHEMA",
        "required_for": ["ISO27001"],
        "iso_ref": "A.12.1.1",
        "priority": 3,
        "owner": "DSI",
        "description": "Cloud Architecture Diagram"
    },
    {
        "code": "SCH-005",
        "name": "Architecture Virtualisation (Proxmox)",
        "type": "SCHEMA",
        "required_for": ["ISO27001"],
        "iso_ref": "A.12.1.1",
        "priority": 3,
        "owner": "DSI",
        "description": "Virtualization Architecture Diagram"
    },
    {
        "code": "SCH-006",
        "name": "Réseau Multi-Sites",
        "type": "SCHEMA",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.13.1.1",
        "priority": 2,
        "owner": "DSI",
        "description": "Multi-Site Network Diagram"
    },
    {
        "code": "SCH-007",
        "name": "Flux PCI-DSS (Données de Paiement)",
        "type": "SCHEMA",
        "required_for": ["PCI-DSS"],
        "iso_ref": "Req. 1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Payment Card Data Flow Diagram"
    },
    {
        "code": "SCH-008",
        "name": "Schéma d'Urbanisation Applicative",
        "type": "SCHEMA",
        "required_for": ["ISO27001"],
        "iso_ref": "A.12.1.1",
        "priority": 3,
        "owner": "DSI",
        "description": "Application Landscape Diagram"
    },

    # =========================================================================
    # MATRICES - 4 documents
    # =========================================================================
    {
        "code": "MAT-001",
        "name": "Matrice de Correspondance Multi-Normes",
        "type": "MATRIX",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2", "ISO22301"],
        "iso_ref": "A.18.1.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Multi-Standard Mapping Matrix"
    },
    {
        "code": "MAT-002",
        "name": "Matrice d'Analyse des Risques",
        "type": "MATRIX",
        "required_for": ["ISO27001", "NIS2", "DORA"],
        "iso_ref": "6.1.2",
        "priority": 1,
        "owner": "RSSI",
        "description": "Risk Assessment Matrix"
    },
    {
        "code": "MAT-003",
        "name": "Matrice BIA (Business Impact Analysis)",
        "type": "MATRIX",
        "required_for": ["ISO27001", "ISO22301", "DORA"],
        "iso_ref": "A.17.1.1",
        "priority": 1,
        "owner": "RSSI",
        "description": "Business Impact Analysis Matrix"
    },
    {
        "code": "MAT-004",
        "name": "Matrice de Traçabilité des Exigences",
        "type": "MATRIX",
        "required_for": ["ISO27001"],
        "iso_ref": "A.18.1.1",
        "priority": 3,
        "owner": "RSSI",
        "description": "Requirements Traceability Matrix"
    },

    # =========================================================================
    # RAPPORTS - 4 documents
    # =========================================================================
    {
        "code": "RPT-001",
        "name": "Rapport de Revue de Direction SMSI",
        "type": "REPORT",
        "required_for": ["ISO27001"],
        "iso_ref": "9.3",
        "priority": 2,
        "owner": "RSSI",
        "description": "Management Review Report"
    },
    {
        "code": "RPT-002",
        "name": "Tableau de Bord SSI",
        "type": "REPORT",
        "required_for": ["ISO27001", "NIS2"],
        "iso_ref": "9.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Security Dashboard / KPIs"
    },
    {
        "code": "RPT-003",
        "name": "Rapport d'Audit Annuel",
        "type": "REPORT",
        "required_for": ["ISO27001", "PCI-DSS"],
        "iso_ref": "A.18.2.1",
        "priority": 2,
        "owner": "RSSI",
        "description": "Annual Audit Report"
    },
    {
        "code": "RPT-004",
        "name": "Bilan Annuel de Conformité",
        "type": "REPORT",
        "required_for": ["ISO27001", "RGPD", "PCI-DSS", "NIS2"],
        "iso_ref": "A.18.2.2",
        "priority": 2,
        "owner": "RSSI/DPO",
        "description": "Annual Compliance Report"
    },

    # =========================================================================
    # TEMPLATES - 4 documents
    # =========================================================================
    {
        "code": "TPL-001",
        "name": "Template de Déclaration d'Applicabilité (DDA)",
        "type": "TEMPLATE",
        "required_for": ["ISO27001"],
        "iso_ref": "6.1.3",
        "priority": 1,
        "owner": "RSSI",
        "description": "Statement of Applicability Template"
    },
    {
        "code": "TPL-002",
        "name": "Template de Plan de Traitement des Risques",
        "type": "TEMPLATE",
        "required_for": ["ISO27001", "NIS2"],
        "iso_ref": "6.1.3",
        "priority": 1,
        "owner": "RSSI",
        "description": "Risk Treatment Plan Template"
    },
    {
        "code": "TPL-003",
        "name": "Template de Compte-Rendu d'Incident",
        "type": "TEMPLATE",
        "required_for": ["ISO27001", "RGPD", "NIS2"],
        "iso_ref": "A.16.1.2",
        "priority": 2,
        "owner": "RSSI",
        "description": "Incident Report Template"
    },
    {
        "code": "TPL-004",
        "name": "Template de Compte-Rendu d'Exercice PCA",
        "type": "TEMPLATE",
        "required_for": ["ISO27001", "ISO22301"],
        "iso_ref": "A.17.1.3",
        "priority": 2,
        "owner": "RSSI",
        "description": "BCP Exercise Report Template"
    },
]


# =============================================================================
# DOCUMENT PACKS CONFIGURATION
# =============================================================================

def get_essential_codes() -> List[str]:
    """Get document codes for the essential pack (~20 documents)."""
    return [
        "DIRSTRAT-001",
        "POL-001", "POL-003", "POL-006", "POL-009", "POL-016", "POL-017",
        "PROC-001", "PROC-007", "PROC-008", "PROC-010", "PROC-011", "PROC-012",
        "REG-001", "REG-002", "REG-003", "REG-009",
        "ANX-001",
        "MAT-002",
    ]


def get_standard_codes() -> List[str]:
    """Get document codes for the standard pack (~50 documents)."""
    return [
        # Toutes les directives
        "DIRSTRAT-001", "DIRSTRAT-002", "DIRSTRAT-003", "DIRSTRAT-004", "DIRSTRAT-005",
        # Politiques principales
        "POL-001", "POL-002", "POL-003", "POL-004", "POL-005", "POL-006", "POL-007",
        "POL-008", "POL-009", "POL-010", "POL-011", "POL-012", "POL-013", "POL-014",
        "POL-015", "POL-016", "POL-017", "POL-018", "POL-019",
        # Procédures principales
        "PROC-001", "PROC-002", "PROC-003", "PROC-004", "PROC-005", "PROC-006",
        "PROC-007", "PROC-008", "PROC-009", "PROC-010", "PROC-011", "PROC-012",
        "PROC-013", "PROC-015", "PROC-017", "PROC-019", "PROC-021", "PROC-026",
        # Registres principaux
        "REG-001", "REG-002", "REG-003", "REG-004", "REG-005", "REG-006",
        "REG-007", "REG-008", "REG-009", "REG-010", "REG-011",
        # Annexes principales
        "ANX-001", "ANX-002", "ANX-003", "ANX-004", "ANX-005", "ANX-006",
        # Schémas principaux
        "SCH-001", "SCH-002", "SCH-003",
        # Matrices principales
        "MAT-001", "MAT-002", "MAT-003",
        # Rapports principaux
        "RPT-001", "RPT-002",
        # Templates principaux
        "TPL-001", "TPL-002", "TPL-003",
    ]


DOCUMENT_PACKS: Dict[str, Dict[str, Any]] = {
    "essential": {
        "name": "Pack Essentiel",
        "description": "Documents fondamentaux pour démarrer votre SMSI. Idéal pour les PME ou une première mise en conformité.",
        "estimated_pages": "50-80 pages",
        "document_codes": get_essential_codes(),
    },
    "standard": {
        "name": "Pack Standard",
        "description": "Couverture complète pour certification ISO 27001 + RGPD. Inclut toutes les politiques et procédures requises.",
        "estimated_pages": "150-200 pages",
        "document_codes": get_standard_codes(),
    },
    "advanced": {
        "name": "Pack Avancé Multi-Normes",
        "description": "Documentation exhaustive couvrant ISO 27001, RGPD, PCI-DSS, NIS2, DORA et ISO 22301. Pour les organisations avec exigences réglementaires multiples.",
        "estimated_pages": "300-400 pages",
        "document_codes": [doc["code"] for doc in ALL_DOCUMENTS],
    }
}


# Framework mappings for document recommendations
FRAMEWORK_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "ISO27001": {
        "name": "ISO 27001:2022",
        "mandatory_docs": ["POL-001", "PROC-001", "REG-001", "REG-009", "TPL-001"],
        "recommended_pack": "standard",
        "description": "Norme internationale pour les SMSI"
    },
    "RGPD": {
        "name": "RGPD (Règlement Général sur la Protection des Données)",
        "mandatory_docs": ["POL-003", "POL-019", "PROC-026", "REG-002", "REG-011"],
        "recommended_pack": "standard",
        "description": "Règlement européen sur la protection des données personnelles"
    },
    "PCI-DSS": {
        "name": "PCI DSS v4.0",
        "mandatory_docs": ["POL-009", "POL-016", "PROC-007", "PROC-013", "REG-004", "SCH-007"],
        "recommended_pack": "advanced",
        "description": "Standard de sécurité des données de paiement"
    },
    "NIS2": {
        "name": "NIS2 (Network and Information Security)",
        "mandatory_docs": ["POL-001", "POL-004", "PROC-001", "PROC-002", "REG-003", "REG-005"],
        "recommended_pack": "standard",
        "description": "Directive européenne sur la cybersécurité des entités essentielles"
    },
    "DORA": {
        "name": "DORA (Digital Operational Resilience Act)",
        "mandatory_docs": ["POL-004", "POL-013", "PROC-004", "PROC-005", "REG-009", "MAT-003"],
        "recommended_pack": "advanced",
        "description": "Règlement européen pour la résilience opérationnelle numérique (secteur financier)"
    },
    "ISO22301": {
        "name": "ISO 22301:2019",
        "mandatory_docs": ["POL-004", "PROC-004", "PROC-005", "PROC-023", "MAT-003"],
        "recommended_pack": "advanced",
        "description": "Norme internationale pour la continuité d'activité"
    },
    "EU-AI-ACT": {
        "name": "EU AI Act",
        "mandatory_docs": ["POL-001", "REG-009"],
        "recommended_pack": "standard",
        "description": "Règlement européen sur l'intelligence artificielle"
    },
    "NIST-CSF": {
        "name": "NIST Cybersecurity Framework",
        "mandatory_docs": ["POL-001", "PROC-001", "REG-009"],
        "recommended_pack": "standard",
        "description": "Cadre de cybersécurité du NIST (USA)"
    }
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_document_by_code(code: str) -> Dict[str, Any] | None:
    """Get a document specification by its code."""
    for doc in ALL_DOCUMENTS:
        if doc["code"] == code:
            return doc
    return None


def get_documents_for_pack(pack_type: str) -> List[Dict[str, Any]]:
    """Get all documents for a specific pack type."""
    pack = DOCUMENT_PACKS.get(pack_type, DOCUMENT_PACKS["standard"])
    codes = pack.get("document_codes", [])
    return [doc for doc in ALL_DOCUMENTS if doc["code"] in codes]


def get_recommended_pack(selected_frameworks: List[str]) -> str:
    """Determine the recommended pack based on selected frameworks."""
    # If DORA, PCI-DSS or ISO22301 selected, recommend advanced
    if any(fw in selected_frameworks for fw in ["DORA", "PCI-DSS", "ISO22301"]):
        return "advanced"

    # If more than 2 frameworks, recommend standard or advanced
    if len(selected_frameworks) > 2:
        return "standard"

    # If only 1 framework and it's ISO27001, standard is enough
    if len(selected_frameworks) == 1 and "ISO27001" in selected_frameworks:
        return "standard"

    # Default to essential for simple cases
    return "essential"


def filter_documents_by_frameworks(
    pack_type: str,
    selected_frameworks: List[str]
) -> List[Dict[str, Any]]:
    """Filter documents in a pack based on selected frameworks."""
    documents = get_documents_for_pack(pack_type)

    # If no frameworks specified, return all documents from pack
    if not selected_frameworks:
        return documents

    filtered = []
    for doc in documents:
        # Include if document is required for any selected framework
        if any(fw in selected_frameworks for fw in doc.get("required_for", [])):
            filtered.append(doc)
        # Or if it's a core document (priority 1) for ISO27001 which is base
        elif doc.get("priority") == 1 and "ISO27001" in doc.get("required_for", []):
            filtered.append(doc)

    # Sort by priority then by code
    filtered.sort(key=lambda x: (x.get("priority", 3), x["code"]))

    return filtered


def get_pack_proposal(selected_frameworks: List[str]) -> Dict[str, Any]:
    """Generate a pack proposal based on selected frameworks."""
    recommended = get_recommended_pack(selected_frameworks)

    proposals = {}
    for pack_type in ["essential", "standard", "advanced"]:
        pack = DOCUMENT_PACKS[pack_type]
        filtered_docs = filter_documents_by_frameworks(pack_type, selected_frameworks)

        # Count by type
        docs_by_type = {
            "DIRECTIVE": len([d for d in filtered_docs if d["type"] == "DIRECTIVE"]),
            "POLICY": len([d for d in filtered_docs if d["type"] == "POLICY"]),
            "PROCEDURE": len([d for d in filtered_docs if d["type"] == "PROCEDURE"]),
            "REGISTER": len([d for d in filtered_docs if d["type"] == "REGISTER"]),
            "ANNEX": len([d for d in filtered_docs if d["type"] == "ANNEX"]),
            "SCHEMA": len([d for d in filtered_docs if d["type"] == "SCHEMA"]),
            "MATRIX": len([d for d in filtered_docs if d["type"] == "MATRIX"]),
            "REPORT": len([d for d in filtered_docs if d["type"] == "REPORT"]),
            "TEMPLATE": len([d for d in filtered_docs if d["type"] == "TEMPLATE"]),
        }

        proposals[pack_type] = {
            "name": pack["name"],
            "description": pack["description"],
            "is_recommended": pack_type == recommended,
            "document_count": len(filtered_docs),
            "estimated_pages": pack["estimated_pages"],
            "documents": filtered_docs,
            "documents_by_type": docs_by_type
        }

    return {
        "selected_frameworks": selected_frameworks,
        "framework_details": {
            fw: FRAMEWORK_REQUIREMENTS.get(fw, {"name": fw})
            for fw in selected_frameworks
        },
        "recommended_pack": recommended,
        "proposals": proposals
    }


def get_documents_by_framework(framework: str) -> List[Dict[str, Any]]:
    """Get all documents required for a specific framework."""
    return [doc for doc in ALL_DOCUMENTS if framework in doc.get("required_for", [])]


def get_framework_statistics() -> Dict[str, int]:
    """Get statistics about documents per framework."""
    stats = {
        "ISO27001": 0,
        "RGPD": 0,
        "PCI-DSS": 0,
        "NIS2": 0,
        "ISO22301": 0,
        "DORA": 0,
    }
    for doc in ALL_DOCUMENTS:
        for fw in doc.get("required_for", []):
            if fw in stats:
                stats[fw] += 1
    return stats


def get_type_labels() -> Dict[str, str]:
    """Get French labels for document types."""
    return {
        "DIRECTIVE": "Directives Stratégiques",
        "POLICY": "Politiques",
        "PROCEDURE": "Procédures",
        "REGISTER": "Registres",
        "ANNEX": "Annexes",
        "SCHEMA": "Schémas",
        "MATRIX": "Matrices",
        "REPORT": "Rapports",
        "TEMPLATE": "Templates",
        "CHECKLIST": "Checklists",
    }


def get_priority_labels() -> Dict[int, str]:
    """Get French labels for priority levels."""
    return {
        1: "Critique",
        2: "Haute",
        3: "Moyenne",
        4: "Basse",
    }


def get_framework_labels() -> Dict[str, str]:
    """Get display labels for frameworks."""
    return {
        "ISO27001": "ISO 27001:2022",
        "RGPD": "RGPD",
        "PCI-DSS": "PCI-DSS v4.0",
        "NIS2": "NIS2",
        "ISO22301": "ISO 22301:2019",
        "DORA": "DORA",
    }
