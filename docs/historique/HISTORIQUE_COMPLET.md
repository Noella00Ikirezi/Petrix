# Petrix — Historique complet du projet

> Document de référence : tout ce qui a été construit, décidé, modifié ou supprimé.  
> Maintenu par : Noëlla IKIREZI (ESGI 4SI4 / Afluens)  
> Dernière mise à jour : juin 2026

---

## Sommaire

1. [Vision initiale du projet](#1-vision-initiale-du-projet)
2. [Architecture technique retenue](#2-architecture-technique-retenue)
3. [Infrastructure AWS](#3-infrastructure-aws)
4. [Backend — Évolution des endpoints](#4-backend--évolution-des-endpoints)
5. [Frontend — Pages et composants](#5-frontend--pages-et-composants)
6. [Agent terrain (petrix-agent)](#6-agent-terrain-petrix-agent)
7. [CI/CD — Historique des décisions](#7-cicd--historique-des-décisions)
8. [Fonctionnalités retirées ou abandonnées](#8-fonctionnalités-retirées-ou-abandonnées)
9. [Bugs critiques rencontrés et résolus](#9-bugs-critiques-rencontrés-et-résolus)
10. [Décisions d'architecture importantes](#10-décisions-darchitecture-importantes)
11. [Sécurité — MFA et gestion des accès](#11-sécurité--mfa-et-gestion-des-accès)

---

## 1. Vision initiale du projet

Petrix est une plateforme de cybersécurité offensive/défensive pensée pour l'audit de réseaux internes et la conformité hardening. L'idée de départ était de centraliser dans un seul outil :

- Le scan de vulnérabilités réseau (type nmap/nikto)
- L'audit de conformité SSH/hardening (HCO)
- La gestion des actifs (CMDB légère)
- La veille CVE en temps réel
- Un agent déployable en interne pour scanner des réseaux isolés

### Modules prévus au départ (liste originale)

| Module | Statut final |
|--------|-------------|
| Scan de vulnérabilités | ✅ Livré |
| Audit hardening (HCO) | ✅ Livré |
| Gestion des actifs | ✅ Livré |
| Agent terrain (petrix-agent) | ✅ Livré |
| Veille CVE (NVD) | ✅ Livré |
| Générateur SMSI | ❌ Retiré (voir §8) |
| Gestion des clients (multi-tenant) | ❌ Retiré (voir §8) |
| Mode "blackbox" (scan sans cible) | ❌ Retiré (voir §8) |
| Journaux d'audit (Audit Logs) | ✅ Livré (page frontend) |

---

## 2. Architecture technique retenue

### Stack final

```
Frontend       React 18 + TypeScript + Vite + TailwindCSS
Backend        FastAPI (Python 3.12) + SQLAlchemy + Alembic
Worker         Celery + Redis (broker)
Base de données PostgreSQL 15
Reverse proxy  Nginx (dans Docker, sert aussi le frontend buildé)
Agent          Python 3.12 (packagé en .exe via PyInstaller pour Windows)
CI/CD          GitLab CI → AWS SSM → Docker cp (sans rebuild)
Hébergement    AWS EC2 (t3.medium, Ubuntu 22.04, eu-west-1)
Stockage       AWS S3 (bucket petrix-storage-655177115922)
Domaine        https://petrix.noellahome.org
```

### Choix importants

- **FastAPI avec `redirect_slashes=False`** : toutes les routes sont déclarées sans `/` final (`@router.get("")` pas `@router.get("/")`). Décision prise car httpx ne suivait pas les redirections 307 sur les POST.
- **Celery séparé du backend** : deux containers Docker distincts (`petrix-backend` et `petrix-celery`) qui partagent le même code.
- **Pas de rebuild Docker en prod** : le deploy copie les fichiers modifiés directement dans les containers via `docker cp` puis restart. Beaucoup plus rapide.

---

## 3. Infrastructure AWS

### EC2

| Élément | Valeur |
|---------|--------|
| Instance ID | `i-0fc0adfd256c0428d` |
| IP publique | `3.255.126.244` |
| Région | `eu-west-1` |
| OS | Ubuntu 22.04 LTS |
| Type | t3.medium |
| Accès SSH | Port 22 restreint à `18.202.216.48/29` (AWS range uniquement) |
| Accès depuis Mac | **SSM uniquement** — `aws ssm start-session --target i-0fc0adfd256c0428d` |

> **Règle absolue** : ne jamais installer de dépendances sur le Mac local. Tout se passe sur EC2 via SSM.

### S3

| Élément | Valeur |
|---------|--------|
| Bucket | `petrix-storage-655177115922` |
| Usage | Transferts de fichiers CI→EC2 (contournement limite 97KB de SSM) |
| Préfixe deploy | `s3://petrix-storage-655177115922/deploy/` |

### Containers Docker sur EC2

| Container | Rôle |
|-----------|------|
| `petrix-backend` | FastAPI + API REST |
| `petrix-celery` | Worker Celery pour les scans |
| `petrix-frontend` | Nginx qui sert le dist React |
| `petrix-db` | PostgreSQL 15 |
| `petrix-redis` | Redis (broker Celery) |

### GitLab

- Remote : `git@gitlab.com:petrix1/petrix.git`
- Branche principale : `main`
- Variables CI nécessaires : `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `EC2_INSTANCE_ID`, `S3_BUCKET`

---

## 4. Backend — Évolution des endpoints

### Routes API v1 (état actuel)

```
/api/v1/auth/          login, logout, refresh, me
/api/v1/users/         CRUD utilisateurs
/api/v1/assets/        CRUD actifs
/api/v1/scans/         CRUD scans + start/cancel + agent endpoints
/api/v1/hardening/     Targets + checks + résultats
/api/v1/vulnerabilities/ CRUD vulns détectées
/api/v1/audit-logs/    Journaux d'événements
/api/v1/agent/download/ Téléchargement du binaire agent
```

### Évolution de `scans.py`

**Phase 1** : endpoint basique, retournait une liste de scans.

**Phase 2** : ajout du mode "blackbox" — quand aucune cible n'était spécifiée, la fonction `_get_blackbox_targets()` renvoyait une liste de sites par défaut (`scanme.nmap.org`, `testphp.vulnweb.com`, IP EC2). **Problème** : tous les scans "audit" scannaient ces sites au lieu du réseau cible.

**Phase 3 (actuelle)** : suppression du fallback blackbox. Si aucune cible valide → `status=FAILED` avec message clair. Ajout des endpoints agent :
- `POST /{scan_id}/agent-results` — reçoit les résultats de l'agent (hosts + findings)
- `PATCH /{scan_id}/agent-complete` — finalise le scan, calcule score/grade

### `ScanConfig` — Pydantic v2

Initialement, `ScanConfig` rejetait les champs inconnus. L'agent envoyait `{"agent": true, "machine": "...", "os": "..."}` mais Pydantic les ignorait silencieusement.

**Fix** : ajout de `model_config = {"extra": "allow"}` pour préserver tous les champs.

### Détection agent dans `create_scan`

```python
config_dict = scan_data.config.model_dump()
is_agent = config_dict.get("agent", False)
if is_agent:
    scan.status = ScanStatus.RUNNING
    scan.started_at = datetime.utcnow()
    scan.current_phase = "agent_scanning"
```

Sans ça, le scan créé par l'agent apparaissait en `PENDING` avec un bouton "Démarrer" dans l'UI — et Celery essayait de le lancer, ce qui échouait car pas de cibles.

---

## 5. Frontend — Pages et composants

### Page d'accueil (`HomePage.tsx`)

**Avant** : affichait 8 modules dont "Générateur SMSI" et "Gestion des clients" qui n'existaient pas/plus dans le backend. Texte en anglais.

**Après** : 6 modules réels en français :
1. Gestion des actifs
2. Scanner de vulnérabilités
3. Scans réseau
4. Hardening (HCO)
5. Agent terrain
6. Journaux d'audit

Ajout d'un lien "Connexion" en plus de "Inscription" (le login n'était pas accessible depuis la homepage).

### Page Actifs (`AssetsPage.tsx`)

**Avant** : formulaire de création basique, aucun lien avec le module hardening.

**Après** : ajout d'une case à cocher "Créer une cible hardening (audit SSH)". Quand cochée + IP/hostname fourni → appel automatique à `hardeningApi.createTarget()` après `assetsApi.create()`.

Champs ajoutés : utilisateur SSH, port SSH. Mapping asset_type → OS via dictionnaire `OS_BY_TYPE`.

### Page Vulnérabilités (`VulnerabilitiesPage.tsx`)

**Avant** : seule liste des vulns détectées en DB.

**Après** : deux onglets :
- "Vulnérabilités détectées" — vulns issues des scans
- "Veille CVE (NVD)" — flux live depuis `https://services.nvd.nist.gov/rest/json/cves/2.0`

Composants ajoutés : `CveFeed` (fetche NVD), `CveCard` (affichage avec CVSS, dates, description, vecteur, liens sources), recherche par mot-clé avec Enter.

### Page Agent (`AgentPage.tsx`)

**Avant** : uniquement onglet "Installation" avec lien de téléchargement.

**Après** : deux onglets :
- "Installation" — instructions Windows (SmartScreen bypass) et Linux/macOS + lien download
- "Console" — polling toutes les 4s sur `/api/v1/scans`, affiche les scans en cours avec barre de progression et phases

**SmartScreen bypass documenté** :
- Méthode 1 : Clic droit → Propriétés → Débloquer → Exécuter en tant qu'admin
- Méthode 2 : PowerShell one-liner avec `Unblock-File` + `Start-Process -Verb RunAs`

### Page Scans (`ScansPage.tsx`)

**Avant** : mode "Blackbox Discovery" permettait de soumettre un scan sans cible (targets: []).

**Après** : suppression du mode blackbox. Tous les types de scan nécessitent une cible explicite. Affichage du champ `error_message` en cas d'échec (avant : affichait `current_phase` qui n'était pas lisible).

### Page Utilisateurs (`UsersPage.tsx`)

**Avant** : tableau sans scroll, bloquait sur liste longue.

**Après** : wrapper `overflow-y-auto max-h-[600px]` autour du tableau.

### Fix TypeScript build

- Création de `frontend/src/vite-env.d.ts` avec `/// <reference types="vite/client" />` (erreur `Property 'env' does not exist on type 'ImportMeta'`)
- Ajout dans `tsconfig.json` d'`exclude` pour les fichiers `*.test.ts` / `*.spec.ts` (les tests bloquaient le build prod)

---

## 6. Agent terrain (petrix-agent)

### Concept

L'agent est un exécutable (`.exe` Windows, `.sh` Linux) déployé directement sur une machine du réseau cible. Il :
1. Détecte automatiquement le(s) subnet(s) local(aux) via `netifaces`
2. Crée un scan sur le serveur Petrix (avec `"agent": true` dans la config)
3. Découvre les hôtes (ARP via scapy → nmap ping → socket sweep)
4. Scanne les ports de chaque hôte (python-nmap → socket fallback)
5. Pousse les résultats sur `/api/v1/scans/{id}/agent-results`
6. Finalise sur `/api/v1/scans/{id}/agent-complete`

### Fichiers principaux

```
agent/
  petrix_agent/
    cli.py           # Point d'entrée, orchestration complète
    reporter.py      # Connexion HTTP vers le serveur Petrix
    scanner/
      network.py     # Découverte réseau (ARP, nmap, socket)
      ports.py       # Scan de ports (nmap, socket fallback)
```

### Problème résolu : trailing slash

`reporter.py` envoyait `POST /api/v1/scans/` avec le slash final. Avec `redirect_slashes=False` sur FastAPI, httpx recevait un 307 mais ne le suivait pas (pas de `follow_redirects=True`). Le scan n'était jamais créé.

**Fix** : `POST /api/v1/scans` sans slash.

### Windows SmartScreen

L'exécutable n'est pas signé (pas de certificat de signature de code commercial). Windows bloque l'exécution avec "Application inconnue".

**Contournement documenté** :
1. Clic droit → Propriétés → décocher "Bloquer" → OK → Exécuter en admin
2. PowerShell : `$f="$env:TEMP\petrix-install.exe"; (New-Object Net.WebClient).DownloadFile('URL', $f); Unblock-File $f; Start-Process $f -Verb RunAs -Wait`

### UAC / droits admin

L'agent demande systématiquement les droits admin au lancement (nécessaire pour nmap raw sockets et ARP). Implémenté en Go (version initiale) puis Python :
- Détection via `net session` (Windows) ou `os.geteuid() == 0` (Linux/macOS)
- Auto-élévation via `Start-Process -Verb RunAs` (Windows) ou `sudo` (Linux/macOS)

---

## 7. CI/CD — Historique des décisions

### Phase 1 : Déploiement automatique cassé

**Configuration initiale** : le job `deploy` se déclenchait automatiquement sur chaque push sur `main`. Il essayait de faire `git pull origin main` sur EC2.

**Problème** : EC2 n'avait pas de clé SSH GitLab configurée. Le `git pull` échouait systématiquement → jobs en FAILED à chaque push.

### Phase 2 : Fix partiel — SSM direct

Tentative de passer les fichiers directement via SSM `AWS-RunShellScript`. Limite atteinte : les commandes SSM sont limitées à 97KB. Un frontend buildé (dist/) fait ~235KB compressé → `MaxDocumentSizeExceeded`.

### Phase 3 (actuelle) : S3 comme intermédiaire + déploiement manuel

**Pipeline actuel** :
1. CI build le frontend (React Vite)
2. CI upload les fichiers modifiés sur S3 (`s3://petrix-storage-655177115922/deploy/`)
3. CI envoie une commande SSM à EC2 : "télécharge depuis S3, `docker cp`, restart containers"
4. CI poll le statut SSM et fail si Status ≠ "Success"

**Décision clé** : `when: manual` — le deploy ne se déclenche JAMAIS automatiquement. Doit être lancé manuellement depuis GitLab → Pipelines → bouton ▶.

### Variables GitLab CI requises

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Clé IAM avec droits SSM + S3 |
| `AWS_SECRET_ACCESS_KEY` | Secret IAM |
| `AWS_DEFAULT_REGION` | `eu-west-1` |
| `EC2_INSTANCE_ID` | `i-0fc0adfd256c0428d` |
| `S3_BUCKET` | `petrix-storage-655177115922` |

---

## 8. Fonctionnalités retirées ou abandonnées

### Générateur SMSI

**Ce que c'était** : module prévu pour générer automatiquement des documents SMSI (Politique de Sécurité, Procédures, etc.) à partir des résultats de scans.

**Pourquoi retiré** : trop complexe à livrer dans les délais. Nécessitait un moteur de templates documentaires non développé. La page existait en frontend mais pointait vers des endpoints inexistants.

**Ce qui a été supprimé** : lien dans la homepage, route frontend `/smsi`.

### Gestion des clients (multi-tenant)

**Ce que c'était** : Petrix devait gérer plusieurs "clients" (organisations), chaque client avec ses propres assets et scans isolés.

**Pourquoi retiré** : complexité d'implémentation multi-tenant avec SQLAlchemy. Décision de rester en mode mono-organisation pour la V1.

**Ce qui a été supprimé** : lien dans la homepage, aucune table `clients` créée en DB.

### Mode Blackbox Discovery

**Ce que c'était** : création d'un scan sans spécifier de cible. La fonction `_get_blackbox_targets()` renvoyait automatiquement :
- `scanme.nmap.org` (site de test nmap officiel)
- `testphp.vulnweb.com` (site vulnérable Acunetix)
- L'IP publique de l'EC2

**Pourquoi retiré** : tous les scans "Audit" créés depuis le frontend se retrouvaient à scanner ces sites de test au lieu du réseau de l'utilisateur. Aucune valeur métier. Remplacé par l'agent terrain qui fait la vraie découverte réseau depuis l'intérieur.

**Ce qui a été supprimé** : `_get_blackbox_targets()` dans `scan_tasks.py`, option "Blackbox Discovery" dans le formulaire de scan frontend.

### Installation locale de l'agent (script Python direct)

**Ce que c'était** : l'agent était distribué comme script Python à lancer en `pip install + python -m petrix_agent`.

**Pourquoi changé** : pas utilisable par des non-techniciens. Remplacé par un exécutable `.exe` (PyInstaller) pour Windows et `.sh` pour Linux/macOS. L'exécutable demande les droits admin dès le lancement.

---

## 9. Bugs critiques rencontrés et résolus

### Bug 1 — Scans ciblent des sites par défaut au lieu du réseau réel

**Symptôme** : scans "Audit" et "Audit test" montraient `scanme.nmap.org` et `testphp.vulnweb.com` comme cibles.

**Cause** : `_get_blackbox_targets()` appelée systématiquement quand `scan.targets` était vide.

**Fix** : suppression du fallback, fail explicite avec message d'erreur si aucune cible.

### Bug 2 — Agent ne crée jamais le scan (trailing slash)

**Symptôme** : l'agent se lançait, mais aucun scan n'apparaissait dans Petrix.

**Cause** : `POST /api/v1/scans/` avec slash → FastAPI renvoyait 307 → httpx ne suivait pas (pas de `follow_redirects=True`).

**Fix** : `POST /api/v1/scans` sans slash final.

### Bug 3 — Champ `agent: True` ignoré par Pydantic

**Symptôme** : scan créé par l'agent apparaissait en `PENDING` au lieu de `RUNNING`.

**Cause** : `ScanConfig(BaseModel)` rejetait silencieusement les champs inconnus (`agent`, `machine`, `os`).

**Fix** : `model_config = {"extra": "allow"}` sur `ScanConfig`.

### Bug 4 — Limite 97KB SSM

**Symptôme** : `MaxDocumentSizeExceeded` lors du deploy CI → la commande SSM était trop grande.

**Cause** : essai d'envoyer le contenu du dist React directement dans le payload SSM.

**Fix** : upload sur S3 d'abord, puis EC2 télécharge depuis S3 via `aws s3 cp`.

### Bug 5 — Variables `${CONTAINER}` non expandées dans SSM

**Symptôme** : `docker cp /tmp/file.py ${CONTAINER}:/app/...` échouait dans SSM.

**Cause** : les variables shell ne sont pas expansées dans les commandes SSM passées en JSON.

**Fix** : utiliser les noms de containers explicites (`petrix-backend`, `petrix-celery`, etc.).

### Bug 6 — TypeScript build échoue sur `ImportMeta.env`

**Symptôme** : `Property 'env' does not exist on type 'ImportMeta'` en CI lors du build Vite.

**Fix** : création de `frontend/src/vite-env.d.ts` avec `/// <reference types="vite/client" />`.

### Bug 7 — CI/CD en FAILED systématique

**Symptôme** : tous les jobs de déploiement en FAILED dès que du code était pushé.

**Cause** : job `deploy` en auto sur chaque push, EC2 sans clé SSH GitLab → `git pull` échouait.

**Fix** : `when: manual`, suppression du `git pull`, passage au modèle S3+SSM.

---

## 10. Décisions d'architecture importantes

### Ne jamais installer sur le Mac local

**Règle** : toute dépendance, tout outil s'installe sur EC2 via SSM. Le Mac local sert uniquement à éditer le code et à faire `git push`.

### `redirect_slashes=False` sur FastAPI

Toutes les routes sont déclarées sans `/` final. Impose d'être rigoureux côté agent/client HTTP : pas de slash final sur les POST.

### Agent = pensé pour les réseaux isolés

L'agent n'a pas besoin d'accès direct aux cibles depuis le serveur. Il s'installe dans le réseau cible, scanne localement, et remonte les résultats via HTTPS vers Petrix. Permet d'auditer des réseaux sans exposer les machines cibles.

### Celery pour les scans serveur, agent pour les réseaux internes

- Scans avec cible explicite (IP publique, domaine) → Celery Worker
- Scans réseau interne → Agent terrain

### Deploy sans rebuild Docker

Le rebuild Docker en prod prend 3–5 minutes et nécessite de pousser l'image sur un registry. Pour des modifications de fichiers Python/React, `docker cp` + restart suffit et prend 20–30 secondes.

---

## 11. Sécurité — MFA et gestion des accès

### MFA (Multi-Factor Authentication)

- MFA implémenté avec TOTP (Google Authenticator compatible)
- **Désactivé temporairement** pour faciliter les tests de l'agent (l'agent utilise login/password, pas MFA)
- À réactiver en production avant livraison finale
- L'endpoint `/api/v1/auth/login` retourne directement `access_token` quand MFA est off

### SES (Simple Email Service AWS)

- Configuré pour l'envoi d'emails (invitations, reset password)
- En mode sandbox : seuls les emails vérifiés peuvent recevoir des mails
- **À faire** : demander le passage en production SES pour pouvoir envoyer à n'importe quelle adresse

### Permissions RBAC

- Système de rôles : `ADMIN`, `ANALYST`, `VIEWER`
- Chaque endpoint vérifié avec `require_permission(Permission.XXX)`
- Pas de multi-tenant : tous les utilisateurs voient les mêmes données (décision V1)

---

*Document généré en juin 2026 — à mettre à jour à chaque décision significative.*
