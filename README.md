# Petrix — Plateforme d'audit cybersécurité

**Projet annuel ESGI 4SI4 · 2025–2026**  
Binôme : Noëlla IKIREZI & Mathieu MISSAK · Tuteur : Geoffrey Lavigne

---

## Présentation

Petrix est une plateforme SaaS self-hosted conçue pour les auditeurs et équipes sécurité. Elle centralise l'audit de durcissement des systèmes (Linux, macOS, Windows), la gestion des vulnérabilités et la veille CERT-FR dans une interface unifiée.

L'objectif est de permettre à un auditeur de lancer un audit de configuration depuis l'interface, obtenir un score de conformité référencé aux normes ANSSI et CIS, identifier les écarts prioritaires avec leur impact en points, et générer un rapport IA exploitable.

**Accès à la plateforme :** [https://petrix.noellahome.org](https://petrix.noellahome.org)

---

## Fonctionnalités principales

| Module | Description |
|--------|-------------|
| **Hardening (HCO)** | Audit de durcissement sur Linux, macOS, Windows — 80+ contrôles, score A–F, référencés ANSSI-BP-028 / CIS Benchmarks |
| **Rapport d'audit** | Écarts classés par sévérité avec impact en points (−15/−8/−3/−1), conformité multi-norme, analyse Mistral AI |
| **Vulnérabilités** | Suivi des CVE détectées, veille CERT-FR en temps réel, liens NVD / MITRE / CVE.org |
| **Inventaire réseau** | Gestion des actifs avec scans nmap automatisés via Celery |
| **Gestion des accès** | RBAC 4 niveaux (VIEWER / ANALYST / AUDITOR / ADMIN) + MFA par OTP email |
| **Audit trail** | Journalisation de toutes les actions utilisateurs |

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | FastAPI · Python 3.11 · Uvicorn |
| Base de données | PostgreSQL (AWS RDS) · SQLAlchemy 2.0 · Alembic |
| File d'attente | Celery 5.3 · Redis 7 |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS |
| IA | Mistral AI — clé stockée dans AWS SSM SecureString |
| Infrastructure | Docker Compose · AWS EC2 eu-west-1 · Nginx |

---

## Architecture

```
backend/
  app/
    api/v1/          # Endpoints REST
    core/            # JWT, RBAC, audit trail, email
    hardening/       # Moteur HCO + agents (linux.sh, macos.sh, windows.ps1)
    workers/         # Tâches Celery (hardening, scans, email)
    infrastructure/  # Modèles SQLAlchemy, connexion DB

frontend/
  src/
    pages/           # Dashboard, Hardening, Vulnérabilités, Rapport, Actifs…
    api/             # Client Axios
    stores/          # État global Zustand

docker/              # docker-compose.prod.yml · nginx.prod.conf
```

---

## Lancer en local

```bash
cp .env.template .env   # Remplir les variables
make dev                # Démarre tous les containers Docker
```

---

## Livrables

- **Code source** — dépôt GitHub (branche `main`)
- **Plateforme déployée** — [https://petrix.noellahome.org](https://petrix.noellahome.org)
- **Rapport d'activité** — document détaillant les choix techniques et le travail réalisé
- **Soutenance** — présentation ESGI · 26 juillet 2026

---

> Projet réalisé dans le cadre du projet annuel ESGI 4ème année — Spécialité Sécurité Informatique (4SI4)  
> Noëlla IKIREZI & Mathieu MISSAK
