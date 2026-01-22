"""Document generation service for SMSI."""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.smsi_models import (
    SMSIProject,
    DocumentTemplate,
    GeneratedDocument,
    QuestionResponse,
    Question,
    DocumentStatus,
    DocumentType,
    ProjectStatus,
)
from app.application.smsi.ai_service import mistral_service, AIGenerationResult


class DocumentGeneratorService:
    """Service for generating SMSI documents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_project_documents(
        self,
        project_id: uuid.UUID,
        template_ids: Optional[List[uuid.UUID]] = None
    ) -> Dict[str, Any]:
        """Generate all documents for a project."""
        # Get project
        project = await self.db.get(SMSIProject, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Update status
        project.status = ProjectStatus.GENERATION
        await self.db.commit()

        # Get templates to generate
        if template_ids:
            stmt = select(DocumentTemplate).where(
                DocumentTemplate.id.in_(template_ids),
                DocumentTemplate.is_active == True
            )
        else:
            stmt = select(DocumentTemplate).where(
                DocumentTemplate.is_active == True
            ).order_by(DocumentTemplate.order_index)

        result = await self.db.execute(stmt)
        templates = result.scalars().all()

        # Get project context
        context = await self._build_project_context(project)

        generated = []
        errors = []
        total_tokens_input = 0
        total_tokens_output = 0
        total_time = 0.0

        for template in templates:
            try:
                doc = await self._generate_document(project, template, context)
                generated.append({
                    "id": str(doc.id),
                    "code": doc.code,
                    "name": doc.name,
                    "status": doc.status.value
                })
                total_tokens_input += doc.ai_tokens_input
                total_tokens_output += doc.ai_tokens_output
                total_time += doc.ai_generation_time
            except Exception as e:
                logger.error(f"Error generating {template.code}: {str(e)}")
                errors.append({
                    "template_code": template.code,
                    "error": str(e)
                })

        # Update project stats
        project.documents_generated = len(generated)
        project.documents_total = len(templates)
        project.ai_tokens_used = total_tokens_input + total_tokens_output
        project.ai_generation_time = total_time
        project.completion_percentage = int((len(generated) / len(templates)) * 100) if templates else 0

        if not errors:
            project.status = ProjectStatus.REVIEW

        await self.db.commit()

        return {
            "project_id": str(project_id),
            "generated": generated,
            "errors": errors,
            "stats": {
                "total_templates": len(templates),
                "generated": len(generated),
                "failed": len(errors),
                "tokens_used": total_tokens_input + total_tokens_output,
                "generation_time": total_time
            }
        }

    async def _generate_document(
        self,
        project: SMSIProject,
        template: DocumentTemplate,
        context: Dict[str, Any]
    ) -> GeneratedDocument:
        """Generate a single document from template."""
        logger.info(f"Generating document: {template.code} - {template.name}")

        # Build prompt from template
        prompt = self._build_template_prompt(template, context)

        # Generate content with AI
        result = await mistral_service.generate_document(
            template_prompt=prompt,
            context=context,
            document_type=template.document_type.value,
            max_tokens=8000,
            temperature=0.3
        )

        if not result.success:
            raise Exception(f"AI generation failed: {result.error}")

        # Create document record
        doc = GeneratedDocument(
            project_id=project.id,
            template_id=template.id,
            code=f"{template.code}-{project.organization_name[:10].upper().replace(' ', '')}",
            name=template.name,
            document_type=template.document_type,
            status=DocumentStatus.DRAFT,
            content_markdown=result.content,
            content_html=self._markdown_to_html(result.content),
            content_json=self._extract_structure(result.content),
            ai_model_used=result.model_used,
            ai_prompt_used=prompt[:2000],  # Store first 2000 chars
            ai_tokens_input=result.tokens_input,
            ai_tokens_output=result.tokens_output,
            ai_generation_time=result.generation_time
        )

        self.db.add(doc)
        await self.db.flush()

        return doc

    def _build_template_prompt(
        self,
        template: DocumentTemplate,
        context: Dict[str, Any]
    ) -> str:
        """Build generation prompt from template."""
        # Use template's AI prompt if available
        if template.ai_prompt_template:
            prompt = template.ai_prompt_template
            # Replace variables
            for var in template.variables:
                value = context.get("responses", {}).get(var, f"[{var}]")
                prompt = prompt.replace(f"{{{var}}}", str(value))
            return prompt

        # Default prompt based on document type
        type_prompts = {
            DocumentType.POLICY: f"""Genere la politique "{template.name}".

Sections a inclure:
1. Objet et perimetre
2. Definitions
3. Roles et responsabilites
4. Principes directeurs
5. Regles applicables
6. Exceptions et derogations
7. Controle et audit
8. Sanctions
9. Documents de reference
10. Historique des versions""",

            DocumentType.PROCEDURE: f"""Genere la procedure "{template.name}".

Sections a inclure:
1. Objectif
2. Champ d'application
3. Documents de reference
4. Definitions et abreviations
5. Responsabilites
6. Description de la procedure (etapes detaillees)
7. Enregistrements
8. Indicateurs
9. Annexes""",

            DocumentType.REGISTER: f"""Genere le registre "{template.name}".

Format: Tableau Markdown avec les colonnes appropriees.
Inclure:
- En-tetes descriptifs
- 3-5 exemples de lignes (a adapter)
- Instructions de mise a jour""",

            DocumentType.CHECKLIST: f"""Genere la checklist "{template.name}".

Format: Liste de controle avec:
- [ ] Points de verification
- Colonnes: Element | Conforme | Non-Conforme | N/A | Commentaires
- Instructions d'utilisation""",

            DocumentType.ANNEX: f"""Genere l'annexe "{template.name}".

Contenu adapte au sujet de l'annexe.""",

            DocumentType.SCHEMA: f"""Decris le schema "{template.name}".

Format: Description textuelle detaillee du schema avec:
- Composants principaux
- Flux et relations
- Legende
Note: Le schema visuel sera genere separement.""",
        }

        base_prompt = type_prompts.get(
            template.document_type,
            f"Genere le document '{template.name}' de type {template.document_type.value}."
        )

        # Add sections from template if defined
        if template.sections:
            base_prompt += "\n\nSections definies:\n"
            for section in template.sections:
                base_prompt += f"- {section.get('title', section)}\n"

        return base_prompt

    async def _build_project_context(self, project: SMSIProject) -> Dict[str, Any]:
        """Build context dictionary from project data."""
        context = {
            "organization": {
                "name": project.organization_name,
                "type": project.organization_type,
                "size": project.organization_size,
                "sector": project.industry_sector
            },
            "security_level": project.security_level.value,
            "frameworks": project.selected_frameworks,
            "responses": {}
        }

        # Get QCM responses
        stmt = select(QuestionResponse, Question).join(
            Question, QuestionResponse.question_id == Question.id
        ).where(QuestionResponse.project_id == project.id)

        result = await self.db.execute(stmt)
        rows = result.all()

        for response, question in rows:
            context["responses"][question.variable_name] = response.response_text or response.response_value

        # Merge with stored context data
        context.update(project.context_data)

        return context

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(
                markdown_content,
                extensions=['tables', 'toc', 'fenced_code']
            )
        except ImportError:
            # Basic conversion if markdown lib not available
            return f"<pre>{markdown_content}</pre>"

    def _extract_structure(self, content: str) -> Dict[str, Any]:
        """Extract document structure from Markdown content."""
        structure = {
            "sections": [],
            "tables": 0,
            "lists": 0,
            "word_count": len(content.split())
        }

        lines = content.split('\n')
        current_section = None

        for line in lines:
            if line.startswith('# '):
                current_section = {"title": line[2:].strip(), "level": 1, "subsections": []}
                structure["sections"].append(current_section)
            elif line.startswith('## ') and current_section:
                current_section["subsections"].append({
                    "title": line[3:].strip(),
                    "level": 2
                })
            elif line.startswith('|'):
                structure["tables"] += 1
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                structure["lists"] += 1

        return structure

    async def regenerate_document(
        self,
        document_id: uuid.UUID,
        feedback: Optional[str] = None
    ) -> GeneratedDocument:
        """Regenerate a document, optionally with feedback."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        project = await self.db.get(SMSIProject, doc.project_id)
        template = await self.db.get(DocumentTemplate, doc.template_id)
        context = await self._build_project_context(project)

        if feedback and doc.content_markdown:
            # Improve existing document
            result = await mistral_service.improve_document(
                content=doc.content_markdown,
                feedback=feedback,
                document_type=doc.document_type.value
            )
        else:
            # Full regeneration
            prompt = self._build_template_prompt(template, context)
            result = await mistral_service.generate_document(
                template_prompt=prompt,
                context=context,
                document_type=doc.document_type.value
            )

        if not result.success:
            raise Exception(f"Regeneration failed: {result.error}")

        # Update document
        doc.content_markdown = result.content
        doc.content_html = self._markdown_to_html(result.content)
        doc.content_json = self._extract_structure(result.content)
        doc.ai_tokens_input += result.tokens_input
        doc.ai_tokens_output += result.tokens_output
        doc.ai_generation_time += result.generation_time
        doc.status = DocumentStatus.DRAFT
        doc.version = self._increment_version(doc.version)

        await self.db.commit()
        return doc

    def _increment_version(self, version: str) -> str:
        """Increment document version."""
        parts = version.split('.')
        if len(parts) == 2:
            return f"{parts[0]}.{int(parts[1]) + 1}"
        return "1.1"
