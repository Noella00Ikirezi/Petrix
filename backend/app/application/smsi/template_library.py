"""Template library for SMSI document generation.

Contains pre-written professional templates that only need variable substitution
and light AI customization. This approach is 10x faster and works with small LLMs.
"""
from typing import Dict, List, Any
from datetime import datetime

# =============================================================================
# TEMPLATE VARIABLES
# =============================================================================
# These variables will be replaced in templates:
# {{ORGANISATION}} - Nom de l'organisation
# {{DATE}} - Date de création
# {{DATE_REVISION}} - Date de prochaine révision (+1 an)
# {{CLASSIFICATION}} - Niveau de classification (Interne/Confidentiel)
# {{AUTEUR}} - Auteur du document
# {{REFERENTIELS}} - Liste des référentiels applicables
# {{NIVEAUX_CLASSIFICATION}} - Niveaux N1/N2/N3 avec descriptions
# {{SECTEUR}} - Secteur d'activité
# {{TAILLE}} - Taille de l'organisation

# =============================================================================
# DOCUMENT TEMPLATES - Markdown format
# =============================================================================

TEMPLATES: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # POL-001 - POLITIQUE DE SÉCURITÉ DE L'INFORMATION
    # =========================================================================
    "POL-001": {
        "code": "POL-001",
        "name": "Politique de Sécurité de l'Information",
        "type": "policy",
        "frameworks": ["ISO27001", "NIS2", "DORA", "NIST-CSF"],
        "content": '''# Politique de Sécurité de l'Information

**Document**: POL-001
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet et Périmètre

### 1.1 Objet
La présente Politique de Sécurité de l'Information (PSI) définit les principes directeurs, les règles et les responsabilités en matière de sécurité de l'information au sein de **{{ORGANISATION}}**.

### 1.2 Périmètre d'application
Cette politique s'applique à :
- L'ensemble des collaborateurs (CDI, CDD, stagiaires, alternants)
- Les prestataires et sous-traitants ayant accès aux systèmes d'information
- Tous les actifs informationnels (données, systèmes, applications, infrastructures)
- Tous les sites et locaux de l'organisation

### 1.3 Référentiels applicables
{{REFERENTIELS}}

---

## 2. Définitions

| Terme | Définition |
|-------|------------|
| Actif informationnel | Toute information ou ressource ayant une valeur pour l'organisation |
| Confidentialité | Propriété garantissant que l'information n'est accessible qu'aux personnes autorisées |
| Intégrité | Propriété garantissant l'exactitude et la complétude de l'information |
| Disponibilité | Propriété garantissant l'accessibilité de l'information en temps voulu |
| RSSI | Responsable de la Sécurité des Systèmes d'Information |
| SMSI | Système de Management de la Sécurité de l'Information |

---

## 3. Rôles et Responsabilités

### 3.1 Direction Générale
- Approuve la présente politique et alloue les ressources nécessaires
- Définit les orientations stratégiques en matière de sécurité
- Nomme le RSSI et lui confère l'autorité nécessaire

### 3.2 RSSI (Responsable de la Sécurité des SI)
- Pilote la mise en œuvre du SMSI
- Coordonne les actions de sécurité
- Rapporte à la Direction sur l'état de la sécurité
- Gère les incidents de sécurité majeurs

### 3.3 Responsables Métier
- Identifient et classifient les actifs informationnels de leur périmètre
- Définissent les besoins de sécurité (DICP)
- Valident les accès aux ressources de leur périmètre

### 3.4 Direction des Systèmes d'Information (DSI)
- Met en œuvre les mesures techniques de sécurité
- Assure la maintenance et la surveillance des systèmes
- Gère les incidents techniques

### 3.5 Collaborateurs
- Respectent les règles de sécurité définies
- Signalent tout incident ou anomalie
- Participent aux actions de sensibilisation

---

## 4. Principes Directeurs

### 4.1 Approche par les risques
{{ORGANISATION}} adopte une approche basée sur les risques pour prioriser ses actions de sécurité. Les mesures de protection sont proportionnées aux enjeux identifiés.

### 4.2 Défense en profondeur
La sécurité repose sur plusieurs lignes de défense complémentaires.

### 4.3 Moindre privilège
Les accès sont attribués selon le principe du besoin d'en connaître.

### 4.4 Amélioration continue
Le SMSI fait l'objet d'une évaluation régulière (cycle PDCA).

---

## 5. Domaines de Sécurité

### 5.1 Organisation de la sécurité
- Gouvernance et pilotage du SMSI
- Comité de sécurité trimestriel
- Revue de direction annuelle

### 5.2 Gestion des actifs
- Inventaire des actifs informationnels
- Classification de l'information ({{NIVEAUX_CLASSIFICATION}})

### 5.3 Contrôle des accès
- Gestion des identités et des accès (IAM)
- Authentification forte pour les accès sensibles
- Revue périodique des droits

### 5.4 Sécurité physique
- Contrôle d'accès aux locaux sensibles
- Protection des équipements

### 5.5 Sécurité des opérations
- Gestion des changements
- Protection contre les malwares
- Sauvegarde et restauration
- Journalisation et surveillance

### 5.6 Sécurité des communications
- Segmentation réseau
- Chiffrement des flux sensibles

### 5.7 Gestion des incidents
- Détection et qualification
- Procédure de réponse
- Analyse post-incident

### 5.8 Continuité d'activité
- Plan de continuité (PCA)
- Plan de reprise (PRA)

### 5.9 Conformité
- Veille réglementaire
- Audits internes et externes

---

## 6. Exceptions et Dérogations

Toute exception doit être :
1. Justifiée par un besoin métier impératif
2. Documentée avec analyse de risques
3. Validée par le RSSI
4. Limitée dans le temps

---

## 7. Sanctions

Le non-respect peut entraîner des sanctions disciplinaires conformément au règlement intérieur.

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Vérification | | DSI | |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}

---

## 9. Historique

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | {{DATE}} | Création initiale |
''',
        "variables": ["ORGANISATION", "DATE", "DATE_REVISION", "AUTEUR", "REFERENTIELS", "NIVEAUX_CLASSIFICATION"],
        "ai_sections": []  # No AI customization needed for this template
    },

    # =========================================================================
    # POL-002 - POLITIQUE DE GESTION DES ACCÈS
    # =========================================================================
    "POL-002": {
        "code": "POL-002",
        "name": "Politique de Gestion des Accès",
        "type": "policy",
        "frameworks": ["ISO27001", "PCI-DSS", "DORA"],
        "content": '''# Politique de Gestion des Accès

**Document**: POL-002
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les règles de gestion des identités et des accès aux systèmes d'information de {{ORGANISATION}}.

---

## 2. Principes

### 2.1 Moindre privilège
Chaque utilisateur dispose uniquement des droits nécessaires à ses fonctions.

### 2.2 Séparation des tâches
Les fonctions incompatibles sont séparées (ex: développement / production).

### 2.3 Traçabilité
Tous les accès sont journalisés et conservés.

---

## 3. Gestion des Identités

### 3.1 Création de compte
- Demande formalisée par le responsable hiérarchique
- Validation par le propriétaire des ressources
- Création par l'équipe IT

### 3.2 Modification
- Demande formalisée pour tout changement de droits
- Mise à jour lors des mobilités internes

### 3.3 Suppression
- Désactivation immédiate au départ du collaborateur
- Suppression définitive après 30 jours

---

## 4. Authentification

### 4.1 Mots de passe
- Minimum 12 caractères
- Complexité : majuscules, minuscules, chiffres, caractères spéciaux
- Renouvellement tous les 90 jours
- Historique : 12 derniers mots de passe interdits

### 4.2 Authentification Multi-Facteurs (MFA)
Obligatoire pour :
- Accès administrateur
- Accès distant (VPN)
- Applications sensibles (niveau N2/N3)

---

## 5. Comptes Privilégiés

### 5.1 Inventaire
Tous les comptes privilégiés sont inventoriés dans le registre REG-004.

### 5.2 Utilisation
- Usage strictement professionnel et justifié
- Traçabilité renforcée
- Revue trimestrielle

### 5.3 Solution PAM
Une solution de gestion des accès privilégiés (PAM) est déployée pour :
- Coffre-fort de mots de passe
- Enregistrement des sessions
- Rotation automatique des secrets

---

## 6. Revue des Accès

| Type d'accès | Fréquence | Responsable |
|--------------|-----------|-------------|
| Comptes utilisateurs | Annuelle | Managers |
| Comptes privilégiés | Trimestrielle | RSSI |
| Accès applications critiques | Semestrielle | Propriétaires |

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
''',
        "variables": ["ORGANISATION", "DATE", "DATE_REVISION", "AUTEUR"],
        "ai_sections": []
    },

    # =========================================================================
    # POL-003 - POLITIQUE DE CLASSIFICATION
    # =========================================================================
    "POL-003": {
        "code": "POL-003",
        "name": "Politique de Classification de l'Information",
        "type": "policy",
        "frameworks": ["ISO27001", "RGPD"],
        "content": '''# Politique de Classification de l'Information

**Document**: POL-003
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les niveaux de classification de l'information et les règles de protection associées.

---

## 2. Niveaux de Classification

### 2.1 N1 - Standard
- **Description** : Informations courantes, impact faible en cas de divulgation
- **Exemples** : Documentation projet interne, procédures opérationnelles
- **Marquage** : Aucun marquage spécifique requis

### 2.2 N2 - Renforcé
- **Description** : Données métier ou réglementaires, impact moyen
- **Exemples** : Données clients, informations financières, données RH
- **Marquage** : "CONFIDENTIEL" en en-tête

### 2.3 N3 - Critique
- **Description** : Données hautement sensibles, impact élevé
- **Exemples** : Secrets commerciaux, données bancaires, clés cryptographiques
- **Marquage** : "SECRET" en en-tête et pied de page

---

## 3. Règles de Manipulation par Niveau

| Critère | N1 - Standard | N2 - Renforcé | N3 - Critique |
|---------|---------------|---------------|---------------|
| Stockage | Serveurs internes | Chiffré | Chiffré + accès restreint |
| Transmission | Email interne | Email chiffré | Canal sécurisé dédié |
| Impression | Libre | Supervisée | Interdite sauf dérogation |
| Partage externe | Autorisé | Accord manager | Accord DG + RSSI |
| Destruction | Corbeille | Broyeur niveau 3 | Broyeur niveau 4 + PV |

---

## 4. Classification par Défaut

En l'absence de classification explicite, l'information est considérée comme **N1 - Standard**.

---

## 5. Responsabilités

- **Créateur** : Classifie l'information à sa création
- **Propriétaire** : Valide et maintient la classification
- **Utilisateurs** : Respectent les règles selon le niveau

---

## 6. Déclassification

La déclassification nécessite :
1. Demande justifiée du propriétaire
2. Validation RSSI
3. Mise à jour du marquage

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
''',
        "variables": ["ORGANISATION", "DATE", "DATE_REVISION", "AUTEUR"],
        "ai_sections": []
    },

    # =========================================================================
    # PROC-001 - PROCÉDURE DE GESTION DES INCIDENTS
    # =========================================================================
    "PROC-001": {
        "code": "PROC-001",
        "name": "Procédure de Gestion des Incidents de Sécurité",
        "type": "procedure",
        "frameworks": ["ISO27001", "NIS2", "DORA"],
        "content": '''# Procédure de Gestion des Incidents de Sécurité

**Document**: PROC-001
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## 1. Objectif

Définir le processus de détection, qualification, traitement et clôture des incidents de sécurité.

---

## 2. Périmètre

Tous les incidents de sécurité affectant les systèmes d'information de {{ORGANISATION}}.

---

## 3. Définitions

| Terme | Définition |
|-------|------------|
| Incident | Événement compromettant la confidentialité, intégrité ou disponibilité |
| Événement | Occurrence observable sur un système |
| Alerte | Signal indiquant un incident potentiel |

---

## 4. Classification des Incidents

| Niveau | Sévérité | Exemples | Délai réponse |
|--------|----------|----------|---------------|
| P1 | Critique | Ransomware, fuite massive | < 1h |
| P2 | Haute | Intrusion détectée, DDoS | < 4h |
| P3 | Moyenne | Malware isolé, phishing réussi | < 24h |
| P4 | Basse | Tentative bloquée, spam | < 72h |

---

## 5. Processus

### 5.1 Détection
- Sources : SIEM, EDR, utilisateurs, partenaires
- Tout collaborateur peut signaler via : {{CANAL_SIGNALEMENT}}

### 5.2 Qualification
1. Réception de l'alerte
2. Analyse préliminaire
3. Classification (P1-P4)
4. Création du ticket incident

### 5.3 Confinement
- Isoler les systèmes impactés
- Préserver les preuves
- Communiquer en interne

### 5.4 Éradication
- Identifier la cause racine
- Supprimer la menace
- Corriger les vulnérabilités

### 5.5 Récupération
- Restaurer les systèmes
- Vérifier l'intégrité
- Reprendre les opérations

### 5.6 Clôture
- Documenter l'incident
- Retour d'expérience (RETEX)
- Actions d'amélioration

---

## 6. Escalade

| Niveau | Escalade vers | Délai |
|--------|---------------|-------|
| P1 | DG + RSSI + Cellule crise | Immédiat |
| P2 | RSSI + DSI | < 2h |
| P3 | Équipe sécurité | < 8h |
| P4 | IT Support | Best effort |

---

## 7. Notification Externe

### 7.1 RGPD (violation données personnelles)
- Notification CNIL sous 72h
- Notification personnes concernées si risque élevé

### 7.2 NIS2 / DORA
- Notification autorité compétente selon criticité
- Rapport initial sous 24h pour incidents significatifs

---

## 8. Indicateurs

- Nombre d'incidents par mois
- Temps moyen de détection (MTTD)
- Temps moyen de résolution (MTTR)
- Taux d'incidents récurrents

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |
''',
        "variables": ["ORGANISATION", "DATE", "AUTEUR", "CANAL_SIGNALEMENT"],
        "ai_sections": []
    },

    # =========================================================================
    # REG-001 - REGISTRE DES ACTIFS
    # =========================================================================
    "REG-001": {
        "code": "REG-001",
        "name": "Registre des Actifs Informationnels",
        "type": "register",
        "frameworks": ["ISO27001"],
        "content": '''# Registre des Actifs Informationnels

**Document**: REG-001
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## Instructions

Ce registre inventorie tous les actifs informationnels de l'organisation.
Mise à jour : **mensuelle** par les propriétaires d'actifs.

---

## Inventaire des Actifs

| ID | Type | Nom | Description | Propriétaire | Localisation | Classification | Criticité | Statut |
|----|------|-----|-------------|--------------|--------------|----------------|-----------|--------|
| ACT-001 | Serveur | SRV-PROD-01 | Serveur production ERP | DSI | DC Principal | N2 | Critique | Actif |
| ACT-002 | Application | ERP | Progiciel de gestion | DAF | Cloud | N2 | Critique | Actif |
| ACT-003 | Base de données | DB-CLIENTS | Base clients CRM | Commerce | DC Principal | N2 | Haute | Actif |
| ACT-004 | Application | CRM | Gestion relation client | Commerce | Cloud | N2 | Haute | Actif |
| ACT-005 | Serveur | SRV-MAIL-01 | Serveur messagerie | DSI | DC Principal | N2 | Critique | Actif |
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |

---

## Légende

**Types** : Serveur, Application, Base de données, Réseau, Poste de travail, Mobile, Document

**Criticité** : Critique, Haute, Moyenne, Basse

**Statut** : Actif, En maintenance, Décommissionné

---

## Historique des mises à jour

| Date | Auteur | Modifications |
|------|--------|---------------|
| {{DATE}} | {{AUTEUR}} | Création initiale |
''',
        "variables": ["ORGANISATION", "DATE", "AUTEUR"],
        "ai_sections": []
    },

    # =========================================================================
    # REG-002 - REGISTRE DES RISQUES
    # =========================================================================
    "REG-002": {
        "code": "REG-002",
        "name": "Registre des Risques",
        "type": "register",
        "frameworks": ["ISO27001", "DORA"],
        "content": '''# Registre des Risques

**Document**: REG-002
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## Instructions

Ce registre recense les risques de sécurité identifiés et leur traitement.
Mise à jour : **trimestrielle** lors du comité de sécurité.

---

## Matrice des Risques

| ID | Risque | Description | Vraisemblance | Impact | Niveau | Traitement | Mesures | Responsable | Échéance | Statut |
|----|--------|-------------|---------------|--------|--------|------------|---------|-------------|----------|--------|
| RSK-001 | Ransomware | Chiffrement malveillant des données | Élevée | Critique | Critique | Réduction | EDR, Sauvegardes, Sensibilisation | RSSI | Continu | En cours |
| RSK-002 | Phishing | Vol de credentials | Élevée | Haute | Haute | Réduction | MFA, Filtrage emails, Formation | RSSI | Continu | En cours |
| RSK-003 | Fuite données | Exfiltration données sensibles | Moyenne | Critique | Haute | Réduction | DLP, Classification, Chiffrement | RSSI | Q2 2026 | Planifié |
| RSK-004 | Indisponibilité | Panne datacenter | Faible | Critique | Moyenne | Transfert | PRA, Hébergement secours | DSI | Q1 2026 | En cours |
| RSK-005 | Non-conformité | Non-respect RGPD | Moyenne | Haute | Haute | Réduction | DPO, Registre traitements | DPO | Continu | En cours |
| | | | | | | | | | | |

---

## Échelle d'évaluation

**Vraisemblance** : Très faible (1), Faible (2), Moyenne (3), Élevée (4), Très élevée (5)

**Impact** : Négligeable (1), Mineur (2), Modéré (3), Majeur (4), Critique (5)

**Niveau de risque** = Vraisemblance × Impact

| Score | Niveau |
|-------|--------|
| 1-5 | Faible |
| 6-12 | Moyen |
| 13-19 | Haut |
| 20-25 | Critique |

---

## Options de traitement

- **Acceptation** : Risque accepté en l'état
- **Réduction** : Mesures de mitigation
- **Transfert** : Assurance, sous-traitance
- **Évitement** : Suppression de l'activité source

---

## Historique

| Date | Auteur | Modifications |
|------|--------|---------------|
| {{DATE}} | {{AUTEUR}} | Création initiale |
''',
        "variables": ["ORGANISATION", "DATE", "AUTEUR"],
        "ai_sections": []
    },

    # =========================================================================
    # REG-003 - REGISTRE DES TRAITEMENTS RGPD
    # =========================================================================
    "REG-006": {
        "code": "REG-006",
        "name": "Registre des Traitements RGPD (Article 30)",
        "type": "register",
        "frameworks": ["RGPD"],
        "content": '''# Registre des Traitements de Données Personnelles

**Document**: REG-006
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}
**DPO** : {{DPO_CONTACT}}

---

## Conformité Article 30 du RGPD

Ce registre est tenu conformément à l'article 30 du Règlement Général sur la Protection des Données.

---

## Registre des Traitements

| ID | Traitement | Finalité | Base légale | Catégories de données | Personnes concernées | Destinataires | Durée conservation | Transferts hors UE | Mesures sécurité |
|----|------------|----------|-------------|----------------------|---------------------|---------------|-------------------|-------------------|------------------|
| TRT-001 | Gestion RH | Gestion du personnel | Contrat de travail | Identité, coordonnées, salaire, évaluations | Salariés | RH, Paie, Médecine du travail | 5 ans après départ | Non | Chiffrement, accès restreint |
| TRT-002 | Gestion clients | Relation commerciale | Contrat | Identité, coordonnées, historique commandes | Clients | Commerce, Comptabilité, Logistique | 3 ans après dernière transaction | Non | Chiffrement, sauvegardes |
| TRT-003 | Prospection | Marketing | Consentement | Email, préférences | Prospects | Marketing | Jusqu'au retrait du consentement | Non | Opt-out disponible |
| TRT-004 | Vidéosurveillance | Sécurité des locaux | Intérêt légitime | Images | Visiteurs, salariés | Sécurité | 30 jours | Non | Accès restreint |
| TRT-005 | Badges accès | Contrôle d'accès | Intérêt légitime | Identité, logs d'accès | Salariés, visiteurs | Sécurité, RH | 3 mois | Non | Journalisation |
| | | | | | | | | | |

---

## Bases légales

- **Consentement** : Accord explicite de la personne
- **Contrat** : Nécessaire à l'exécution du contrat
- **Obligation légale** : Imposé par la loi
- **Intérêt légitime** : Intérêt de l'organisation (balance des intérêts)
- **Mission d'intérêt public** : Exercice de l'autorité publique
- **Intérêts vitaux** : Protection de la vie

---

## Contact DPO

Pour toute question : {{DPO_CONTACT}}

---

## Historique

| Date | Auteur | Modifications |
|------|--------|---------------|
| {{DATE}} | {{AUTEUR}} | Création initiale |
''',
        "variables": ["ORGANISATION", "DATE", "AUTEUR", "DPO_CONTACT"],
        "ai_sections": []
    },
}


def get_template(code: str) -> Dict[str, Any]:
    """Get a template by its code."""
    return TEMPLATES.get(code)


def list_templates() -> List[Dict[str, Any]]:
    """List all available templates."""
    return [
        {
            "code": t["code"],
            "name": t["name"],
            "type": t["type"],
            "frameworks": t["frameworks"]
        }
        for t in TEMPLATES.values()
    ]


def fill_template(
    template_code: str,
    context: Dict[str, Any]
) -> str:
    """Fill a template with context values."""
    template = TEMPLATES.get(template_code)
    if not template:
        raise ValueError(f"Template {template_code} not found")

    content = template["content"]

    # Standard variable replacements
    replacements = {
        "{{ORGANISATION}}": context.get("organization", {}).get("name", "[Organisation]"),
        "{{DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{DATE_REVISION}}": (datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y-%m-%d"),
        "{{AUTEUR}}": context.get("author", "[À compléter]"),
        "{{SECTEUR}}": context.get("organization", {}).get("sector", "[Secteur]"),
        "{{TAILLE}}": context.get("organization", {}).get("size", "[Taille]"),
        "{{DPO_CONTACT}}": context.get("dpo_contact", "dpo@organisation.fr"),
        "{{CANAL_SIGNALEMENT}}": context.get("incident_channel", "security@organisation.fr"),
    }

    # Referentiels list
    frameworks = context.get("frameworks", ["ISO 27001"])
    ref_list = "\n".join([f"- {fw}" for fw in frameworks])
    replacements["{{REFERENTIELS}}"] = ref_list

    # Classification levels
    security_level = context.get("security_level", "n1_standard")
    if security_level == "n3_critical":
        levels = "N1 Standard / N2 Renforcé / N3 Critique"
    elif security_level == "n2_reinforced":
        levels = "N1 Standard / N2 Renforcé"
    else:
        levels = "N1 Standard / N2 Confidentiel"
    replacements["{{NIVEAUX_CLASSIFICATION}}"] = levels

    # Apply all replacements
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, str(value))

    return content
