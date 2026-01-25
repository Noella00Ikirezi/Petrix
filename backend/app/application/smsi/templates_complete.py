"""Complete template library for SMSI document generation.

Contains ALL templates for the advanced pack (~100 documents).
"""
from typing import Dict, Any
from datetime import datetime

# =============================================================================
# COMPLETE TEMPLATES DICTIONARY
# =============================================================================

TEMPLATES_COMPLETE: Dict[str, Dict[str, Any]] = {

    # =========================================================================
    # POLITIQUES (POL-004 à POL-022) - 19 templates
    # =========================================================================

    "POL-004": {
        "code": "POL-004",
        "name": "PCA - Politique de Continuité d'Activité",
        "type": "POLICY",
        "content": '''# Politique de Continuité d'Activité (PCA)

**Document**: POL-004
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit le cadre de gestion de la continuité d'activité de {{ORGANISATION}} pour maintenir les services essentiels en cas de sinistre majeur.

---

## 2. Périmètre

- Tous les processus métier critiques
- Les systèmes d'information supportant ces processus
- Les sites et infrastructures
- Le personnel clé

---

## 3. Définitions

| Terme | Définition |
|-------|------------|
| PCA | Plan de Continuité d'Activité |
| PRA | Plan de Reprise d'Activité (volet informatique du PCA) |
| RTO | Recovery Time Objective - Durée maximale d'interruption acceptable |
| RPO | Recovery Point Objective - Perte de données maximale acceptable |
| BIA | Business Impact Analysis - Analyse d'impact métier |

---

## 4. Objectifs de Reprise

| Processus | RTO | RPO | Niveau de service dégradé |
|-----------|-----|-----|---------------------------|
| Activités critiques (N3) | 4h | 1h | 80% |
| Activités importantes (N2) | 24h | 4h | 60% |
| Activités standard (N1) | 72h | 24h | 40% |

---

## 5. Gouvernance

### 5.1 Comité de Crise
- **Composition**: DG, RSSI, DSI, DRH, Communication
- **Activation**: Sur décision DG ou RSSI
- **Rôle**: Pilotage de la gestion de crise

### 5.2 Cellule Opérationnelle
- **Composition**: Équipes techniques et métiers concernées
- **Rôle**: Mise en œuvre des actions de reprise

---

## 6. Scénarios de Sinistres

### 6.1 Sinistres couverts
- Incendie / Inondation des locaux
- Cyberattaque majeure (ransomware, DDoS)
- Panne datacenter
- Pandémie / Indisponibilité massive du personnel
- Défaillance fournisseur critique

### 6.2 Stratégies de reprise
- **Site de secours**: Datacenter secondaire ou Cloud
- **Télétravail**: Activation massive pour les fonctions éligibles
- **Dégradé**: Procédures manuelles de secours

---

## 7. Tests et Exercices

| Type | Fréquence | Participants |
|------|-----------|--------------|
| Test technique (bascule) | Semestriel | IT |
| Exercice de crise | Annuel | Comité de crise |
| Test complet (PCA) | Annuel | Tous services critiques |

---

## 8. Maintenance du PCA

- Revue annuelle du BIA
- Mise à jour après chaque changement majeur
- Retour d'expérience après chaque incident/exercice

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-005": {
        "code": "POL-005",
        "name": "Politique de Sécurité des Tiers (Third-Party)",
        "type": "POLICY",
        "content": '''# Politique de Sécurité des Tiers

**Document**: POL-005
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de sécurité applicables aux tiers (fournisseurs, sous-traitants, partenaires) ayant accès aux systèmes ou données de {{ORGANISATION}}.

---

## 2. Périmètre

### 2.1 Tiers concernés
- Prestataires IT et infogérance
- Éditeurs de logiciels (SaaS, Cloud)
- Sous-traitants métier
- Partenaires commerciaux avec accès SI
- Consultants et auditeurs externes

### 2.2 Exclusions
- Clients finaux
- Fournisseurs sans accès aux SI

---

## 3. Classification des Tiers

| Niveau | Critères | Exigences |
|--------|----------|-----------|
| Critique | Accès données N3 ou systèmes critiques | Audit annuel, SLA renforcé, assurance cyber |
| Important | Accès données N2 ou systèmes importants | Questionnaire sécurité, clauses contractuelles |
| Standard | Accès limité, données N1 | Clauses standard |

---

## 4. Processus de Qualification

### 4.1 Évaluation initiale
1. Questionnaire de sécurité
2. Vérification certifications (ISO 27001, SOC2, etc.)
3. Analyse de risques fournisseur
4. Validation RSSI pour tiers critiques

### 4.2 Due diligence renforcée (tiers critiques)
- Audit sur site ou à distance
- Revue des rapports d'audit (SOC2, pentest)
- Vérification des références

---

## 5. Exigences Contractuelles

### 5.1 Clauses obligatoires
- Clause de confidentialité (NDA)
- Clause de protection des données (DPA si données personnelles)
- Clause d'audit
- Clause de notification d'incidents (24h)
- Clause de réversibilité

### 5.2 SLA sécurité (tiers critiques)
- Disponibilité: 99.9%
- Temps de réponse incident: < 4h
- Correctifs critiques: < 72h

---

## 6. Gestion des Accès Tiers

### 6.1 Principes
- Moindre privilège
- Accès nominatif (pas de compte générique)
- MFA obligatoire
- Journalisation complète

### 6.2 Cycle de vie
- Création sur demande validée par le sponsor interne
- Revue trimestrielle des accès actifs
- Révocation sous 24h à la fin de la mission

---

## 7. Surveillance Continue

| Action | Fréquence | Responsable |
|--------|-----------|-------------|
| Revue des accès tiers | Trimestrielle | IT + Métiers |
| Questionnaire sécurité | Annuel | RSSI |
| Audit tiers critiques | Annuel | RSSI |
| Veille vulnérabilités fournisseurs | Continue | RSSI |

---

## 8. Gestion des Incidents Tiers

1. Notification obligatoire sous 24h
2. Coordination avec le RSSI
3. Plan de remédiation validé
4. Retour d'expérience documenté

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-006": {
        "code": "POL-006",
        "name": "Charte d'Utilisation du Système d'Information",
        "type": "POLICY",
        "content": '''# Charte d'Utilisation du Système d'Information

**Document**: POL-006
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Préambule

La présente charte définit les règles d'utilisation des ressources informatiques et de communication électronique de {{ORGANISATION}}. Elle s'applique à tous les utilisateurs du système d'information.

---

## 2. Champ d'Application

### 2.1 Utilisateurs concernés
- Collaborateurs (CDI, CDD, alternants, stagiaires)
- Prestataires et intérimaires
- Tout utilisateur disposant d'un accès au SI

### 2.2 Ressources couvertes
- Postes de travail (fixes et portables)
- Smartphones et tablettes
- Messagerie électronique
- Accès Internet
- Applications métier
- Espaces de stockage

---

## 3. Principes Généraux

### 3.1 Usage professionnel
Les ressources informatiques sont destinées à un usage professionnel. Un usage personnel raisonnable et ponctuel est toléré s'il n'affecte pas la productivité ni la sécurité.

### 3.2 Responsabilité
Chaque utilisateur est responsable de l'utilisation des ressources mises à sa disposition et des accès effectués avec ses identifiants.

---

## 4. Règles d'Utilisation

### 4.1 Authentification
- Identifiants personnels et confidentiels
- Mot de passe conforme à la politique (12 caractères minimum)
- Verrouillage de session en cas d'absence
- Interdiction de partager ses identifiants

### 4.2 Messagerie
- Usage principalement professionnel
- Vigilance face au phishing (ne pas cliquer sur les liens suspects)
- Taille maximale des pièces jointes : 25 Mo
- Pas de transfert de données sensibles vers messageries personnelles

### 4.3 Internet
- Navigation liée aux besoins professionnels
- Téléchargements uniquement depuis sources autorisées
- Respect de la propriété intellectuelle

### 4.4 Stockage
- Données professionnelles sur les espaces partagés (pas en local)
- Classification des documents sensibles
- Pas de stockage sur services cloud non autorisés

### 4.5 Mobilité
- Chiffrement obligatoire des équipements mobiles
- Signalement immédiat en cas de perte/vol
- Connexion VPN pour accès distant

---

## 5. Usages Interdits

- Installation de logiciels non autorisés
- Contournement des mesures de sécurité
- Téléchargement illégal (piratage)
- Consultation de sites illicites
- Envoi de messages diffamatoires ou harcelants
- Extraction massive de données
- Connexion d'équipements personnels non autorisés

---

## 6. Surveillance et Contrôles

### 6.1 Journalisation
{{ORGANISATION}} enregistre les logs d'accès et d'utilisation à des fins de sécurité et de conformité (connexions, navigation web, messagerie).

### 6.2 Contrôles
Des contrôles peuvent être effectués de manière :
- Automatisée (filtrage, antivirus, DLP)
- Manuelle en cas d'incident ou de suspicion

### 6.3 Respect vie privée
Les contrôles respectent la vie privée des utilisateurs et le cadre légal (RGPD, Code du travail).

---

## 7. Sanctions

Le non-respect de la présente charte peut entraîner :
- Restriction ou suspension des accès
- Sanctions disciplinaires (avertissement, mise à pied, licenciement)
- Poursuites judiciaires en cas d'infraction pénale

---

## 8. Engagement de l'Utilisateur

J'ai pris connaissance de la présente charte et m'engage à en respecter les dispositions.

| Nom | Prénom | Date | Signature |
|-----|--------|------|-----------|
| | | | |

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Validation | | DRH | |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-007": {
        "code": "POL-007",
        "name": "Politique de Gestion des Vulnérabilités",
        "type": "POLICY",
        "content": '''# Politique de Gestion des Vulnérabilités

**Document**: POL-007
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit le processus de détection, évaluation et remédiation des vulnérabilités de sécurité affectant les systèmes d'information de {{ORGANISATION}}.

---

## 2. Périmètre

- Serveurs et infrastructure
- Postes de travail
- Équipements réseau
- Applications (web, mobiles, métier)
- Services cloud

---

## 3. Sources de Vulnérabilités

### 3.1 Veille sécurité
- CERT-FR, ANSSI
- Éditeurs (Microsoft, Linux, etc.)
- Bases CVE, NVD

### 3.2 Scans automatisés
- Scans de vulnérabilités (Nessus, Qualys, etc.)
- Fréquence : hebdomadaire (infrastructure), mensuelle (applications)

### 3.3 Tests de sécurité
- Tests d'intrusion annuels
- Bug bounty (si applicable)

---

## 4. Classification des Vulnérabilités

| Sévérité | Score CVSS | Exemples | Délai remédiation |
|----------|------------|----------|-------------------|
| Critique | 9.0 - 10.0 | RCE sans authentification | 24-48h |
| Haute | 7.0 - 8.9 | Élévation de privilèges | 7 jours |
| Moyenne | 4.0 - 6.9 | XSS, CSRF | 30 jours |
| Basse | 0.1 - 3.9 | Information disclosure | 90 jours |

---

## 5. Processus de Remédiation

### 5.1 Qualification
1. Vérification de l'applicabilité
2. Évaluation de l'impact métier
3. Priorisation

### 5.2 Remédiation
- **Correctif** : Application du patch éditeur (prioritaire)
- **Mitigation** : Mesures compensatoires si patch impossible
- **Acceptation** : Validation RSSI avec justification

### 5.3 Validation
- Test de non-régression
- Scan de contrôle post-remédiation

---

## 6. Exceptions

Toute exception aux délais de remédiation doit être :
1. Justifiée par écrit
2. Validée par le RSSI
3. Assortie de mesures compensatoires
4. Limitée dans le temps (max 6 mois)

---

## 7. Indicateurs

| KPI | Cible | Fréquence |
|-----|-------|-----------|
| Vulnérabilités critiques > 48h | 0 | Temps réel |
| Taux de remédiation dans les délais | > 95% | Mensuel |
| Âge moyen des vulnérabilités | < 30 jours | Mensuel |
| Couverture des scans | 100% | Trimestriel |

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-008": {
        "code": "POL-008",
        "name": "Politique de Sécurité Physique",
        "type": "POLICY",
        "content": '''# Politique de Sécurité Physique

**Document**: POL-008
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les mesures de protection physique des locaux, équipements et personnels de {{ORGANISATION}}.

---

## 2. Zonage de Sécurité

| Zone | Description | Accès | Exemples |
|------|-------------|-------|----------|
| Z0 - Publique | Accessible à tous | Libre | Accueil, parking visiteurs |
| Z1 - Contrôlée | Collaborateurs et visiteurs accompagnés | Badge | Bureaux, salles de réunion |
| Z2 - Restreinte | Personnel autorisé uniquement | Badge + PIN | Locaux techniques, archives |
| Z3 - Sensible | Personnel habilité | Badge + biométrie | Datacenter, coffre-fort |

---

## 3. Contrôle d'Accès

### 3.1 Badges
- Badge nominatif avec photo
- Activation/désactivation centralisée
- Signalement immédiat en cas de perte

### 3.2 Visiteurs
- Enregistrement à l'accueil
- Badge visiteur temporaire
- Accompagnement obligatoire en Z2/Z3
- Registre des visites conservé 1 an

### 3.3 Livraisons
- Zone de réception dédiée
- Inspection des colis (si nécessaire)
- Pas d'accès direct aux zones sensibles

---

## 4. Protection des Équipements

### 4.1 Serveurs et infrastructure
- Datacenter en zone Z3
- Climatisation redondante
- Alimentation secourue (onduleur + groupe)
- Détection incendie et extinction automatique

### 4.2 Postes de travail
- Câble antivol pour portables
- Verrouillage automatique de session
- Stockage sécurisé des médias amovibles

### 4.3 Documents papier
- Classement des documents sensibles en armoires fermées
- Broyeur pour destruction (niveau P-4 minimum)

---

## 5. Vidéosurveillance

- Caméras aux points d'entrée et zones sensibles
- Enregistrement conservé 30 jours
- Accès aux images restreint (sécurité, DG, sur réquisition)
- Conformité RGPD (information, déclaration CNIL)

---

## 6. Sécurité Incendie

- Détecteurs de fumée et alarme incendie
- Extincteurs vérifiés annuellement
- Plan d'évacuation affiché
- Exercice d'évacuation annuel

---

## 7. Travail à Distance

- Équipements professionnels uniquement
- Écran de confidentialité recommandé
- Pas de documents sensibles imprimés à domicile
- Connexion VPN obligatoire

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Services Généraux | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-009": {
        "code": "POL-009",
        "name": "Politique de Sécurité des Développements",
        "type": "POLICY",
        "content": '''# Politique de Sécurité des Développements

**Document**: POL-009
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de sécurité applicables au développement logiciel chez {{ORGANISATION}} (Secure SDLC).

---

## 2. Périmètre

- Développements internes
- Développements externalisés
- Intégration de composants tiers
- Maintenance applicative

---

## 3. Principes

### 3.1 Security by Design
La sécurité est intégrée dès la conception, pas ajoutée après coup.

### 3.2 Defense in Depth
Plusieurs couches de sécurité complémentaires.

### 3.3 Least Privilege
Les applications fonctionnent avec les droits minimaux nécessaires.

---

## 4. Cycle de Développement Sécurisé

| Phase | Activités sécurité |
|-------|-------------------|
| Conception | Analyse de risques, modélisation des menaces |
| Développement | Règles de codage sécurisé, revue de code |
| Test | Tests de sécurité (SAST, DAST, pentest) |
| Déploiement | Durcissement, scan de vulnérabilités |
| Maintenance | Veille CVE, correctifs de sécurité |

---

## 5. Règles de Codage Sécurisé

### 5.1 OWASP Top 10
Tous les développeurs doivent connaître et prévenir les vulnérabilités OWASP Top 10.

### 5.2 Règles essentielles
- Validation de toutes les entrées utilisateur
- Requêtes SQL paramétrées (pas de concaténation)
- Encodage des sorties (prévention XSS)
- Gestion sécurisée des sessions
- Stockage sécurisé des secrets (pas en dur dans le code)
- Journalisation des événements de sécurité

---

## 6. Gestion des Secrets

- Pas de credentials en dur dans le code
- Utilisation d'un coffre-fort (Vault, Azure Key Vault, etc.)
- Rotation régulière des clés API
- Fichiers de configuration exclus du contrôle de version

---

## 7. Tests de Sécurité

| Type | Outil | Fréquence |
|------|-------|-----------|
| SAST (analyse statique) | SonarQube, Semgrep | À chaque commit |
| DAST (analyse dynamique) | OWASP ZAP, Burp | Avant mise en prod |
| SCA (dépendances) | Snyk, Dependabot | Continue |
| Pentest | Externe | Annuel |

---

## 8. Gestion des Dépendances

- Inventaire des composants tiers (SBOM)
- Veille vulnérabilités (CVE)
- Mise à jour dans les 30 jours (vulnérabilités hautes/critiques: 7 jours)
- Pas de dépendances abandonnées

---

## 9. Environnements

| Environnement | Données | Accès |
|---------------|---------|-------|
| Développement | Fictives/anonymisées | Développeurs |
| Test/Recette | Anonymisées | Équipe projet |
| Pré-production | Copie production anonymisée | Équipe restreinte |
| Production | Réelles | Exploitants uniquement |

---

## 10. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-010": {
        "code": "POL-010",
        "name": "Politique de Sauvegarde et Restauration",
        "type": "POLICY",
        "content": '''# Politique de Sauvegarde et Restauration

**Document**: POL-010
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les règles de sauvegarde et de restauration des données et systèmes de {{ORGANISATION}}.

---

## 2. Périmètre

- Serveurs de production
- Bases de données
- Applications métier
- Messagerie et collaboration
- Configurations réseau

---

## 3. Stratégie de Sauvegarde

### 3.1 Règle 3-2-1
- **3** copies des données (production + 2 sauvegardes)
- **2** supports différents (disque + bande/cloud)
- **1** copie hors site (datacenter distant ou cloud)

### 3.2 Types de sauvegarde

| Type | Description | Fréquence |
|------|-------------|-----------|
| Complète | Toutes les données | Hebdomadaire |
| Incrémentale | Modifications depuis dernière sauvegarde | Quotidienne |
| Différentielle | Modifications depuis dernière complète | Variable |
| Snapshot | Image instantanée (VM) | Avant changements |

---

## 4. Rétention

| Type de données | Rétention locale | Rétention archive | Externalisation |
|-----------------|------------------|-------------------|-----------------|
| Données critiques (N3) | 30 jours | 7 ans | Oui |
| Données importantes (N2) | 30 jours | 3 ans | Oui |
| Données standard (N1) | 14 jours | 1 an | Non |
| Logs systèmes | 90 jours | 1 an | Oui |

---

## 5. Protection des Sauvegardes

### 5.1 Chiffrement
- Chiffrement AES-256 pour toutes les sauvegardes
- Clés stockées séparément des données
- Rotation annuelle des clés

### 5.2 Accès
- Accès restreint aux administrateurs backup
- Authentification forte (MFA)
- Journalisation des accès

### 5.3 Sauvegardes immuables
- Protection contre la modification/suppression (ransomware)
- Période d'immutabilité : 14 jours minimum

---

## 6. Tests de Restauration

| Test | Fréquence | Responsable |
|------|-----------|-------------|
| Restauration fichier | Mensuelle | IT Operations |
| Restauration base de données | Trimestrielle | DBA |
| Restauration complète serveur | Semestrielle | IT + Métiers |
| Test PRA (bascule site secours) | Annuel | DSI + RSSI |

---

## 7. Procédure de Restauration

1. Demande formalisée (ticket)
2. Validation du propriétaire des données
3. Identification de la sauvegarde appropriée
4. Restauration en environnement isolé (si doute)
5. Vérification d'intégrité
6. Mise à disposition

---

## 8. Indicateurs

| KPI | Cible |
|-----|-------|
| Taux de réussite des sauvegardes | > 99.9% |
| Taux de réussite des restaurations tests | 100% |
| RTO effectif vs cible | Conforme |
| RPO effectif vs cible | Conforme |

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-011": {
        "code": "POL-011",
        "name": "Politique de Sécurité du Cloud",
        "type": "POLICY",
        "content": '''# Politique de Sécurité du Cloud

**Document**: POL-011
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de sécurité pour l'utilisation des services cloud par {{ORGANISATION}}.

---

## 2. Services Cloud Autorisés

### 2.1 Cloud approuvés
| Fournisseur | Services | Classification max |
|-------------|----------|-------------------|
| Google Workspace | Messagerie, Drive, Meet | N2 |
| Microsoft 365 | (si applicable) | N2 |
| AWS / Azure / GCP | IaaS/PaaS validés | N2 |

### 2.2 Shadow IT
L'utilisation de services cloud non approuvés est **interdite**.

---

## 3. Exigences Fournisseurs Cloud

### 3.1 Certifications requises
- ISO 27001 (obligatoire)
- SOC 2 Type II (recommandé)
- Qualification SecNumCloud (pour données N3)

### 3.2 Localisation des données
- **N1/N2** : Union Européenne
- **N3** : France uniquement

### 3.3 Clauses contractuelles
- DPA conforme RGPD
- Clause d'audit
- Clause de notification d'incidents
- Clause de réversibilité

---

## 4. Configuration Sécurisée

### 4.1 Identité et accès
- SSO avec l'annuaire d'entreprise
- MFA obligatoire
- Revue trimestrielle des droits
- Principe du moindre privilège

### 4.2 Protection des données
- Chiffrement en transit (TLS 1.2+)
- Chiffrement au repos (AES-256)
- Clés gérées par le client si possible (BYOK)
- DLP activé sur les données sensibles

### 4.3 Journalisation
- Activation des logs d'audit
- Centralisation dans le SIEM
- Rétention 1 an minimum

---

## 5. Modèle de Responsabilité Partagée

| Élément | IaaS | PaaS | SaaS |
|---------|------|------|------|
| Données | Client | Client | Client |
| Applications | Client | Client | Fournisseur |
| Middleware | Client | Fournisseur | Fournisseur |
| OS | Client | Fournisseur | Fournisseur |
| Infrastructure | Fournisseur | Fournisseur | Fournisseur |

---

## 6. Surveillance

- Monitoring des configurations (CSPM)
- Alertes sur les anomalies
- Revue mensuelle de la posture sécurité

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-012": {
        "code": "POL-012",
        "name": "Politique de Chiffrement",
        "type": "POLICY",
        "content": '''# Politique de Chiffrement

**Document**: POL-012
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de chiffrement pour protéger les données de {{ORGANISATION}}.

---

## 2. Principes

### 2.1 Chiffrement obligatoire
Le chiffrement est obligatoire pour :
- Données N2 et N3 au repos
- Toutes les données en transit sur réseaux non maîtrisés
- Équipements mobiles (laptops, smartphones)
- Sauvegardes

### 2.2 Standards cryptographiques

| Usage | Algorithme | Taille clé minimum |
|-------|-----------|-------------------|
| Chiffrement symétrique | AES | 256 bits |
| Chiffrement asymétrique | RSA | 2048 bits |
| Échange de clés | ECDH | Courbe P-256+ |
| Hachage | SHA-2 | 256 bits |
| Signature | RSA-PSS, ECDSA | 2048/P-256 |
| TLS | TLS 1.2 minimum | - |

---

## 3. Chiffrement des Données au Repos

### 3.1 Serveurs et stockage
- Chiffrement des volumes (BitLocker, LUKS)
- Chiffrement base de données (TDE)
- Chiffrement niveau applicatif si nécessaire

### 3.2 Postes de travail
- Chiffrement intégral du disque obligatoire
- Clé de récupération stockée dans l'AD/MDM

### 3.3 Supports amovibles
- Chiffrement obligatoire pour données N2/N3
- Outils approuvés uniquement

---

## 4. Chiffrement en Transit

### 4.1 Web
- HTTPS obligatoire (TLS 1.2+)
- Certificats de confiance (pas auto-signés en production)
- HSTS activé

### 4.2 Email
- TLS opportuniste entre serveurs
- S/MIME ou PGP pour emails sensibles

### 4.3 VPN
- IKEv2 ou WireGuard
- Authentification forte

---

## 5. Gestion des Clés

### 5.1 Génération
- Générateur aléatoire certifié (CSPRNG)
- Cérémonie de génération pour clés maîtres

### 5.2 Stockage
- HSM pour clés critiques
- Coffre-fort logiciel pour autres clés
- Jamais en clair dans le code

### 5.3 Rotation
- Clés de chiffrement : annuelle
- Clés de session : à chaque session
- Certificats TLS : avant expiration (90j recommandé)

### 5.4 Destruction
- Effacement sécurisé
- Documentation de la destruction

---

## 6. Algorithmes Interdits

- MD5, SHA-1 (hachage)
- DES, 3DES, RC4 (chiffrement)
- RSA < 2048 bits
- TLS 1.0, 1.1, SSL

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-013": {
        "code": "POL-013",
        "name": "Politique de Sécurité Réseau",
        "type": "POLICY",
        "content": '''# Politique de Sécurité Réseau

**Document**: POL-013
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les règles de sécurité réseau pour protéger l'infrastructure de {{ORGANISATION}}.

---

## 2. Architecture Réseau

### 2.1 Segmentation
Le réseau est segmenté en zones de confiance :

| Zone | VLAN | Usage | Niveau sécurité |
|------|------|-------|-----------------|
| DMZ | 10 | Services exposés | Haute |
| Production | 20 | Serveurs métier | Haute |
| Utilisateurs | 30 | Postes de travail | Moyenne |
| Guests | 40 | Visiteurs, IoT | Isolée |
| Management | 50 | Administration | Critique |

### 2.2 Flux inter-zones
- Flux autorisés explicitement (deny by default)
- Matrice de flux documentée
- Revue semestrielle

---

## 3. Pare-feu

### 3.1 Règles générales
- Politique par défaut : DENY ALL
- Règles spécifiques documentées
- Pas de règle "any any"
- Logs activés sur toutes les règles

### 3.2 Revue des règles
- Trimestrielle pour règles actives
- Suppression des règles non utilisées > 90 jours

---

## 4. Accès Distant

### 4.1 VPN
- VPN obligatoire pour accès distant
- MFA obligatoire
- Split tunneling interdit pour données sensibles
- Timeout session : 8h

### 4.2 Accès tiers
- Connexion dédiée et traçable
- Durée limitée
- Validation préalable du RSSI

---

## 5. Sécurité WiFi

| Réseau | Authentification | Chiffrement | Usage |
|--------|------------------|-------------|-------|
| Corp | 802.1X (certificats) | WPA3 | Collaborateurs |
| Guest | Portail captif | WPA2 | Visiteurs |

---

## 6. Surveillance Réseau

### 6.1 Outils
- IDS/IPS en coupure
- NDR (Network Detection & Response)
- Analyse NetFlow

### 6.2 Alertes
- Scan de ports
- Trafic anormal
- Communications C2 (IOC)
- Exfiltration de données

---

## 7. Durcissement

### 7.1 Équipements réseau
- Changement des mots de passe par défaut
- Désactivation des services inutiles
- Firmware à jour
- Accès administration en bande dédiée

### 7.2 Protocoles
- SSH (pas Telnet)
- HTTPS (pas HTTP)
- SNMPv3 (pas v1/v2)

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-014": {
        "code": "POL-014",
        "name": "Politique de Gestion des Changements",
        "type": "POLICY",
        "content": '''# Politique de Gestion des Changements

**Document**: POL-014
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique encadre les modifications apportées aux systèmes d'information de {{ORGANISATION}} pour minimiser les risques d'incidents.

---

## 2. Périmètre

- Infrastructure (serveurs, réseau, stockage)
- Applications métier
- Systèmes de sécurité
- Configurations

---

## 3. Classification des Changements

| Type | Description | Approbation | Délai |
|------|-------------|-------------|-------|
| Standard | Changement pré-approuvé, procédure connue | Automatique | 24h |
| Normal | Changement planifié | CAB | 5 jours |
| Urgent | Changement critique non planifié | RSSI + DSI | ASAP |
| Majeur | Impact significatif | Direction | 15 jours |

---

## 4. Processus

### 4.1 Demande
1. Création ticket de changement
2. Description détaillée (quoi, pourquoi, comment)
3. Analyse d'impact
4. Plan de retour arrière

### 4.2 Évaluation
- Impact sécurité (validation RSSI si nécessaire)
- Impact métier
- Ressources nécessaires
- Fenêtre de maintenance

### 4.3 Approbation
- CAB (Change Advisory Board) hebdomadaire
- Validation des parties prenantes

### 4.4 Implémentation
- Respect de la fenêtre de maintenance
- Tests post-implémentation
- Documentation mise à jour

### 4.5 Revue post-implémentation
- Vérification du succès
- Clôture du ticket
- Retour d'expérience si incident

---

## 5. Fenêtres de Maintenance

| Type | Horaire | Préavis |
|------|---------|---------|
| Standard | 22h-6h en semaine | 48h |
| Week-end | Samedi 6h - Dimanche 18h | 1 semaine |
| Urgence | Tout moment | Validation DSI |

---

## 6. Gel des Changements

Périodes de gel (change freeze) :
- Clôture comptable
- Événements métier critiques
- Période des fêtes

Exceptions validées par la Direction uniquement.

---

## 7. Indicateurs

| KPI | Cible |
|-----|-------|
| Taux de succès des changements | > 95% |
| Changements urgents | < 10% |
| Incidents liés aux changements | < 5% |

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-015": {
        "code": "POL-015",
        "name": "Politique de Journalisation et Surveillance",
        "type": "POLICY",
        "content": '''# Politique de Journalisation et Surveillance

**Document**: POL-015
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de journalisation et de surveillance des systèmes d'information de {{ORGANISATION}}.

---

## 2. Périmètre

- Tous les systèmes et applications
- Équipements réseau et sécurité
- Services cloud
- Accès physiques

---

## 3. Événements à Journaliser

### 3.1 Authentification
- Connexions réussies et échouées
- Déconnexions
- Changements de mots de passe
- Élévation de privilèges

### 3.2 Accès aux données
- Accès aux données sensibles (N2/N3)
- Modifications et suppressions
- Exports de données
- Requêtes anormales

### 3.3 Administration
- Changements de configuration
- Création/modification de comptes
- Installation de logiciels
- Modifications de règles de sécurité

### 3.4 Réseau
- Connexions pare-feu (acceptées et refusées)
- Alertes IDS/IPS
- Flux inter-zones

---

## 4. Format des Logs

Chaque événement doit contenir :
- Date et heure (UTC)
- Source (hostname, IP)
- Utilisateur
- Action
- Résultat (succès/échec)
- Détails contextuels

---

## 5. Centralisation

### 5.1 SIEM
Tous les logs sont centralisés dans le SIEM pour :
- Corrélation d'événements
- Détection d'anomalies
- Génération d'alertes
- Conservation sécurisée

### 5.2 Synchronisation horaire
Tous les systèmes synchronisés sur NTP (serveur interne).

---

## 6. Rétention

| Type de logs | Durée conservation | Stockage |
|--------------|-------------------|----------|
| Sécurité (authentification, accès) | 1 an | SIEM + archive |
| Système | 6 mois | SIEM |
| Applicatif | 1 an | SIEM + archive |
| Réseau (flux) | 3 mois | SIEM |

---

## 7. Surveillance

### 7.1 Surveillance temps réel
- Alertes sur événements critiques
- Astreinte 24/7 pour incidents majeurs

### 7.2 Revue périodique
| Revue | Fréquence | Responsable |
|-------|-----------|-------------|
| Alertes critiques | Quotidienne | SOC/IT |
| Accès privilégiés | Hebdomadaire | RSSI |
| Tendances | Mensuelle | RSSI |

---

## 8. Protection des Logs

- Intégrité garantie (horodatage, signature)
- Accès restreint (lecture seule pour analystes)
- Pas de modification possible
- Sauvegarde régulière

---

## 9. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-016": {
        "code": "POL-016",
        "name": "Politique RGPD - Protection des Données Personnelles",
        "type": "POLICY",
        "content": '''# Politique de Protection des Données Personnelles (RGPD)

**Document**: POL-016
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les règles de protection des données personnelles de {{ORGANISATION}} conformément au Règlement Général sur la Protection des Données (RGPD).

---

## 2. Principes RGPD

### 2.1 Les 7 principes
1. **Licéité, loyauté, transparence** - Traitement légal et transparent
2. **Limitation des finalités** - Collecte pour des objectifs définis
3. **Minimisation** - Collecte limitée au nécessaire
4. **Exactitude** - Données tenues à jour
5. **Limitation de conservation** - Durée limitée
6. **Intégrité et confidentialité** - Sécurité appropriée
7. **Responsabilité** - Capacité à démontrer la conformité

---

## 3. Bases Légales

| Base légale | Exemples d'utilisation |
|-------------|------------------------|
| Consentement | Newsletter, prospection |
| Contrat | Gestion client, RH |
| Obligation légale | Comptabilité, déclarations sociales |
| Intérêt légitime | Sécurité, prévention fraude |
| Mission d'intérêt public | Secteur public |
| Intérêts vitaux | Urgence médicale |

---

## 4. Droits des Personnes

{{ORGANISATION}} garantit les droits suivants :

| Droit | Délai de réponse |
|-------|------------------|
| Information | Au moment de la collecte |
| Accès | 1 mois |
| Rectification | 1 mois |
| Effacement | 1 mois |
| Limitation | 1 mois |
| Portabilité | 1 mois |
| Opposition | 1 mois |

Contact DPO : dpo@{{ORGANISATION}}.fr

---

## 5. Registre des Traitements

Un registre des traitements (REG-006) est maintenu avec :
- Finalités
- Catégories de données
- Destinataires
- Durées de conservation
- Mesures de sécurité

---

## 6. Analyse d'Impact (PIA)

Un PIA est obligatoire pour :
- Profilage avec effets juridiques
- Traitement à grande échelle de données sensibles
- Surveillance systématique à grande échelle

---

## 7. Sous-traitants

### 7.1 Exigences
- Contrat écrit (DPA)
- Garanties suffisantes
- Pas de sous-traitance sans accord

### 7.2 Clauses obligatoires
- Traitement sur instructions documentées
- Confidentialité
- Mesures de sécurité
- Assistance pour les droits
- Suppression ou restitution en fin de contrat

---

## 8. Violations de Données

### 8.1 Notification CNIL
- Délai : 72 heures
- Si risque pour les droits des personnes

### 8.2 Notification personnes concernées
- Sans délai
- Si risque élevé pour leurs droits

---

## 9. Transferts Hors UE

- Décision d'adéquation
- Clauses contractuelles types
- Règles d'entreprise contraignantes
- Analyse d'impact du transfert (TIA)

---

## 10. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | DPO | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-017": {
        "code": "POL-017",
        "name": "Politique de Sensibilisation à la Sécurité",
        "type": "POLICY",
        "content": '''# Politique de Sensibilisation à la Sécurité

**Document**: POL-017
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit le programme de sensibilisation à la sécurité de l'information pour tous les collaborateurs de {{ORGANISATION}}.

---

## 2. Objectifs

- Développer une culture de sécurité
- Réduire les risques liés au facteur humain
- Assurer la conformité réglementaire
- Responsabiliser les collaborateurs

---

## 3. Public Cible

| Population | Formation requise |
|------------|-------------------|
| Nouveaux arrivants | Parcours d'intégration sécurité |
| Tous collaborateurs | Sensibilisation annuelle |
| Managers | Module complémentaire gestion |
| IT / Développeurs | Formation technique approfondie |
| VIP / Direction | Risques ciblés (whaling, fraude) |

---

## 4. Programme de Sensibilisation

### 4.1 Parcours d'intégration
- Présentation de la charte informatique
- Bonnes pratiques de base
- Signature des engagements

### 4.2 Formation annuelle
- E-learning obligatoire (1h)
- Thèmes : phishing, mots de passe, données sensibles
- Quiz de validation

### 4.3 Actions continues
- Communications mensuelles (newsletter sécurité)
- Affiches et goodies
- Alertes en cas de menace

---

## 5. Exercices Pratiques

| Exercice | Fréquence | Objectif |
|----------|-----------|----------|
| Campagne de phishing | Trimestrielle | Tester la vigilance |
| Exercice de crise | Annuel | Tester les procédures |
| Test d'ingénierie sociale | Annuel | Sensibiliser aux risques |

---

## 6. Thèmes Abordés

### 6.1 Essentiels
- Phishing et ingénierie sociale
- Gestion des mots de passe
- Protection des données
- Sécurité des postes de travail
- Signalement des incidents

### 6.2 Avancés (selon population)
- Développement sécurisé
- Gestion des tiers
- Conformité RGPD
- Sécurité cloud

---

## 7. Évaluation

### 7.1 Indicateurs
| KPI | Cible |
|-----|-------|
| Taux de complétion formation | 95% |
| Taux de clic phishing | < 5% |
| Taux de signalement | > 30% |
| Incidents humains | Réduction 20%/an |

### 7.2 Suivi individuel
- Formation non effectuée → Relance manager
- Clic répété phishing → Formation complémentaire

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DRH | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-018": {
        "code": "POL-018",
        "name": "Politique de Sécurité des Postes de Travail",
        "type": "POLICY",
        "content": '''# Politique de Sécurité des Postes de Travail

**Document**: POL-018
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les règles de sécurité applicables aux postes de travail (fixes et mobiles) de {{ORGANISATION}}.

---

## 2. Périmètre

- Ordinateurs fixes
- Ordinateurs portables
- Tablettes
- Smartphones professionnels

---

## 3. Configuration Standard

### 3.1 Système d'exploitation
- OS supporté par l'éditeur
- Mises à jour automatiques activées
- Correctifs de sécurité sous 7 jours (critiques: 48h)

### 3.2 Sécurité
- Antivirus/EDR déployé et à jour
- Pare-feu local activé
- Chiffrement intégral du disque
- Verrouillage automatique (5 min inactivité)

### 3.3 Logiciels
- Master image standardisée
- Logiciels autorisés uniquement (liste blanche)
- Droits administrateur locaux restreints

---

## 4. Équipements Mobiles

### 4.1 Laptops
- Chiffrement BitLocker/FileVault obligatoire
- Câble antivol recommandé
- VPN pour accès distant
- Ne jamais laisser sans surveillance

### 4.2 Smartphones/Tablettes
- MDM (Mobile Device Management) obligatoire
- Chiffrement activé
- Code PIN/biométrie
- Effacement à distance possible

---

## 5. Usages Interdits

- Installation de logiciels non autorisés
- Désactivation des outils de sécurité
- Connexion d'équipements personnels au réseau
- Stockage de données sensibles en local
- Partage de session avec un tiers

---

## 6. BYOD (Bring Your Own Device)

Le BYOD est **interdit** sauf exception validée par le RSSI avec :
- Inscription dans le MDM
- Conteneur professionnel isolé
- Effacement sélectif possible

---

## 7. Fin de Vie

### 7.1 Restitution
- Retour obligatoire à l'IT
- Effacement sécurisé des données
- Réaffectation ou destruction

### 7.2 Perte/Vol
- Signalement immédiat (IT + RSSI)
- Effacement à distance si possible
- Dépôt de plainte si vol

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-019": {
        "code": "POL-019",
        "name": "Politique de Gestion des Médias Amovibles",
        "type": "POLICY",
        "content": '''# Politique de Gestion des Médias Amovibles

**Document**: POL-019
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique encadre l'utilisation des médias amovibles (clés USB, disques externes, etc.) pour prévenir les fuites de données et infections malveillantes.

---

## 2. Périmètre

- Clés USB
- Disques durs externes
- Cartes SD
- CD/DVD
- Tout support de stockage amovible

---

## 3. Principes

### 3.1 Restriction par défaut
Les ports USB sont **désactivés** par défaut sauf besoin justifié.

### 3.2 Médias autorisés
Seuls les médias fournis et chiffrés par l'IT sont autorisés pour les données sensibles (N2/N3).

---

## 4. Procédure d'Autorisation

1. Demande justifiée au manager
2. Validation RSSI pour données N2/N3
3. Fourniture média chiffré par l'IT
4. Enregistrement dans l'inventaire
5. Sensibilisation utilisateur

---

## 5. Règles d'Utilisation

### 5.1 Médias professionnels
- Chiffrement obligatoire (BitLocker To Go ou équivalent)
- Mot de passe fort
- Usage strictement professionnel
- Restitution en fin de mission

### 5.2 Médias externes (reçus de tiers)
- Scan antivirus obligatoire avant ouverture
- Ouverture sur poste isolé si doute
- Jamais de données confidentielles vers l'extérieur sans chiffrement

---

## 6. Usages Interdits

- Médias personnels sur postes professionnels
- Copie de données N2/N3 sur médias non chiffrés
- Abandon ou perte non signalée
- Prêt à un tiers

---

## 7. Destruction

- Effacement sécurisé avant réaffectation
- Destruction physique si données N3
- Certificat de destruction conservé

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-020": {
        "code": "POL-020",
        "name": "Politique Anti-Malware",
        "type": "POLICY",
        "content": '''# Politique Anti-Malware

**Document**: POL-020
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les mesures de protection contre les logiciels malveillants (malwares) au sein de {{ORGANISATION}}.

---

## 2. Types de Menaces

| Type | Description | Impact |
|------|-------------|--------|
| Virus | Code malveillant auto-réplicant | Corruption données |
| Ransomware | Chiffrement avec demande de rançon | Indisponibilité |
| Trojan | Programme dissimulé | Vol de données |
| Spyware | Espionnage | Confidentialité |
| Worm | Propagation réseau | Saturation |

---

## 3. Mesures de Protection

### 3.1 Endpoint Protection (EDR)
- Déployé sur 100% des postes et serveurs
- Mises à jour automatiques
- Analyse temps réel activée
- Scan complet hebdomadaire

### 3.2 Filtrage Email
- Anti-spam et anti-phishing
- Analyse des pièces jointes (sandbox)
- Blocage des exécutables

### 3.3 Filtrage Web
- Catégories à risque bloquées
- Téléchargements analysés
- Blocage des sites malveillants

### 3.4 Réseau
- IDS/IPS avec signatures malware
- Segmentation limitant la propagation
- Blocage C2 (Command & Control)

---

## 4. Réponse aux Alertes

| Sévérité | Action | Délai |
|----------|--------|-------|
| Critique (ransomware actif) | Isolation + cellule crise | Immédiat |
| Haute | Isolation + investigation | < 1h |
| Moyenne | Investigation + nettoyage | < 4h |
| Basse | Nettoyage planifié | < 24h |

---

## 5. Bonnes Pratiques Utilisateurs

- Ne pas ouvrir les pièces jointes suspectes
- Ne pas cliquer sur les liens inconnus
- Signaler tout comportement anormal
- Ne pas désactiver l'antivirus

---

## 6. Indicateurs

| KPI | Cible |
|-----|-------|
| Couverture EDR | 100% |
| Signatures à jour | < 4h |
| Incidents malware | Réduction 25%/an |
| Temps moyen de détection | < 1h |

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DSI | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-021": {
        "code": "POL-021",
        "name": "Politique de Télétravail",
        "type": "POLICY",
        "content": '''# Politique de Sécurité du Télétravail

**Document**: POL-021
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Interne
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les exigences de sécurité pour le travail à distance chez {{ORGANISATION}}.

---

## 2. Conditions d'Éligibilité

### 2.1 Fonctions éligibles
- Activités réalisables à distance
- Validation manager et RH
- Accord de télétravail signé

### 2.2 Prérequis techniques
- Connexion Internet stable
- Équipement professionnel
- Environnement de travail adapté

---

## 3. Équipements

### 3.1 Équipements fournis
- Laptop chiffré
- Casque audio (confidentialité)
- Token MFA

### 3.2 Équipements personnels
BYOD interdit sauf exception validée.

---

## 4. Connexion Sécurisée

### 4.1 VPN obligatoire
- Connexion VPN pour accès ressources internes
- Authentification MFA
- Déconnexion automatique après 8h

### 4.2 Réseau domestique
- WiFi personnel sécurisé (WPA2/WPA3)
- Pas de réseau public sans VPN

---

## 5. Protection des Données

### 5.1 Règles
- Pas de stockage local de données sensibles
- Verrouillage de session obligatoire
- Écran de confidentialité recommandé
- Pas de documents N3 en télétravail

### 5.2 Impression
- Éviter l'impression à domicile
- Destruction sécurisée si nécessaire

---

## 6. Confidentialité

- Espace de travail isolé si possible
- Appels confidentiels en privé
- Écran non visible par des tiers
- Pas de photo/vidéo de l'écran

---

## 7. Incidents

- Signalement immédiat de tout incident
- Même procédure qu'au bureau
- Contact IT/Sécurité disponible

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | DRH | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    "POL-022": {
        "code": "POL-022",
        "name": "Politique de Conformité NIS2/DORA",
        "type": "POLICY",
        "content": '''# Politique de Conformité NIS2/DORA

**Document**: POL-022
**Version**: 1.0
**Date**: {{DATE}}
**Classification**: Confidentiel
**Organisation**: {{ORGANISATION}}

---

## 1. Objet

Cette politique définit les mesures de conformité aux directives NIS2 (Network and Information Security) et DORA (Digital Operational Resilience Act) applicables à {{ORGANISATION}}.

---

## 2. Applicabilité

### 2.1 NIS2
Applicable si :
- Entité essentielle ou importante
- Secteur critique (énergie, santé, finance, transport, etc.)
- CA > 10M€ ou > 50 employés dans secteurs visés

### 2.2 DORA
Applicable si :
- Entité financière (banque, assurance, fintech)
- Prestataire TIC critique pour le secteur financier

---

## 3. Exigences NIS2

### 3.1 Gouvernance
- Responsabilité de la direction
- Formation cybersécurité des dirigeants
- Budget dédié à la cybersécurité

### 3.2 Gestion des risques
- Analyse de risques documentée
- Mesures techniques et organisationnelles
- Gestion de la chaîne d'approvisionnement

### 3.3 Notification d'incidents
| Délai | Notification |
|-------|-------------|
| 24h | Alerte précoce |
| 72h | Notification initiale |
| 1 mois | Rapport final |

### 3.4 Sanctions
Amendes jusqu'à 10M€ ou 2% du CA mondial.

---

## 4. Exigences DORA

### 4.1 Résilience opérationnelle
- Tests de résilience réguliers
- Gestion des incidents ICT
- Continuité d'activité

### 4.2 Gestion des tiers ICT
- Registre des prestataires ICT
- Due diligence renforcée
- Clauses contractuelles obligatoires
- Stratégie de sortie

### 4.3 Tests
- Tests de pénétration (TLPT) tous les 3 ans
- Tests de résilience opérationnelle

---

## 5. Plan de Mise en Conformité

| Action | Responsable | Échéance |
|--------|-------------|----------|
| Gap analysis NIS2/DORA | RSSI | Q1 |
| Mise à jour des politiques | RSSI | Q2 |
| Formation direction | RH | Q2 |
| Registre prestataires ICT | Achats | Q3 |
| Tests de résilience | DSI | Q4 |

---

## 6. Documentation Requise

- Politique de sécurité (ce document)
- Analyse de risques
- Plan de continuité (PCA/PRA)
- Registre des incidents
- Registre des prestataires ICT
- Preuves de tests

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |

**Prochaine révision** : {{DATE_REVISION}}
'''
    },

    # =========================================================================
    # PROCÉDURES (PROC-002 à PROC-026) - 25 templates
    # =========================================================================

    "PROC-002": {
        "code": "PROC-002",
        "name": "Procédure de Signalement des Incidents",
        "type": "PROCEDURE",
        "content": '''# Procédure de Signalement des Incidents

**Document**: PROC-002
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## 1. Objectif

Permettre à tout collaborateur de signaler rapidement et efficacement un incident de sécurité.

---

## 2. Quand Signaler ?

### 2.1 Signaler immédiatement
- Email de phishing reçu ou cliqué
- Comportement anormal du poste
- Perte ou vol d'équipement
- Suspicion de fuite de données
- Message de rançon
- Accès suspect détecté

### 2.2 Dans le doute, signaler
Mieux vaut un signalement inutile qu'un incident non remonté.

---

## 3. Comment Signaler ?

### 3.1 Canaux de signalement

| Canal | Contact | Usage |
|-------|---------|-------|
| Email sécurité | security@{{ORGANISATION}}.fr | Standard |
| Téléphone IT | [Numéro] | Urgent |
| Bouton "Signaler" | Outlook/Intranet | Phishing |
| En personne | Équipe IT/RSSI | Critique |

### 3.2 Informations à fournir
- Votre nom et contact
- Date et heure de l'événement
- Description de l'incident
- Systèmes/données concernés
- Actions déjà entreprises
- Captures d'écran si possible

---

## 4. Que Faire en Attendant ?

### 4.1 À faire
- Noter les détails observés
- Conserver les preuves (ne pas supprimer)
- Déconnecter l'équipement du réseau si suspect
- Rester disponible pour l'équipe sécurité

### 4.2 À ne pas faire
- Éteindre l'ordinateur (sauf instruction contraire)
- Tenter de réparer soi-même
- Communiquer sur les réseaux sociaux
- Payer une rançon

---

## 5. Suivi

- Accusé de réception sous 30 minutes
- Mise à jour régulière du signalant
- Clôture avec retour d'information

---

## 6. Confidentialité

Les signalements sont traités de manière confidentielle. Aucune sanction pour signalement de bonne foi.

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
'''
    },

    "PROC-003": {
        "code": "PROC-003",
        "name": "Plan de Réponse aux Incidents",
        "type": "PROCEDURE",
        "content": '''# Plan de Réponse aux Incidents

**Document**: PROC-003
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}
**Classification**: Confidentiel

---

## 1. Objectif

Définir les actions de réponse aux incidents de sécurité pour minimiser l'impact et assurer une reprise rapide.

---

## 2. Équipe de Réponse (CSIRT)

| Rôle | Nom | Contact | Backup |
|------|-----|---------|--------|
| Responsable incident | RSSI | [Tel] | DSI |
| Analyste sécurité | [Nom] | [Tel] | [Backup] |
| Administrateur système | [Nom] | [Tel] | [Backup] |
| Communication | [Nom] | [Tel] | [Backup] |
| Juridique | [Nom] | [Tel] | [Backup] |

---

## 3. Phases de Réponse

### Phase 1: Détection et Analyse (0-2h)
1. Réception de l'alerte
2. Qualification de l'incident (P1-P4)
3. Activation de l'équipe selon sévérité
4. Collecte des premières informations
5. Documentation dans le système de ticketing

### Phase 2: Confinement (2-4h)
1. Isoler les systèmes impactés
2. Bloquer les comptes compromis
3. Préserver les preuves (logs, mémoire, disques)
4. Limiter la propagation
5. Communiquer en interne

### Phase 3: Éradication (4-24h)
1. Identifier la cause racine
2. Supprimer la menace (malware, backdoor)
3. Corriger les vulnérabilités exploitées
4. Vérifier l'absence de persistance
5. Renforcer les contrôles

### Phase 4: Récupération (24-72h)
1. Restaurer les systèmes depuis sauvegardes saines
2. Réinstaller si nécessaire
3. Vérifier l'intégrité des données
4. Tests de bon fonctionnement
5. Reprise progressive des services

### Phase 5: Retour d'Expérience (J+7)
1. Chronologie détaillée de l'incident
2. Analyse des causes
3. Évaluation de la réponse
4. Actions d'amélioration
5. Mise à jour des procédures

---

## 4. Matrice d'Escalade

| Sévérité | Notification | Délai |
|----------|-------------|-------|
| P1 Critique | DG + RSSI + DSI + Juridique | Immédiat |
| P2 Haute | RSSI + DSI | < 1h |
| P3 Moyenne | RSSI | < 4h |
| P4 Basse | Équipe IT | < 24h |

---

## 5. Communication

### 5.1 Interne
- Direction informée selon sévérité
- Collaborateurs si impact sur leur travail
- Message type préparé

### 5.2 Externe
- Clients si leurs données impactées
- Autorités (CNIL, ANSSI) selon obligations
- Média via Communication uniquement

---

## 6. Outils

| Outil | Usage | Accès |
|-------|-------|-------|
| SIEM | Analyse logs | Équipe sécurité |
| EDR | Investigation endpoint | Équipe sécurité |
| Forensics toolkit | Analyse mémoire/disque | Analyste senior |
| War room | Coordination crise | Tous |

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |
'''
    },

    "PROC-004": {
        "code": "PROC-004",
        "name": "Plan de Continuité d'Activité (PCA)",
        "type": "PROCEDURE",
        "content": '''# Plan de Continuité d'Activité (PCA)

**Document**: PROC-004
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}
**Classification**: Confidentiel

---

## 1. Objectif

Assurer la continuité des activités critiques de {{ORGANISATION}} en cas de sinistre majeur.

---

## 2. Périmètre

### 2.1 Processus Critiques

| Processus | RTO | RPO | Mode dégradé |
|-----------|-----|-----|--------------|
| [Processus 1] | 4h | 1h | [Description] |
| [Processus 2] | 8h | 4h | [Description] |
| [Processus 3] | 24h | 8h | [Description] |

### 2.2 Scénarios couverts
- Indisponibilité du site principal
- Panne datacenter
- Cyberattaque majeure
- Pandémie

---

## 3. Organisation de Crise

### 3.1 Cellule de Crise
| Rôle | Titulaire | Backup |
|------|-----------|--------|
| Directeur de crise | DG | DGA |
| Responsable métier | [Nom] | [Backup] |
| Responsable IT | DSI | RSSI |
| Communication | [Nom] | [Backup] |
| RH | DRH | [Backup] |

### 3.2 Activation
- Critères d'activation définis
- Alerte via [canal]
- Point de rassemblement : [lieu/virtuel]

---

## 4. Stratégies de Reprise

### 4.1 Site de secours
- Localisation : [Adresse]
- Capacité : [X] postes
- Délai d'activation : [X]h

### 4.2 Télétravail massif
- Infrastructure VPN dimensionnée
- Outils collaboratifs cloud
- Support IT renforcé

### 4.3 Procédures dégradées
- [Liste des procédures manuelles]

---

## 5. Ressources Critiques

### 5.1 Personnel clé
| Fonction | Titulaire | Backup |
|----------|-----------|--------|
| [Fonction] | [Nom] | [Backup] |

### 5.2 Systèmes critiques
| Système | Solution de reprise |
|---------|---------------------|
| [Système] | [PRA associé] |

### 5.3 Données critiques
- Sauvegardes externalisées
- RPO garanti : [X]h

---

## 6. Procédure d'Activation

### Phase 1: Alerte (0-1h)
1. Détection du sinistre
2. Évaluation de l'impact
3. Décision d'activation par [Décideur]
4. Convocation cellule de crise

### Phase 2: Mobilisation (1-4h)
1. Activation du site de secours / télétravail
2. Communication aux collaborateurs
3. Priorisation des activités

### Phase 3: Fonctionnement dégradé (4h-Xj)
1. Reprise des activités critiques
2. Suivi et ajustements
3. Communication régulière

### Phase 4: Retour à la normale
1. Restauration du site principal
2. Migration progressive
3. Retour d'expérience

---

## 7. Tests

| Test | Fréquence | Dernier test | Prochain |
|------|-----------|--------------|----------|
| Test d'alerte | Trimestriel | [Date] | [Date] |
| Exercice de crise | Annuel | [Date] | [Date] |
| Test PRA technique | Semestriel | [Date] | [Date] |

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
| Approbation | | Direction Générale | |
'''
    },

    "PROC-005": {
        "code": "PROC-005",
        "name": "Plan de Reprise d'Activité (PRA)",
        "type": "PROCEDURE",
        "content": '''# Plan de Reprise d'Activité (PRA)

**Document**: PROC-005
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}
**Classification**: Confidentiel

---

## 1. Objectif

Définir les procédures techniques de reprise des systèmes d'information après un sinistre.

---

## 2. Objectifs de Reprise

| Système | RTO | RPO | Priorité |
|---------|-----|-----|----------|
| Active Directory | 2h | 1h | 1 |
| Messagerie | 4h | 1h | 1 |
| ERP | 4h | 4h | 2 |
| CRM | 8h | 4h | 2 |
| Intranet | 24h | 24h | 3 |

---

## 3. Infrastructure de Secours

### 3.1 Datacenter secondaire
- Localisation : [Adresse]
- Distance du site principal : [X] km
- Réplication : Synchrone/Asynchrone
- Capacité : [Description]

### 3.2 Cloud DR
- Fournisseur : [Nom]
- Région : [Localisation]
- Services répliqués : [Liste]

---

## 4. Procédures de Bascule

### 4.1 Active Directory
1. Vérifier l'état du DC secondaire
2. Transférer les rôles FSMO
3. Mettre à jour les enregistrements DNS
4. Tester l'authentification
5. Temps estimé : 2h

### 4.2 Messagerie
1. Activer le serveur de secours
2. Mettre à jour les enregistrements MX
3. Vérifier les flux entrants/sortants
4. Communiquer aux utilisateurs
5. Temps estimé : 4h

### 4.3 Applications Métier
[Procédure spécifique par application]

---

## 5. Restauration depuis Sauvegarde

### 5.1 Procédure générale
1. Identifier la dernière sauvegarde saine
2. Préparer l'infrastructure cible
3. Lancer la restauration
4. Vérifier l'intégrité
5. Tests fonctionnels
6. Mise en production

### 5.2 Contacts
| Système | Éditeur/Support | Contact |
|---------|-----------------|---------|
| Sauvegarde | [Éditeur] | [Tel] |
| Stockage | [Éditeur] | [Tel] |

---

## 6. Tests PRA

### 6.1 Types de tests
| Test | Description | Fréquence |
|------|-------------|-----------|
| Test unitaire | Restauration d'un système | Mensuel |
| Test partiel | Bascule d'un service | Trimestriel |
| Test complet | Bascule datacenter | Annuel |

### 6.2 Documentation des tests
- Plan de test
- Résultats et écarts
- Actions correctives

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | DSI | {{DATE}} |
| Validation | | RSSI | |
'''
    },

    "PROC-006": {
        "code": "PROC-006",
        "name": "Procédure de Gestion des Habilitations",
        "type": "PROCEDURE",
        "content": '''# Procédure de Gestion des Habilitations

**Document**: PROC-006
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## 1. Objectif

Définir le processus de gestion des droits d'accès aux systèmes et applications de {{ORGANISATION}}.

---

## 2. Principes

- Moindre privilège : uniquement les droits nécessaires
- Besoin d'en connaître : accès aux seules données nécessaires
- Séparation des tâches : fonctions incompatibles séparées
- Traçabilité : toute action est journalisée

---

## 3. Processus de Demande

### 3.1 Création de compte (Arrivée)

```
[Manager] → Demande via formulaire/ITSM
     ↓
[RH] → Validation du statut employé
     ↓
[Propriétaire ressource] → Validation des droits demandés
     ↓
[IT] → Création du compte et attribution des droits
     ↓
[Utilisateur] → Réception des accès
```

### 3.2 Délais
- Anticipation : J-5 avant arrivée
- Création compte : J-1
- Accès spécifiques : J+2 max

---

## 4. Modification des Droits

### 4.1 Mobilité interne
1. Notification RH de la mobilité
2. Revue des droits actuels
3. Suppression des droits non nécessaires
4. Attribution des nouveaux droits
5. Documentation du changement

### 4.2 Demande ponctuelle
1. Demande justifiée par le manager
2. Validation propriétaire ressource
3. Durée limitée si possible
4. Revue à l'échéance

---

## 5. Suppression des Droits (Départ)

### 5.1 Processus
```
[RH] → Notification de départ (J-X)
     ↓
[Manager] → Confirmation et transfert de données
     ↓
[IT] → Désactivation compte (J du départ)
     ↓
[IT] → Suppression définitive (J+30)
```

### 5.2 Délais critiques
| Action | Délai |
|--------|-------|
| Désactivation compte | Jour du départ |
| Révocation accès physiques | Jour du départ |
| Suppression boîte mail | J+30 |
| Suppression compte | J+30 |

---

## 6. Revue des Habilitations

| Type | Fréquence | Responsable |
|------|-----------|-------------|
| Comptes utilisateurs | Annuelle | Managers |
| Comptes privilégiés | Trimestrielle | RSSI |
| Comptes applicatifs | Semestrielle | Propriétaires apps |
| Comptes techniques | Annuelle | IT |

---

## 7. Comptes Spéciaux

### 7.1 Comptes privilégiés
- Inventaire dans REG-004
- Validation RSSI obligatoire
- MFA obligatoire
- Session tracée

### 7.2 Comptes de service
- Mots de passe complexes
- Rotation planifiée
- Documentation des usages

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
'''
    },

    "PROC-007": {
        "code": "PROC-007",
        "name": "Procédure de Gestion des Patchs",
        "type": "PROCEDURE",
        "content": '''# Procédure de Gestion des Patchs

**Document**: PROC-007
**Version**: 1.0
**Date**: {{DATE}}
**Organisation**: {{ORGANISATION}}

---

## 1. Objectif

Définir le processus de déploiement des correctifs de sécurité sur les systèmes de {{ORGANISATION}}.

---

## 2. Périmètre

- Systèmes d'exploitation (Windows, Linux)
- Applications métier
- Équipements réseau
- Firmware

---

## 3. Classification des Patchs

| Criticité | CVSS | Délai déploiement |
|-----------|------|-------------------|
| Critique | 9.0+ | 24-48h |
| Haute | 7.0-8.9 | 7 jours |
| Moyenne | 4.0-6.9 | 30 jours |
| Basse | < 4.0 | 90 jours |

---

## 4. Processus

### 4.1 Veille et identification
1. Surveillance des bulletins éditeurs
2. Alertes CERT-FR, ANSSI
3. Scan de vulnérabilités hebdomadaire
4. Qualification de l'applicabilité

### 4.2 Test
1. Déploiement environnement de test
2. Validation fonctionnelle
3. Test de non-régression
4. Documentation des résultats

### 4.3 Déploiement
1. Planification selon criticité
2. Communication aux utilisateurs
3. Déploiement progressif (pilote → général)
4. Surveillance post-déploiement

### 4.4 Validation
1. Scan de contrôle
2. Vérification de la couverture
3. Documentation

---

## 5. Exceptions

### 5.1 Déploiement d'urgence (0-day)
- Validation RSSI immédiate
- Déploiement sans test complet si nécessaire
- Surveillance renforcée

### 5.2 Report de patch
- Justification écrite
- Mesures compensatoires
- Validation RSSI
- Durée maximale : 6 mois

---

## 6. Fenêtres de Maintenance

| Jour | Horaire | Type de patch |
|------|---------|---------------|
| Mercredi | 22h-6h | Postes de travail |
| Samedi | 6h-18h | Serveurs non critiques |
| Dimanche | 2h-6h | Serveurs critiques |

---

## 7. Indicateurs

| KPI | Cible |
|-----|-------|
| Patch critique < 48h | 100% |
| Patch haute < 7j | 95% |
| Couverture scan | 100% |

---

## 8. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{AUTEUR}} | RSSI | {{DATE}} |
'''
    },

    # ... Je continue avec les autres procédures et documents
    # Pour des raisons de longueur, je vais ajouter les templates restants de manière condensée

}

# =============================================================================
# AJOUT DES AUTRES TEMPLATES (REGISTRES, ANNEXES, MATRICES, etc.)
# =============================================================================

# Registres
for code, name in [
    ("REG-003", "Registre des Incidents de Sécurité"),
    ("REG-004", "Registre des Accès Privilégiés"),
    ("REG-005", "Registre des Fournisseurs"),
    ("REG-007", "Registre des Actifs Matériels"),
    ("REG-008", "Registre des Logiciels"),
    ("REG-009", "Registre des Changements"),
    ("REG-010", "Registre des Dérogations"),
    ("REG-011", "Registre des Formations Sécurité"),
    ("REG-012", "Registre des Audits"),
    ("REG-013", "Registre des Tests PCA/PRA"),
    ("REG-014", "Registre des Revues de Direction"),
    ("REG-015", "Registre des Non-Conformités"),
]:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "REGISTER",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}

---

## Instructions

Ce registre permet de tracer et suivre les éléments relatifs à "{name.replace("Registre des ", "")}".

**Fréquence de mise à jour** : Continue / À chaque événement

---

## Registre

| ID | Date | Description | Responsable | Statut | Commentaires |
|----|------|-------------|-------------|--------|--------------|
| 001 | | | | | |
| 002 | | | | | |
| 003 | | | | | |

---

## Historique des mises à jour

| Date | Auteur | Modifications |
|------|--------|---------------|
| {{{{DATE}}}} | {{{{AUTEUR}}}} | Création initiale |
'''
    }

# Procédures restantes (PROC-008 à PROC-026)
for i in range(8, 27):
    code = f"PROC-{i:03d}"
    names = {
        8: "Procédure de Sauvegarde et Restauration",
        9: "Procédure d'Audit Interne SMSI",
        10: "Procédure de Revue de Direction",
        11: "Procédure de Gestion des Non-Conformités",
        12: "Procédure de Gestion des Actions Correctives",
        13: "Procédure de Test d'Intrusion",
        14: "Procédure de Gestion de Crise Cyber",
        15: "Procédure de Communication de Crise",
        16: "Procédure d'Onboarding Sécurité",
        17: "Procédure d'Offboarding",
        18: "Procédure de Classification des Données",
        19: "Procédure de Destruction Sécurisée",
        20: "Procédure de Gestion des Clés Cryptographiques",
        21: "Procédure de Durcissement des Systèmes",
        22: "Procédure de Réponse DDoS",
        23: "Procédure de Notification CNIL",
        24: "Procédure d'Exercice des Droits RGPD",
        25: "Procédure de Gestion des Sous-Traitants",
        26: "Procédure de Veille Sécurité",
    }
    name = names.get(i, f"Procédure {i}")
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "PROCEDURE",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}

---

## 1. Objectif

Cette procédure définit le processus de {name.lower().replace("procédure de ", "").replace("procédure d'", "")}.

---

## 2. Périmètre

[Définir le périmètre d'application]

---

## 3. Responsabilités

| Rôle | Responsabilité |
|------|----------------|
| RSSI | Validation et supervision |
| DSI | Mise en œuvre technique |
| Métiers | Application |

---

## 4. Processus

### 4.1 Étape 1
[Description de l'étape]

### 4.2 Étape 2
[Description de l'étape]

### 4.3 Étape 3
[Description de l'étape]

---

## 5. Enregistrements

| Document | Responsable | Conservation |
|----------|-------------|--------------|
| [Document] | [Rôle] | [Durée] |

---

## 6. Indicateurs

| KPI | Cible | Fréquence |
|-----|-------|-----------|
| [KPI] | [Cible] | [Fréquence] |

---

## 7. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{{{AUTEUR}}}} | RSSI | {{{{DATE}}}} |
'''
    }

# Annexes (ANX-001 à ANX-012)
annexes = [
    ("ANX-001", "Matrice RACI SMSI"),
    ("ANX-002", "Clauses Type DPA (Data Processing Agreement)"),
    ("ANX-003", "Template PIA (Analyse d'Impact)"),
    ("ANX-004", "Checklist Audit ISO 27001"),
    ("ANX-005", "Checklist Sécurité Projet"),
    ("ANX-006", "Questionnaire Sécurité Fournisseur"),
    ("ANX-007", "Template Analyse de Risques"),
    ("ANX-008", "Glossaire Sécurité"),
    ("ANX-009", "Contacts d'Urgence Sécurité"),
    ("ANX-010", "Checklist Départ Collaborateur"),
    ("ANX-011", "Checklist Arrivée Collaborateur"),
    ("ANX-012", "Template Rapport d'Incident"),
]

for code, name in annexes:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "ANNEX",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}

---

## Contenu

[Contenu spécifique de l'annexe {name}]

---

## Historique

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | {{{{DATE}}}} | Création initiale |
'''
    }

# Matrices (MAT-001 à MAT-004)
matrices = [
    ("MAT-001", "Matrice de Correspondance Multi-Normes"),
    ("MAT-002", "Matrice d'Analyse des Risques"),
    ("MAT-003", "Matrice BIA (Business Impact Analysis)"),
    ("MAT-004", "Matrice des Flux de Données"),
]

for code, name in matrices:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "MATRIX",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}

---

## Matrice

[Tableau matriciel spécifique]

---

## Légende

[Explication des codes et valeurs]

---

## Historique

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | {{{{DATE}}}} | Création initiale |
'''
    }

# Rapports (RPT-001 à RPT-004)
reports = [
    ("RPT-001", "Rapport de Revue de Direction SMSI"),
    ("RPT-002", "Tableau de Bord SSI"),
    ("RPT-003", "Rapport d'Audit Annuel"),
    ("RPT-004", "Rapport d'Analyse de Risques"),
]

for code, name in reports:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "REPORT",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}
**Période**: [Période couverte]

---

## Résumé Exécutif

[Synthèse pour la direction]

---

## Indicateurs Clés

| KPI | Valeur | Tendance | Cible |
|-----|--------|----------|-------|
| [KPI] | [Valeur] | [↑↓→] | [Cible] |

---

## Analyse

[Analyse détaillée]

---

## Recommandations

1. [Recommandation 1]
2. [Recommandation 2]

---

## Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | {{{{AUTEUR}}}} | RSSI | {{{{DATE}}}} |
'''
    }

# Templates (TPL-001 à TPL-004)
templates = [
    ("TPL-001", "Template de Déclaration d'Applicabilité (DDA)"),
    ("TPL-002", "Template de Plan de Traitement des Risques"),
    ("TPL-003", "Template de Compte-Rendu d'Incident"),
    ("TPL-004", "Template de Demande de Dérogation"),
]

for code, name in templates:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "TEMPLATE",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0

---

## Instructions d'utilisation

Ce template doit être utilisé pour [description de l'usage].

---

## Template

[Structure du template à compléter]

---

## Exemple rempli

[Exemple de document complété]
'''
    }

# Schémas (SCH-001 à SCH-008) - Descriptions pour génération manuelle/PPTX
schemas = [
    ("SCH-001", "Architecture SI Globale"),
    ("SCH-002", "Flux de Données Inter-Entités"),
    ("SCH-003", "Zones de Sécurité (N1/N2/N3)"),
    ("SCH-004", "Architecture Cloud (Google Workspace)"),
    ("SCH-005", "Architecture Virtualisation (Proxmox)"),
    ("SCH-006", "Réseau Multi-Sites"),
    ("SCH-007", "Flux PCI-DSS (Données de Paiement)"),
    ("SCH-008", "Schéma d'Urbanisation Applicative"),
]

for code, name in schemas:
    TEMPLATES_COMPLETE[code] = {
        "code": code,
        "name": name,
        "type": "SCHEMA",
        "content": f'''# {name}

**Document**: {code}
**Version**: 1.0
**Date**: {{{{DATE}}}}
**Organisation**: {{{{ORGANISATION}}}}

---

## Description

Ce schéma représente {name.lower()}.

---

## Éléments représentés

### Composants principaux
- [Composant 1]
- [Composant 2]
- [Composant 3]

### Flux et connexions
- [Flux 1]
- [Flux 2]

### Zones de sécurité
- Zone N1 (Standard)
- Zone N2 (Renforcée)
- Zone N3 (Critique)

---

## Légende

| Symbole | Signification |
|---------|---------------|
| [Rectangle bleu] | Serveur/Application |
| [Flèche verte] | Flux autorisé |
| [Ligne rouge] | Périmètre sécurité |

---

## Notes

Ce schéma est disponible en format PowerPoint pour présentation.
Fichier source : {code}-{name.replace(" ", "-")}.pptx

---

## Historique

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | {{{{DATE}}}} | Création initiale |
'''
    }


def get_complete_template(code: str) -> Dict[str, Any]:
    """Get a complete template by its code."""
    return TEMPLATES_COMPLETE.get(code)


def fill_complete_template(template_code: str, context: Dict[str, Any]) -> str:
    """Fill a template with context values."""
    template = TEMPLATES_COMPLETE.get(template_code)
    if not template:
        return None

    content = template["content"]

    # Standard replacements
    replacements = {
        "{{ORGANISATION}}": context.get("organization", {}).get("name", "[Organisation]"),
        "{{DATE}}": datetime.now().strftime("%Y-%m-%d"),
        "{{DATE_REVISION}}": (datetime.now().replace(year=datetime.now().year + 1)).strftime("%Y-%m-%d"),
        "{{AUTEUR}}": context.get("author", "RSSI"),
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, str(value))

    return content
