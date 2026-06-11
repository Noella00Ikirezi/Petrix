"""
Configuration centrale du projet SMSI-Ollama
"""
import os
from pathlib import Path

# === CHEMINS ===
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
OUTPUTS_DIR = BASE_DIR / "outputs"
DOCUMENTS_DIR = OUTPUTS_DIR / "documents"
AUDITS_DIR = OUTPUTS_DIR / "audits"
ANALYSES_DIR = OUTPUTS_DIR / "analyses"

# === OLLAMA ===
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # ou qwen2.5:14b
OLLAMA_TIMEOUT = 120  # secondes

# === MODÈLES PAR TÂCHE ===
MODELS = {
    "documentation": "mistral",      # Génération de documents
    "analysis": "mistral",           # Analyse de conformité
    "assistant": "mistral",          # Chat interactif
    "audit": "mistral",              # Rapports d'audit
    "code": "qwen2.5-coder:7b",      # Si besoin de générer des scripts
}

# === PARAMÈTRES LLM ===
LLM_PARAMS = {
    "documentation": {
        "temperature": 0.3,
        "top_p": 0.9,
        "num_predict": 4096,
    },
    "analysis": {
        "temperature": 0.1,
        "top_p": 0.95,
        "num_predict": 4096,
    },
    "assistant": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_predict": 2048,
    },
    "audit": {
        "temperature": 0.2,
        "top_p": 0.9,
        "num_predict": 8192,
    },
}

# === ORGANISATION (À PERSONNALISER) ===
ORGANIZATION = {
    "name": "Votre Organisation",
    "sector": "Services numériques",
    "size": "50-250 employés",
    "scope": "Système d'information principal",
    "frameworks": ["ISO 27001:2022", "RGPD", "NIS2"],
    "maturity_level": "Initial",
}

# === CLASSIFICATION DES DOCUMENTS ===
DOC_CLASSIFICATION = {
    "public": "Public",
    "internal": "Interne",
    "confidential": "Confidentiel",
    "secret": "Secret",
}

# === MAPPING DES TYPES DE DOCUMENTS ===
DOC_TYPES = {
    "POL": "Politique",
    "PRO": "Procédure",
    "GUI": "Guide",
    "REG": "Registre",
    "CHK": "Checklist",
    "FOR": "Formulaire",
    "RAP": "Rapport",
}

# === PRIORITÉS ===
PRIORITIES = {
    "critical": {"label": "Critique", "days": 30},
    "high": {"label": "Haute", "days": 90},
    "medium": {"label": "Moyenne", "days": 180},
    "low": {"label": "Basse", "days": 365},
}

# === NIVEAUX DE MATURITÉ ===
MATURITY_LEVELS = {
    0: {"name": "Inexistant", "description": "Aucune mesure en place"},
    1: {"name": "Initial", "description": "Mesures ad-hoc, non documentées"},
    2: {"name": "Géré", "description": "Mesures documentées, application incohérente"},
    3: {"name": "Défini", "description": "Processus standardisé et communiqué"},
    4: {"name": "Maîtrisé", "description": "Mesures surveillées avec métriques"},
    5: {"name": "Optimisé", "description": "Amélioration continue"},
}
