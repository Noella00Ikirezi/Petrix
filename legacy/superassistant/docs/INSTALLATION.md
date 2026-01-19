# Installation de SuperAssistant

Guide d'installation complet pour SuperAssistant.

## 📋 Prérequis

### 1. Python 3.10+
```bash
# Vérifier la version
python3 --version

# macOS - Installation via Homebrew
brew install python@3.10

# Linux
sudo apt-get update
sudo apt-get install python3.10 python3.10-venv
```

### 2. Node.js 18+
```bash
# Vérifier la version
node --version

# macOS
brew install node

# Linux
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 3. Clé API Anthropic
1. Créez un compte sur https://console.anthropic.com
2. Générez une clé API dans Settings
3. Conservez-la pour la configuration

## 🚀 Installation automatique

```bash
# Cloner ou télécharger le projet
cd superassistant

# Rendre le script exécutable
chmod +x setup.sh

# Lancer l'installation
./setup.sh
```

Le script `setup.sh` va :
- Créer un environnement virtuel Python
- Installer les dépendances backend
- Installer les dépendances frontend
- Créer le fichier `.env`
- Initialiser la base de données

## 🔧 Installation manuelle

### Backend

```bash
cd backend

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Copier et configurer .env
cp .env.example .env
# Éditer .env et ajouter votre clé API Anthropic
nano .env
```

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Créer le fichier de configuration
cp .env.example .env.local
```

## ⚙️ Configuration

### Backend (.env)

Éditez `backend/.env` :

```bash
ANTHROPIC_API_KEY=sk-ant-...  # Votre clé API
DATABASE_URL=sqlite:///./superassistant.db
APP_NAME=SuperAssistant
DEBUG=True
```

### Frontend (.env.local)

Éditez `frontend/.env.local` :

```bash
VITE_API_URL=http://localhost:8000
```

## 🗄️ Initialisation de la base de données

La base de données sera créée automatiquement au premier lancement du backend.

Pour réinitialiser la base de données :

```bash
cd backend
rm superassistant.db
python main.py
```

## 🎬 Démarrage

### Option 1 : Script automatique

```bash
# À la racine du projet
./start.sh
```

Cela démarre automatiquement backend ET frontend.

### Option 2 : Démarrage manuel

**Terminal 1 - Backend :**
```bash
cd backend
source venv/bin/activate  # macOS/Linux
python main.py
```

Le backend sera disponible sur : http://localhost:8000

**Terminal 2 - Frontend :**
```bash
cd frontend
npm run dev
```

Le frontend sera disponible sur : http://localhost:5173

## ✅ Vérification

1. **Backend** : Accédez à http://localhost:8000
   - Vous devriez voir `{"status": "running"}`

2. **API Docs** : http://localhost:8000/docs
   - Documentation Swagger interactive

3. **Frontend** : http://localhost:5173
   - Interface SuperAssistant

## 🔍 Résolution de problèmes

### Erreur : Port déjà utilisé

```bash
# Trouver et arrêter le processus sur le port 8000
lsof -ti:8000 | xargs kill -9

# Ou sur le port 5173
lsof -ti:5173 | xargs kill -9
```

### Erreur : Module anthropic non trouvé

```bash
cd backend
source venv/bin/activate
pip install anthropic
```

### Erreur : Permission denied sur setup.sh

```bash
chmod +x setup.sh
chmod +x start.sh
```

### Erreur : Clé API invalide

Vérifiez dans `backend/.env` que :
- La clé commence par `sk-ant-`
- Il n'y a pas d'espaces avant/après
- Le fichier est bien nommé `.env` (pas `.env.txt`)

## 📦 Dépendances principales

**Backend :**
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- Anthropic 0.18.1
- Pydantic 2.5.3

**Frontend :**
- React 18
- TypeScript 5
- Vite 5
- TailwindCSS 3
- FullCalendar 6

## 🔄 Mise à jour

```bash
# Backend
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

## 🗑️ Désinstallation

```bash
# Supprimer l'environnement virtuel
rm -rf backend/venv

# Supprimer node_modules
rm -rf frontend/node_modules

# Supprimer la base de données
rm backend/superassistant.db
```

## 📞 Support

En cas de problème :
1. Vérifiez les logs du backend (dans le terminal)
2. Ouvrez la console du navigateur (F12)
3. Consultez [USAGE.md](USAGE.md)

---

Installation terminée ! Consultez [USAGE.md](USAGE.md) pour commencer à utiliser SuperAssistant.
