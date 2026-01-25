"""PSSIG-inspired template library for professional SMSI document generation.

Based on the PSSIG (Politique de Sécurité des Systèmes d'Information du Groupe)
documentation framework from La Poste, which follows ISO 27001 with a 4-level
document hierarchy:
- Niveau 1: Cadre général (General Framework)
- Niveau 2: Directives stratégiques et chartes (Strategic Directives)
- Niveau 3: Directives tactiques (Tactical Directives - entity-specific)
- Niveau 4: Procédures opérationnelles et guides (Operational Procedures)

Document structure follows the PSSIG format:
- Page de garde (Cover page with metadata)
- Table des matières (Table of contents)
- Préambule: Objet, Positionnement, Périmètre, Validité
- Glossaire (Definitions)
- Règles de sécurité numérotées (Numbered security rules)
- Annexes
"""
from typing import Dict, List, Any
from datetime import datetime


# =============================================================================
# DOCUMENT STRUCTURE HELPERS
# =============================================================================

def generate_cover_page(context: Dict[str, Any]) -> str:
    """Generate a professional cover page following PSSIG format."""
    return f'''---
title: "{context.get('document_title', 'Document SMSI')}"
organization: "{context.get('organization', 'Organisation')}"
document_code: "{context.get('code', 'DOC-XXX')}"
version: "{context.get('version', '1.0')}"
classification: "{context.get('classification', 'Interne')}"
status: "{context.get('status', 'Brouillon')}"
---

# {context.get('document_title', 'Document SMSI')}

| | |
|---|---|
| **Organisation** | {context.get('organization', 'Organisation')} |
| **Code document** | {context.get('code', 'DOC-XXX')} |
| **Version** | {context.get('version', '1.0')} |
| **Date** | {context.get('date', datetime.now().strftime('%d/%m/%Y'))} |
| **Classification** | {context.get('classification', 'Interne')} |
| **Statut** | {context.get('status', 'Brouillon')} |
| **Propriétaire** | {context.get('owner', 'RSSI')} |

---

'''


def generate_preamble(context: Dict[str, Any]) -> str:
    """Generate the preamble section (Objet, Positionnement, Périmètre, Validité)."""
    return f'''## Préambule

### Objet
{context.get('object', 'Ce document définit les règles de sécurité applicables.')}

### Positionnement documentaire
Ce document fait partie du référentiel de sécurité de **{context.get('organization', 'l\'organisation')}**.

**Niveau documentaire** : {context.get('level', 'Niveau 2 - Directive Stratégique')}

**Documents parents** :
{context.get('parent_docs', '- Politique de Sécurité de l\'Information (POL-001)')}

**Documents enfants** :
{context.get('child_docs', '- Procédures opérationnelles associées')}

### Périmètre d'application
{context.get('scope', 'Ce document s\'applique à l\'ensemble des collaborateurs et des systèmes d\'information.')}

### Validité et révision

| | |
|---|---|
| **Date de prise d'effet** | {context.get('effective_date', datetime.now().strftime('%d/%m/%Y'))} |
| **Date de prochaine révision** | {context.get('review_date', (datetime.now().replace(year=datetime.now().year + 1)).strftime('%d/%m/%Y'))} |
| **Fréquence de révision** | {context.get('review_frequency', 'Annuelle')} |

---

'''


def generate_glossary(terms: List[Dict[str, str]]) -> str:
    """Generate a glossary section."""
    if not terms:
        terms = [
            {"term": "SI", "definition": "Système d'Information"},
            {"term": "SMSI", "definition": "Système de Management de la Sécurité de l'Information"},
            {"term": "RSSI", "definition": "Responsable de la Sécurité des Systèmes d'Information"},
            {"term": "DICP", "definition": "Disponibilité, Intégrité, Confidentialité, Preuve"},
        ]

    glossary = "## Glossaire\n\n| Terme | Définition |\n|-------|------------|\n"
    for item in terms:
        glossary += f"| {item['term']} | {item['definition']} |\n"
    glossary += "\n---\n\n"
    return glossary


def generate_approval_block(context: Dict[str, Any]) -> str:
    """Generate the approval and history block."""
    return f'''---

## Approbation

| Rôle | Nom | Fonction | Date | Signature |
|------|-----|----------|------|-----------|
| Rédaction | {context.get('author', '[À compléter]')} | {context.get('author_role', 'RSSI')} | {context.get('date', datetime.now().strftime('%d/%m/%Y'))} | |
| Vérification | | DSI | | |
| Approbation | | Direction Générale | | |

---

## Historique des versions

| Version | Date | Auteur | Description des modifications |
|---------|------|--------|-------------------------------|
| 1.0 | {context.get('date', datetime.now().strftime('%d/%m/%Y'))} | {context.get('author', '[À compléter]')} | Création initiale |

---

*Fin du document*
'''


# =============================================================================
# PSSIG TEMPLATES - Niveau 2 Directives Stratégiques
# =============================================================================

PSSIG_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # DIRSTRAT-001 - Organisation de la Sécurité de l'Information
    # =========================================================================
    "DIRSTRAT-001": {
        "code": "DIRSTRAT-001",
        "name": "Directive Stratégique - Organisation de la Sécurité de l'Information",
        "short_name": "Organisation Sécurité",
        "type": "DIRECTIVE",
        "level": "Niveau 2 - Directive Stratégique",
        "frameworks": ["ISO27001", "NIS2", "DORA"],
        "iso_domain": "A.5 - Politiques de sécurité de l'information",
        "content": '''# Directive Stratégique - Organisation de la Sécurité de l'Information

{{COVER_PAGE}}

## Table des matières
1. [Préambule](#préambule)
2. [Glossaire](#glossaire)
3. [Gouvernance de la sécurité](#gouvernance)
4. [Rôles et responsabilités](#rôles)
5. [Comités de sécurité](#comités)
6. [Règles de sécurité](#règles)
7. [Approbation](#approbation)

{{PREAMBLE}}

{{GLOSSARY}}

## 1. Gouvernance de la Sécurité {#gouvernance}

### 1.1 Principes de gouvernance

**{{ORGANISATION}}** s'engage à mettre en place une gouvernance de la sécurité de l'information efficace, basée sur :

- **L'engagement de la direction** : Soutien actif et allocation des ressources
- **L'approche par les risques** : Priorisation des actions selon les enjeux
- **L'amélioration continue** : Cycle PDCA (Plan-Do-Check-Act)
- **La conformité réglementaire** : Respect des obligations légales

### 1.2 Périmètre du SMSI

Le Système de Management de la Sécurité de l'Information couvre :
- L'ensemble des systèmes d'information
- Les processus métier critiques
- Les données sensibles de l'organisation
- Les relations avec les tiers

---

## 2. Rôles et Responsabilités {#rôles}

### 2.1 Direction Générale

| Responsabilité | Description |
|----------------|-------------|
| Engagement | Approuve la politique de sécurité et alloue les ressources |
| Gouvernance | Définit les orientations stratégiques |
| Nomination | Désigne le RSSI avec l'autorité nécessaire |
| Revue | Participe à la revue de direction annuelle |

### 2.2 RSSI (Responsable de la Sécurité des SI)

| Responsabilité | Description |
|----------------|-------------|
| Pilotage | Coordonne la mise en œuvre du SMSI |
| Conseil | Conseille la direction sur les risques |
| Veille | Assure la veille sécuritaire et réglementaire |
| Incidents | Gère les incidents de sécurité majeurs |
| Reporting | Rapporte sur l'état de la sécurité |

### 2.3 Propriétaires d'actifs

| Responsabilité | Description |
|----------------|-------------|
| Classification | Classifient les actifs de leur périmètre |
| Risques | Valident les analyses de risques |
| Accès | Autorisent les accès aux ressources |
| Conformité | Vérifient la conformité de leur périmètre |

### 2.4 Collaborateurs

| Responsabilité | Description |
|----------------|-------------|
| Conformité | Respectent les règles de sécurité |
| Vigilance | Signalent les incidents et anomalies |
| Formation | Participent aux sensibilisations |

---

## 3. Comités de Sécurité {#comités}

### 3.1 Comité de Direction Sécurité (CODIR Sécurité)

| Caractéristique | Description |
|-----------------|-------------|
| **Fréquence** | Trimestrielle |
| **Participants** | DG, DSI, RSSI, Directeurs métiers |
| **Objectifs** | Orientations stratégiques, arbitrages budgétaires |
| **Livrables** | Compte-rendu, plan d'actions |

### 3.2 Comité Opérationnel de Sécurité

| Caractéristique | Description |
|-----------------|-------------|
| **Fréquence** | Mensuelle |
| **Participants** | RSSI, équipes IT, correspondants sécurité |
| **Objectifs** | Suivi opérationnel, gestion des risques |
| **Livrables** | Tableau de bord, incidents en cours |

### 3.3 Revue de Direction

| Caractéristique | Description |
|-----------------|-------------|
| **Fréquence** | Annuelle |
| **Participants** | Direction Générale, RSSI |
| **Objectifs** | Évaluation du SMSI, amélioration continue |
| **Livrables** | Rapport de revue, axes d'amélioration |

---

## 4. Règles de Sécurité {#règles}

### RSO-001 : Engagement de la direction
> La Direction Générale doit formellement approuver et communiquer son engagement envers la sécurité de l'information.

### RSO-002 : Nomination du RSSI
> Un RSSI doit être nommé avec une lettre de mission définissant ses responsabilités et son autorité.

### RSO-003 : Comités de sécurité
> Les comités de sécurité doivent se réunir selon les fréquences définies et produire des comptes-rendus.

### RSO-004 : Revue de direction
> Une revue de direction du SMSI doit être réalisée au minimum annuellement.

### RSO-005 : Séparation des tâches
> Les rôles incompatibles doivent être séparés (développement/production, validation/exécution).

### RSO-006 : Correspondants sécurité
> Chaque direction métier doit désigner un correspondant sécurité.

### RSO-007 : Sensibilisation
> L'ensemble des collaborateurs doit suivre une sensibilisation sécurité annuelle.

### RSO-008 : Documentation
> Le référentiel documentaire de sécurité doit être maintenu à jour et accessible.

---

{{APPROVAL}}
''',
        "variables": ["ORGANISATION", "COVER_PAGE", "PREAMBLE", "GLOSSARY", "APPROVAL"],
        "glossary_terms": [
            {"term": "SMSI", "definition": "Système de Management de la Sécurité de l'Information"},
            {"term": "RSSI", "definition": "Responsable de la Sécurité des Systèmes d'Information"},
            {"term": "CODIR", "definition": "Comité de Direction"},
            {"term": "PDCA", "definition": "Plan-Do-Check-Act - Cycle d'amélioration continue"},
        ]
    },

    # =========================================================================
    # DIRSTRAT-002 - Contrôle des Accès
    # =========================================================================
    "DIRSTRAT-002": {
        "code": "DIRSTRAT-002",
        "name": "Directive Stratégique - Contrôle d'Accès",
        "short_name": "Contrôle d'Accès",
        "type": "DIRECTIVE",
        "level": "Niveau 2 - Directive Stratégique",
        "frameworks": ["ISO27001", "PCI-DSS", "DORA"],
        "iso_domain": "A.9 - Contrôle d'accès",
        "content": '''# Directive Stratégique - Contrôle d'Accès

{{COVER_PAGE}}

## Table des matières
1. [Préambule](#préambule)
2. [Glossaire](#glossaire)
3. [Principes généraux](#principes)
4. [Gestion des identités](#identités)
5. [Authentification](#authentification)
6. [Gestion des accès privilégiés](#privilégiés)
7. [Règles de sécurité](#règles)
8. [Approbation](#approbation)

{{PREAMBLE}}

{{GLOSSARY}}

## 1. Principes Généraux {#principes}

### 1.1 Moindre privilège
Chaque utilisateur dispose uniquement des droits strictement nécessaires à l'exercice de ses fonctions.

### 1.2 Besoin d'en connaître
L'accès aux informations est accordé uniquement aux personnes ayant un besoin légitime.

### 1.3 Séparation des tâches
Les fonctions sensibles sont réparties entre plusieurs personnes pour éviter les conflits d'intérêts.

### 1.4 Traçabilité
Toutes les actions d'accès sont journalisées et conservées.

---

## 2. Gestion des Identités {#identités}

### 2.1 Cycle de vie des comptes

| Phase | Processus | Délai |
|-------|-----------|-------|
| **Création** | Demande formalisée + validation manager + propriétaire | J+2 max |
| **Modification** | Demande de changement de droits | J+1 max |
| **Désactivation** | Départ collaborateur | Immédiat |
| **Suppression** | Après période de rétention | J+30 |

### 2.2 Revue des accès

| Type d'accès | Fréquence | Responsable |
|--------------|-----------|-------------|
| Comptes utilisateurs | Annuelle | Managers |
| Comptes privilégiés | Trimestrielle | RSSI |
| Comptes de service | Semestrielle | DSI |
| Accès applications critiques | Semestrielle | Propriétaires |

---

## 3. Authentification {#authentification}

### 3.1 Politique de mots de passe

| Critère | Niveau Standard (N1) | Niveau Renforcé (N2) | Niveau Critique (N3) |
|---------|---------------------|---------------------|---------------------|
| Longueur minimale | 10 caractères | 12 caractères | 14 caractères |
| Complexité | 3 types sur 4 | 4 types sur 4 | 4 types + phrase |
| Renouvellement | 180 jours | 90 jours | 60 jours |
| Historique | 6 derniers | 12 derniers | 24 derniers |
| Verrouillage | 5 échecs | 3 échecs | 3 échecs |

### 3.2 Authentification Multi-Facteurs (MFA)

Le MFA est **obligatoire** pour :
- Tous les accès administrateurs
- Accès distant (VPN, portail)
- Applications de niveau N2 et N3
- Accès aux consoles cloud
- Accès aux outils de sécurité

---

## 4. Gestion des Accès Privilégiés {#privilégiés}

### 4.1 Définition
Sont considérés comme privilégiés :
- Administrateurs système et réseau
- Administrateurs d'applications
- Comptes de service avec droits élevés
- Accès root/admin aux équipements

### 4.2 Mesures de protection

| Mesure | Description |
|--------|-------------|
| **Inventaire** | Tous les comptes privilégiés sont inventoriés |
| **Coffre-fort** | Mots de passe stockés dans un PAM |
| **Session** | Enregistrement des sessions privilégiées |
| **Rotation** | Rotation automatique des secrets |
| **Justification** | Chaque accès doit être justifié |

---

## 5. Règles de Sécurité {#règles}

### RCA-001 : Principe du moindre privilège
> Les droits d'accès doivent être accordés selon le principe du moindre privilège et du besoin d'en connaître.

### RCA-002 : Unicité des comptes
> Chaque utilisateur doit disposer d'un compte nominatif unique. Les comptes génériques sont interdits sauf exception documentée.

### RCA-003 : Authentification forte
> L'authentification multi-facteurs est obligatoire pour tous les accès sensibles (niveau N2/N3, accès distant, privilégiés).

### RCA-004 : Politique de mots de passe
> Les mots de passe doivent respecter les critères de complexité définis selon le niveau de sécurité.

### RCA-005 : Gestion des comptes privilégiés
> Les comptes privilégiés doivent être gérés via une solution PAM avec enregistrement des sessions.

### RCA-006 : Revue des accès
> Une revue des droits d'accès doit être réalisée selon les fréquences définies par type d'accès.

### RCA-007 : Désactivation au départ
> Les comptes doivent être désactivés immédiatement lors du départ d'un collaborateur.

### RCA-008 : Accès distant
> Tout accès distant doit transiter par une solution VPN avec authentification forte.

### RCA-009 : Séparation des environnements
> Les accès de développement et de production doivent être séparés.

### RCA-010 : Journalisation
> Toutes les tentatives d'accès (réussies et échouées) doivent être journalisées et conservées 12 mois minimum.

---

{{APPROVAL}}
''',
        "variables": ["ORGANISATION", "COVER_PAGE", "PREAMBLE", "GLOSSARY", "APPROVAL"],
        "glossary_terms": [
            {"term": "MFA", "definition": "Multi-Factor Authentication - Authentification multi-facteurs"},
            {"term": "PAM", "definition": "Privileged Access Management - Gestion des accès privilégiés"},
            {"term": "VPN", "definition": "Virtual Private Network - Réseau privé virtuel"},
            {"term": "SSO", "definition": "Single Sign-On - Authentification unique"},
            {"term": "IAM", "definition": "Identity and Access Management - Gestion des identités et accès"},
        ]
    },

    # =========================================================================
    # DIRSTRAT-003 - Gestion des Incidents
    # =========================================================================
    "DIRSTRAT-003": {
        "code": "DIRSTRAT-003",
        "name": "Directive Stratégique - Gestion des Incidents de Sécurité",
        "short_name": "Gestion Incidents",
        "type": "DIRECTIVE",
        "level": "Niveau 2 - Directive Stratégique",
        "frameworks": ["ISO27001", "NIS2", "DORA", "RGPD"],
        "iso_domain": "A.16 - Gestion des incidents liés à la sécurité",
        "content": '''# Directive Stratégique - Gestion des Incidents de Sécurité

{{COVER_PAGE}}

## Table des matières
1. [Préambule](#préambule)
2. [Glossaire](#glossaire)
3. [Classification des incidents](#classification)
4. [Processus de gestion](#processus)
5. [Escalade et notification](#escalade)
6. [Règles de sécurité](#règles)
7. [Approbation](#approbation)

{{PREAMBLE}}

{{GLOSSARY}}

## 1. Classification des Incidents {#classification}

### 1.1 Définitions

| Terme | Définition |
|-------|------------|
| **Événement** | Occurrence observable sur un système d'information |
| **Alerte** | Signal indiquant un incident potentiel |
| **Incident** | Événement compromettant la sécurité de l'information |
| **Crise** | Incident majeur nécessitant une gestion de crise |

### 1.2 Niveaux de sévérité

| Niveau | Sévérité | Impact | Exemples | SLA Réponse |
|--------|----------|--------|----------|-------------|
| **P1** | Critique | Arrêt activité / Fuite massive | Ransomware, APT, fuite données N3 | < 1 heure |
| **P2** | Haute | Dégradation majeure | Intrusion, DDoS, compromission compte privilégié | < 4 heures |
| **P3** | Moyenne | Impact limité | Malware isolé, phishing réussi, vol laptop | < 24 heures |
| **P4** | Basse | Impact minimal | Tentative bloquée, spam, alerte faux positif | < 72 heures |

---

## 2. Processus de Gestion {#processus}

### 2.1 Phase 1 - Détection

**Sources de détection :**
- SIEM (Security Information and Event Management)
- EDR (Endpoint Detection and Response)
- Signalements utilisateurs
- Alertes partenaires/CERT
- Veille threat intelligence

**Point de contact :** {{SECURITY_EMAIL}}

### 2.2 Phase 2 - Qualification

1. Réception et enregistrement de l'alerte
2. Analyse préliminaire et collecte d'informations
3. Classification de l'incident (P1-P4)
4. Création du ticket incident
5. Notification selon niveau

### 2.3 Phase 3 - Confinement

**Actions immédiates :**
- Isolation des systèmes compromis
- Préservation des preuves (forensics)
- Blocage des vecteurs d'attaque
- Communication interne

### 2.4 Phase 4 - Éradication

- Identification de la cause racine
- Suppression de la menace
- Correction des vulnérabilités exploitées
- Renforcement des mesures de protection

### 2.5 Phase 5 - Récupération

- Restauration des systèmes
- Vérification de l'intégrité
- Tests de bon fonctionnement
- Reprise progressive des activités

### 2.6 Phase 6 - Post-incident

- Documentation complète de l'incident
- Retour d'expérience (RETEX)
- Identification des axes d'amélioration
- Mise à jour des procédures

---

## 3. Escalade et Notification {#escalade}

### 3.1 Matrice d'escalade

| Niveau | Escalade interne | Délai |
|--------|------------------|-------|
| **P1** | DG + RSSI + Cellule de crise | Immédiat |
| **P2** | RSSI + DSI | < 2 heures |
| **P3** | Équipe sécurité | < 8 heures |
| **P4** | Support IT | Best effort |

### 3.2 Notifications externes obligatoires

#### RGPD (violation données personnelles)
| Action | Délai | Destinataire |
|--------|-------|--------------|
| Notification CNIL | 72 heures | Autorité de contrôle |
| Notification personnes | Sans délai si risque élevé | Personnes concernées |

#### NIS2 / DORA (entités essentielles/financières)
| Action | Délai | Destinataire |
|--------|-------|--------------|
| Alerte préliminaire | 24 heures | CSIRT national / Autorité |
| Notification complète | 72 heures | Autorité de régulation |
| Rapport final | 1 mois | Autorité de régulation |

---

## 4. Règles de Sécurité {#règles}

### RGI-001 : Signalement obligatoire
> Tout incident ou suspicion d'incident de sécurité doit être signalé immédiatement au point de contact sécurité.

### RGI-002 : Classification des incidents
> Chaque incident doit être classifié selon les niveaux de sévérité P1 à P4.

### RGI-003 : Délais de réponse
> Les délais de réponse définis par niveau de sévérité doivent être respectés.

### RGI-004 : Préservation des preuves
> Les preuves numériques doivent être préservées pour permettre une analyse forensique.

### RGI-005 : Cellule de crise
> Une cellule de crise doit être activée pour tout incident P1.

### RGI-006 : Notification CNIL
> Toute violation de données personnelles doit être notifiée à la CNIL sous 72 heures.

### RGI-007 : Documentation
> Chaque incident doit être documenté de manière exhaustive (chronologie, actions, impacts).

### RGI-008 : Retour d'expérience
> Un RETEX doit être réalisé pour tout incident P1/P2 dans les 15 jours suivant la clôture.

### RGI-009 : Communication
> La communication externe relative aux incidents est exclusivement gérée par la Direction Communication en coordination avec le RSSI.

### RGI-010 : Tests et exercices
> Des exercices de gestion d'incidents doivent être réalisés au minimum annuellement.

---

{{APPROVAL}}
''',
        "variables": ["ORGANISATION", "COVER_PAGE", "PREAMBLE", "GLOSSARY", "APPROVAL", "SECURITY_EMAIL"],
        "glossary_terms": [
            {"term": "SIEM", "definition": "Security Information and Event Management"},
            {"term": "EDR", "definition": "Endpoint Detection and Response"},
            {"term": "SOC", "definition": "Security Operations Center"},
            {"term": "CERT/CSIRT", "definition": "Computer Emergency Response Team"},
            {"term": "APT", "definition": "Advanced Persistent Threat - Menace persistante avancée"},
            {"term": "RETEX", "definition": "Retour d'expérience"},
            {"term": "DDoS", "definition": "Distributed Denial of Service"},
        ]
    },

    # =========================================================================
    # DIRSTRAT-004 - Cryptographie
    # =========================================================================
    "DIRSTRAT-004": {
        "code": "DIRSTRAT-004",
        "name": "Directive Stratégique - Cryptographie",
        "short_name": "Cryptographie",
        "type": "DIRECTIVE",
        "level": "Niveau 2 - Directive Stratégique",
        "frameworks": ["ISO27001", "PCI-DSS", "DORA"],
        "iso_domain": "A.10 - Cryptographie",
        "content": '''# Directive Stratégique - Cryptographie

{{COVER_PAGE}}

## Table des matières
1. [Préambule](#préambule)
2. [Glossaire](#glossaire)
3. [Principes cryptographiques](#principes)
4. [Standards de chiffrement](#standards)
5. [Gestion des clés](#clés)
6. [Règles de sécurité](#règles)
7. [Approbation](#approbation)

{{PREAMBLE}}

{{GLOSSARY}}

## 1. Principes Cryptographiques {#principes}

### 1.1 Objectifs
La cryptographie est utilisée pour assurer :
- **Confidentialité** : Protection contre la divulgation non autorisée
- **Intégrité** : Détection des modifications non autorisées
- **Authenticité** : Garantie de l'origine des données
- **Non-répudiation** : Preuve d'envoi et de réception

### 1.2 Cas d'usage obligatoires

| Cas d'usage | Chiffrement | Justification |
|-------------|-------------|---------------|
| Données au repos N2/N3 | AES-256 | Protection stockage |
| Flux réseau externes | TLS 1.2+ | Confidentialité transit |
| Emails sensibles | S/MIME ou PGP | Protection communications |
| Sauvegardes | AES-256 | Protection copies |
| Mots de passe | Bcrypt/Argon2 | Protection authentifiants |

---

## 2. Standards de Chiffrement {#standards}

### 2.1 Algorithmes autorisés

| Usage | Algorithme recommandé | Algorithmes acceptés | Interdits |
|-------|----------------------|---------------------|-----------|
| **Chiffrement symétrique** | AES-256-GCM | AES-128-GCM, ChaCha20 | DES, 3DES, RC4, Blowfish |
| **Chiffrement asymétrique** | RSA-4096 | RSA-2048, ECDSA-384 | RSA < 2048 |
| **Hachage** | SHA-256 | SHA-384, SHA-512 | MD5, SHA-1 |
| **MAC** | HMAC-SHA256 | HMAC-SHA384 | HMAC-MD5 |
| **Échange de clés** | ECDHE | DHE-2048+ | DH < 2048 |

### 2.2 Protocoles

| Protocole | Version minimale | Recommandation |
|-----------|------------------|----------------|
| **TLS** | 1.2 | TLS 1.3 |
| **SSH** | 2.0 | OpenSSH récent |
| **IPsec** | IKEv2 | Suite B |

---

## 3. Gestion des Clés {#clés}

### 3.1 Cycle de vie des clés

| Phase | Description | Responsable |
|-------|-------------|-------------|
| **Génération** | Utilisation de générateurs cryptographiques sûrs | Équipe sécurité |
| **Distribution** | Transmission sécurisée aux utilisateurs | Gestionnaire de clés |
| **Stockage** | HSM ou coffre-fort logiciel certifié | Infrastructure |
| **Utilisation** | Accès restreint et journalisé | Utilisateurs autorisés |
| **Rotation** | Selon fréquence définie | Automatisée |
| **Révocation** | En cas de compromission suspectée | RSSI |
| **Archivage** | Conservation sécurisée pour déchiffrement | Archives |
| **Destruction** | Effacement sécurisé | Équipe sécurité |

### 3.2 Périodes de rotation

| Type de clé | Fréquence de rotation |
|-------------|----------------------|
| Clés de chiffrement données | Annuelle |
| Certificats serveurs | 1 à 2 ans |
| Clés de signature | 2 à 3 ans |
| Clés racines CA | 10 ans |

### 3.3 Séquestre et récupération

- Les clés de chiffrement de données doivent être séquestrées
- Procédure de récupération documentée et testée
- Double contrôle pour l'accès aux clés séquestrées

---

## 4. Règles de Sécurité {#règles}

### RCR-001 : Chiffrement des données sensibles
> Les données de niveau N2 et N3 doivent être chiffrées au repos et en transit.

### RCR-002 : Algorithmes approuvés
> Seuls les algorithmes de chiffrement approuvés dans cette directive peuvent être utilisés.

### RCR-003 : Longueur des clés
> Les longueurs de clés minimales définies doivent être respectées (AES-128 minimum, RSA-2048 minimum).

### RCR-004 : Protocoles de transport
> TLS 1.2 est le minimum requis. TLS 1.3 est recommandé.

### RCR-005 : Stockage des clés
> Les clés cryptographiques doivent être stockées dans un HSM ou un coffre-fort certifié.

### RCR-006 : Rotation des clés
> Les clés doivent être renouvelées selon les fréquences définies.

### RCR-007 : Séquestre des clés
> Les clés de chiffrement de données critiques doivent être séquestrées.

### RCR-008 : Certificats
> Les certificats SSL/TLS doivent être émis par une autorité reconnue et renouvelés avant expiration.

### RCR-009 : Chiffrement des sauvegardes
> Toutes les sauvegardes de données sensibles doivent être chiffrées.

### RCR-010 : Interdiction d'algorithmes faibles
> L'utilisation de MD5, SHA-1, DES, 3DES, RC4 et RSA < 2048 bits est strictement interdite.

---

{{APPROVAL}}
''',
        "variables": ["ORGANISATION", "COVER_PAGE", "PREAMBLE", "GLOSSARY", "APPROVAL"],
        "glossary_terms": [
            {"term": "AES", "definition": "Advanced Encryption Standard"},
            {"term": "RSA", "definition": "Rivest-Shamir-Adleman - Algorithme de chiffrement asymétrique"},
            {"term": "TLS", "definition": "Transport Layer Security"},
            {"term": "HSM", "definition": "Hardware Security Module - Module matériel de sécurité"},
            {"term": "PKI", "definition": "Public Key Infrastructure - Infrastructure à clés publiques"},
            {"term": "CA", "definition": "Certificate Authority - Autorité de certification"},
        ]
    },

    # =========================================================================
    # DIRSTRAT-005 - Continuité d'Activité
    # =========================================================================
    "DIRSTRAT-005": {
        "code": "DIRSTRAT-005",
        "name": "Directive Stratégique - Continuité d'Activité",
        "short_name": "Continuité Activité",
        "type": "DIRECTIVE",
        "level": "Niveau 2 - Directive Stratégique",
        "frameworks": ["ISO27001", "DORA", "NIS2"],
        "iso_domain": "A.17 - Aspects de la sécurité dans la gestion de la continuité",
        "content": '''# Directive Stratégique - Continuité d'Activité

{{COVER_PAGE}}

## Table des matières
1. [Préambule](#préambule)
2. [Glossaire](#glossaire)
3. [Gouvernance de la continuité](#gouvernance)
4. [Analyse d'impact (BIA)](#bia)
5. [Stratégie de continuité](#stratégie)
6. [Règles de sécurité](#règles)
7. [Approbation](#approbation)

{{PREAMBLE}}

{{GLOSSARY}}

## 1. Gouvernance de la Continuité {#gouvernance}

### 1.1 Objectifs
Garantir la capacité de **{{ORGANISATION}}** à :
- Maintenir ses activités critiques en cas de sinistre
- Reprendre ses opérations dans les délais acceptables
- Minimiser les impacts financiers et réputationnels

### 1.2 Responsabilités

| Rôle | Responsabilité |
|------|----------------|
| Direction Générale | Valide la stratégie et les budgets |
| RSSI | Coordonne le programme de continuité |
| Responsables métiers | Définissent les besoins et participent aux tests |
| DSI | Met en œuvre les solutions techniques |

---

## 2. Analyse d'Impact (BIA) {#bia}

### 2.1 Critères d'évaluation

| Critère | Description |
|---------|-------------|
| **RTO** (Recovery Time Objective) | Durée maximale d'interruption acceptable |
| **RPO** (Recovery Point Objective) | Perte de données maximale acceptable |
| **MTPD** (Maximum Tolerable Period of Disruption) | Durée maximale avant impacts irréversibles |

### 2.2 Classification des processus

| Catégorie | RTO | RPO | Exemples |
|-----------|-----|-----|----------|
| **Critique** | < 4h | < 1h | Paiements, production |
| **Essentiel** | < 24h | < 4h | Messagerie, ERP |
| **Important** | < 72h | < 24h | RH, comptabilité |
| **Normal** | < 1 semaine | < 48h | Archivage, reporting |

---

## 3. Stratégie de Continuité {#stratégie}

### 3.1 Plan de Continuité d'Activité (PCA)

**Composantes :**
- Activation et gouvernance de crise
- Procédures de continuité métier
- Ressources humaines et logistiques
- Communication de crise

### 3.2 Plan de Reprise d'Activité (PRA)

**Infrastructures de secours :**

| Type | Description | RTO cible |
|------|-------------|-----------|
| **Site de secours actif/actif** | Réplication temps réel | < 15 min |
| **Site de secours actif/passif** | Basculement manuel | < 4h |
| **Cloud DR** | Reconstruction cloud | < 24h |
| **Sauvegarde externe** | Restauration depuis backup | > 24h |

### 3.3 Tests et exercices

| Type de test | Fréquence | Scope |
|--------------|-----------|-------|
| Test technique (backup/restore) | Trimestriel | Infrastructure |
| Test de basculement | Semestriel | Applications critiques |
| Exercice de crise | Annuel | Organisation complète |

---

## 4. Règles de Sécurité {#règles}

### RCA-001 : Analyse d'impact
> Une analyse d'impact sur l'activité (BIA) doit être réalisée et maintenue à jour annuellement.

### RCA-002 : Classification des processus
> Chaque processus métier doit être classifié selon sa criticité avec RTO/RPO définis.

### RCA-003 : PCA/PRA documentés
> Des plans de continuité (PCA) et de reprise (PRA) doivent être formalisés et validés.

### RCA-004 : Site de secours
> Les systèmes critiques doivent disposer d'une solution de reprise adaptée au RTO requis.

### RCA-005 : Sauvegardes
> Les sauvegardes doivent être conformes aux RPO définis et testées régulièrement.

### RCA-006 : Tests réguliers
> Des tests de continuité doivent être réalisés selon les fréquences définies.

### RCA-007 : Mise à jour des plans
> Les plans PCA/PRA doivent être revus après chaque changement majeur ou exercice.

### RCA-008 : Cellule de crise
> Une cellule de crise doit être constituée avec des suppléants identifiés.

### RCA-009 : Communication de crise
> Un plan de communication de crise doit être préparé et testé.

### RCA-010 : Contrats fournisseurs
> Les contrats avec les fournisseurs critiques doivent inclure des SLA de continuité.

---

{{APPROVAL}}
''',
        "variables": ["ORGANISATION", "COVER_PAGE", "PREAMBLE", "GLOSSARY", "APPROVAL"],
        "glossary_terms": [
            {"term": "BIA", "definition": "Business Impact Analysis - Analyse d'impact sur l'activité"},
            {"term": "PCA", "definition": "Plan de Continuité d'Activité"},
            {"term": "PRA", "definition": "Plan de Reprise d'Activité"},
            {"term": "RTO", "definition": "Recovery Time Objective - Durée maximale d'interruption"},
            {"term": "RPO", "definition": "Recovery Point Objective - Perte de données maximale"},
            {"term": "DRP", "definition": "Disaster Recovery Plan"},
        ]
    },
}


# =============================================================================
# TEMPLATE RENDERING FUNCTIONS
# =============================================================================

def render_pssig_template(
    template_code: str,
    context: Dict[str, Any]
) -> str:
    """Render a PSSIG template with full professional structure."""
    template = PSSIG_TEMPLATES.get(template_code)
    if not template:
        raise ValueError(f"Template {template_code} not found")

    content = template["content"]

    # Prepare context for cover page
    cover_context = {
        "document_title": template["name"],
        "organization": context.get("organization", {}).get("name", "[Organisation]"),
        "code": template["code"],
        "version": context.get("version", "1.0"),
        "classification": context.get("classification", "Interne"),
        "status": context.get("status", "Brouillon"),
        "owner": context.get("owner", "RSSI"),
        "date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Prepare context for preamble
    preamble_context = {
        "organization": cover_context["organization"],
        "object": f"Cette directive définit les règles de sécurité relatives à {template['short_name'].lower()} au sein de {cover_context['organization']}.",
        "level": template["level"],
        "parent_docs": "- Politique de Sécurité de l'Information (POL-001)",
        "child_docs": "- Procédures opérationnelles associées",
        "scope": f"Ce document s'applique à l'ensemble des collaborateurs, prestataires et systèmes d'information de {cover_context['organization']}.",
        "effective_date": datetime.now().strftime("%d/%m/%Y"),
        "review_date": (datetime.now().replace(year=datetime.now().year + 1)).strftime("%d/%m/%Y"),
        "review_frequency": "Annuelle",
    }

    # Prepare context for approval
    approval_context = {
        "author": context.get("author", "[À compléter]"),
        "author_role": context.get("author_role", "RSSI"),
        "date": datetime.now().strftime("%d/%m/%Y"),
    }

    # Generate sections
    cover_page = generate_cover_page(cover_context)
    preamble = generate_preamble(preamble_context)
    glossary = generate_glossary(template.get("glossary_terms", []))
    approval = generate_approval_block(approval_context)

    # Replace placeholders
    content = content.replace("{{COVER_PAGE}}", cover_page)
    content = content.replace("{{PREAMBLE}}", preamble)
    content = content.replace("{{GLOSSARY}}", glossary)
    content = content.replace("{{APPROVAL}}", approval)
    content = content.replace("{{ORGANISATION}}", cover_context["organization"])
    content = content.replace("{{SECURITY_EMAIL}}", context.get("security_email", "security@organisation.fr"))

    return content


def list_pssig_templates() -> List[Dict[str, Any]]:
    """List all available PSSIG templates."""
    return [
        {
            "code": t["code"],
            "name": t["name"],
            "short_name": t["short_name"],
            "type": t["type"],
            "level": t["level"],
            "frameworks": t["frameworks"],
            "iso_domain": t.get("iso_domain", ""),
        }
        for t in PSSIG_TEMPLATES.values()
    ]


def get_pssig_template(code: str) -> Dict[str, Any]:
    """Get a PSSIG template by its code."""
    return PSSIG_TEMPLATES.get(code)
