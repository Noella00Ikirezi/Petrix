"""API endpoints for SMSI Generator module."""
import uuid
import traceback
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from loguru import logger
import io

from app.infrastructure.database.connection import get_async_db
from app.infrastructure.database.smsi_models import (
    Framework,
    FrameworkControl,
    DocumentTemplate,
    Question,
    SMSIProject,
    QuestionResponse,
    GeneratedDocument,
    ComplianceFramework,
    DocumentType,
    DocumentStatus,
    ProjectStatus,
    SecurityLevel,
    QuestionType,
)
from app.api.v1.deps import get_current_active_user
from app.infrastructure.database.models import User
from app.core.permissions import UserRole, Permission
from app.application.smsi.ai_service import mistral_service
from app.application.smsi.document_generator import DocumentGeneratorService
from app.application.smsi.export_service import export_service
from app.application.smsi.fast_generator import get_fast_generator
from app.application.smsi.document_packs import get_pack_proposal, DOCUMENT_PACKS
from app.application.smsi.document_service import get_document_service

router = APIRouter(prefix="/smsi", tags=["SMSI Generator"])


# =============================================================================
# SCHEMAS
# =============================================================================

class FrameworkBase(BaseModel):
    code: str
    name: str
    version: str
    description: Optional[str] = None
    category: str = "general"
    region: str = "eu"
    is_mandatory: bool = False


class FrameworkResponse(FrameworkBase):
    id: uuid.UUID
    total_controls: int
    total_requirements: int
    icon: Optional[str]
    color: Optional[str]

    class Config:
        from_attributes = True


class ControlResponse(BaseModel):
    id: uuid.UUID
    control_id: str
    title: str
    description: Optional[str]
    domain: Optional[str]
    subdomain: Optional[str]
    is_mandatory: bool
    security_level: Optional[str]
    implementation_guidance: Optional[str]

    class Config:
        from_attributes = True


class DocumentTemplateResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    document_type: str
    description: Optional[str]
    output_formats: List[str]
    min_security_level: str
    version: str
    tags: List[str]

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    help_text: Optional[str]
    placeholder: Optional[str]
    options: List[dict]
    is_required: bool
    variable_name: str
    group_name: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    organization_name: str = Field(..., min_length=2, max_length=200)
    organization_type: Optional[str] = None
    organization_size: Optional[str] = None
    industry_sector: Optional[str] = None
    selected_frameworks: List[str] = Field(default_factory=list)
    security_level: str = "n1_standard"
    pack_type: str = Field(default="advanced", pattern="^(essential|standard|advanced)$")


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    organization_name: str
    organization_type: Optional[str]
    organization_size: Optional[str]
    industry_sector: Optional[str]
    selected_frameworks: List[str]
    security_level: str
    pack_type: str
    completion_percentage: int
    documents_generated: int
    documents_total: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ResponseSubmit(BaseModel):
    question_id: uuid.UUID
    response_value: dict
    response_text: Optional[str] = None


class ResponseBulkSubmit(BaseModel):
    responses: List[ResponseSubmit]


class GeneratedDocumentResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    document_type: str
    version: str
    status: str
    ai_model_used: Optional[str]
    ai_tokens_input: int
    ai_tokens_output: int
    ai_generation_time: float
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentExportRequest(BaseModel):
    format: str = Field(..., pattern="^(md|html|docx|pdf|xlsx|csv|pptx)$")


class AISuggestionRequest(BaseModel):
    question: str
    context: dict = Field(default_factory=dict)
    options: Optional[List[str]] = None


# =============================================================================
# FRAMEWORKS ENDPOINTS
# =============================================================================

@router.get("/frameworks", response_model=List[FrameworkResponse])
async def list_frameworks(
    category: Optional[str] = None,
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all available compliance frameworks."""
    stmt = select(Framework)

    if category:
        stmt = stmt.where(Framework.category == category)
    if region:
        stmt = stmt.where(Framework.region == region)

    stmt = stmt.order_by(Framework.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/frameworks/{framework_id}", response_model=FrameworkResponse)
async def get_framework(
    framework_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get framework details."""
    framework = await db.get(Framework, framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    return framework


@router.get("/frameworks/{framework_id}/controls", response_model=List[ControlResponse])
async def list_framework_controls(
    framework_id: uuid.UUID,
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List controls for a framework."""
    stmt = select(FrameworkControl).where(
        FrameworkControl.framework_id == framework_id
    )

    if domain:
        stmt = stmt.where(FrameworkControl.domain == domain)

    stmt = stmt.order_by(FrameworkControl.order_index)
    result = await db.execute(stmt)
    return result.scalars().all()


# =============================================================================
# DOCUMENT TEMPLATES ENDPOINTS
# =============================================================================

@router.get("/templates", response_model=List[DocumentTemplateResponse])
async def list_templates(
    document_type: Optional[str] = None,
    framework_id: Optional[uuid.UUID] = None,
    security_level: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List document templates."""
    stmt = select(DocumentTemplate).where(DocumentTemplate.is_active == True)

    if document_type:
        stmt = stmt.where(DocumentTemplate.document_type == document_type)
    if framework_id:
        stmt = stmt.where(DocumentTemplate.framework_id == framework_id)
    if security_level:
        stmt = stmt.where(DocumentTemplate.min_security_level == security_level)

    stmt = stmt.order_by(DocumentTemplate.order_index)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/templates/{template_id}", response_model=DocumentTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get template details."""
    template = await db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/templates/{template_id}/questions", response_model=List[QuestionResponse])
async def list_template_questions(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List questions for a template."""
    stmt = select(Question).where(
        Question.template_id == template_id
    ).order_by(Question.order_index)

    result = await db.execute(stmt)
    return result.scalars().all()


# =============================================================================
# PROJECT ENDPOINTS
# =============================================================================

@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new SMSI project."""
    # Validate security level
    try:
        security_level = SecurityLevel(project_data.security_level)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid security level. Use: {[e.value for e in SecurityLevel]}"
        )

    # Count required templates
    stmt = select(func.count()).select_from(DocumentTemplate).where(
        DocumentTemplate.is_active == True
    )
    result = await db.execute(stmt)
    total_templates = result.scalar() or 0

    project = SMSIProject(
        created_by_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        organization_name=project_data.organization_name,
        organization_type=project_data.organization_type,
        organization_size=project_data.organization_size,
        industry_sector=project_data.industry_sector,
        selected_frameworks=project_data.selected_frameworks,
        security_level=security_level,
        pack_type=project_data.pack_type,
        documents_total=total_templates
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List user's SMSI projects."""
    stmt = select(SMSIProject).where(
        SMSIProject.created_by_id == current_user.id
    )

    if status:
        stmt = stmt.where(SMSIProject.status == status)

    stmt = stmt.order_by(SMSIProject.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)

    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get project details."""
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a project."""
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(project)
    await db.commit()


# =============================================================================
# QCM / RESPONSES ENDPOINTS
# =============================================================================

@router.post("/projects/{project_id}/responses")
async def submit_responses(
    project_id: uuid.UUID,
    data: ResponseBulkSubmit,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit QCM responses for a project."""
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update project status
    if project.status == ProjectStatus.CREATED:
        project.status = ProjectStatus.ASSESSMENT

    submitted = []
    for resp in data.responses:
        # Check if question exists
        question = await db.get(Question, resp.question_id)
        if not question:
            continue

        # Check for existing response
        stmt = select(QuestionResponse).where(
            QuestionResponse.project_id == project_id,
            QuestionResponse.question_id == resp.question_id
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.response_value = resp.response_value
            existing.response_text = resp.response_text
        else:
            new_response = QuestionResponse(
                project_id=project_id,
                question_id=resp.question_id,
                response_value=resp.response_value,
                response_text=resp.response_text
            )
            db.add(new_response)

        submitted.append(str(resp.question_id))

    await db.commit()

    return {
        "project_id": str(project_id),
        "responses_submitted": len(submitted),
        "status": project.status.value
    }


@router.get("/projects/{project_id}/responses")
async def get_project_responses(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all responses for a project."""
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = select(QuestionResponse, Question).join(
        Question, QuestionResponse.question_id == Question.id
    ).where(QuestionResponse.project_id == project_id)

    result = await db.execute(stmt)
    rows = result.all()

    responses = []
    for resp, question in rows:
        responses.append({
            "question_id": str(question.id),
            "variable_name": question.variable_name,
            "question_text": question.question_text,
            "response_value": resp.response_value,
            "response_text": resp.response_text,
            "ai_suggested": resp.ai_suggested
        })

    return {"project_id": str(project_id), "responses": responses}


# =============================================================================
# DOCUMENT GENERATION ENDPOINTS
# =============================================================================

@router.post("/projects/{project_id}/generate")
async def generate_documents(
    project_id: uuid.UUID,
    pack_type: str = Query(None, pattern="^(essential|standard|advanced)$"),
    use_ai: bool = Query(False, description="Use AI customization (slower)"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate SMSI documents for a project using fast template-based generation.

    Args:
        project_id: Project UUID
        pack_type: Document pack to use (essential, standard, advanced).
                   If not provided, uses the project's configured pack_type.
        use_ai: Whether to use AI for customization (slower but more personalized)
    """
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Use project's pack_type if not specified in query
    effective_pack_type = pack_type or getattr(project, 'pack_type', 'standard') or 'standard'

    # Use fast generator with pre-written templates
    generator = get_fast_generator(db)

    try:
        result = await generator.generate_project_documents(
            project_id=project_id,
            pack_type=effective_pack_type,
            use_ai_customization=use_ai
        )
        return result
    except Exception as e:
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Generation error for project {project_id}: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/documents", response_model=List[GeneratedDocumentResponse])
async def list_project_documents(
    project_id: uuid.UUID,
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List generated documents for a project."""
    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = select(GeneratedDocument).where(GeneratedDocument.project_id == project_id)

    if status:
        stmt = stmt.where(GeneratedDocument.status == status)
    if document_type:
        stmt = stmt.where(GeneratedDocument.document_type == document_type)

    stmt = stmt.order_by(GeneratedDocument.created_at.desc())
    result = await db.execute(stmt)

    return result.scalars().all()


@router.get("/documents", response_model=List[GeneratedDocumentResponse])
async def list_all_documents(
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all documents for the current user across all projects."""
    stmt = select(GeneratedDocument).join(
        SMSIProject, GeneratedDocument.project_id == SMSIProject.id
    ).where(SMSIProject.created_by_id == current_user.id)

    if status:
        stmt = stmt.where(GeneratedDocument.status == status)
    if document_type:
        stmt = stmt.where(GeneratedDocument.document_type == document_type)

    stmt = stmt.order_by(GeneratedDocument.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)

    return result.scalars().all()


@router.get("/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get document details with content."""
    doc = await db.get(GeneratedDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check access
    project = await db.get(SMSIProject, doc.project_id)
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": str(doc.id),
        "code": doc.code,
        "name": doc.name,
        "document_type": doc.document_type.value,
        "version": doc.version,
        "status": doc.status.value,
        "content_markdown": doc.content_markdown,
        "content_html": doc.content_html,
        "content_json": doc.content_json,
        "ai_model_used": doc.ai_model_used,
        "ai_tokens_input": doc.ai_tokens_input,
        "ai_tokens_output": doc.ai_tokens_output,
        "ai_generation_time": doc.ai_generation_time,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }


@router.post("/documents/{document_id}/regenerate")
async def regenerate_document(
    document_id: uuid.UUID,
    feedback: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Regenerate a document with optional feedback."""
    doc = await db.get(GeneratedDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    project = await db.get(SMSIProject, doc.project_id)
    if project.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    generator = DocumentGeneratorService(db)

    try:
        updated_doc = await generator.regenerate_document(document_id, feedback)
        return {
            "id": str(updated_doc.id),
            "version": updated_doc.version,
            "status": updated_doc.status.value,
            "message": "Document regenerated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# DOCUMENT EDITING & VERSIONING ENDPOINTS
# =============================================================================

class DocumentUpdateRequest(BaseModel):
    content_markdown: str
    change_summary: Optional[str] = None


class CommentRequest(BaseModel):
    content: str
    comment_type: str = "general"
    section_ref: Optional[str] = None
    line_number: Optional[int] = None


@router.get("/documents/{document_id}/view")
async def get_document_for_editing(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get document with full details for viewing/editing."""
    service = get_document_service(db)
    try:
        return await service.get_document(document_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/documents/{document_id}/lock")
async def acquire_document_lock(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Acquire editing lock on a document."""
    service = get_document_service(db)
    try:
        return await service.acquire_lock(document_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/documents/{document_id}/lock")
async def release_document_lock(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Release editing lock on a document."""
    service = get_document_service(db)
    try:
        return await service.release_lock(document_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/documents/{document_id}")
async def update_document(
    document_id: uuid.UUID,
    request: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update document content and create a new version."""
    service = get_document_service(db)
    try:
        return await service.update_document(
            document_id,
            current_user.id,
            request.content_markdown,
            request.change_summary
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{document_id}/versions")
async def get_document_versions(
    document_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get version history for a document."""
    service = get_document_service(db)
    try:
        return await service.get_version_history(document_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/documents/{document_id}/versions/{version_number}")
async def get_document_version_content(
    document_id: uuid.UUID,
    version_number: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get content of a specific version."""
    service = get_document_service(db)
    try:
        return await service.get_version_content(document_id, version_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/documents/{document_id}/rollback/{version_number}")
async def rollback_document(
    document_id: uuid.UUID,
    version_number: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Rollback document to a previous version."""
    service = get_document_service(db)
    try:
        return await service.rollback_to_version(document_id, version_number, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{document_id}/rollback-validated")
async def rollback_to_validated(
    document_id: uuid.UUID,
    use_second_last: bool = Query(False, description="Use second last validated version"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Quick rollback to last (or second last) validated version."""
    service = get_document_service(db)
    try:
        return await service.rollback_to_last_validated(document_id, current_user.id, use_second_last)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{document_id}/validate")
async def validate_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Validate the current version of a document."""
    service = get_document_service(db)
    try:
        return await service.validate_version(document_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/documents/{document_id}/owner/{new_owner_id}")
async def set_document_owner(
    document_id: uuid.UUID,
    new_owner_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set document owner."""
    service = get_document_service(db)
    try:
        return await service.set_owner(document_id, new_owner_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# DOCUMENT COMMENTS ENDPOINTS
# =============================================================================

@router.post("/documents/{document_id}/comments")
async def add_document_comment(
    document_id: uuid.UUID,
    request: CommentRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a comment to a document."""
    service = get_document_service(db)
    try:
        return await service.add_comment(
            document_id,
            current_user.id,
            request.content,
            request.comment_type,
            request.section_ref,
            request.line_number
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{document_id}/comments")
async def get_document_comments(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all comments for a document."""
    service = get_document_service(db)
    return await service.get_comments(document_id)


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark a comment as resolved."""
    service = get_document_service(db)
    try:
        return await service.resolve_comment(comment_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================

@router.post("/documents/{document_id}/export")
async def export_document(
    document_id: uuid.UUID,
    request: DocumentExportRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export a document to specified format."""
    doc = await db.get(GeneratedDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    project = await db.get(SMSIProject, doc.project_id)
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await export_service.export_document(
        doc,
        request.format,
        organization_name=project.organization_name
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Export failed"))

    # Return file as download
    content = result["content"]
    filename = result["filename"]

    content_types = {
        "md": "text/markdown",
        "html": "text/html",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }

    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_types.get(request.format, "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/projects/{project_id}/export-all")
async def export_all_documents(
    project_id: uuid.UUID,
    format: str = Query(..., pattern="^(md|html|docx|pdf|xlsx|csv|pptx)$"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export all project documents as a ZIP archive."""
    import zipfile

    project = await db.get(SMSIProject, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.created_by_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get all documents
    stmt = select(GeneratedDocument).where(GeneratedDocument.project_id == project_id)
    result = await db.execute(stmt)
    documents = result.scalars().all()

    if not documents:
        raise HTTPException(status_code=404, detail="No documents to export")

    # Create ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for doc in documents:
            export_result = await export_service.export_document(
                doc,
                format,
                organization_name=project.organization_name
            )
            if export_result["success"]:
                zip_file.writestr(export_result["filename"], export_result["content"])

    zip_buffer.seek(0)

    filename = f"{project.organization_name.replace(' ', '_')}_SMSI_{datetime.now().strftime('%Y%m%d')}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# =============================================================================
# AI SUGGESTION ENDPOINTS
# =============================================================================

@router.post("/ai/suggest")
async def get_ai_suggestion(
    request: AISuggestionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Get AI suggestion for a QCM question."""
    result = await mistral_service.suggest_answer(
        question=request.question,
        context=request.context,
        options=request.options
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "AI suggestion failed")
        )

    return result


# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================

@router.get("/stats")
async def get_smsi_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get SMSI module statistics."""
    # Count frameworks
    frameworks_count = await db.execute(select(func.count()).select_from(Framework))
    frameworks = frameworks_count.scalar() or 0

    # Count templates
    templates_count = await db.execute(
        select(func.count()).select_from(DocumentTemplate).where(DocumentTemplate.is_active == True)
    )
    templates = templates_count.scalar() or 0

    # Count user's projects
    projects_count = await db.execute(
        select(func.count()).select_from(SMSIProject).where(
            SMSIProject.created_by_id == current_user.id
        )
    )
    projects = projects_count.scalar() or 0

    # Count generated documents for user
    stmt = select(func.count()).select_from(GeneratedDocument).join(
        SMSIProject, GeneratedDocument.project_id == SMSIProject.id
    ).where(SMSIProject.created_by_id == current_user.id)
    docs_count = await db.execute(stmt)
    documents = docs_count.scalar() or 0

    # Total tokens used
    stmt = select(func.sum(SMSIProject.ai_tokens_used)).where(
        SMSIProject.created_by_id == current_user.id
    )
    tokens_result = await db.execute(stmt)
    tokens_used = tokens_result.scalar() or 0

    return {
        "frameworks_available": frameworks,
        "templates_available": templates,
        "user_projects": projects,
        "documents_generated": documents,
        "ai_tokens_used": tokens_used
    }


# =============================================================================
# DOCUMENT PACKS ENDPOINTS
# =============================================================================

@router.post("/packs/propose")
async def propose_document_packs(
    selected_frameworks: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """Propose document packs based on selected frameworks.

    Returns 3 pack options (essential, standard, advanced) with a recommended one.
    Each pack contains a list of documents appropriate for the selected frameworks.
    """
    if not selected_frameworks:
        raise HTTPException(
            status_code=400,
            detail="At least one framework must be selected"
        )

    # Validate frameworks
    valid_frameworks = ["ISO27001", "DORA", "NIS2", "RGPD", "PCI-DSS", "EU-AI-ACT", "NIST-CSF"]
    for fw in selected_frameworks:
        if fw not in valid_frameworks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework: {fw}. Valid options: {valid_frameworks}"
            )

    return get_pack_proposal(selected_frameworks)


@router.get("/packs")
async def list_document_packs(
    current_user: User = Depends(get_current_active_user)
):
    """List all available document packs."""
    packs = []
    for pack_type, pack_data in DOCUMENT_PACKS.items():
        packs.append({
            "type": pack_type,
            "name": pack_data["name"],
            "description": pack_data["description"],
            "estimated_pages": pack_data["estimated_pages"],
            "document_count": len(pack_data["documents"]),
            "documents_preview": [
                {"code": d["code"], "name": d["name"], "type": d["type"]}
                for d in pack_data["documents"][:5]  # First 5 documents as preview
            ]
        })
    return packs


@router.get("/packs/{pack_type}")
async def get_document_pack(
    pack_type: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get details of a specific document pack."""
    if pack_type not in DOCUMENT_PACKS:
        raise HTTPException(
            status_code=404,
            detail=f"Pack not found. Valid packs: {list(DOCUMENT_PACKS.keys())}"
        )

    pack = DOCUMENT_PACKS[pack_type]
    return {
        "type": pack_type,
        "name": pack["name"],
        "description": pack["description"],
        "estimated_pages": pack["estimated_pages"],
        "documents": pack["documents"]
    }
