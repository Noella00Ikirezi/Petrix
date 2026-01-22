"""Ollama AI integration service for SMSI document generation.

100% Open Source - Self-hosted LLM with Mistral, Mixtral, Llama3, etc.
No API key required, no data sent to external services.
"""
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx
from loguru import logger

from app.config import settings


@dataclass
class AIGenerationResult:
    """Result of AI document generation."""
    content: str
    tokens_input: int
    tokens_output: int
    generation_time: float
    model_used: str
    success: bool
    error: Optional[str] = None


class OllamaAIService:
    """Service for Ollama AI integration - 100% Open Source, Self-hosted.

    Supported models:
    - mistral (7B) - Bon équilibre performance/vitesse
    - mixtral (8x7B) - Plus performant, nécessite plus de RAM
    - llama3 (8B/70B) - Très performant
    - codellama - Spécialisé code
    - phi3 - Léger et rapide
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_API_URL
        self.default_model = settings.OLLAMA_MODEL
        self.timeout = 300.0  # 5 minutes for large documents

    async def check_health(self) -> Dict[str, Any]:
        """Check Ollama service health and available models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "models_available": models,
                        "current_model": self.default_model,
                        "model_ready": self.default_model in models or f"{self.default_model}:latest" in models
                    }
                return {"status": "error", "message": "Unexpected response"}
        except httpx.ConnectError:
            return {"status": "offline", "message": "Ollama not reachable"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def pull_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Pull a model from Ollama library."""
        model = model_name or self.default_model
        try:
            logger.info(f"Pulling model {model}...")
            async with httpx.AsyncClient(timeout=1800.0) as client:  # 30 min timeout
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model, "stream": False}
                )
                if response.status_code == 200:
                    logger.info(f"Model {model} pulled successfully")
                    return {"success": True, "model": model}
                return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Failed to pull model: {str(e)}")
            return {"success": False, "error": str(e)}

    async def generate_document(
        self,
        template_prompt: str,
        context: Dict[str, Any],
        document_type: str,
        max_tokens: int = 8000,
        temperature: float = 0.3
    ) -> AIGenerationResult:
        """Generate a SMSI document using Ollama."""
        start_time = time.time()

        try:
            # Build prompts
            system_prompt = self._build_system_prompt(document_type)
            user_prompt = self._build_user_prompt(template_prompt, context)

            # Make API call to Ollama
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.default_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "top_p": 0.95,
                        }
                    }
                )

                response.raise_for_status()
                data = response.json()

            generation_time = time.time() - start_time

            # Extract content
            content = data.get("message", {}).get("content", "")

            # Token counts from Ollama
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            logger.info(
                f"Ollama generation completed: "
                f"{prompt_eval_count} input, "
                f"{eval_count} output tokens, "
                f"{generation_time:.2f}s"
            )

            return AIGenerationResult(
                content=content,
                tokens_input=prompt_eval_count,
                tokens_output=eval_count,
                generation_time=generation_time,
                model_used=self.default_model,
                success=True
            )

        except httpx.ConnectError:
            error_msg = "Ollama not reachable. Start with: docker-compose up ollama"
            logger.error(error_msg)
            return AIGenerationResult(
                content="",
                tokens_input=0,
                tokens_output=0,
                generation_time=time.time() - start_time,
                model_used=self.default_model,
                success=False,
                error=error_msg
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code}")
            return AIGenerationResult(
                content="",
                tokens_input=0,
                tokens_output=0,
                generation_time=time.time() - start_time,
                model_used=self.default_model,
                success=False,
                error=f"API Error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Ollama generation error: {str(e)}")
            return AIGenerationResult(
                content="",
                tokens_input=0,
                tokens_output=0,
                generation_time=time.time() - start_time,
                model_used=self.default_model,
                success=False,
                error=str(e)
            )

    def _build_system_prompt(self, document_type: str) -> str:
        """Build system prompt based on document type."""
        base_prompt = """Tu es un expert en cybersecurite et conformite reglementaire, specialise dans la creation de Systemes de Management de la Securite de l'Information (SMSI).

Tu dois generer des documents professionnels en francais, conformes aux normes suivantes:
- ISO 27001:2022 et ISO 27002:2022
- DORA (Digital Operational Resilience Act)
- NIS2 (Network and Information Security Directive)
- RGPD (Reglement General sur la Protection des Donnees)
- PCI DSS v4.0
- EU AI Act (Reglement europeen sur l'Intelligence Artificielle)

Regles de generation:
1. Utilise un langage professionnel et precis
2. Structure le document avec des sections claires
3. Inclus des references aux articles et controles des normes applicables
4. Adapte le contenu au contexte de l'organisation
5. Propose des mesures concretes et actionnables
6. Respecte le niveau de securite demande (N1/N2/N3)

Format de sortie: Markdown structure avec titres, sous-titres, listes et tableaux."""

        type_prompts = {
            "policy": """

Tu generes une POLITIQUE de securite. Une politique definit:
- Les objectifs de securite
- Le perimetre d'application
- Les roles et responsabilites
- Les principes directeurs
- Les sanctions en cas de non-respect""",

            "procedure": """

Tu generes une PROCEDURE operationnelle. Une procedure definit:
- L'objectif de la procedure
- Le champ d'application
- Les etapes detaillees (qui, quoi, quand, comment)
- Les documents associes
- Les indicateurs de suivi""",

            "register": """

Tu generes un REGISTRE ou INVENTAIRE. Structure:
- En-tetes de colonnes clairs
- Format tableau Markdown
- Exemples de donnees a remplir
- Instructions de mise a jour""",

            "checklist": """

Tu generes une CHECKLIST de controle. Structure:
- Questions ou points de verification
- Cases a cocher (format Markdown)
- Colonnes: Element, Conforme, Non-conforme, N/A, Commentaires
- Instructions d'utilisation"""
        }

        return base_prompt + type_prompts.get(document_type, "")

    def _build_user_prompt(self, template_prompt: str, context: Dict[str, Any]) -> str:
        """Build user prompt with organization context."""
        context_text = self._format_context(context)

        return f"""# Contexte de l'organisation

{context_text}

# Instructions de generation

{template_prompt}

# Format attendu

Genere le document complet en Markdown, pret a etre converti en DOCX/PDF.
Inclus un cartouche de document avec:
- Titre du document
- Version
- Date de creation
- Classification
- Auteur/Approbateur (a completer)
"""

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable text."""
        lines = []

        if "organization" in context:
            org = context["organization"]
            lines.append(f"**Organisation**: {org.get('name', 'N/A')}")
            lines.append(f"**Type**: {org.get('type', 'N/A')}")
            lines.append(f"**Taille**: {org.get('size', 'N/A')}")
            lines.append(f"**Secteur**: {org.get('sector', 'N/A')}")
            lines.append("")

        if "security_level" in context:
            level_names = {
                "n1_standard": "N1 - Standard",
                "n2_reinforced": "N2 - Renforce",
                "n3_critical": "N3 - Critique"
            }
            lines.append(f"**Niveau de securite**: {level_names.get(context['security_level'], context['security_level'])}")
            lines.append("")

        if "frameworks" in context:
            lines.append("**Referentiels applicables**:")
            for fw in context["frameworks"]:
                lines.append(f"- {fw}")
            lines.append("")

        if "responses" in context:
            lines.append("**Informations collectees**:")
            for key, value in context["responses"].items():
                if isinstance(value, list):
                    lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(f"- {key}: {value}")
            lines.append("")

        return "\n".join(lines)

    async def suggest_answer(
        self,
        question: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Suggest an answer to a QCM question based on context."""
        try:
            prompt = f"""En tant qu'expert SMSI, suggere une reponse pour la question suivante.

Contexte:
{self._format_context(context)}

Question: {question}
"""
            if options:
                prompt += "\nOptions disponibles:\n"
                for i, opt in enumerate(options, 1):
                    prompt += f"{i}. {opt}\n"
                prompt += "\nIndique le numero de l'option recommandee et explique brievement pourquoi."
            else:
                prompt += "\nPropose une reponse appropriee et explique brievement."

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.default_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 500,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()

            suggestion = data.get("message", {}).get("content", "")

            return {
                "suggestion": suggestion,
                "confidence": 0.8,
                "success": True
            }

        except Exception as e:
            logger.error(f"AI suggestion error: {str(e)}")
            return {
                "suggestion": None,
                "confidence": 0,
                "success": False,
                "error": str(e)
            }

    async def improve_document(
        self,
        content: str,
        feedback: str,
        document_type: str
    ) -> AIGenerationResult:
        """Improve an existing document based on feedback."""
        prompt = f"""Ameliore le document suivant en tenant compte du feedback.

# Document actuel

{content}

# Feedback / Demandes d'amelioration

{feedback}

# Instructions

1. Conserve la structure generale du document
2. Integre les ameliorations demandees
3. Maintiens la coherence avec les normes de securite
4. Genere le document complet ameliore en Markdown
"""

        return await self.generate_document(
            template_prompt=prompt,
            context={},
            document_type=document_type
        )

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("models", [])
                return []
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []


# Singleton instance
ollama_service = OllamaAIService()

# Alias for backward compatibility
mistral_service = ollama_service
