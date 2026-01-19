from typing import List, Optional
from .ai_service import AIService


class DocumentService:
    """Service de génération de documents SMSI"""

    def __init__(self):
        self.ai_service = AIService()
        self.system_prompt = """Tu es un expert en rédaction de documentation SMSI conforme aux normes ISO 27001 et ANSSI.

Génère des documents structurés, professionnels, avec:
- Vocabulaire technique approprié
- Structure claire et logique
- Conformité aux normes de sécurité
- Suggestions de clauses RGPD si pertinent

Utilise un français professionnel et technique."""

    async def generate_document(
        self,
        doc_type: str,
        title: str,
        scope: str,
        requirements: List[str],
        references: Optional[List[str]] = None
    ) -> dict:
        """Génère un document SMSI complet"""

        refs_text = ""
        if references:
            refs_text = f"\nDocuments/normes de référence:\n{self._format_list(references)}"

        user_message = f"""Génère un document SMSI de type "{doc_type}":

Titre: {title}
Périmètre/contexte: {scope}

Exigences spécifiques:
{self._format_list(requirements)}
{refs_text}

Le document doit être structuré selon les standards ISO 27001/ANSSI pour un "{doc_type}".

Retourne un JSON avec cette structure exacte:
{{
    "title": str (titre formaté du document),
    "content": str (contenu complet en Markdown avec toutes les sections),
    "structure": List[str] (liste des sections principales créées),
    "compliance_notes": List[str] (notes sur la conformité RGPD/ANSSI)
}}"""

        response_format = {
            "title": "string",
            "content": "string",
            "structure": "List[string]",
            "compliance_notes": "List[string]"
        }

        result = await self.ai_service.generate_structured_response(
            system_prompt=self.system_prompt,
            user_message=user_message,
            response_format=response_format,
            max_tokens=4000
        )

        return result

    def _format_list(self, items: List[str]) -> str:
        """Formate une liste d'items"""
        return "\n".join([f"- {item}" for item in items])
