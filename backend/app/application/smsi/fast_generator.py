"""Fast document generation service using pre-written templates.

This service generates documents 10x faster by:
1. Using pre-written professional templates (no AI generation from scratch)
2. Simple variable substitution for organization details
3. Light AI customization only for specific sections (optional)

Works with small LLMs (qwen2:0.5b, phi3:mini) that have limited memory.
"""
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.smsi_models import (
    SMSIProject,
    DocumentTemplate,
    GeneratedDocument,
    DocumentStatus,
    DocumentType,
    ProjectStatus,
)
from app.application.smsi.template_library import TEMPLATES, fill_template
from app.application.smsi.document_packs import (
    DOCUMENT_PACKS,
    get_pack_proposal,
    filter_documents_by_frameworks,
)
from app.application.smsi.ai_service import ollama_service


@dataclass
class GenerationResult:
    """Result of document generation."""
    document_id: str
    code: str
    name: str
    status: str
    generation_time: float
    tokens_used: int
    error: Optional[str] = None


class FastDocumentGenerator:
    """Fast document generator using templates + light AI customization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pack_proposals(
        self,
        selected_frameworks: List[str]
    ) -> Dict[str, Any]:
        """Get document pack proposals based on selected frameworks.

        Returns 3 options (essential, standard, advanced) with recommended pack.
        """
        return get_pack_proposal(selected_frameworks)

    async def generate_project_documents(
        self,
        project_id: uuid.UUID,
        pack_type: str = "standard",
        use_ai_customization: bool = False
    ) -> Dict[str, Any]:
        """Generate all documents for a project using templates.

        Args:
            project_id: The project UUID
            pack_type: "essential", "standard", or "advanced"
            use_ai_customization: If True, uses AI to customize some sections (slower)
        """
        start_time = time.time()

        # Get project
        project = await self.db.get(SMSIProject, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Update status
        project.status = ProjectStatus.GENERATION
        await self.db.commit()

        # Build context from project
        context = self._build_context(project)

        # Get documents to generate based on pack and frameworks
        documents_to_generate = filter_documents_by_frameworks(
            pack_type,
            project.selected_frameworks
        )

        generated = []
        errors = []
        total_tokens = 0

        for doc_spec in documents_to_generate:
            try:
                result = await self._generate_document(
                    project=project,
                    doc_spec=doc_spec,
                    context=context,
                    use_ai=use_ai_customization
                )
                generated.append({
                    "id": result.document_id,
                    "code": result.code,
                    "name": result.name,
                    "status": result.status,
                    "generation_time": result.generation_time
                })
                total_tokens += result.tokens_used
            except Exception as e:
                logger.error(f"Error generating {doc_spec['code']}: {str(e)}")
                errors.append({
                    "template_code": doc_spec["code"],
                    "error": str(e)
                })

        # Update project stats
        total_time = time.time() - start_time
        project.documents_generated = len(generated)
        project.documents_total = len(documents_to_generate)
        project.ai_tokens_used = total_tokens
        project.ai_generation_time = total_time
        project.completion_percentage = int(
            (len(generated) / len(documents_to_generate)) * 100
        ) if documents_to_generate else 0

        if not errors:
            project.status = ProjectStatus.REVIEW

        await self.db.commit()

        return {
            "project_id": str(project_id),
            "pack_type": pack_type,
            "generated": generated,
            "errors": errors,
            "stats": {
                "total_documents": len(documents_to_generate),
                "generated": len(generated),
                "failed": len(errors),
                "tokens_used": total_tokens,
                "generation_time": total_time
            }
        }

    async def _generate_document(
        self,
        project: SMSIProject,
        doc_spec: Dict[str, Any],
        context: Dict[str, Any],
        use_ai: bool = False
    ) -> GenerationResult:
        """Generate a single document from template."""
        start_time = time.time()
        code = doc_spec["code"]

        logger.info(f"Generating document: {code} - {doc_spec['name']}")

        # Check if we have a pre-written template
        template = TEMPLATES.get(code)
        tokens_used = 0

        if template:
            # Use pre-written template with variable substitution
            content = fill_template(code, context)
            logger.info(f"  → Using pre-written template (fast mode)")
        else:
            # Fallback: Generate with AI (slower)
            logger.info(f"  → No template found, using AI generation")
            if use_ai:
                content, tokens_used = await self._generate_with_ai(
                    doc_spec, context
                )
            else:
                # Create a basic placeholder document
                content = self._create_placeholder_document(doc_spec, context)

        generation_time = time.time() - start_time

        # Create document record
        doc = GeneratedDocument(
            project_id=project.id,
            template_id=None,  # Templates are now in code
            code=f"{code}-{project.organization_name[:10].upper().replace(' ', '')}",
            name=doc_spec["name"],
            document_type=DocumentType(doc_spec["type"]),
            status=DocumentStatus.DRAFT,
            content_markdown=content,
            content_html=self._markdown_to_html(content),
            content_json={"sections": self._extract_sections(content)},
            ai_model_used="template" if template else "qwen2:0.5b",
            ai_prompt_used="Template-based generation",
            ai_tokens_input=0,
            ai_tokens_output=tokens_used,
            ai_generation_time=generation_time
        )

        self.db.add(doc)
        await self.db.flush()

        return GenerationResult(
            document_id=str(doc.id),
            code=doc.code,
            name=doc.name,
            status=doc.status.value,
            generation_time=generation_time,
            tokens_used=tokens_used
        )

    async def _generate_with_ai(
        self,
        doc_spec: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[str, int]:
        """Generate document content using AI (fallback for missing templates)."""
        # Simple prompt for light customization
        prompt = f"""Génère un document {doc_spec['type']} intitulé "{doc_spec['name']}"
pour l'organisation {context['organization']['name']}.

Format: Markdown avec titres, sections et tableaux si nécessaire.
Longueur: 1-2 pages maximum.
Style: Professionnel, concis.

Contexte:
- Secteur: {context['organization'].get('sector', 'N/A')}
- Taille: {context['organization'].get('size', 'N/A')}
- Référentiels: {', '.join(context.get('frameworks', ['ISO 27001']))}
"""

        result = await ollama_service.generate_document(
            template_prompt=prompt,
            context=context,
            document_type=doc_spec["type"],
            max_tokens=2000,  # Limit for small models
            temperature=0.3
        )

        if result.success:
            return result.content, result.tokens_output
        else:
            # Return placeholder on failure
            return self._create_placeholder_document(doc_spec, context), 0

    def _create_placeholder_document(
        self,
        doc_spec: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Create a basic placeholder document when no template is available."""
        org_name = context['organization'].get('name', '[Organisation]')
        date = datetime.now().strftime("%Y-%m-%d")

        return f'''# {doc_spec['name']}

**Document**: {doc_spec['code']}
**Version**: 1.0
**Date**: {date}
**Organisation**: {org_name}

---

## 1. Objet

[À compléter - Définir l'objet de ce document]

---

## 2. Périmètre

[À compléter - Définir le périmètre d'application]

---

## 3. Contenu

[À compléter - Ce document nécessite une rédaction personnalisée]

---

## 4. Approbation

| Action | Nom | Fonction | Date |
|--------|-----|----------|------|
| Rédaction | | | {date} |
| Approbation | | | |

---

*Document généré automatiquement - À personnaliser*
'''

    def _build_context(self, project: SMSIProject) -> Dict[str, Any]:
        """Build context dictionary from project."""
        return {
            "organization": {
                "name": project.organization_name,
                "type": project.organization_type,
                "size": project.organization_size,
                "sector": project.industry_sector
            },
            "security_level": project.security_level.value,
            "frameworks": project.selected_frameworks,
            "author": "RSSI",
            "dpo_contact": f"dpo@{project.organization_name.lower().replace(' ', '')}.fr",
            "incident_channel": f"security@{project.organization_name.lower().replace(' ', '')}.fr",
        }

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(
                markdown_content,
                extensions=['tables', 'toc', 'fenced_code']
            )
        except ImportError:
            return f"<pre>{markdown_content}</pre>"

    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections from markdown content."""
        sections = []
        lines = content.split('\n')

        for line in lines:
            if line.startswith('## '):
                sections.append({
                    "title": line[3:].strip(),
                    "level": 2
                })
            elif line.startswith('### '):
                sections.append({
                    "title": line[4:].strip(),
                    "level": 3
                })

        return sections


# Singleton instance for easy import
fast_generator = None

def get_fast_generator(db: AsyncSession) -> FastDocumentGenerator:
    """Get a FastDocumentGenerator instance."""
    return FastDocumentGenerator(db)
