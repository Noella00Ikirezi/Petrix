# Documentation API - SuperAssistant

Documentation complète de l'API REST de SuperAssistant.

## Base URL

```
http://localhost:8000
```

## Documentation Interactive

Swagger UI : http://localhost:8000/docs

ReDoc : http://localhost:8000/redoc

## Endpoints Principaux

### ✅ Tâches (`/api/tasks`)

#### GET `/api/tasks`
Récupère toutes les tâches avec filtres optionnels.

**Paramètres de requête** :
- `skip` (int) : Nombre d'éléments à sauter
- `limit` (int) : Nombre maximum d'éléments
- `category` (string) : Filtrer par catégorie
- `status` (string) : Filtrer par statut

**Exemple** :
```bash
curl http://localhost:8000/api/tasks?status=todo&category=SMSI
```

**Réponse** :
```json
[
  {
    "id": 1,
    "title": "Rédiger politique mots de passe",
    "description": "Politique conforme ANSSI",
    "category": "SMSI",
    "priority": "haute",
    "status": "todo",
    "deadline": "2025-01-15T10:00:00",
    "estimated_time": 3.0,
    "actual_time": null,
    "tags": ["politique", "anssi"],
    "project_id": null,
    "created_at": "2025-01-10T09:00:00",
    "updated_at": "2025-01-10T09:00:00"
  }
]
```

#### POST `/api/tasks`
Crée une nouvelle tâche.

**Corps de requête** :
```json
{
  "title": "Ma nouvelle tâche",
  "description": "Description détaillée",
  "category": "Études",
  "priority": "moyenne",
  "status": "todo",
  "deadline": "2025-01-20T12:00:00",
  "estimated_time": 2.5,
  "tags": ["projet", "urgent"]
}
```

#### PATCH `/api/tasks/{task_id}`
Met à jour une tâche.

#### DELETE `/api/tasks/{task_id}`
Supprime une tâche.

---

### 🎯 Projets (`/api/projects`)

#### GET `/api/projects`
Liste tous les projets.

#### POST `/api/projects`
Crée un nouveau projet.

**Exemple** :
```json
{
  "name": "Mise en conformité RGPD",
  "description": "Projet de mise en conformité complète",
  "status": "active",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-06-30T00:00:00",
  "progress": 0
}
```

---

### 📅 Agenda (`/api/calendar`)

#### GET `/api/calendar`
Récupère les événements.

**Paramètres** :
- `start_date` (datetime) : Date de début
- `end_date` (datetime) : Date de fin
- `category` (string) : Filtrer par catégorie

#### POST `/api/calendar`
Crée un événement.

---

### 🤖 IA (`/api/ai`)

#### POST `/api/ai/prioritize`
Analyse et priorise les tâches avec l'IA.

**Corps de requête** :
```json
{
  "context": {
    "week_type": "entreprise",
    "focus_area": "SMSI"
  }
}
```

**Réponse** :
```json
{
  "top_tasks": [
    {
      "task_id": 5,
      "title": "Finaliser registre des traitements",
      "priority_score": 95.5,
      "justification": "Deadline dans 2 jours, priorité haute, requis pour audit RGPD imminent."
    }
  ],
  "daily_plan": "Matinée (9h-12h): Registre des traitements\nAprès-midi (14h-17h): Revue politique de sécurité",
  "analysis": "Charge de travail élevée cette semaine avec 3 deadlines critiques. Focus sur les tâches RGPD prioritaires."
}
```

#### POST `/api/ai/generate-email`
Génère un email professionnel.

**Corps de requête** :
```json
{
  "recipient_type": "manager",
  "context": "smsi",
  "tone": "professionnel",
  "subject": "Avancement projet mise en conformité",
  "key_points": [
    "80% des politiques rédigées",
    "Formation utilisateurs planifiée",
    "Audit prévu mi-février"
  ],
  "user_context": "Alternance cybersécurité, responsable SMSI"
}
```

**Réponse** :
```json
{
  "subject": "Point d'avancement - Projet mise en conformité RGPD",
  "body": "Bonjour M. Dupont,\n\nJe vous fais un point sur l'avancement du projet...",
  "suggestions": [
    "Ajouter un planning détaillé en pièce jointe",
    "Proposer une réunion de suivi"
  ]
}
```

#### POST `/api/ai/generate-document`
Génère un document SMSI.

**Corps de requête** :
```json
{
  "doc_type": "politique",
  "title": "Politique de gestion des mots de passe",
  "scope": "Tous les collaborateurs et systèmes de l'entreprise",
  "requirements": [
    "Conformité ANSSI",
    "Mots de passe minimum 12 caractères",
    "Changement tous les 90 jours",
    "Pas de réutilisation des 5 derniers"
  ],
  "references": ["ISO 27001:2013", "ANSSI BP-012"]
}
```

**Réponse** :
```json
{
  "title": "POL-SEC-001 - Politique de Gestion des Mots de Passe",
  "content": "# Politique de Gestion des Mots de Passe\n\n## 1. Objet\n...",
  "structure": [
    "1. Objet",
    "2. Périmètre",
    "3. Règles de complexité",
    "4. Règles de gestion",
    "5. Exceptions",
    "6. Sanctions"
  ],
  "compliance_notes": [
    "Article 32 RGPD: Mesures techniques et organisationnelles appropriées",
    "ANSSI BP-012: Recommandations relatives aux mots de passe"
  ]
}
```

#### POST `/api/ai/chat`
Assistant conversationnel.

**Corps de requête** :
```json
{
  "message": "Comment organiser ma semaine avec 3 gros projets ?",
  "context": {}
}
```

---

### 📄 Documents (`/api/documents`)

#### GET `/api/documents`
Liste les documents sauvegardés.

**Paramètres** :
- `type` (string) : Filtrer par type
- `status` (string) : Filtrer par statut

#### POST `/api/documents`
Sauvegarde un document.

---

### 📚 Base de Connaissances (`/api/knowledge`)

#### GET `/api/knowledge`
Récupère les items de connaissance.

#### POST `/api/knowledge`
Crée un nouvel item.

---

## Codes de Statut HTTP

| Code | Signification |
|------|---------------|
| 200 | OK - Requête réussie |
| 201 | Created - Ressource créée |
| 204 | No Content - Suppression réussie |
| 400 | Bad Request - Données invalides |
| 404 | Not Found - Ressource non trouvée |
| 500 | Internal Server Error - Erreur serveur |

## Gestion des Erreurs

Format de réponse d'erreur :

```json
{
  "detail": "Message d'erreur explicatif"
}
```

## Authentification

**Actuellement** : Aucune authentification (usage local mono-utilisateur)

**Futur** : Possibilité d'ajouter JWT si multi-utilisateurs

## Rate Limiting

**Actuellement** : Aucune limitation

**Note** : L'API Anthropic a ses propres limites (voir documentation Claude)

## Exemples d'Utilisation

### Python

```python
import requests

# Créer une tâche
task = {
    "title": "Finaliser audit",
    "category": "SMSI",
    "priority": "haute"
}
response = requests.post("http://localhost:8000/api/tasks", json=task)
print(response.json())

# Prioriser avec l'IA
response = requests.post("http://localhost:8000/api/ai/prioritize", json={})
priorities = response.json()
for task in priorities["top_tasks"]:
    print(f"{task['title']}: {task['justification']}")
```

### JavaScript

```javascript
// Récupérer les tâches
const tasks = await fetch('http://localhost:8000/api/tasks')
  .then(res => res.json());

// Générer un email
const emailRequest = {
  recipient_type: 'professeur',
  context: 'demande',
  tone: 'formel',
  subject: 'Demande de rendez-vous',
  key_points: ['Sujet: projet de fin d'études', 'Disponibilités: lundi ou jeudi']
};

const email = await fetch('http://localhost:8000/api/ai/generate-email', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(emailRequest)
}).then(res => res.json());

console.log(email.body);
```

### cURL

```bash
# Lister les tâches en cours
curl -X GET "http://localhost:8000/api/tasks?status=in_progress"

# Créer un projet
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Projet de fin d'études",
    "status": "active",
    "progress": 0
  }'

# Générer un document SMSI
curl -X POST "http://localhost:8000/api/ai/generate-document" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_type": "procedure",
    "title": "Procédure de gestion des incidents",
    "scope": "Équipe sécurité",
    "requirements": ["ISO 27035", "Processus en 5 étapes"]
  }'
```

## Webhooks (Futur)

Fonctionnalité prévue pour notifier des événements :
- Nouvelle tâche créée
- Deadline approchante
- Document généré

## Versioning

Version actuelle : **v1.0.0**

L'API suit le versioning sémantique (SemVer).

---

**Pour plus d'informations** : Consultez la documentation Swagger interactive à http://localhost:8000/docs
