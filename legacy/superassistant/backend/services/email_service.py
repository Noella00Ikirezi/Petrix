from typing import List, Optional
from .ai_service import AIService


class EmailService:
    """Service de génération d'emails professionnels"""

    def __init__(self):
        self.ai_service = AIService()
        self.system_prompt = """Tu es un assistant de rédaction professionnelle spécialisé en cybersécurité.

Génère des emails en français, professionnels et bien structurés.

Adapte:
- Le ton selon le destinataire
- Le vocabulaire technique si nécessaire
- Les formules de politesse appropriées
- La structure (intro/développement/conclusion)

Sois précis, concis et professionnel."""

    async def generate_email(
        self,
        recipient_type: str,
        context: str,
        tone: str,
        subject: str,
        key_points: List[str],
        user_context: Optional[str] = None
    ) -> dict:
        """Génère un email complet"""

        user_message = f"""Génère un email professionnel avec ces paramètres:

Destinataire: {recipient_type}
Contexte: {context}
Ton souhaité: {tone}
Sujet: {subject}

Points clés à inclure:
{self._format_points(key_points)}

Contexte additionnel: {user_context if user_context else "Aucun"}

Retourne un JSON avec cette structure exacte:
{{
    "subject": str (ligne d'objet optimisée),
    "body": str (corps de l'email complet avec formules de politesse),
    "suggestions": List[str] (2-3 suggestions d'amélioration optionnelles)
}}"""

        response_format = {
            "subject": "string",
            "body": "string",
            "suggestions": "List[string]"
        }

        result = await self.ai_service.generate_structured_response(
            system_prompt=self.system_prompt,
            user_message=user_message,
            response_format=response_format,
            max_tokens=1500
        )

        return result

    def _format_points(self, points: List[str]) -> str:
        """Formate les points clés"""
        return "\n".join([f"- {point}" for point in points])
