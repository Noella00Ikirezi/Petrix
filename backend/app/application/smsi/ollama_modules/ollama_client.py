"""
Client Ollama pour SMSI
Gère toutes les communications avec l'API Ollama
"""
import requests
import json
from typing import Optional, Generator, Dict, List
from dataclasses import dataclass
import sys
sys.path.append('..')
from config.settings import OLLAMA_HOST, OLLAMA_TIMEOUT, MODELS, LLM_PARAMS


@dataclass
class OllamaResponse:
    """Structure de réponse Ollama"""
    content: str
    model: str
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class OllamaClient:
    """
    Client pour interagir avec Ollama

    Usage:
        client = OllamaClient()
        response = client.generate("Explique l'ISO 27001")
        print(response.content)
    """

    def __init__(self, host: str = OLLAMA_HOST, default_model: str = None):
        self.host = host.rstrip('/')
        self.default_model = default_model or MODELS.get("assistant", "mistral")
        self._check_connection()

    def _check_connection(self) -> bool:
        """Vérifie la connexion à Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Impossible de se connecter à Ollama sur {self.host}")
            print("   Assurez-vous qu'Ollama est lancé : ollama serve")
            return False

    def list_models(self) -> List[str]:
        """Liste les modèles disponibles"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            print(f"Erreur lors de la récupération des modèles: {e}")
            return []

    def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        task_type: str = "assistant",
        stream: bool = False,
        **kwargs
    ) -> OllamaResponse:
        """
        Génère une réponse avec Ollama

        Args:
            prompt: Le prompt utilisateur
            model: Modèle à utiliser (optionnel)
            system: System prompt (optionnel)
            task_type: Type de tâche pour les paramètres (documentation/analysis/assistant/audit)
            stream: Si True, retourne un générateur
            **kwargs: Paramètres additionnels pour Ollama

        Returns:
            OllamaResponse avec le contenu généré
        """
        model = model or MODELS.get(task_type, self.default_model)
        params = LLM_PARAMS.get(task_type, {}).copy()
        params.update(kwargs)

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": params.get("temperature", 0.7),
                "top_p": params.get("top_p", 0.9),
                "num_predict": params.get("num_predict", 2048),
            }
        }

        if system:
            payload["system"] = system

        try:
            if stream:
                return self._stream_generate(payload)
            else:
                response = requests.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=OLLAMA_TIMEOUT
                )

                if response.status_code == 200:
                    data = response.json()
                    return OllamaResponse(
                        content=data.get("response", ""),
                        model=model,
                        total_duration=data.get("total_duration"),
                        eval_count=data.get("eval_count"),
                        success=True
                    )
                else:
                    return OllamaResponse(
                        content="",
                        model=model,
                        success=False,
                        error=f"Erreur HTTP {response.status_code}: {response.text}"
                    )

        except requests.exceptions.Timeout:
            return OllamaResponse(
                content="",
                model=model,
                success=False,
                error="Timeout - La génération a pris trop de temps"
            )
        except Exception as e:
            return OllamaResponse(
                content="",
                model=model,
                success=False,
                error=str(e)
            )

    def _stream_generate(self, payload: Dict) -> Generator[str, None, None]:
        """Génération en streaming"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                stream=True,
                timeout=OLLAMA_TIMEOUT
            )

            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break

        except Exception as e:
            yield f"\n[Erreur: {e}]"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        task_type: str = "assistant",
        stream: bool = False
    ) -> OllamaResponse:
        """
        Chat multi-tour avec historique

        Args:
            messages: Liste de messages [{"role": "user/assistant/system", "content": "..."}]
            model: Modèle à utiliser
            task_type: Type de tâche
            stream: Mode streaming

        Returns:
            OllamaResponse
        """
        model = model or MODELS.get(task_type, self.default_model)
        params = LLM_PARAMS.get(task_type, {})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": params.get("temperature", 0.7),
                "top_p": params.get("top_p", 0.9),
                "num_predict": params.get("num_predict", 2048),
            }
        }

        try:
            if stream:
                return self._stream_chat(payload)
            else:
                response = requests.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=OLLAMA_TIMEOUT
                )

                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", {})
                    return OllamaResponse(
                        content=message.get("content", ""),
                        model=model,
                        total_duration=data.get("total_duration"),
                        eval_count=data.get("eval_count"),
                        success=True
                    )
                else:
                    return OllamaResponse(
                        content="",
                        model=model,
                        success=False,
                        error=f"Erreur HTTP {response.status_code}"
                    )

        except Exception as e:
            return OllamaResponse(
                content="",
                model=model,
                success=False,
                error=str(e)
            )

    def _stream_chat(self, payload: Dict) -> Generator[str, None, None]:
        """Chat en streaming"""
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                stream=True,
                timeout=OLLAMA_TIMEOUT
            )

            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    message = data.get("message", {})
                    if "content" in message:
                        yield message["content"]
                    if data.get("done", False):
                        break

        except Exception as e:
            yield f"\n[Erreur: {e}]"


# Test rapide
if __name__ == "__main__":
    client = OllamaClient()
    print("Modèles disponibles:", client.list_models())

    print("\nTest de génération...")
    response = client.generate(
        "En une phrase, qu'est-ce que l'ISO 27001 ?",
        task_type="assistant"
    )

    if response.success:
        print(f"Réponse: {response.content}")
    else:
        print(f"Erreur: {response.error}")
