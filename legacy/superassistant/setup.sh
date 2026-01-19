#!/bin/bash

# SuperAssistant - Script d'installation automatique

set -e

echo "🚀 Installation de SuperAssistant..."
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier Python
echo -e "${BLUE}🐍 Vérification de Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    echo "Installez Python 3.10+ depuis https://www.python.org/"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} trouvé${NC}"
echo ""

# Vérifier Node.js
echo -e "${BLUE}📦 Vérification de Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js n'est pas installé${NC}"
    echo "Installez Node.js 18+ depuis https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION} trouvé${NC}"
echo ""

# Installation Backend
echo -e "${BLUE}🔧 Installation du backend...${NC}"
cd backend

# Créer environnement virtuel
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Environnement virtuel créé${NC}"
fi

# Activer environnement virtuel
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dépendances backend installées${NC}"

# Configurer .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Fichier .env créé${NC}"
    echo -e "${BLUE}⚠️  N'oubliez pas d'ajouter votre clé API Anthropic dans backend/.env${NC}"
fi

cd ..
echo ""

# Installation Frontend
echo -e "${BLUE}🎨 Installation du frontend...${NC}"
cd frontend

npm install
echo -e "${GREEN}✓ Dépendances frontend installées${NC}"

# Configurer .env.local
if [ ! -f ".env.local" ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env.local
    echo -e "${GREEN}✓ Fichier .env.local créé${NC}"
fi

cd ..
echo ""

# Résumé
echo -e "${GREEN}✅ Installation terminée avec succès!${NC}"
echo ""
echo -e "${BLUE}📝 Prochaines étapes:${NC}"
echo "1. Éditez backend/.env et ajoutez votre clé API Anthropic"
echo "2. Lancez l'application avec: ./start.sh"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- Installation: docs/INSTALLATION.md"
echo "- Utilisation: docs/USAGE.md"
echo ""
echo -e "${GREEN}Bonne productivité avec SuperAssistant! 🚀${NC}"
