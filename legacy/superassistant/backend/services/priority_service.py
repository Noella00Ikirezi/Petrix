from typing import List, Dict, Any
from datetime import datetime, timedelta
from .ai_service import AIService
from models.task import Task


class PriorityService:
    """Service de priorisation intelligente des tâches"""

    def __init__(self):
        self.ai_service = AIService()
        self.system_prompt = """Tu es un assistant de productivité pour un apprenti cybersécurité en alternance.

Ton rôle est d'analyser les tâches et de recommander une priorisation optimale.

Prends en compte :
- Les deadlines (proximité)
- La priorité manuelle (haute/moyenne/basse)
- L'effort estimé
- Les dépendances (projets)
- Le contexte professionnel/académique

Pour chaque tâche recommandée, donne un score de 0 à 100 et une justification en 1-2 phrases.

Propose également un planning journalier optimisé."""

    async def prioritize_tasks(
        self,
        tasks: List[Task],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyse et priorise les tâches"""

        # Préparer les données des tâches
        task_data = []
        for task in tasks:
            days_until_deadline = None
            if task.deadline:
                delta = task.deadline - datetime.utcnow()
                days_until_deadline = delta.days

            task_data.append({
                "id": task.id,
                "title": task.title,
                "category": task.category,
                "priority": task.priority,
                "status": task.status,
                "deadline": str(task.deadline) if task.deadline else None,
                "days_until_deadline": days_until_deadline,
                "estimated_time": task.estimated_time,
                "tags": task.tags,
                "description": task.description[:100] if task.description else None
            })

        # Construire le message utilisateur
        user_message = f"""Analyse ces tâches et recommande les 5 prioritaires pour aujourd'hui:

Tâches:
{self._format_tasks(task_data)}

Contexte additionnel: {context if context else "Journée normale"}

Retourne un JSON avec cette structure exacte:
{{
    "top_tasks": [
        {{
            "task_id": int,
            "title": str,
            "priority_score": float (0-100),
            "justification": str
        }}
    ],
    "daily_plan": str (planning suggéré pour la journée),
    "analysis": str (analyse générale de la charge de travail)
}}"""

        response_format = {
            "top_tasks": "List[dict]",
            "daily_plan": "string",
            "analysis": "string"
        }

        result = await self.ai_service.generate_structured_response(
            system_prompt=self.system_prompt,
            user_message=user_message,
            response_format=response_format,
            max_tokens=2500
        )

        return result

    def _format_tasks(self, task_data: List[Dict]) -> str:
        """Formate les tâches pour le prompt"""
        formatted = []
        for task in task_data:
            deadline_str = f"Deadline: dans {task['days_until_deadline']} jours" if task['days_until_deadline'] is not None else "Pas de deadline"
            time_str = f"{task['estimated_time']}h" if task['estimated_time'] else "?"

            formatted.append(
                f"- [{task['id']}] {task['title']} | {task['category']} | "
                f"Priorité: {task['priority']} | {deadline_str} | Effort: {time_str}"
            )

        return "\n".join(formatted)
