# 🚀 SuperAssistant - Démarrage Ultra-Rapide

Guide de démarrage en 5 minutes pour SuperAssistant.

## ⚡ Installation Express

```bash
# 1. Aller dans le dossier
cd superassistant

# 2. Installer (une seule fois)
chmod +x setup.sh
./setup.sh

# 3. Configurer la clé API
nano backend/.env
# Ajoutez : ANTHROPIC_API_KEY=sk-ant-votre-clé

# 4. Démarrer
chmod +x start.sh
./start.sh
```

**C'est tout ! 🎉**

Ouvrez : http://localhost:5173

## 🎯 Premières Actions

### 1. Créez votre première tâche

```
Dashboard → Tâches → Nouvelle tâche
- Titre: "Test SuperAssistant"
- Catégorie: "Personnel"
- Priorité: "Haute"
→ Créer
```

### 2. Testez la priorisation IA

```
Dashboard → "Analyser mes tâches"
```

L'IA vous donne :
- Top 5 priorités
- Justifications
- Planning suggéré

### 3. Générez un document SMSI

```
Documents SMSI →
- Type: "Politique"
- Titre: "Test politique de sécurité"
- Périmètre: "Organisation de 50 personnes"
- Exigences: "Conformité ISO 27001"
→ Générer
```

## 🛠️ Commandes Utiles

```bash
# Démarrer
./start.sh

# Arrêter
Ctrl+C dans le terminal

# Réinstaller
rm -rf backend/venv frontend/node_modules
./setup.sh

# Voir les logs backend
cd backend && source venv/bin/activate && python main.py

# Voir les logs frontend
cd frontend && npm run dev
```

## 📚 Documentation Complète

- [README.md](README.md) - Vue d'ensemble
- [INSTALLATION.md](docs/INSTALLATION.md) - Installation détaillée
- [USAGE.md](docs/USAGE.md) - Guide d'utilisation complet
- [API.md](docs/API.md) - Documentation API

## 🐛 Problèmes Fréquents

### "Port déjà utilisé"
```bash
# Tuer le processus
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
```

### "Clé API invalide"
Vérifiez dans `backend/.env` :
- Clé commence par `sk-ant-`
- Pas d'espaces
- Fichier bien nommé `.env` (pas `.env.txt`)

### "Module not found"
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## 💡 Astuces

- **Dark mode** : Bouton en haut à droite
- **API Docs** : http://localhost:8000/docs
- **Sauvegarde DB** : `cp backend/superassistant.db backup.db`

## 📞 Besoin d'Aide ?

1. Consultez [USAGE.md](docs/USAGE.md)
2. Vérifiez [API.md](docs/API.md)
3. Ouvrez une issue GitHub

---

**Prêt à booster votre productivité ! 🚀**
