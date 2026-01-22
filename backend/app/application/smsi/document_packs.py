"""Document packs configuration for SMSI generation.

Each pack defines a pre-configured set of documents based on selected frameworks.
The user selects frameworks, and the system proposes compatible document structures.
"""
from typing import Dict, List, Any
from enum import Enum


class PackType(str, Enum):
    """Types of document packs."""
    ESSENTIAL = "essential"      # Pack minimal - documents essentiels uniquement
    STANDARD = "standard"        # Pack standard - couverture complète
    ADVANCED = "advanced"        # Pack avancé - avec annexes et outils


# Document structure templates for each pack
DOCUMENT_PACKS: Dict[str, Dict[str, Any]] = {
    # ==========================================================================
    # PACK ESSENTIEL - Minimum viable SMSI
    # ==========================================================================
    "essential": {
        "name": "Pack Essentiel",
        "description": "Documents fondamentaux pour démarrer votre SMSI. Idéal pour les PME ou une première mise en conformité.",
        "estimated_pages": "50-80 pages",
        "documents": [
            {
                "code": "POL-001",
                "name": "Politique de Sécurité de l'Information",
                "type": "policy",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "POL-002",
                "name": "Politique de Gestion des Accès",
                "type": "policy",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 1
            },
            {
                "code": "PROC-001",
                "name": "Procédure de Gestion des Incidents",
                "type": "procedure",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "REG-001",
                "name": "Registre des Actifs",
                "type": "register",
                "required_for": ["ISO27001"],
                "priority": 2
            },
            {
                "code": "REG-002",
                "name": "Registre des Risques",
                "type": "register",
                "required_for": ["ISO27001", "DORA"],
                "priority": 1
            },
        ]
    },

    # ==========================================================================
    # PACK STANDARD - Couverture ISO 27001 complète
    # ==========================================================================
    "standard": {
        "name": "Pack Standard",
        "description": "Couverture complète pour certification ISO 27001. Inclut toutes les politiques et procédures requises.",
        "estimated_pages": "150-200 pages",
        "documents": [
            # Politiques
            {
                "code": "POL-001",
                "name": "Politique de Sécurité de l'Information",
                "type": "policy",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "POL-002",
                "name": "Politique de Gestion des Accès",
                "type": "policy",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 1
            },
            {
                "code": "POL-003",
                "name": "Politique de Classification de l'Information",
                "type": "policy",
                "required_for": ["ISO27001", "RGPD"],
                "priority": 1
            },
            {
                "code": "POL-004",
                "name": "Politique d'Utilisation Acceptable",
                "type": "policy",
                "required_for": ["ISO27001"],
                "priority": 2
            },
            {
                "code": "POL-005",
                "name": "Politique de Sauvegarde",
                "type": "policy",
                "required_for": ["ISO27001", "DORA"],
                "priority": 2
            },
            {
                "code": "POL-006",
                "name": "Politique de Gestion des Changements",
                "type": "policy",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            # Procédures
            {
                "code": "PROC-001",
                "name": "Procédure de Gestion des Incidents",
                "type": "procedure",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "PROC-002",
                "name": "Procédure de Gestion des Accès",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 1
            },
            {
                "code": "PROC-003",
                "name": "Procédure de Gestion des Vulnérabilités",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS", "DORA"],
                "priority": 2
            },
            {
                "code": "PROC-004",
                "name": "Procédure de Sauvegarde et Restauration",
                "type": "procedure",
                "required_for": ["ISO27001", "DORA"],
                "priority": 2
            },
            {
                "code": "PROC-005",
                "name": "Procédure de Gestion des Changements",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            # Registres
            {
                "code": "REG-001",
                "name": "Registre des Actifs",
                "type": "register",
                "required_for": ["ISO27001"],
                "priority": 1
            },
            {
                "code": "REG-002",
                "name": "Registre des Risques",
                "type": "register",
                "required_for": ["ISO27001", "DORA"],
                "priority": 1
            },
            {
                "code": "REG-003",
                "name": "Registre des Incidents",
                "type": "register",
                "required_for": ["ISO27001", "NIS2"],
                "priority": 2
            },
            {
                "code": "REG-004",
                "name": "Registre des Accès Privilégiés",
                "type": "register",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            {
                "code": "REG-005",
                "name": "Registre des Fournisseurs",
                "type": "register",
                "required_for": ["ISO27001", "NIS2"],
                "priority": 2
            },
        ]
    },

    # ==========================================================================
    # PACK AVANCÉ - Multi-normes complet
    # ==========================================================================
    "advanced": {
        "name": "Pack Avancé Multi-Normes",
        "description": "Documentation exhaustive couvrant ISO 27001, DORA, NIS2, RGPD et PCI-DSS. Pour les organisations avec exigences réglementaires multiples.",
        "estimated_pages": "300-400 pages",
        "documents": [
            # === POLITIQUES ===
            {
                "code": "POL-001",
                "name": "Politique de Sécurité de l'Information",
                "type": "policy",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "POL-002",
                "name": "Politique de Gestion des Accès",
                "type": "policy",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 1
            },
            {
                "code": "POL-003",
                "name": "Politique de Classification de l'Information",
                "type": "policy",
                "required_for": ["ISO27001", "RGPD"],
                "priority": 1
            },
            {
                "code": "POL-004",
                "name": "Politique d'Utilisation Acceptable",
                "type": "policy",
                "required_for": ["ISO27001"],
                "priority": 2
            },
            {
                "code": "POL-005",
                "name": "Politique de Sauvegarde et Archivage",
                "type": "policy",
                "required_for": ["ISO27001", "DORA"],
                "priority": 2
            },
            {
                "code": "POL-006",
                "name": "Politique de Gestion des Changements",
                "type": "policy",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            {
                "code": "POL-007",
                "name": "Politique de Continuité d'Activité",
                "type": "policy",
                "required_for": ["ISO27001", "DORA", "NIS2"],
                "priority": 1
            },
            {
                "code": "POL-008",
                "name": "Politique de Protection des Données (RGPD)",
                "type": "policy",
                "required_for": ["RGPD"],
                "priority": 1
            },
            {
                "code": "POL-009",
                "name": "Politique de Gestion des Tiers/Fournisseurs",
                "type": "policy",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 2
            },
            {
                "code": "POL-010",
                "name": "Politique de Résilience Opérationnelle (DORA)",
                "type": "policy",
                "required_for": ["DORA"],
                "priority": 1
            },
            # === PROCÉDURES ===
            {
                "code": "PROC-001",
                "name": "Procédure de Gestion des Incidents de Sécurité",
                "type": "procedure",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "PROC-002",
                "name": "Procédure de Gestion des Accès",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 1
            },
            {
                "code": "PROC-003",
                "name": "Procédure de Gestion des Vulnérabilités",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS", "DORA"],
                "priority": 1
            },
            {
                "code": "PROC-004",
                "name": "Procédure de Sauvegarde et Restauration",
                "type": "procedure",
                "required_for": ["ISO27001", "DORA"],
                "priority": 2
            },
            {
                "code": "PROC-005",
                "name": "Procédure de Gestion des Changements",
                "type": "procedure",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            {
                "code": "PROC-006",
                "name": "Procédure de Notification des Violations (RGPD)",
                "type": "procedure",
                "required_for": ["RGPD", "NIS2"],
                "priority": 1
            },
            {
                "code": "PROC-007",
                "name": "Procédure de Gestion des Droits des Personnes",
                "type": "procedure",
                "required_for": ["RGPD"],
                "priority": 1
            },
            {
                "code": "PROC-008",
                "name": "Procédure de Test de Résilience (DORA)",
                "type": "procedure",
                "required_for": ["DORA"],
                "priority": 2
            },
            {
                "code": "PROC-009",
                "name": "Procédure d'Évaluation des Fournisseurs TIC",
                "type": "procedure",
                "required_for": ["DORA", "NIS2"],
                "priority": 2
            },
            # === REGISTRES ===
            {
                "code": "REG-001",
                "name": "Registre des Actifs Informationnels",
                "type": "register",
                "required_for": ["ISO27001"],
                "priority": 1
            },
            {
                "code": "REG-002",
                "name": "Registre des Risques",
                "type": "register",
                "required_for": ["ISO27001", "DORA"],
                "priority": 1
            },
            {
                "code": "REG-003",
                "name": "Registre des Incidents",
                "type": "register",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 1
            },
            {
                "code": "REG-004",
                "name": "Registre des Accès Privilégiés",
                "type": "register",
                "required_for": ["ISO27001", "PCI-DSS"],
                "priority": 2
            },
            {
                "code": "REG-005",
                "name": "Registre des Fournisseurs et Sous-Traitants",
                "type": "register",
                "required_for": ["ISO27001", "NIS2", "DORA"],
                "priority": 2
            },
            {
                "code": "REG-006",
                "name": "Registre des Traitements (RGPD Art.30)",
                "type": "register",
                "required_for": ["RGPD"],
                "priority": 1
            },
            {
                "code": "REG-007",
                "name": "Registre des Violations de Données",
                "type": "register",
                "required_for": ["RGPD"],
                "priority": 1
            },
            {
                "code": "REG-008",
                "name": "Registre des Tests de Résilience",
                "type": "register",
                "required_for": ["DORA"],
                "priority": 2
            },
            # === ANNEXES ===
            {
                "code": "ANX-001",
                "name": "Matrice RACI SMSI",
                "type": "annex",
                "required_for": ["ISO27001"],
                "priority": 3
            },
            {
                "code": "ANX-002",
                "name": "Clauses Contractuelles Type (DPA)",
                "type": "annex",
                "required_for": ["RGPD"],
                "priority": 2
            },
            {
                "code": "ANX-003",
                "name": "Template Analyse d'Impact (PIA/AIPD)",
                "type": "annex",
                "required_for": ["RGPD"],
                "priority": 2
            },
            {
                "code": "ANX-004",
                "name": "Questionnaire Évaluation Fournisseur",
                "type": "annex",
                "required_for": ["ISO27001", "DORA"],
                "priority": 3
            },
            {
                "code": "ANX-005",
                "name": "Plan de Continuité d'Activité (PCA)",
                "type": "annex",
                "required_for": ["ISO27001", "DORA"],
                "priority": 2
            },
            {
                "code": "ANX-006",
                "name": "Plan de Reprise d'Activité (PRA)",
                "type": "annex",
                "required_for": ["DORA"],
                "priority": 2
            },
        ]
    }
}


# Framework mappings for document recommendations
FRAMEWORK_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "ISO27001": {
        "name": "ISO 27001:2022",
        "mandatory_docs": ["POL-001", "PROC-001", "REG-001", "REG-002"],
        "recommended_pack": "standard",
        "description": "Norme internationale pour les SMSI"
    },
    "DORA": {
        "name": "DORA (Digital Operational Resilience Act)",
        "mandatory_docs": ["POL-001", "POL-007", "POL-010", "PROC-001", "PROC-008", "REG-002", "REG-003"],
        "recommended_pack": "advanced",
        "description": "Règlement européen pour la résilience opérationnelle numérique (secteur financier)"
    },
    "NIS2": {
        "name": "NIS2 (Network and Information Security)",
        "mandatory_docs": ["POL-001", "POL-007", "PROC-001", "PROC-006", "REG-003", "REG-005"],
        "recommended_pack": "standard",
        "description": "Directive européenne sur la cybersécurité des entités essentielles"
    },
    "RGPD": {
        "name": "RGPD (Règlement Général sur la Protection des Données)",
        "mandatory_docs": ["POL-003", "POL-008", "PROC-006", "PROC-007", "REG-006", "REG-007"],
        "recommended_pack": "standard",
        "description": "Règlement européen sur la protection des données personnelles"
    },
    "PCI-DSS": {
        "name": "PCI DSS v4.0",
        "mandatory_docs": ["POL-002", "POL-006", "PROC-002", "PROC-003", "PROC-005", "REG-004"],
        "recommended_pack": "advanced",
        "description": "Standard de sécurité des données de paiement"
    },
    "EU-AI-ACT": {
        "name": "EU AI Act",
        "mandatory_docs": ["POL-001", "REG-002"],
        "recommended_pack": "standard",
        "description": "Règlement européen sur l'intelligence artificielle"
    },
    "NIST-CSF": {
        "name": "NIST Cybersecurity Framework",
        "mandatory_docs": ["POL-001", "PROC-001", "REG-002"],
        "recommended_pack": "standard",
        "description": "Cadre de cybersécurité du NIST (USA)"
    }
}


def get_recommended_pack(selected_frameworks: List[str]) -> str:
    """Determine the recommended pack based on selected frameworks."""
    # If DORA or PCI-DSS selected, recommend advanced
    if any(fw in selected_frameworks for fw in ["DORA", "PCI-DSS"]):
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
    pack = DOCUMENT_PACKS.get(pack_type, DOCUMENT_PACKS["standard"])

    filtered = []
    for doc in pack["documents"]:
        # Include if document is required for any selected framework
        if any(fw in selected_frameworks for fw in doc["required_for"]):
            filtered.append(doc)
        # Or if it's a core document (priority 1) for ISO27001 which is base
        elif doc["priority"] == 1 and "ISO27001" in doc["required_for"]:
            filtered.append(doc)

    # Sort by priority then by code
    filtered.sort(key=lambda x: (x["priority"], x["code"]))

    return filtered


def get_pack_proposal(selected_frameworks: List[str]) -> Dict[str, Any]:
    """Generate a pack proposal based on selected frameworks."""
    recommended = get_recommended_pack(selected_frameworks)

    proposals = {}
    for pack_type in ["essential", "standard", "advanced"]:
        pack = DOCUMENT_PACKS[pack_type]
        filtered_docs = filter_documents_by_frameworks(pack_type, selected_frameworks)

        proposals[pack_type] = {
            "name": pack["name"],
            "description": pack["description"],
            "is_recommended": pack_type == recommended,
            "document_count": len(filtered_docs),
            "estimated_pages": pack["estimated_pages"],
            "documents": filtered_docs,
            "documents_by_type": {
                "policy": len([d for d in filtered_docs if d["type"] == "policy"]),
                "procedure": len([d for d in filtered_docs if d["type"] == "procedure"]),
                "register": len([d for d in filtered_docs if d["type"] == "register"]),
                "annex": len([d for d in filtered_docs if d["type"] == "annex"]),
            }
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
