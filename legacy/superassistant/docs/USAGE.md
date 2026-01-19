# Guide d'Utilisation - SuperAssistant

Guide complet pour utiliser toutes les fonctionnalités de SuperAssistant.

## 🚀 Démarrage Rapide

### Première Utilisation

1. **Lancez l'application** :
   ```bash
   ./start.sh
   ```

2. **Accédez à l'interface** : http://localhost:5173

3. **Vérifiez le backend** : http://localhost:8000/health

## 📊 Dashboard

Le Dashboard est votre point de départ quotidien.

### Statistiques
- **Total Tâches** : Nombre total de tâches actives
- **À faire** : Tâches non commencées
- **En cours** : Tâches en progression

### Priorisation IA 🤖

1. Cliquez sur **"Analyser mes tâches"**
2. L'IA analyse toutes vos tâches selon :
   - Deadlines
   - Priorités
   - Effort estimé
   - Dépendances
3. Vous recevez :
   - **Top 5 priorités** avec justifications
   - **Planning journalier optimisé**
   - **Analyse de charge de travail**

**Astuce** : Lancez la priorisation chaque matin pour organiser votre journée !

## ✅ Gestion des Tâches

### Créer une Tâche

1. Allez dans **Tâches**
2. Cliquez **"Nouvelle tâche"**
3. Remplissez :
   - **Titre** : Description courte
   - **Catégorie** : Études/SMSI/Support/Projets/Personnel
   - **Priorité** : Haute/Moyenne/Basse
   - **Deadline** : Date limite (optionnel)
   - **Temps estimé** : En heures (optionnel)
   - **Tags** : Mots-clés pour filtrer

### Filtrer les Tâches

Utilisez les boutons de filtre :
- **Toutes** : Vue complète
- **À faire** : Tâches non démarrées
- **En cours** : Travail actuel
- **Terminées** : Archive

### Workflow Recommandé

1. **Matin** : Créez vos tâches pour la journée
2. **Lancez la priorisation IA**
3. **Travaillez** sur les top 5 recommandées
4. **Soir** : Marquez comme terminées

## 🎯 Gestion de Projets

### Créer un Projet

1. Allez dans **Projets**
2. Cliquez **"Nouveau projet"**
3. Définissez :
   - **Nom** du projet
   - **Description**
   - **Dates** (début/fin)
   - **Statut** : Active/Terminé/Archivé

### Lier des Tâches à un Projet

Lors de la création d'une tâche, sélectionnez le projet dans le champ `project_id`.

### Suivi de Progression

La progression est calculée automatiquement selon :
- Nombre de tâches liées
- Tâches complétées
- Mise à jour en temps réel

## 📅 Agenda (À venir)

Fonctionnalités prévues :
- Vue Jour/Semaine/Mois
- Timeboxing (glisser-déposer tâches)
- Timer Pomodoro intégré
- Codes couleur par catégorie

## 📄 Documents SMSI

### Générer un Document avec l'IA

1. Allez dans **Documents SMSI**
2. Dans le formulaire :
   - **Type** : Politique/Procédure/Guide/Registre/Rapport/CR
   - **Titre** : Ex: "Politique de gestion des mots de passe"
   - **Périmètre** : Contexte et périmètre d'application
   - **Exigences** : Ajoutez vos exigences spécifiques

3. Cliquez **"Générer le document"**

4. L'IA génère :
   - Document complet structuré
   - Conforme ISO 27001 / ANSSI
   - Notes de conformité RGPD
   - Prêt à l'emploi

5. **Sauvegardez** pour le retrouver plus tard

### Types de Documents Supportés

| Type | Exemple | Usage |
|------|---------|-------|
| **Politique** | Politique de mots de passe | Règles générales |
| **Procédure** | Procédure de gestion des incidents | Processus détaillé |
| **Guide** | Guide utilisateur VPN | Instructions |
| **Registre** | Registre des risques | Suivi/inventaire |
| **Rapport** | Rapport d'audit | Compte-rendu |
| **CR** | Compte-rendu COPIL | Réunion |

### Bonnes Pratiques

**Soyez précis dans le périmètre** :
- ✅ "Application pour les 50 collaborateurs du siège et 20 télétravail leurs"
- ❌ "Tous les utilisateurs"

**Listez vos exigences clairement** :
- ✅ "Conformité RGPD article 32"
- ✅ "Mots de passe minimum 12 caractères"
- ❌ "Bonne sécurité"

## 📚 Base de Connaissances (À venir)

Fonctionnalités prévues :
- Stockage de templates réutilisables
- Solutions aux problèmes récurrents
- Notes personnelles
- Recherche full-text

## 🤖 Assistant IA

### Utilisation via l'API

L'IA est disponible pour :

1. **Priorisation** : Analyse automatique quotidienne
2. **Emails** : Génération d'emails professionnels
3. **Documents** : Rédaction de docs SMSI
4. **Chat** : Questions générales (bientôt interface)

### Contexte Utilisateur

L'IA utilise votre contexte pour personnaliser ses réponses :
- Rôle et responsabilités
- Planning d'alternance
- Préférences de style
- Historique de projets

Configurez dans **Paramètres** > **Contexte Utilisateur**

## ⚙️ Paramètres

### Configuration API

La clé API Anthropic est configurée dans `backend/.env` :

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

**Sécurité** : Ne partagez JAMAIS votre clé API !

### Thème

Basculez entre mode clair/sombre avec le bouton en haut à droite.

### Sauvegarde

Vos données sont stockées localement dans `backend/superassistant.db`.

**Sauvegarde manuelle** :
```bash
cp backend/superassistant.db backup_$(date +%Y%m%d).db
```

## 💡 Astuces & Workflow

### Routine Matinale (5 min)

1. Ouvrez SuperAssistant
2. Créez vos tâches pour la journée
3. Lancez la **priorisation IA**
4. Suivez le planning suggéré

### Gestion de l'Alternance

**Semaine École** :
- Catégorie : "Études"
- Tags : #cours #projet #examen

**Semaine Entreprise** :
- Catégories : "SMSI", "Support", "Projets"
- Tags : #urgent #client #interne

### Rédaction de Documents

**Workflow efficace** :
1. Listez vos exigences d'abord
2. Générez avec l'IA
3. Relisez et ajustez
4. Sauvegardez en version "draft"
5. Faites relire puis passez en "approved"

### Pomodoro (à venir)

Technique recommandée :
- 25 min focus sur tâche prioritaire
- 5 min pause
- Après 4 cycles : 15-30 min pause longue

## 🐛 Dépannage

### L'IA ne répond pas

1. Vérifiez la clé API dans `backend/.env`
2. Vérifiez les logs du backend
3. Testez : `curl http://localhost:8000/health`

### Tâches non chargées

1. Vérifiez que le backend est démarré
2. Ouvrez la console navigateur (F12)
3. Regardez l'onglet Network pour les erreurs

### Base de données corrompue

```bash
cd backend
rm superassistant.db
python main.py  # Recrée la DB
```

## 📞 Raccourcis Clavier (à venir)

| Raccourci | Action |
|-----------|--------|
| `Ctrl+N` | Nouvelle tâche |
| `Ctrl+P` | Prioriser |
| `Ctrl+D` | Dashboard |
| `Ctrl+/` | Assistant IA |

## 🔄 Mises à Jour

Pour mettre à jour SuperAssistant :

```bash
# Backend
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

## 📖 Pour Aller Plus Loin

- [INSTALLATION.md](INSTALLATION.md) - Installation complète
- [API.md](API.md) - Documentation de l'API
- [GitHub Issues](https://github.com/votre-repo) - Signaler un bug

---

**Bon travail avec SuperAssistant ! 🚀**

N'oubliez pas : l'IA est là pour vous assister, pas vous remplacer. Utilisez-la comme un outil d'optimisation de votre productivité.
