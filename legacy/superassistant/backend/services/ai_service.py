import httpx
import os
from typing import Dict, Any, List
from config import get_settings

settings = get_settings()


class AIService:
    """Service principal pour toutes les interactions avec Ollama (Mistral local)"""

    def __init__(self):
        self.base_url = "http://localhost:11434/api"
        self.model = "mistral:7b"

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000
    ) -> str:
        """Génère une réponse avec Mistral via Ollama"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json={
                        "model": self.model,
                        "prompt": f"{system_prompt}\n\n{user_message}",
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            raise Exception(f"Erreur AI Service: {str(e)}")

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_message: str,
        response_format: Dict[str, Any],
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Génère une réponse structurée (JSON)"""
        format_instruction = f"\n\nRéponds UNIQUEMENT avec un JSON valide respectant cette structure: {response_format}"
        full_system = system_prompt + format_instruction

        response_text = await self.generate_response(
            system_prompt=full_system,
            user_message=user_message,
            max_tokens=max_tokens
        )

        # Parser le JSON de la réponse
        import json
        try:
            # Extraire le JSON si la réponse contient du texte avant/après
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            return json.loads(json_str)
        except json.JSONDecodeError:
            raise Exception("La réponse de l'IA n'est pas un JSON valide")
