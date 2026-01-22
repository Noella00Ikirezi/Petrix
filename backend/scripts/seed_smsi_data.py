"""Seed script for SMSI Generator module - Frameworks, Controls, and Templates."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.infrastructure.database.smsi_models import (
    Framework,
    FrameworkControl,
    DocumentTemplate,
    Question,
    DocumentType,
    SecurityLevel,
    QuestionType,
)
from app.config import settings


# =============================================================================
# FRAMEWORKS DATA
# =============================================================================

FRAMEWORKS = [
    {
        "code": "iso_27001",
        "name": "ISO 27001:2022",
        "version": "2022",
        "description": "Standard international pour le management de la sécurité de l'information",
        "category": "general",
        "region": "international",
        "is_mandatory": False,
        "total_controls": 93,
        "total_requirements": 93,
        "icon": "shield",
        "color": "#3B82F6"
    },
    {
        "code": "iso_27002",
        "name": "ISO 27002:2022",
        "version": "2022",
        "description": "Guide de bonnes pratiques pour les contrôles de sécurité de l'information",
        "category": "general",
        "region": "international",
        "is_mandatory": False,
        "total_controls": 93,
        "total_requirements": 93,
        "icon": "shield-check",
        "color": "#2563EB"
    },
    {
        "code": "dora",
        "name": "DORA",
        "version": "2024",
        "description": "Digital Operational Resilience Act - Résilience opérationnelle numérique pour le secteur financier",
        "category": "financial",
        "region": "eu",
        "is_mandatory": True,
        "total_controls": 64,
        "total_requirements": 120,
        "icon": "bank",
        "color": "#8B5CF6"
    },
    {
        "code": "nis2",
        "name": "NIS2",
        "version": "2024",
        "description": "Directive Network and Information Security 2 - Cybersécurité des infrastructures critiques",
        "category": "general",
        "region": "eu",
        "is_mandatory": True,
        "total_controls": 45,
        "total_requirements": 82,
        "icon": "globe-europe",
        "color": "#6366F1"
    },
    {
        "code": "rgpd",
        "name": "RGPD",
        "version": "2018",
        "description": "Règlement Général sur la Protection des Données personnelles",
        "category": "general",
        "region": "eu",
        "is_mandatory": True,
        "total_controls": 99,
        "total_requirements": 99,
        "icon": "user-shield",
        "color": "#10B981"
    },
    {
        "code": "pci_dss",
        "name": "PCI DSS",
        "version": "4.0",
        "description": "Payment Card Industry Data Security Standard - Sécurité des paiements par carte",
        "category": "financial",
        "region": "international",
        "is_mandatory": False,
        "total_controls": 264,
        "total_requirements": 12,
        "icon": "credit-card",
        "color": "#F97316"
    },
    {
        "code": "eu_ai_act",
        "name": "EU AI Act",
        "version": "2024",
        "description": "Règlement européen sur l'Intelligence Artificielle",
        "category": "general",
        "region": "eu",
        "is_mandatory": True,
        "total_controls": 48,
        "total_requirements": 85,
        "icon": "cpu",
        "color": "#EC4899"
    },
    {
        "code": "nist_csf",
        "name": "NIST CSF",
        "version": "2.0",
        "description": "NIST Cybersecurity Framework - Cadre de cybersécurité américain",
        "category": "general",
        "region": "international",
        "is_mandatory": False,
        "total_controls": 108,
        "total_requirements": 108,
        "icon": "shield-alt",
        "color": "#06B6D4"
    },
    {
        "code": "soc2",
        "name": "SOC 2",
        "version": "2017",
        "description": "Service Organization Control 2 - Contrôles pour les fournisseurs de services",
        "category": "industry",
        "region": "international",
        "is_mandatory": False,
        "total_controls": 64,
        "total_requirements": 64,
        "icon": "clipboard-check",
        "color": "#14B8A6"
    },
    {
        "code": "enisa",
        "name": "ENISA Guidelines",
        "version": "2023",
        "description": "Recommandations de l'Agence européenne pour la cybersécurité",
        "category": "general",
        "region": "eu",
        "is_mandatory": False,
        "total_controls": 52,
        "total_requirements": 52,
        "icon": "book",
        "color": "#8B5CF6"
    },
    {
        "code": "anssi_hds",
        "name": "HDS (ANSSI)",
        "version": "2024",
        "description": "Hébergement de Données de Santé - Certification française",
        "category": "healthcare",
        "region": "france",
        "is_mandatory": False,
        "total_controls": 78,
        "total_requirements": 78,
        "icon": "hospital",
        "color": "#EF4444"
    },
    {
        "code": "secnumcloud",
        "name": "SecNumCloud",
        "version": "3.2",
        "description": "Qualification ANSSI pour les services cloud de confiance",
        "category": "industry",
        "region": "france",
        "is_mandatory": False,
        "total_controls": 96,
        "total_requirements": 96,
        "icon": "cloud-shield",
        "color": "#0EA5E9"
    },
]


# =============================================================================
# DOCUMENT TEMPLATES DATA
# =============================================================================

DOCUMENT_TEMPLATES = [
    # Policies
    {
        "code": "POL-001",
        "name": "Politique de Sécurité des Systèmes d'Information (PSSI)",
        "document_type": DocumentType.POLICY,
        "description": "Document cadre définissant les objectifs et principes de sécurité",
        "sections": [
            {"title": "Objet et périmètre", "order": 1},
            {"title": "Définitions", "order": 2},
            {"title": "Engagement de la direction", "order": 3},
            {"title": "Gouvernance de la sécurité", "order": 4},
            {"title": "Gestion des risques", "order": 5},
            {"title": "Classification de l'information", "order": 6},
            {"title": "Sécurité des ressources humaines", "order": 7},
            {"title": "Gestion des actifs", "order": 8},
            {"title": "Contrôle des accès", "order": 9},
            {"title": "Cryptographie", "order": 10},
            {"title": "Sécurité physique", "order": 11},
            {"title": "Sécurité opérationnelle", "order": 12},
            {"title": "Sécurité des communications", "order": 13},
            {"title": "Conformité", "order": 14},
            {"title": "Révision et amélioration", "order": 15},
        ],
        "output_formats": ["docx", "pdf", "md", "html"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "nis2", "fondamental"],
        "order_index": 1
    },
    {
        "code": "POL-002",
        "name": "Politique de Sécurité Physique (PSP)",
        "document_type": DocumentType.POLICY,
        "description": "Politique de protection des locaux et équipements",
        "sections": [
            {"title": "Objectif", "order": 1},
            {"title": "Périmètre de sécurité", "order": 2},
            {"title": "Contrôle d'accès physique", "order": 3},
            {"title": "Sécurisation des zones sensibles", "order": 4},
            {"title": "Protection des équipements", "order": 5},
            {"title": "Maintenance", "order": 6},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "physique"],
        "order_index": 2
    },
    {
        "code": "POL-003",
        "name": "Politique de Classification de l'Information",
        "document_type": DocumentType.POLICY,
        "description": "Règles de classification et de protection des données",
        "sections": [
            {"title": "Niveaux de classification", "order": 1},
            {"title": "Critères de classification", "order": 2},
            {"title": "Marquage des documents", "order": 3},
            {"title": "Manipulation et stockage", "order": 4},
            {"title": "Transmission", "order": 5},
            {"title": "Destruction", "order": 6},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "rgpd", "classification"],
        "order_index": 3
    },
    {
        "code": "POL-004",
        "name": "Plan de Continuité d'Activité (PCA)",
        "document_type": DocumentType.POLICY,
        "description": "Stratégie et organisation de la continuité d'activité",
        "sections": [
            {"title": "Contexte et objectifs", "order": 1},
            {"title": "Analyse d'impact (BIA)", "order": 2},
            {"title": "Stratégies de continuité", "order": 3},
            {"title": "Organisation de crise", "order": 4},
            {"title": "Plans de reprise", "order": 5},
            {"title": "Tests et exercices", "order": 6},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N2_REINFORCED,
        "tags": ["iso27001", "dora", "nis2", "continuite"],
        "order_index": 4
    },
    {
        "code": "POL-005",
        "name": "Politique de Gestion des Tiers",
        "document_type": DocumentType.POLICY,
        "description": "Exigences de sécurité pour les fournisseurs et partenaires",
        "sections": [
            {"title": "Classification des tiers", "order": 1},
            {"title": "Évaluation préalable", "order": 2},
            {"title": "Exigences contractuelles", "order": 3},
            {"title": "Suivi et audit", "order": 4},
            {"title": "Fin de relation", "order": 5},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "dora", "tiers"],
        "order_index": 5
    },
    {
        "code": "POL-006",
        "name": "Charte d'Utilisation du SI",
        "document_type": DocumentType.POLICY,
        "description": "Règles d'utilisation des ressources informatiques par les utilisateurs",
        "sections": [
            {"title": "Objet et champ d'application", "order": 1},
            {"title": "Règles d'utilisation", "order": 2},
            {"title": "Messagerie et internet", "order": 3},
            {"title": "Télétravail et mobilité", "order": 4},
            {"title": "Protection des données", "order": 5},
            {"title": "Sanctions", "order": 6},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "rgpd", "utilisateur"],
        "order_index": 6
    },
    {
        "code": "POL-007",
        "name": "Politique de Conformité RGPD",
        "document_type": DocumentType.POLICY,
        "description": "Principes et organisation pour la protection des données personnelles",
        "sections": [
            {"title": "Principes du RGPD", "order": 1},
            {"title": "Rôles et responsabilités (DPO)", "order": 2},
            {"title": "Registre des traitements", "order": 3},
            {"title": "Droits des personnes", "order": 4},
            {"title": "Sécurité des données", "order": 5},
            {"title": "Violations de données", "order": 6},
            {"title": "Transferts internationaux", "order": 7},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["rgpd", "conformite"],
        "order_index": 7
    },
    {
        "code": "POL-008",
        "name": "Politique de Gestion de Crise",
        "document_type": DocumentType.POLICY,
        "description": "Organisation et processus de gestion des crises cyber",
        "sections": [
            {"title": "Définition et critères de crise", "order": 1},
            {"title": "Organisation de crise", "order": 2},
            {"title": "Processus d'escalade", "order": 3},
            {"title": "Communication de crise", "order": 4},
            {"title": "Retour à la normale", "order": 5},
            {"title": "Retour d'expérience", "order": 6},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N2_REINFORCED,
        "tags": ["iso27001", "dora", "nis2", "crise"],
        "order_index": 8
    },

    # Procedures
    {
        "code": "PROC-001",
        "name": "Procédure de Gestion des Accès",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de gestion des droits d'accès au SI",
        "sections": [
            {"title": "Demande d'accès", "order": 1},
            {"title": "Validation et attribution", "order": 2},
            {"title": "Revue des droits", "order": 3},
            {"title": "Suppression des accès", "order": 4},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "iam"],
        "order_index": 10
    },
    {
        "code": "PROC-002",
        "name": "Procédure de Gestion des Incidents de Sécurité",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de détection, analyse et traitement des incidents",
        "sections": [
            {"title": "Détection et signalement", "order": 1},
            {"title": "Qualification et priorisation", "order": 2},
            {"title": "Investigation et confinement", "order": 3},
            {"title": "Éradication et remédiation", "order": 4},
            {"title": "Clôture et capitalisation", "order": 5},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "dora", "nis2", "incident"],
        "order_index": 11
    },
    {
        "code": "PROC-003",
        "name": "Procédure de Sauvegarde et Restauration",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de backup et recovery des données",
        "sections": [
            {"title": "Stratégie de sauvegarde", "order": 1},
            {"title": "Exécution des sauvegardes", "order": 2},
            {"title": "Tests de restauration", "order": 3},
            {"title": "Procédure de restauration", "order": 4},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "backup"],
        "order_index": 12
    },
    {
        "code": "PROC-004",
        "name": "Procédure de Gestion des Vulnérabilités",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de détection et correction des vulnérabilités",
        "sections": [
            {"title": "Scans de vulnérabilités", "order": 1},
            {"title": "Analyse et priorisation", "order": 2},
            {"title": "Remédiation", "order": 3},
            {"title": "Vérification", "order": 4},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "vulnerabilite"],
        "order_index": 13
    },
    {
        "code": "PROC-005",
        "name": "Procédure de Gestion des Changements",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de gestion des changements SI",
        "sections": [
            {"title": "Demande de changement", "order": 1},
            {"title": "Évaluation d'impact", "order": 2},
            {"title": "Approbation", "order": 3},
            {"title": "Implémentation", "order": 4},
            {"title": "Revue post-implémentation", "order": 5},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "change"],
        "order_index": 14
    },
    {
        "code": "PROC-006",
        "name": "Procédure RGPD - Droits des Personnes",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de traitement des demandes d'exercice des droits",
        "sections": [
            {"title": "Réception des demandes", "order": 1},
            {"title": "Vérification d'identité", "order": 2},
            {"title": "Traitement par type de droit", "order": 3},
            {"title": "Délais et réponse", "order": 4},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["rgpd", "droits"],
        "order_index": 15
    },
    {
        "code": "PROC-007",
        "name": "Procédure de Violation de Données",
        "document_type": DocumentType.PROCEDURE,
        "description": "Processus de notification des violations de données personnelles",
        "sections": [
            {"title": "Détection et qualification", "order": 1},
            {"title": "Évaluation du risque", "order": 2},
            {"title": "Notification CNIL (72h)", "order": 3},
            {"title": "Notification personnes concernées", "order": 4},
            {"title": "Documentation", "order": 5},
        ],
        "output_formats": ["docx", "pdf", "md"],
        "min_security_level": SecurityLevel.N2_REINFORCED,
        "tags": ["rgpd", "dora", "nis2", "breach"],
        "order_index": 16
    },

    # Registers
    {
        "code": "REG-001",
        "name": "Registre des Actifs SI",
        "document_type": DocumentType.REGISTER,
        "description": "Inventaire des actifs informationnels et matériels",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "actif"],
        "order_index": 20
    },
    {
        "code": "REG-002",
        "name": "Registre des Traitements RGPD",
        "document_type": DocumentType.REGISTER,
        "description": "Registre des activités de traitement (Article 30)",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["rgpd", "traitement"],
        "order_index": 21
    },
    {
        "code": "REG-003",
        "name": "Registre des Incidents",
        "document_type": DocumentType.REGISTER,
        "description": "Journal des incidents de sécurité",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "incident"],
        "order_index": 22
    },
    {
        "code": "REG-004",
        "name": "Registre des Accès Privilégiés",
        "document_type": DocumentType.REGISTER,
        "description": "Inventaire des comptes à privilèges",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N2_REINFORCED,
        "tags": ["iso27001", "privilege"],
        "order_index": 23
    },
    {
        "code": "REG-005",
        "name": "Registre des Risques",
        "document_type": DocumentType.REGISTER,
        "description": "Cartographie et suivi des risques identifiés",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "risque"],
        "order_index": 24
    },
    {
        "code": "REG-006",
        "name": "Registre des Fournisseurs",
        "document_type": DocumentType.REGISTER,
        "description": "Inventaire et évaluation des tiers",
        "sections": [],
        "output_formats": ["xlsx", "csv"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["iso27001", "dora", "tiers"],
        "order_index": 25
    },

    # Annexes
    {
        "code": "ANX-001",
        "name": "Matrice RACI SMSI",
        "document_type": DocumentType.ANNEX,
        "description": "Matrice des responsabilités pour le SMSI",
        "sections": [],
        "output_formats": ["xlsx", "pdf"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["gouvernance"],
        "order_index": 30
    },
    {
        "code": "ANX-002",
        "name": "Clauses de Sous-Traitance (DPA)",
        "document_type": DocumentType.ANNEX,
        "description": "Modèle de clauses contractuelles RGPD",
        "sections": [],
        "output_formats": ["docx", "pdf"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["rgpd", "contrat"],
        "order_index": 31
    },
    {
        "code": "ANX-003",
        "name": "Template PIA / AIPD",
        "document_type": DocumentType.TEMPLATE,
        "description": "Modèle d'analyse d'impact sur la protection des données",
        "sections": [],
        "output_formats": ["docx", "pdf"],
        "min_security_level": SecurityLevel.N2_REINFORCED,
        "tags": ["rgpd", "pia"],
        "order_index": 32
    },
    {
        "code": "ANX-004",
        "name": "Questionnaire Évaluation Fournisseur",
        "document_type": DocumentType.TEMPLATE,
        "description": "Questionnaire de sécurité pour les tiers",
        "sections": [],
        "output_formats": ["xlsx", "docx"],
        "min_security_level": SecurityLevel.N1_STANDARD,
        "tags": ["tiers", "evaluation"],
        "order_index": 33
    },
]


# =============================================================================
# QUESTIONS DATA (Sample for PSSI)
# =============================================================================

QUESTIONS_PSSI = [
    {
        "question_text": "Quel est le nom officiel de votre organisation ?",
        "question_type": QuestionType.TEXT,
        "help_text": "Nom tel qu'il apparaîtra dans les documents officiels",
        "is_required": True,
        "variable_name": "org_name",
        "group_name": "Organisation",
        "order_index": 1
    },
    {
        "question_text": "Qui est le RSSI ou responsable de la sécurité ?",
        "question_type": QuestionType.TEXT,
        "help_text": "Nom et fonction de la personne responsable",
        "is_required": True,
        "variable_name": "rssi_name",
        "group_name": "Gouvernance",
        "order_index": 2
    },
    {
        "question_text": "Quelle est la taille de votre organisation ?",
        "question_type": QuestionType.SINGLE_CHOICE,
        "options": [
            {"value": "tpe", "label": "TPE (< 10 salariés)"},
            {"value": "pme", "label": "PME (10-250 salariés)"},
            {"value": "eti", "label": "ETI (250-5000 salariés)"},
            {"value": "ge", "label": "Grande Entreprise (> 5000 salariés)"}
        ],
        "is_required": True,
        "variable_name": "org_size",
        "group_name": "Organisation",
        "order_index": 3
    },
    {
        "question_text": "Combien de sites géographiques possédez-vous ?",
        "question_type": QuestionType.SINGLE_CHOICE,
        "options": [
            {"value": "1", "label": "1 site unique"},
            {"value": "2-5", "label": "2 à 5 sites"},
            {"value": "5-10", "label": "5 à 10 sites"},
            {"value": "10+", "label": "Plus de 10 sites"}
        ],
        "is_required": True,
        "variable_name": "nb_sites",
        "group_name": "Organisation",
        "order_index": 4
    },
    {
        "question_text": "Quels types de données traitez-vous ? (plusieurs choix possibles)",
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "options": [
            {"value": "personal", "label": "Données personnelles (clients, employés)"},
            {"value": "health", "label": "Données de santé"},
            {"value": "financial", "label": "Données financières"},
            {"value": "payment", "label": "Données de paiement (cartes bancaires)"},
            {"value": "industrial", "label": "Données industrielles / Secrets"},
            {"value": "public", "label": "Données publiques uniquement"}
        ],
        "is_required": True,
        "variable_name": "data_types",
        "group_name": "Données",
        "order_index": 5
    },
    {
        "question_text": "Disposez-vous d'une équipe IT/Sécurité dédiée ?",
        "question_type": QuestionType.YES_NO,
        "help_text": "Équipe interne dédiée à la gestion du SI et de la sécurité",
        "is_required": True,
        "variable_name": "has_it_team",
        "group_name": "Gouvernance",
        "order_index": 6
    },
    {
        "question_text": "Utilisez-vous des services cloud ?",
        "question_type": QuestionType.MULTIPLE_CHOICE,
        "options": [
            {"value": "saas", "label": "SaaS (Office 365, Salesforce, etc.)"},
            {"value": "iaas", "label": "IaaS (AWS, Azure, GCP)"},
            {"value": "paas", "label": "PaaS (Heroku, etc.)"},
            {"value": "private", "label": "Cloud privé"},
            {"value": "none", "label": "Pas de cloud"}
        ],
        "is_required": True,
        "variable_name": "cloud_usage",
        "group_name": "Infrastructure",
        "order_index": 7
    },
    {
        "question_text": "Quelle est la fréquence souhaitée pour la revue de la PSSI ?",
        "question_type": QuestionType.SINGLE_CHOICE,
        "options": [
            {"value": "annual", "label": "Annuelle"},
            {"value": "biannual", "label": "Semestrielle"},
            {"value": "quarterly", "label": "Trimestrielle"},
            {"value": "on_change", "label": "Sur changement majeur uniquement"}
        ],
        "is_required": True,
        "variable_name": "review_frequency",
        "group_name": "Gouvernance",
        "order_index": 8
    },
]


# =============================================================================
# SEED FUNCTIONS
# =============================================================================

async def seed_frameworks(session: AsyncSession):
    """Insert frameworks into database."""
    print("Seeding frameworks...")

    for fw_data in FRAMEWORKS:
        # Check if exists
        stmt = select(Framework).where(Framework.code == fw_data["code"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            framework = Framework(**fw_data)
            session.add(framework)
            print(f"  Added: {fw_data['name']}")
        else:
            print(f"  Exists: {fw_data['name']}")

    await session.commit()
    print(f"Frameworks seeded: {len(FRAMEWORKS)}")


async def seed_templates(session: AsyncSession):
    """Insert document templates into database."""
    print("\nSeeding document templates...")

    for tpl_data in DOCUMENT_TEMPLATES:
        stmt = select(DocumentTemplate).where(DocumentTemplate.code == tpl_data["code"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            template = DocumentTemplate(**tpl_data)
            session.add(template)
            print(f"  Added: {tpl_data['code']} - {tpl_data['name']}")
        else:
            print(f"  Exists: {tpl_data['code']}")

    await session.commit()
    print(f"Templates seeded: {len(DOCUMENT_TEMPLATES)}")


async def seed_questions(session: AsyncSession):
    """Insert questions for PSSI template."""
    print("\nSeeding questions...")

    # Get PSSI template
    stmt = select(DocumentTemplate).where(DocumentTemplate.code == "POL-001")
    result = await session.execute(stmt)
    pssi_template = result.scalar_one_or_none()

    if not pssi_template:
        print("  PSSI template not found, skipping questions")
        return

    for q_data in QUESTIONS_PSSI:
        stmt = select(Question).where(
            Question.template_id == pssi_template.id,
            Question.variable_name == q_data["variable_name"]
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            question = Question(
                template_id=pssi_template.id,
                **q_data
            )
            session.add(question)
            print(f"  Added: {q_data['variable_name']}")
        else:
            print(f"  Exists: {q_data['variable_name']}")

    await session.commit()
    print(f"Questions seeded: {len(QUESTIONS_PSSI)}")


async def main():
    """Main seed function."""
    print("=" * 60)
    print("SMSI Generator - Database Seeding")
    print("=" * 60)

    # Create async engine
    database_url = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(database_url, echo=False)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await seed_frameworks(session)
        await seed_templates(session)
        await seed_questions(session)

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
