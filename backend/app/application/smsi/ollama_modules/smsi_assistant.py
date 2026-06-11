"""
Assistant SMSI Interactif
Chatbot expert en sécurité de l'information et conformité
"""
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import ORGANIZATION, KNOWLEDGE_BASE_DIR
from modules.ollama_client import OllamaClient


@dataclass
class ChatMessage:
    """Message de conversation"""
    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SMSIAssistant:
    """
    Assistant SMSI interactif avec mémoire de conversation

    Usage:
        assistant = SMSIAssistant()
        assistant.start_chat()  # Mode interactif

        # Ou programmatiquement
        response = assistant.ask("Qu'est-ce que l'ISO 27001 ?")
    """

    SYSTEM_PROMPT = """# IDENTITÉ
Tu es ARIA (Assistant pour le Référentiel et l'Intelligence en Audit), un expert en sécurité de l'information.

# EXPERTISE COMPLÈTE

## Normes et Standards
- **ISO/IEC 27001:2022** : SMSI - toutes les clauses (4-10) et 93 mesures Annexe A
- **ISO/IEC 27002:2022** : Guide d'implémentation des mesures
- **ISO/IEC 27005:2022** : Gestion des risques SI
- **ISO/IEC 27701:2019** : Extension vie privée (PIMS)
- **ISO 22301:2019** : Continuité d'activité (SMCA)
- **ISO 31000:2018** : Management du risque

## Réglementations
- **RGPD** (UE 2016/679) : 99 articles + considérants
- **NIS2** (UE 2022/2555) : Directive cybersécurité
- **AI Act** (UE 2024/1689) : Règlement IA
- **PCI-DSS v4.0** : Sécurité des données de paiement
- **DORA** : Résilience opérationnelle numérique (finance)
- **HDS** : Hébergement données de santé
- **LPM** : Loi de programmation militaire (OIV/OSE)

## Méthodologies
- **EBIOS Risk Manager** : Méthode ANSSI d'analyse de risques
- **MEHARI** : Méthode harmonisée d'analyse des risques
- **ISO 27005** : Processus de gestion des risques
- **ISO 19011** : Lignes directrices d'audit

# CONTEXTE UTILISATEUR
Organisation : {org_name}
Secteur : {org_sector}
Référentiels cibles : {frameworks}

# RÈGLES DE COMPORTEMENT

1. **Précision** : Cite TOUJOURS les références exactes (Article X, Clause Y, Mesure A.X.X)
2. **Praticité** : Donne des exemples concrets et actionnables
3. **Pédagogie** : Explique les concepts complexes simplement
4. **Honnêteté** : Si tu n'es pas sûr, dis-le clairement
5. **Français** : Réponds toujours en français
6. **Structure** : Utilise le Markdown pour structurer tes réponses

# FORMAT DE RÉPONSE

Pour une question technique :
```
## Réponse
[Réponse directe et concise]

## Explication détaillée
[Développement si nécessaire]

## Références
- [Norme/Règlement] Article/Clause X : "Citation ou résumé"

## En pratique
[Comment appliquer concrètement]

## Points d'attention
- [Risques ou pièges à éviter]
```

Pour une demande de conseil :
```
## Recommandation
[Conseil principal]

## Options possibles
1. [Option A] - Avantages/Inconvénients
2. [Option B] - Avantages/Inconvénients

## Notre suggestion
[Option recommandée avec justification]
```

# COMMANDES SPÉCIALES
L'utilisateur peut utiliser ces commandes :
- `/aide` : Afficher l'aide
- `/mesure A.X.X` : Expliquer une mesure ISO 27001
- `/article XX` : Expliquer un article RGPD
- `/risque [sujet]` : Analyser les risques
- `/checklist [sujet]` : Générer une checklist
- `/comparer [norme1] [norme2]` : Comparer deux exigences

Réponds de manière experte, précise et pédagogique."""

    # Base de connaissances intégrée
    KNOWLEDGE_BASE = {
        "iso27001_clauses": {
            "4": "Contexte de l'organisation",
            "5": "Leadership",
            "6": "Planification",
            "7": "Support",
            "8": "Fonctionnement",
            "9": "Évaluation des performances",
            "10": "Amélioration"
        },
        "iso27001_domains": {
            "A.5": "Mesures organisationnelles (37 mesures)",
            "A.6": "Mesures relatives aux personnes (8 mesures)",
            "A.7": "Mesures physiques (14 mesures)",
            "A.8": "Mesures technologiques (34 mesures)"
        },
        "rgpd_key_articles": {
            "5": "Principes relatifs au traitement",
            "6": "Licéité du traitement",
            "7": "Conditions du consentement",
            "12-22": "Droits des personnes concernées",
            "24": "Responsabilité du responsable",
            "25": "Protection dès la conception (Privacy by Design)",
            "28": "Sous-traitant",
            "30": "Registre des traitements",
            "32": "Sécurité du traitement",
            "33": "Notification de violation à l'autorité",
            "34": "Communication de violation aux personnes",
            "35": "Analyse d'impact (AIPD/PIA)",
            "37-39": "Délégué à la protection des données (DPO)"
        },
        "quick_answers": {
            "différence iso 27001 27002": "ISO 27001 définit les EXIGENCES du SMSI (certification possible). ISO 27002 est un GUIDE de bonnes pratiques pour implémenter les mesures.",
            "combien mesures iso 27001": "ISO 27001:2022 contient 93 mesures réparties en 4 thèmes : Organisationnelles (37), Personnes (8), Physiques (14), Technologiques (34).",
            "c'est quoi smsi": "Un SMSI (Système de Management de la Sécurité de l'Information) est un ensemble de politiques, procédures et contrôles pour gérer la sécurité de l'information de manière systématique."
        }
    }

    def __init__(self, client: OllamaClient = None):
        self.client = client or OllamaClient()
        self.conversation_history: List[ChatMessage] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _build_system_prompt(self) -> str:
        """Construit le system prompt avec le contexte"""
        return self.SYSTEM_PROMPT.format(
            org_name=ORGANIZATION.get("name", "Non défini"),
            org_sector=ORGANIZATION.get("sector", "Non défini"),
            frameworks=", ".join(ORGANIZATION.get("frameworks", ["ISO 27001"]))
        )

    def _check_special_commands(self, user_input: str) -> Optional[str]:
        """Vérifie et traite les commandes spéciales"""
        input_lower = user_input.lower().strip()

        if input_lower == "/aide" or input_lower == "/help":
            return """
## Commandes disponibles

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/aide` | Afficher cette aide | `/aide` |
| `/mesure A.X.X` | Expliquer une mesure ISO 27001 | `/mesure A.5.1` |
| `/article XX` | Expliquer un article RGPD | `/article 32` |
| `/risque [sujet]` | Analyser les risques | `/risque télétravail` |
| `/checklist [sujet]` | Générer une checklist | `/checklist audit` |
| `/historique` | Voir l'historique de conversation | `/historique` |
| `/clear` | Effacer l'historique | `/clear` |
| `/quitter` | Quitter l'assistant | `/quitter` |

## Questions que vous pouvez poser
- "Qu'est-ce que l'ISO 27001 ?"
- "Comment implémenter la mesure A.9.1.1 ?"
- "Quelles sont les obligations RGPD pour les sous-traitants ?"
- "Compare ISO 27001 et SOC 2"
"""

        if input_lower == "/historique":
            if not self.conversation_history:
                return "Aucun historique de conversation."
            history = "\n".join([
                f"**{msg.role.upper()}** ({msg.timestamp[:16]}): {msg.content[:100]}..."
                for msg in self.conversation_history[-10:]
            ])
            return f"## Historique récent\n\n{history}"

        if input_lower == "/clear":
            self.conversation_history = []
            return "✅ Historique effacé."

        return None

    def _enrich_context(self, user_input: str) -> str:
        """Enrichit la question avec du contexte de la base de connaissances"""
        input_lower = user_input.lower()

        # Recherche de réponses rapides
        for key, answer in self.KNOWLEDGE_BASE["quick_answers"].items():
            if key in input_lower:
                return f"{user_input}\n\n[Contexte: {answer}]"

        return user_input

    def ask(
        self,
        question: str,
        include_history: bool = True,
        stream: bool = False
    ) -> str:
        """
        Pose une question à l'assistant

        Args:
            question: La question à poser
            include_history: Inclure l'historique de conversation
            stream: Mode streaming (affichage progressif)

        Returns:
            Réponse de l'assistant
        """
        # Vérifier les commandes spéciales
        special_response = self._check_special_commands(question)
        if special_response:
            return special_response

        # Enrichir le contexte
        enriched_question = self._enrich_context(question)

        # Construire les messages
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]

        # Ajouter l'historique (limité aux 10 derniers échanges)
        if include_history and self.conversation_history:
            for msg in self.conversation_history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})

        # Ajouter la question actuelle
        messages.append({"role": "user", "content": enriched_question})

        # Obtenir la réponse
        if stream:
            response_parts = []
            for chunk in self.client.chat(messages, task_type="assistant", stream=True):
                print(chunk, end="", flush=True)
                response_parts.append(chunk)
            print()  # Nouvelle ligne à la fin
            response_text = "".join(response_parts)
        else:
            response = self.client.chat(messages, task_type="assistant")
            if not response.success:
                return f"❌ Erreur : {response.error}"
            response_text = response.content

        # Sauvegarder dans l'historique
        self.conversation_history.append(ChatMessage(role="user", content=question))
        self.conversation_history.append(ChatMessage(role="assistant", content=response_text))

        return response_text

    def start_chat(self):
        """Lance le mode chat interactif"""
        print("=" * 60)
        print("🛡️  ARIA - Assistant SMSI Interactif")
        print("=" * 60)
        print(f"Organisation : {ORGANIZATION.get('name', 'Non définie')}")
        print(f"Référentiels : {', '.join(ORGANIZATION.get('frameworks', []))}")
        print("-" * 60)
        print("Tapez /aide pour voir les commandes disponibles")
        print("Tapez /quitter pour sortir")
        print("=" * 60)
        print()

        while True:
            try:
                user_input = input("👤 Vous : ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("/quitter", "/quit", "/exit", "exit", "quit"):
                    print("\n👋 Au revoir ! Bonne continuation avec votre SMSI.")
                    break

                print("\n🤖 ARIA : ", end="")

                # Utiliser le streaming pour une meilleure expérience
                response = self.ask(user_input, stream=True)

                print()  # Ligne vide après la réponse

            except KeyboardInterrupt:
                print("\n\n👋 Session interrompue. Au revoir !")
                break
            except Exception as e:
                print(f"\n❌ Erreur : {e}")

    def save_conversation(self, filepath: Path = None) -> Path:
        """Sauvegarde la conversation"""
        if filepath is None:
            filepath = KNOWLEDGE_BASE_DIR / f"conversation_{self.session_id}.json"

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": self.session_id,
            "organization": ORGANIZATION.get("name"),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in self.conversation_history
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Conversation sauvegardée : {filepath}")
        return filepath

    def load_conversation(self, filepath: Path) -> None:
        """Charge une conversation précédente"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.session_id = data.get("session_id", self.session_id)
        self.conversation_history = [
            ChatMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg.get("timestamp", "")
            )
            for msg in data.get("messages", [])
        ]
        print(f"📂 Conversation chargée : {len(self.conversation_history)} messages")


# Test et lancement
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Assistant SMSI Interactif")
    parser.add_argument("--question", "-q", help="Poser une question unique")
    parser.add_argument("--interactive", "-i", action="store_true", help="Mode interactif")

    args = parser.parse_args()

    assistant = SMSIAssistant()

    if args.question:
        print(assistant.ask(args.question))
    else:
        assistant.start_chat()

    import atexit
    atexit.register(assitant)
