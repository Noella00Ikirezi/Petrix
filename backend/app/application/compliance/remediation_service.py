"""Service for generating remediation actions using AI."""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.client_requirements_models import (
    RequirementCompliance,
    ClientRequirement,
    RemediationAction,
    ComplianceStatus,
    ActionStatus,
    ActionType,
    RequirementPriority,
)
from app.application.smsi.ai_service import ollama_service


class RemediationService:
    """Service for generating and managing remediation actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_remediation_plan(
        self,
        compliance_record_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[RemediationAction]:
        """Generate AI-powered remediation actions for a non-compliant requirement."""

        # Get compliance record with requirement
        stmt = select(RequirementCompliance, ClientRequirement).join(
            ClientRequirement, RequirementCompliance.requirement_id == ClientRequirement.id
        ).where(RequirementCompliance.id == compliance_record_id)

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            raise ValueError(f"Compliance record {compliance_record_id} not found")

        compliance_record, requirement = row

        # Only generate for non-compliant or partially compliant
        if compliance_record.status not in [
            ComplianceStatus.NON_COMPLIANT,
            ComplianceStatus.PARTIALLY_COMPLIANT
        ]:
            logger.info(f"Requirement {requirement.code} is compliant, no remediation needed")
            return []

        # Build context for AI
        context = self._build_remediation_context(compliance_record, requirement)

        # Generate remediation plan with AI
        ai_result = await ollama_service.generate_document(
            template_prompt=self._build_remediation_prompt(requirement, compliance_record),
            context=context,
            document_type="procedure",
            max_tokens=4000,
            temperature=0.3
        )

        if not ai_result.success:
            logger.error(f"AI generation failed: {ai_result.error}")
            # Create a basic action as fallback
            return await self._create_fallback_action(
                compliance_record, requirement, user_id
            )

        # Parse AI response and create actions
        actions = await self._parse_and_create_actions(
            ai_result.content,
            compliance_record,
            requirement,
            user_id,
            ai_result.content
        )

        return actions

    def _build_remediation_context(
        self,
        compliance_record: RequirementCompliance,
        requirement: ClientRequirement
    ) -> Dict[str, Any]:
        """Build context for AI remediation generation."""
        return {
            "requirement": {
                "code": requirement.code,
                "title": requirement.title,
                "description": requirement.description,
                "category": requirement.category.value,
                "priority": requirement.priority.value,
                "acceptance_criteria": requirement.acceptance_criteria,
                "evidence_required": requirement.evidence_required,
            },
            "compliance": {
                "status": compliance_record.status.value,
                "compliance_level": compliance_record.compliance_level,
                "gap_description": compliance_record.gap_description,
                "findings": compliance_record.findings,
            },
            "framework_mappings": requirement.framework_mappings,
        }

    def _build_remediation_prompt(
        self,
        requirement: ClientRequirement,
        compliance_record: RequirementCompliance
    ) -> str:
        """Build prompt for AI remediation generation."""
        return f"""Genere un plan de remediation detaille pour l'exigence non-conforme suivante.

# Exigence
- Code: {requirement.code}
- Titre: {requirement.title}
- Description: {requirement.description or 'Non specifiee'}
- Categorie: {requirement.category.value}
- Priorite: {requirement.priority.value}
- Criteres d'acceptation: {requirement.acceptance_criteria or 'Non specifies'}

# Ecart constate
- Niveau de conformite: {compliance_record.compliance_level or 'Non evalue'}%
- Description de l'ecart: {compliance_record.gap_description or 'Non decrit'}
- Constats: {compliance_record.findings or 'Aucun'}

# Instructions
Genere un plan de remediation avec 2 a 5 actions concretes.
Pour chaque action, fournis:
1. Titre de l'action (max 100 caracteres)
2. Description detaillee
3. Type: technique, organisationnel, documentation, formation, processus, outil, audit
4. Priorite: critical, high, medium, low
5. Effort estime: jours ou semaines
6. Etapes de mise en oeuvre (liste)
7. Livrables attendus

Format de sortie (JSON):
```json
{{
  "actions": [
    {{
      "title": "Titre de l'action",
      "description": "Description detaillee",
      "type": "technical",
      "priority": "high",
      "estimated_effort": "5 jours",
      "steps": ["Etape 1", "Etape 2"],
      "deliverables": ["Livrable 1", "Livrable 2"]
    }}
  ]
}}
```
"""

    async def _parse_and_create_actions(
        self,
        ai_response: str,
        compliance_record: RequirementCompliance,
        requirement: ClientRequirement,
        user_id: uuid.UUID,
        ai_prompt: str
    ) -> List[RemediationAction]:
        """Parse AI response and create remediation actions."""
        import json
        import re

        actions = []

        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON directly
                json_match = re.search(r'\{[\s\S]*"actions"[\s\S]*\}', ai_response)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            data = json.loads(json_str)
            action_data_list = data.get("actions", [])

            # Map string types to enums
            type_mapping = {
                "technical": ActionType.TECHNICAL,
                "technique": ActionType.TECHNICAL,
                "organizational": ActionType.ORGANIZATIONAL,
                "organisationnel": ActionType.ORGANIZATIONAL,
                "documentation": ActionType.DOCUMENTATION,
                "training": ActionType.TRAINING,
                "formation": ActionType.TRAINING,
                "process": ActionType.PROCESS,
                "processus": ActionType.PROCESS,
                "tool": ActionType.TOOL,
                "outil": ActionType.TOOL,
                "audit": ActionType.AUDIT,
            }

            priority_mapping = {
                "critical": RequirementPriority.CRITICAL,
                "critique": RequirementPriority.CRITICAL,
                "high": RequirementPriority.HIGH,
                "haute": RequirementPriority.HIGH,
                "medium": RequirementPriority.MEDIUM,
                "moyenne": RequirementPriority.MEDIUM,
                "low": RequirementPriority.LOW,
                "basse": RequirementPriority.LOW,
            }

            for i, action_data in enumerate(action_data_list[:5]):  # Max 5 actions
                action_type = type_mapping.get(
                    action_data.get("type", "").lower(),
                    ActionType.TECHNICAL
                )
                priority = priority_mapping.get(
                    action_data.get("priority", "").lower(),
                    requirement.priority
                )

                # Parse effort to estimate due date
                effort = action_data.get("estimated_effort", "")
                due_date = self._estimate_due_date(effort, priority)

                # Create implementation steps
                steps = action_data.get("steps", [])
                implementation_steps = [
                    {"step": i + 1, "description": step, "completed": False}
                    for i, step in enumerate(steps)
                ]

                action = RemediationAction(
                    compliance_record_id=compliance_record.id,
                    created_by_id=user_id,
                    title=action_data.get("title", f"Action {i + 1}")[:300],
                    description=action_data.get("description", ""),
                    action_type=action_type,
                    priority=priority,
                    status=ActionStatus.PLANNED,
                    estimated_effort=effort,
                    due_date=due_date,
                    implementation_steps=implementation_steps,
                    deliverables=action_data.get("deliverables", []),
                    ai_generated=True,
                    ai_prompt_used=ai_prompt[:2000]
                )

                self.db.add(action)
                actions.append(action)

            await self.db.commit()

            for action in actions:
                await self.db.refresh(action)

            logger.info(f"Created {len(actions)} remediation actions for {requirement.code}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            actions = await self._create_fallback_action(
                compliance_record, requirement, user_id
            )
        except Exception as e:
            logger.error(f"Error creating actions: {e}")
            actions = await self._create_fallback_action(
                compliance_record, requirement, user_id
            )

        return actions

    def _estimate_due_date(
        self,
        effort: str,
        priority: RequirementPriority
    ) -> datetime:
        """Estimate due date based on effort and priority."""
        import re

        # Default days based on priority
        priority_days = {
            RequirementPriority.CRITICAL: 7,
            RequirementPriority.HIGH: 14,
            RequirementPriority.MEDIUM: 30,
            RequirementPriority.LOW: 60,
        }

        days = priority_days.get(priority, 30)

        # Try to parse effort string
        if effort:
            effort_lower = effort.lower()

            # Match patterns like "5 jours", "2 semaines", "1 mois"
            day_match = re.search(r'(\d+)\s*(jour|day)', effort_lower)
            week_match = re.search(r'(\d+)\s*(semaine|week)', effort_lower)
            month_match = re.search(r'(\d+)\s*(mois|month)', effort_lower)

            if day_match:
                days = int(day_match.group(1))
            elif week_match:
                days = int(week_match.group(1)) * 7
            elif month_match:
                days = int(month_match.group(1)) * 30

        return datetime.utcnow() + timedelta(days=days)

    async def _create_fallback_action(
        self,
        compliance_record: RequirementCompliance,
        requirement: ClientRequirement,
        user_id: uuid.UUID
    ) -> List[RemediationAction]:
        """Create a basic fallback action when AI fails."""
        action = RemediationAction(
            compliance_record_id=compliance_record.id,
            created_by_id=user_id,
            title=f"Plan de remediation pour {requirement.code}",
            description=f"""Action de remediation pour l'exigence non-conforme:

Exigence: {requirement.title}
Ecart: {compliance_record.gap_description or 'A documenter'}

Actions recommandees:
1. Analyser l'ecart en detail
2. Identifier les mesures correctives
3. Planifier la mise en oeuvre
4. Implementer les corrections
5. Verifier la conformite""",
            action_type=ActionType.TECHNICAL,
            priority=requirement.priority,
            status=ActionStatus.PLANNED,
            estimated_effort="A estimer",
            due_date=datetime.utcnow() + timedelta(days=30),
            implementation_steps=[
                {"step": 1, "description": "Analyser l'ecart en detail", "completed": False},
                {"step": 2, "description": "Identifier les mesures correctives", "completed": False},
                {"step": 3, "description": "Planifier la mise en oeuvre", "completed": False},
                {"step": 4, "description": "Implementer les corrections", "completed": False},
                {"step": 5, "description": "Verifier la conformite", "completed": False},
            ],
            deliverables=["Plan d'action detaille", "Preuves de conformite"],
            ai_generated=False
        )

        self.db.add(action)
        await self.db.commit()
        await self.db.refresh(action)

        return [action]

    async def assess_compliance_with_ai(
        self,
        requirement: ClientRequirement,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to assess compliance based on provided evidence."""
        prompt = f"""Evalue la conformite de l'organisation par rapport a l'exigence suivante.

# Exigence
- Code: {requirement.code}
- Titre: {requirement.title}
- Description: {requirement.description or 'Non specifiee'}
- Criteres d'acceptation: {requirement.acceptance_criteria or 'Non specifies'}
- Preuves requises: {', '.join(requirement.evidence_required) if requirement.evidence_required else 'Non specifiees'}

# Preuves fournies
{self._format_evidence(evidence)}

# Instructions
Evalue si l'organisation est conforme a cette exigence.
Fournis:
1. Statut: compliant, partially_compliant, non_compliant
2. Niveau de conformite (0-100)
3. Analyse des ecarts
4. Recommandations

Format JSON:
```json
{{
  "status": "compliant|partially_compliant|non_compliant",
  "compliance_level": 75,
  "gap_analysis": "Description des ecarts constates",
  "recommendations": "Recommandations pour atteindre la conformite"
}}
```
"""

        result = await ollama_service.generate_document(
            template_prompt=prompt,
            context={},
            document_type="checklist",
            max_tokens=2000,
            temperature=0.2
        )

        if result.success:
            return self._parse_assessment_response(result.content)
        else:
            return {
                "status": "not_assessed",
                "compliance_level": None,
                "gap_analysis": "Evaluation automatique non disponible",
                "recommendations": "Effectuer une evaluation manuelle",
                "error": result.error
            }

    def _format_evidence(self, evidence: Dict[str, Any]) -> str:
        """Format evidence dictionary for AI prompt."""
        lines = []
        for key, value in evidence.items():
            if isinstance(value, list):
                lines.append(f"- {key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "Aucune preuve fournie"

    def _parse_assessment_response(self, response: str) -> Dict[str, Any]:
        """Parse AI assessment response."""
        import json
        import re

        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group(0))

        except json.JSONDecodeError:
            pass

        return {
            "status": "not_assessed",
            "compliance_level": None,
            "gap_analysis": response,
            "recommendations": ""
        }
