#!/bin/bash

# SuperAssistant - Script de démarrage

set -e

echo "🚀 Démarrage de SuperAssistant..."
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier que l'installation est faite
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}❌ Backend non installé${NC}"
    echo "Lancez d'abord: ./setup.sh"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo -e "${RED}❌ Frontend non installé${NC}"
    echo "Lancez d'abord: ./setup.sh"
    exit 1
fi

# Vérifier la clé API
if ! grep -q "^ANTHROPIC_API_KEY=sk-ant-" backend/.env 2>/dev/null; then
    echo -e "${RED}❌ Clé API Anthropic non configurée${NC}"
    echo "Éditez backend/.env et ajoutez votre clé API"
    exit 1
fi

# Fonction pour tuer les processus à la sortie
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Arrêt de SuperAssistant...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Arrêté${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Démarrer le backend
echo -e "${BLUE}🔧 Démarrage du backend...${NC}"
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
echo -e "${BLUE}⏳ Attente du backend...${NC}"
sleep 3

# Vérifier que le backend est démarré
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Le backend n'a pas démarré correctement${NC}"
    kill $BACKEND_PID
    exit 1
fi
echo -e "${GREEN}✓ Backend démarré sur http://localhost:8000${NC}"

# Démarrer le frontend
echo -e "${BLUE}🎨 Démarrage du frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Attendre que le frontend soit prêt
sleep 3
echo -e "${GREEN}✓ Frontend démarré sur http://localhost:5173${NC}"

echo ""
echo -e "${GREEN}✅ SuperAssistant est prêt!${NC}"
echo ""
echo -e "${BLUE}📱 Interface: http://localhost:5173${NC}"
echo -e "${BLUE}📊 API: http://localhost:8000${NC}"
echo -e "${BLUE}📚 Docs API: http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}Appuyez sur Ctrl+C pour arrêter${NC}"
echo ""

# Attendre
wait
