# Petrix — Livrable de production

> Ce document décrit uniquement ce qui est **réellement déployé et utilisé** en production.  
> Pas d'historique, pas de features expérimentales — seulement ce qui fonctionne.  
> Dernière mise à jour : juin 2026

---

## Sommaire

1. [Accès et URLs](#1-accès-et-urls)
2. [Architecture déployée](#2-architecture-déployée)
3. [Backend API — Endpoints actifs](#3-backend-api--endpoints-actifs)
4. [Frontend — Pages disponibles](#4-frontend--pages-disponibles)
5. [Agent terrain — Installation et usage](#5-agent-terrain--installation-et-usage)
6. [Déploiement — Procédure](#6-déploiement--procédure)
7. [Opérations courantes](#7-opérations-courantes)

---

## 1. Accès et URLs

| Ressource | URL |
|-----------|-----|
| Application web | https://petrix.noellahome.org |
| API REST | https://petrix.noellahome.org/api/v1/ |
| Documentation API (Swagger) | https://petrix.noellahome.org/docs |
| EC2 (accès admin) | SSM : `aws ssm start-session --target i-0fc0adfd256c0428d` |
| GitLab | https://gitlab.com/petrix1/petrix |

---

## 2. Architecture déployée

```
Internet
    │
    ▼
EC2 t3.medium (eu-west-1 / IP publique : 3.255.126.244)
    │
    ├── [petrix-frontend]  Nginx → sert le dist React compilé
    │       ↕ proxy /api → petrix-backend:8000
    │
    ├── [petrix-backend]   FastAPI sur :8000
    │       ↕ SQLAlchemy
    │
    ├── [petrix-celery]    Worker Celery (même code que backend)
    │       ↕ Redis broker
    │
    ├── [petrix-db]        PostgreSQL 15
    └── [petrix-redis]     Redis 7

S3 : petrix-storage-655177115922  (fichiers déployés par CI)
```

### Commandes utiles sur EC2

```bash
# Accéder à EC2
aws ssm start-session --target i-0fc0adfd256c0428d

# Voir les containers
docker ps

# Logs backend
docker logs petrix-backend --tail 50 -f

# Logs celery
docker logs petrix-celery --tail 50 -f

# Redémarrer tous les containers
docker restart petrix-backend petrix-celery petrix-frontend
```

---

## 3. Backend API — Endpoints actifs

Base URL : `https://petrix.noellahome.org/api/v1`

### Authentification

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/auth/login` | Login email + password → JWT |
| POST | `/auth/logout` | Invalidation token |
| GET | `/auth/me` | Profil utilisateur connecté |
| POST | `/auth/refresh` | Renouveler le JWT |

### Utilisateurs

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/users` | Liste des utilisateurs |
| POST | `/users` | Créer un utilisateur |
| GET | `/users/{id}` | Détail d'un utilisateur |
| PATCH | `/users/{id}` | Modifier un utilisateur |
| DELETE | `/users/{id}` | Supprimer un utilisateur |

### Actifs (CMDB)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/assets` | Liste des actifs |
| POST | `/assets` | Créer un actif |
| GET | `/assets/{id}` | Détail d'un actif |
| PATCH | `/assets/{id}` | Modifier un actif |
| DELETE | `/assets/{id}` | Supprimer un actif |

### Scans

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/scans` | Liste des scans (filtrable par type/statut) |
| POST | `/scans` | Créer un scan |
| GET | `/scans/{id}` | Détail d'un scan |
| POST | `/scans/{id}/start` | Lancer un scan en PENDING |
| POST | `/scans/{id}/cancel` | Annuler un scan |
| DELETE | `/scans/{id}` | Supprimer un scan |
| GET | `/scans/{id}/findings` | Résultats détaillés (hosts + vulns) |
| POST | `/scans/{id}/agent-results` | Réception résultats agent terrain |
| PATCH | `/scans/{id}/agent-complete` | Finalisation scan agent |
| GET | `/scans/stats/summary` | Statistiques globales |

**Types de scan valides** : `full`, `network`, `vuln`, `hardening`, `compliance`

**Statuts possibles** : `pending`, `running`, `completed`, `failed`, `cancelled`

> **Important** : aucune cible par défaut. Si `targets` est vide → scan échoue avec message d'erreur explicite.

### Hardening (HCO)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/hardening/targets` | Liste des cibles hardening |
| POST | `/hardening/targets` | Créer une cible (IP + OS + SSH user) |
| GET | `/hardening/targets/{id}` | Détail d'une cible |
| POST | `/hardening/targets/{id}/run` | Lancer un audit hardening |
| GET | `/hardening/targets/{id}/results` | Résultats du dernier audit |

### Vulnérabilités

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/vulnerabilities` | Liste des vulns détectées |
| GET | `/vulnerabilities/{id}` | Détail d'une vulnérabilité |
| PATCH | `/vulnerabilities/{id}` | Mettre à jour (statut, remédiation) |

### Journaux d'audit

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/audit-logs` | Liste des événements journalisés |

### Téléchargement agent

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/agent/download` | Télécharger le binaire agent (OS auto-détecté) |

---

## 4. Frontend — Pages disponibles

URL de base : `https://petrix.noellahome.org`

| Page | Route | Description |
|------|-------|-------------|
| Accueil | `/` | Vue d'ensemble des 6 modules |
| Connexion | `/login` | Login email + password |
| Inscription | `/register` | Créer un compte |
| Actifs | `/assets` | CMDB — liste et création d'actifs avec option hardening |
| Scans | `/scans` | Créer et suivre des scans réseau |
| Vulnérabilités | `/vulnerabilities` | Vulns détectées + veille CVE NVD en direct |
| Hardening | `/hardening` | Audit de conformité SSH par cible |
| Agent | `/agent` | Téléchargement + console de suivi agents |
| Utilisateurs | `/users` | Gestion des comptes (admin) |
| Journaux | `/audit-logs` | Historique des événements |

### Fonctionnalités clés par page

**Actifs** : lors de la création d'un actif avec IP/hostname, une case à cocher permet de créer simultanément une cible hardening pour l'audit SSH.

**Vulnérabilités** :
- Onglet 1 : vulnérabilités remontées par les scans
- Onglet 2 : veille CVE live — recherche sur l'API NVD (NIST), filtrable par mot-clé, avec score CVSS, vecteur d'attaque, dates et liens sources

**Agent** :
- Onglet "Installation" : instructions et lien de téléchargement (`.exe` Windows, `.sh` Linux/macOS)
- Onglet "Console" : suivi en temps réel des scans agents (polling toutes les 4 secondes)

---

## 5. Agent terrain — Installation et usage

L'agent s'installe dans le réseau cible et scanne depuis l'intérieur. Il ne nécessite pas d'accès direct depuis le serveur Petrix vers les machines du réseau.

### Flux de fonctionnement

```
Machine cible (réseau interne)
    │
    │  1. Détecte subnet local (netifaces)
    │  2. Crée un scan sur Petrix (POST /api/v1/scans avec "agent":true)
    │  3. Découvre les hôtes (ARP → nmap → socket)
    │  4. Scanne les ports de chaque hôte
    │  5. Envoie les résultats (POST /api/v1/scans/{id}/agent-results)
    │  6. Finalise le scan (PATCH /api/v1/scans/{id}/agent-complete)
    │
    ▼
Petrix (HTTPS) — résultats visibles dans l'interface
```

### Installation Windows

> L'exécutable n'est pas signé → Windows SmartScreen bloque. Procédure de contournement :

**Méthode rapide** :
1. Télécharger `petrix-install.exe` depuis https://petrix.noellahome.org/agent
2. Clic droit sur le fichier → Propriétés → cocher "Débloquer" → OK
3. Double-clic → UAC → Autoriser

**Méthode PowerShell (une seule commande)** :
```powershell
$f="$env:TEMP\petrix-install.exe"
(New-Object Net.WebClient).DownloadFile("https://petrix.noellahome.org/api/v1/agent/download", $f)
Unblock-File $f
Start-Process $f -Verb RunAs -Wait
```

### Installation Linux/macOS

```bash
curl -O https://petrix.noellahome.org/api/v1/agent/download
chmod +x petrix-install.sh
sudo ./petrix-install.sh
```

### Ce que fait l'agent

1. Demande les identifiants Petrix (email + mot de passe)
2. S'authentifie et récupère un JWT
3. Détecte automatiquement tous les sous-réseaux locaux
4. Lance la découverte réseau (ARP broadcast, ping sweep)
5. Scanne les 1000 ports les plus courants sur chaque hôte découvert
6. Remonte dans Petrix : liste des hôtes (IP, MAC, OS, hostname), ports ouverts et services détectés
7. Auto-crée les actifs dans la CMDB pour chaque hôte découvert

---

## 6. Déploiement — Procédure

### Déploiement manuel depuis GitLab CI

Le déploiement ne se fait **jamais automatiquement**. Il est déclenché manuellement :

1. Pousser les changements sur `main` : `git push origin main`
2. Aller sur GitLab → CI/CD → Pipelines
3. Attendre que les jobs lint/test/build passent
4. Cliquer sur le bouton ▶ du job `deploy-production`

### Ce que fait le job de déploiement

```
CI Runner
  │
  ├── 1. Build frontend (npm ci + vite build)
  ├── 2. Upload dist/ + fichiers Python modifiés → S3
  │
  └── 3. Commande SSM sur EC2 :
          ├── Télécharge depuis S3
          ├── docker cp dist/ → petrix-frontend:/usr/share/nginx/html/
          ├── docker cp scans.py → petrix-backend:/app/...
          ├── docker cp scan_tasks.py → petrix-backend:/app/...
          ├── docker cp scan_tasks.py → petrix-celery:/app/...
          └── docker restart petrix-backend petrix-celery
```

### Déploiement manuel direct sur EC2 (urgent)

```bash
# Se connecter à EC2
aws ssm start-session --target i-0fc0adfd256c0428d

# Copier un fichier depuis S3
aws s3 cp s3://petrix-storage-655177115922/deploy/monFichier.py /tmp/

# Copier dans le container
docker cp /tmp/monFichier.py petrix-backend:/app/chemin/vers/fichier.py

# Redémarrer
docker restart petrix-backend
```

---

## 7. Opérations courantes

### Se connecter à Petrix

```
URL    : https://petrix.noellahome.org/login
Email  : (compte admin créé au setup)
Mot de passe : défini lors de l'initialisation
```

### Lancer un scan depuis l'UI

1. Aller sur **Scans** → Nouveau scan
2. Choisir un type (Réseau, Vulnérabilités, Hardening...)
3. Ajouter au moins une cible (IP, plage, hostname) — **obligatoire**
4. Créer → le scan passe en PENDING
5. Cliquer "Démarrer" → Celery prend en charge

### Lancer un audit via l'agent

1. Télécharger et installer l'agent sur une machine du réseau cible
2. Saisir l'URL Petrix et les identifiants
3. L'agent crée automatiquement le scan et commence la découverte
4. Suivre la progression dans **Agent → Console**

### Consulter la veille CVE

1. Aller sur **Vulnérabilités** → onglet "Veille CVE (NVD)"
2. Taper un mot-clé (ex: `windows`, `apache`, `OpenSSH`) + Entrée
3. Les CVE récentes s'affichent avec CVSS, dates, vecteur et liens NVD

### Créer un actif avec audit hardening

1. Aller sur **Actifs** → Nouvel actif
2. Renseigner le nom, type, IP/hostname
3. Cocher "Créer une cible hardening (audit SSH)"
4. Renseigner l'utilisateur SSH et le port
5. L'actif **et** la cible hardening sont créés en même temps

### Accéder aux logs

- **Logs applicatifs** : EC2 via SSM → `docker logs petrix-backend -f`
- **Logs d'audit** : Interface Petrix → **Journaux d'audit**
- **Logs CI/CD** : GitLab → CI/CD → Pipelines → job → logs

---

*Document livrable — reflète l'état de production en juin 2026.*
