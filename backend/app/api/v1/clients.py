"""API endpoints for Client Requirements Management."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.infrastructure.database import get_async_db
from app.infrastructure.database.client_requirements_models import (
    Client,
    ClientRequirement,
    ComplianceAssessment,
    RequirementCompliance,
    RemediationAction,
    Evidence,
    ComplianceStatus,
    ActionStatus,
    RequirementCategory,
    RequirementPriority,
    EvidenceType,
)
from app.infrastructure.database.models import User
from app.schemas.client_requirements import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse,
    RequirementListResponse,
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentSummary,
    ComplianceRecordUpdate,
    ComplianceRecordResponse,
    ComplianceRecordWithRequirement,
    RemediationActionCreate,
    RemediationActionUpdate,
    RemediationActionResponse,
    RemediationPlanGenerate,
    RemediationPlanResponse,
    AIAssessmentRequest,
    AIAssessmentResponse,
    ClientComplianceStats,
    RemediationStats,
    EvidenceCreate,
    EvidenceUpdate,
    EvidenceResponse,
    EvidenceVerify,
    ClientDashboard,
    AssessmentTrendPoint,
    CategoryScore,
    PriorityScore,
    EvidenceStats,
)
from app.application.compliance.remediation_service import RemediationService
from app.api.v1.deps import get_current_active_user

router = APIRouter(prefix="/clients", tags=["Clients & Requirements"])


# =============================================================================
# CLIENTS ENDPOINTS
# =============================================================================

@router.get("", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    industry_sector: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all clients with pagination and filters."""
    query = select(Client)
    count_query = select(func.count(Client.id))

    # Apply filters
    if search:
        search_filter = or_(
            Client.name.ilike(f"%{search}%"),
            Client.code.ilike(f"%{search}%"),
            Client.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if is_active is not None:
        query = query.where(Client.is_active == is_active)
        count_query = count_query.where(Client.is_active == is_active)

    if industry_sector:
        query = query.where(Client.industry_sector == industry_sector)
        count_query = count_query.where(Client.industry_sector == industry_sector)

    # Get total count
    total = await db.scalar(count_query)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Client.name)

    result = await db.execute(query)
    clients = result.scalars().all()

    # Get requirements count for each client
    items = []
    for client in clients:
        req_count = await db.scalar(
            select(func.count(ClientRequirement.id))
            .where(ClientRequirement.client_id == client.id)
        )
        client_dict = {
            **{c.key: getattr(client, c.key) for c in Client.__table__.columns},
            "requirements_count": req_count,
            "compliance_score": None,
        }
        items.append(ClientResponse(**client_dict))

    return ClientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new client."""
    # Check if code already exists
    existing = await db.scalar(
        select(Client).where(Client.code == client_in.code)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Client with code '{client_in.code}' already exists",
        )

    client = Client(**client_in.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)

    logger.info(f"Created client: {client.name} ({client.code})")

    return ClientResponse(
        **{c.key: getattr(client, c.key) for c in Client.__table__.columns},
        requirements_count=0,
        compliance_score=None,
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a client by ID."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    req_count = await db.scalar(
        select(func.count(ClientRequirement.id))
        .where(ClientRequirement.client_id == client.id)
    )

    return ClientResponse(
        **{c.key: getattr(client, c.key) for c in Client.__table__.columns},
        requirements_count=req_count,
        compliance_score=None,
    )


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    req_count = await db.scalar(
        select(func.count(ClientRequirement.id))
        .where(ClientRequirement.client_id == client.id)
    )

    return ClientResponse(
        **{c.key: getattr(client, c.key) for c in Client.__table__.columns},
        requirements_count=req_count,
        compliance_score=None,
    )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    await db.delete(client)
    await db.commit()
    logger.info(f"Deleted client: {client.name} ({client.code})")


@router.get("/{client_id}/stats", response_model=ClientComplianceStats)
async def get_client_stats(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get compliance statistics for a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get latest assessment
    latest_assessment = await db.scalar(
        select(ComplianceAssessment)
        .where(ComplianceAssessment.client_id == client_id)
        .order_by(ComplianceAssessment.assessment_date.desc())
        .limit(1)
    )

    if latest_assessment:
        total = latest_assessment.total_requirements
        compliant = latest_assessment.compliant_count
        partially = latest_assessment.partially_compliant_count
        non_compliant = latest_assessment.non_compliant_count
        not_assessed = latest_assessment.not_assessed_count
        score = latest_assessment.compliance_score or 0
    else:
        total = await db.scalar(
            select(func.count(ClientRequirement.id))
            .where(ClientRequirement.client_id == client_id)
        )
        compliant = 0
        partially = 0
        non_compliant = 0
        not_assessed = total
        score = 0

    # Get open actions count
    open_actions = await db.scalar(
        select(func.count(RemediationAction.id))
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            RemediationAction.status.in_([ActionStatus.PLANNED, ActionStatus.IN_PROGRESS])
        )
    ) or 0

    # Get overdue actions count
    overdue_actions = await db.scalar(
        select(func.count(RemediationAction.id))
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            RemediationAction.status.in_([ActionStatus.PLANNED, ActionStatus.IN_PROGRESS]),
            RemediationAction.due_date < datetime.utcnow()
        )
    ) or 0

    return ClientComplianceStats(
        client_id=client_id,
        client_name=client.name,
        total_requirements=total,
        compliant=compliant,
        partially_compliant=partially,
        non_compliant=non_compliant,
        not_assessed=not_assessed,
        compliance_score=score,
        open_actions=open_actions,
        overdue_actions=overdue_actions,
    )


# =============================================================================
# REQUIREMENTS ENDPOINTS
# =============================================================================

@router.get("/{client_id}/requirements", response_model=RequirementListResponse)
async def list_requirements(
    client_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[RequirementCategory] = None,
    priority: Optional[RequirementPriority] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List requirements for a client."""
    # Verify client exists
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    query = select(ClientRequirement).where(ClientRequirement.client_id == client_id)
    count_query = select(func.count(ClientRequirement.id)).where(
        ClientRequirement.client_id == client_id
    )

    if category:
        query = query.where(ClientRequirement.category == category)
        count_query = count_query.where(ClientRequirement.category == category)

    if priority:
        query = query.where(ClientRequirement.priority == priority)
        count_query = count_query.where(ClientRequirement.priority == priority)

    if is_active is not None:
        query = query.where(ClientRequirement.is_active == is_active)
        count_query = count_query.where(ClientRequirement.is_active == is_active)

    if search:
        search_filter = or_(
            ClientRequirement.code.ilike(f"%{search}%"),
            ClientRequirement.title.ilike(f"%{search}%"),
            ClientRequirement.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = await db.scalar(count_query)

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(ClientRequirement.code)

    result = await db.execute(query)
    requirements = result.scalars().all()

    items = [
        RequirementResponse(
            **{c.key: getattr(req, c.key) for c in ClientRequirement.__table__.columns},
            current_compliance_status=None,
        )
        for req in requirements
    ]

    return RequirementListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{client_id}/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    client_id: uuid.UUID,
    requirement_in: RequirementCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new requirement for a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Check duplicate code for this client
    existing = await db.scalar(
        select(ClientRequirement).where(
            ClientRequirement.client_id == client_id,
            ClientRequirement.code == requirement_in.code,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requirement with code '{requirement_in.code}' already exists for this client",
        )

    requirement = ClientRequirement(
        **requirement_in.model_dump(exclude={"client_id"}),
        client_id=client_id,
    )
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)

    logger.info(f"Created requirement: {requirement.code} for client {client.code}")

    return RequirementResponse(
        **{c.key: getattr(requirement, c.key) for c in ClientRequirement.__table__.columns},
        current_compliance_status=None,
    )


@router.get("/{client_id}/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(
    client_id: uuid.UUID,
    requirement_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a requirement by ID."""
    requirement = await db.scalar(
        select(ClientRequirement).where(
            ClientRequirement.id == requirement_id,
            ClientRequirement.client_id == client_id,
        )
    )
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return RequirementResponse(
        **{c.key: getattr(requirement, c.key) for c in ClientRequirement.__table__.columns},
        current_compliance_status=None,
    )


@router.patch("/{client_id}/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    client_id: uuid.UUID,
    requirement_id: uuid.UUID,
    requirement_in: RequirementUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a requirement."""
    requirement = await db.scalar(
        select(ClientRequirement).where(
            ClientRequirement.id == requirement_id,
            ClientRequirement.client_id == client_id,
        )
    )
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    update_data = requirement_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(requirement, field, value)

    await db.commit()
    await db.refresh(requirement)

    return RequirementResponse(
        **{c.key: getattr(requirement, c.key) for c in ClientRequirement.__table__.columns},
        current_compliance_status=None,
    )


@router.delete("/{client_id}/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    client_id: uuid.UUID,
    requirement_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a requirement."""
    requirement = await db.scalar(
        select(ClientRequirement).where(
            ClientRequirement.id == requirement_id,
            ClientRequirement.client_id == client_id,
        )
    )
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    await db.delete(requirement)
    await db.commit()


# =============================================================================
# ASSESSMENTS ENDPOINTS
# =============================================================================

@router.get("/{client_id}/assessments", response_model=List[AssessmentResponse])
async def list_assessments(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all assessments for a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    result = await db.execute(
        select(ComplianceAssessment)
        .where(ComplianceAssessment.client_id == client_id)
        .order_by(ComplianceAssessment.assessment_date.desc())
    )
    assessments = result.scalars().all()

    return [
        AssessmentResponse(
            **{c.key: getattr(a, c.key) for c in ComplianceAssessment.__table__.columns}
        )
        for a in assessments
    ]


@router.post("/{client_id}/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    client_id: uuid.UUID,
    assessment_in: AssessmentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new compliance assessment for a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get requirements to assess
    if assessment_in.requirement_ids:
        requirements = (await db.execute(
            select(ClientRequirement).where(
                ClientRequirement.id.in_(assessment_in.requirement_ids),
                ClientRequirement.client_id == client_id,
            )
        )).scalars().all()
    else:
        requirements = (await db.execute(
            select(ClientRequirement).where(
                ClientRequirement.client_id == client_id,
                ClientRequirement.is_active == True,
            )
        )).scalars().all()

    # Create assessment
    assessment = ComplianceAssessment(
        client_id=client_id,
        assessed_by_id=current_user.id,
        name=assessment_in.name,
        description=assessment_in.description,
        scope=assessment_in.scope,
        period_start=assessment_in.period_start,
        period_end=assessment_in.period_end,
        total_requirements=len(requirements),
        not_assessed_count=len(requirements),
    )
    db.add(assessment)
    await db.flush()

    # Create compliance records for each requirement
    for req in requirements:
        compliance_record = RequirementCompliance(
            assessment_id=assessment.id,
            requirement_id=req.id,
            status=ComplianceStatus.NOT_ASSESSED,
        )
        db.add(compliance_record)

    await db.commit()
    await db.refresh(assessment)

    logger.info(f"Created assessment '{assessment.name}' for client {client.code} with {len(requirements)} requirements")

    return AssessmentResponse(
        **{c.key: getattr(assessment, c.key) for c in ComplianceAssessment.__table__.columns}
    )


@router.get("/{client_id}/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get an assessment by ID."""
    assessment = await db.scalar(
        select(ComplianceAssessment).where(
            ComplianceAssessment.id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    return AssessmentResponse(
        **{c.key: getattr(assessment, c.key) for c in ComplianceAssessment.__table__.columns}
    )


@router.get("/{client_id}/assessments/{assessment_id}/summary", response_model=AssessmentSummary)
async def get_assessment_summary(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get detailed summary of an assessment."""
    assessment = await db.scalar(
        select(ComplianceAssessment).where(
            ComplianceAssessment.id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    # Get compliance records with requirements
    result = await db.execute(
        select(RequirementCompliance, ClientRequirement)
        .join(ClientRequirement)
        .where(RequirementCompliance.assessment_id == assessment_id)
    )
    records = result.all()

    # Build stats by category and priority
    by_category = {}
    by_priority = {}

    for record, requirement in records:
        cat = requirement.category.value
        pri = requirement.priority.value
        status_val = record.status.value

        if cat not in by_category:
            by_category[cat] = {s.value: 0 for s in ComplianceStatus}
        by_category[cat][status_val] += 1

        if pri not in by_priority:
            by_priority[pri] = {s.value: 0 for s in ComplianceStatus}
        by_priority[pri][status_val] += 1

    return AssessmentSummary(
        total_requirements=assessment.total_requirements,
        compliant=assessment.compliant_count,
        partially_compliant=assessment.partially_compliant_count,
        non_compliant=assessment.non_compliant_count,
        not_applicable=assessment.not_applicable_count,
        not_assessed=assessment.not_assessed_count,
        compliance_score=assessment.compliance_score or 0,
        by_category=by_category,
        by_priority=by_priority,
    )


@router.post("/{client_id}/assessments/{assessment_id}/finalize", response_model=AssessmentResponse)
async def finalize_assessment(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Finalize an assessment and calculate final score."""
    assessment = await db.scalar(
        select(ComplianceAssessment).where(
            ComplianceAssessment.id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    if assessment.is_final:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is already finalized",
        )

    # Count statuses
    counts = await db.execute(
        select(
            RequirementCompliance.status,
            func.count(RequirementCompliance.id)
        )
        .where(RequirementCompliance.assessment_id == assessment_id)
        .group_by(RequirementCompliance.status)
    )

    status_counts = {row[0]: row[1] for row in counts}

    assessment.compliant_count = status_counts.get(ComplianceStatus.COMPLIANT, 0)
    assessment.partially_compliant_count = status_counts.get(ComplianceStatus.PARTIALLY_COMPLIANT, 0)
    assessment.non_compliant_count = status_counts.get(ComplianceStatus.NON_COMPLIANT, 0)
    assessment.not_applicable_count = status_counts.get(ComplianceStatus.NOT_APPLICABLE, 0)
    assessment.not_assessed_count = status_counts.get(ComplianceStatus.NOT_ASSESSED, 0)

    # Calculate compliance score (excluding not_applicable and not_assessed)
    assessed = assessment.total_requirements - assessment.not_applicable_count - assessment.not_assessed_count
    if assessed > 0:
        score = (
            (assessment.compliant_count * 100) +
            (assessment.partially_compliant_count * 50)
        ) / assessed
        assessment.compliance_score = round(score, 2)
    else:
        assessment.compliance_score = 0

    assessment.is_final = True
    assessment.status = "completed"
    assessment.finalized_at = datetime.utcnow()

    await db.commit()
    await db.refresh(assessment)

    logger.info(f"Finalized assessment '{assessment.name}' with score {assessment.compliance_score}%")

    return AssessmentResponse(
        **{c.key: getattr(assessment, c.key) for c in ComplianceAssessment.__table__.columns}
    )


# =============================================================================
# COMPLIANCE RECORDS ENDPOINTS
# =============================================================================

@router.get("/{client_id}/assessments/{assessment_id}/records", response_model=List[ComplianceRecordWithRequirement])
async def list_compliance_records(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    status_filter: Optional[ComplianceStatus] = None,
    category: Optional[RequirementCategory] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List compliance records for an assessment."""
    assessment = await db.scalar(
        select(ComplianceAssessment).where(
            ComplianceAssessment.id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    query = (
        select(RequirementCompliance, ClientRequirement)
        .join(ClientRequirement)
        .where(RequirementCompliance.assessment_id == assessment_id)
    )

    if status_filter:
        query = query.where(RequirementCompliance.status == status_filter)

    if category:
        query = query.where(ClientRequirement.category == category)

    query = query.order_by(ClientRequirement.code)

    result = await db.execute(query)
    records = result.all()

    items = []
    for record, requirement in records:
        # Count remediation actions
        actions_count = await db.scalar(
            select(func.count(RemediationAction.id))
            .where(RemediationAction.compliance_record_id == record.id)
        ) or 0

        # Count evidence
        evidence_count = await db.scalar(
            select(func.count(Evidence.id))
            .where(Evidence.compliance_record_id == record.id)
        ) or 0

        record_dict = {c.key: getattr(record, c.key) for c in RequirementCompliance.__table__.columns}
        req_dict = {c.key: getattr(requirement, c.key) for c in ClientRequirement.__table__.columns}

        items.append(ComplianceRecordWithRequirement(
            **record_dict,
            requirement=RequirementResponse(**req_dict, current_compliance_status=None),
            remediation_actions_count=actions_count,
            evidence_count=evidence_count,
        ))

    return items


@router.patch("/{client_id}/assessments/{assessment_id}/records/{record_id}", response_model=ComplianceRecordResponse)
async def update_compliance_record(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    record_in: ComplianceRecordUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a compliance record."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    # Store previous status
    if record_in.status and record_in.status != record.status:
        record.previous_status = record.status.value

    update_data = record_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    record.assessed_by_id = current_user.id
    record.assessed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(record)

    actions_count = await db.scalar(
        select(func.count(RemediationAction.id))
        .where(RemediationAction.compliance_record_id == record.id)
    ) or 0

    return ComplianceRecordResponse(
        **{c.key: getattr(record, c.key) for c in RequirementCompliance.__table__.columns},
        remediation_actions_count=actions_count,
    )


# =============================================================================
# REMEDIATION ACTIONS ENDPOINTS
# =============================================================================

@router.get("/{client_id}/assessments/{assessment_id}/records/{record_id}/actions", response_model=List[RemediationActionResponse])
async def list_remediation_actions(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List remediation actions for a compliance record."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    result = await db.execute(
        select(RemediationAction)
        .where(RemediationAction.compliance_record_id == record_id)
        .order_by(RemediationAction.priority, RemediationAction.created_at)
    )
    actions = result.scalars().all()

    return [
        RemediationActionResponse(
            **{c.key: getattr(a, c.key) for c in RemediationAction.__table__.columns}
        )
        for a in actions
    ]


@router.post("/{client_id}/assessments/{assessment_id}/records/{record_id}/actions/generate", response_model=RemediationPlanResponse)
async def generate_remediation_plan(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate AI-powered remediation plan for a non-compliant requirement."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    requirement = await db.get(ClientRequirement, record.requirement_id)

    service = RemediationService(db)
    actions = await service.generate_remediation_plan(record_id, current_user.id)

    return RemediationPlanResponse(
        compliance_record_id=record_id,
        requirement_code=requirement.code,
        requirement_title=requirement.title,
        gap_description=record.gap_description,
        actions=[
            RemediationActionResponse(
                **{c.key: getattr(a, c.key) for c in RemediationAction.__table__.columns}
            )
            for a in actions
        ],
        generated_at=datetime.utcnow(),
    )


@router.post("/{client_id}/assessments/{assessment_id}/records/{record_id}/actions", response_model=RemediationActionResponse, status_code=status.HTTP_201_CREATED)
async def create_remediation_action(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    action_in: RemediationActionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a manual remediation action."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    action = RemediationAction(
        **action_in.model_dump(exclude={"compliance_record_id"}),
        compliance_record_id=record_id,
        created_by_id=current_user.id,
        ai_generated=False,
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)

    return RemediationActionResponse(
        **{c.key: getattr(action, c.key) for c in RemediationAction.__table__.columns}
    )


@router.patch("/{client_id}/actions/{action_id}", response_model=RemediationActionResponse)
async def update_remediation_action(
    client_id: uuid.UUID,
    action_id: uuid.UUID,
    action_in: RemediationActionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a remediation action."""
    action = await db.scalar(
        select(RemediationAction)
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RemediationAction.id == action_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remediation action not found",
        )

    update_data = action_in.model_dump(exclude_unset=True)

    # Handle status transitions
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == ActionStatus.IN_PROGRESS and not action.started_at:
            action.started_at = datetime.utcnow()
        elif new_status == ActionStatus.COMPLETED:
            action.completed_at = datetime.utcnow()
            action.progress_percentage = 100

    for field, value in update_data.items():
        setattr(action, field, value)

    await db.commit()
    await db.refresh(action)

    return RemediationActionResponse(
        **{c.key: getattr(action, c.key) for c in RemediationAction.__table__.columns}
    )


@router.delete("/{client_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_remediation_action(
    client_id: uuid.UUID,
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a remediation action."""
    action = await db.scalar(
        select(RemediationAction)
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RemediationAction.id == action_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Remediation action not found",
        )

    await db.delete(action)
    await db.commit()


# =============================================================================
# AI ASSESSMENT ENDPOINT
# =============================================================================

@router.post("/{client_id}/assessments/{assessment_id}/records/{record_id}/ai-assess", response_model=AIAssessmentResponse)
async def ai_assess_compliance(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    request: AIAssessmentRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Use AI to assess compliance based on provided evidence."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    requirement = await db.get(ClientRequirement, record.requirement_id)

    service = RemediationService(db)
    result = await service.assess_compliance_with_ai(requirement, request.evidence)

    # Update record with AI assessment
    record.ai_assessment = result.get("gap_analysis")
    record.ai_recommendations = result.get("recommendations")
    record.ai_confidence = 0.8 if result.get("status") != "not_assessed" else 0

    await db.commit()

    status_mapping = {
        "compliant": ComplianceStatus.COMPLIANT,
        "partially_compliant": ComplianceStatus.PARTIALLY_COMPLIANT,
        "non_compliant": ComplianceStatus.NON_COMPLIANT,
        "not_assessed": ComplianceStatus.NOT_ASSESSED,
    }

    return AIAssessmentResponse(
        status=status_mapping.get(result.get("status"), ComplianceStatus.NOT_ASSESSED),
        compliance_level=result.get("compliance_level"),
        gap_analysis=result.get("gap_analysis"),
        recommendations=result.get("recommendations"),
        confidence=0.8 if result.get("status") != "not_assessed" else 0,
        success=result.get("status") != "not_assessed",
        error=result.get("error"),
    )


# =============================================================================
# REMEDIATION STATS ENDPOINT
# =============================================================================

@router.get("/{client_id}/remediation-stats", response_model=RemediationStats)
async def get_remediation_stats(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get remediation statistics for a client."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Count actions by status
    counts = await db.execute(
        select(
            RemediationAction.status,
            func.count(RemediationAction.id)
        )
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(ComplianceAssessment.client_id == client_id)
        .group_by(RemediationAction.status)
    )
    status_counts = {row[0]: row[1] for row in counts}

    total = sum(status_counts.values())
    completed = status_counts.get(ActionStatus.COMPLETED, 0)

    # Count overdue
    overdue = await db.scalar(
        select(func.count(RemediationAction.id))
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            RemediationAction.status.in_([ActionStatus.PLANNED, ActionStatus.IN_PROGRESS]),
            RemediationAction.due_date < datetime.utcnow()
        )
    ) or 0

    return RemediationStats(
        total_actions=total,
        planned=status_counts.get(ActionStatus.PLANNED, 0),
        in_progress=status_counts.get(ActionStatus.IN_PROGRESS, 0),
        completed=completed,
        blocked=status_counts.get(ActionStatus.BLOCKED, 0),
        cancelled=status_counts.get(ActionStatus.CANCELLED, 0),
        overdue=overdue,
        completion_rate=round((completed / total * 100) if total > 0 else 0, 2),
    )


# =============================================================================
# EVIDENCE ENDPOINTS
# =============================================================================

@router.get("/{client_id}/assessments/{assessment_id}/records/{record_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List evidence for a compliance record."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    result = await db.execute(
        select(Evidence)
        .where(Evidence.compliance_record_id == record_id)
        .order_by(Evidence.created_at.desc())
    )
    evidence_list = result.scalars().all()

    return [
        EvidenceResponse(
            **{c.key: getattr(e, c.key) for c in Evidence.__table__.columns}
        )
        for e in evidence_list
    ]


@router.post("/{client_id}/assessments/{assessment_id}/records/{record_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    client_id: uuid.UUID,
    assessment_id: uuid.UUID,
    record_id: uuid.UUID,
    evidence_in: EvidenceCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add evidence to a compliance record."""
    record = await db.scalar(
        select(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            RequirementCompliance.id == record_id,
            RequirementCompliance.assessment_id == assessment_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance record not found",
        )

    # Check if evidence is expired
    is_expired = False
    if evidence_in.valid_until and evidence_in.valid_until < datetime.utcnow():
        is_expired = True

    evidence = Evidence(
        **evidence_in.model_dump(exclude={"compliance_record_id"}),
        compliance_record_id=record_id,
        uploaded_by_id=current_user.id,
        is_expired=is_expired,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    logger.info(f"Added evidence '{evidence.name}' to compliance record {record_id}")

    return EvidenceResponse(
        **{c.key: getattr(evidence, c.key) for c in Evidence.__table__.columns}
    )


@router.patch("/{client_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    client_id: uuid.UUID,
    evidence_id: uuid.UUID,
    evidence_in: EvidenceUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update evidence."""
    evidence = await db.scalar(
        select(Evidence)
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            Evidence.id == evidence_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    update_data = evidence_in.model_dump(exclude_unset=True)

    # Update expiry status if valid_until changed
    if "valid_until" in update_data and update_data["valid_until"]:
        evidence.is_expired = update_data["valid_until"] < datetime.utcnow()

    for field, value in update_data.items():
        setattr(evidence, field, value)

    await db.commit()
    await db.refresh(evidence)

    return EvidenceResponse(
        **{c.key: getattr(evidence, c.key) for c in Evidence.__table__.columns}
    )


@router.post("/{client_id}/evidence/{evidence_id}/verify", response_model=EvidenceResponse)
async def verify_evidence(
    client_id: uuid.UUID,
    evidence_id: uuid.UUID,
    verify_in: EvidenceVerify,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Verify or reject evidence."""
    evidence = await db.scalar(
        select(Evidence)
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            Evidence.id == evidence_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    evidence.is_verified = verify_in.is_verified
    evidence.verified_by_id = current_user.id
    evidence.verified_at = datetime.utcnow()
    evidence.verification_notes = verify_in.verification_notes

    await db.commit()
    await db.refresh(evidence)

    logger.info(f"Evidence '{evidence.name}' {'verified' if verify_in.is_verified else 'rejected'}")

    return EvidenceResponse(
        **{c.key: getattr(evidence, c.key) for c in Evidence.__table__.columns}
    )


@router.delete("/{client_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    client_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete evidence."""
    evidence = await db.scalar(
        select(Evidence)
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            Evidence.id == evidence_id,
            ComplianceAssessment.client_id == client_id,
        )
    )
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )

    await db.delete(evidence)
    await db.commit()


# =============================================================================
# CLIENT DASHBOARD ENDPOINT
# =============================================================================

@router.get("/{client_id}/dashboard", response_model=ClientDashboard)
async def get_client_dashboard(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive client dashboard with evolution and metrics."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get all finalized assessments ordered by date
    assessments_result = await db.execute(
        select(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            ComplianceAssessment.is_final == True
        )
        .order_by(ComplianceAssessment.assessment_date.asc())
    )
    assessments = assessments_result.scalars().all()

    # Build trend data
    assessment_trend = []
    for assessment in assessments:
        assessment_trend.append(AssessmentTrendPoint(
            assessment_id=assessment.id,
            assessment_name=assessment.name,
            date=assessment.assessment_date,
            compliance_score=assessment.compliance_score or 0,
            compliant_count=assessment.compliant_count,
            partially_compliant_count=assessment.partially_compliant_count,
            non_compliant_count=assessment.non_compliant_count,
            total_requirements=assessment.total_requirements,
        ))

    # Get latest assessment for current stats
    latest_assessment = assessments[-1] if assessments else None
    previous_assessment = assessments[-2] if len(assessments) >= 2 else None

    current_score = latest_assessment.compliance_score if latest_assessment else 0
    previous_score = previous_assessment.compliance_score if previous_assessment else None
    score_change = (current_score - previous_score) if previous_score is not None else None

    # Current status counts
    if latest_assessment:
        compliant_count = latest_assessment.compliant_count
        partially_compliant_count = latest_assessment.partially_compliant_count
        non_compliant_count = latest_assessment.non_compliant_count
        not_assessed_count = latest_assessment.not_assessed_count
        not_applicable_count = latest_assessment.not_applicable_count
        total_requirements = latest_assessment.total_requirements
    else:
        total_requirements = await db.scalar(
            select(func.count(ClientRequirement.id))
            .where(ClientRequirement.client_id == client_id, ClientRequirement.is_active == True)
        ) or 0
        compliant_count = 0
        partially_compliant_count = 0
        non_compliant_count = 0
        not_assessed_count = total_requirements
        not_applicable_count = 0

    # Get breakdown by category (from latest assessment)
    by_category = []
    if latest_assessment:
        cat_result = await db.execute(
            select(
                ClientRequirement.category,
                RequirementCompliance.status,
                func.count(RequirementCompliance.id)
            )
            .join(ClientRequirement)
            .where(RequirementCompliance.assessment_id == latest_assessment.id)
            .group_by(ClientRequirement.category, RequirementCompliance.status)
        )
        cat_data = {}
        for row in cat_result:
            cat = row[0].value
            status_val = row[1].value
            count = row[2]
            if cat not in cat_data:
                cat_data[cat] = {"total": 0, "compliant": 0, "partially_compliant": 0, "non_compliant": 0, "not_assessed": 0}
            cat_data[cat]["total"] += count
            if status_val == "compliant":
                cat_data[cat]["compliant"] += count
            elif status_val == "partially_compliant":
                cat_data[cat]["partially_compliant"] += count
            elif status_val == "non_compliant":
                cat_data[cat]["non_compliant"] += count
            elif status_val == "not_assessed":
                cat_data[cat]["not_assessed"] += count

        category_labels = {
            "security": "Securite",
            "privacy": "Confidentialite",
            "availability": "Disponibilite",
            "integrity": "Integrite",
            "audit": "Audit",
            "reporting": "Reporting",
            "sla": "SLA",
            "contractual": "Contractuel",
            "regulatory": "Reglementaire",
            "technical": "Technique",
            "organizational": "Organisationnel",
        }

        for cat, data in cat_data.items():
            assessed = data["total"] - data["not_assessed"]
            score = ((data["compliant"] * 100 + data["partially_compliant"] * 50) / assessed) if assessed > 0 else 0
            by_category.append(CategoryScore(
                category=cat,
                category_label=category_labels.get(cat, cat),
                total=data["total"],
                compliant=data["compliant"],
                partially_compliant=data["partially_compliant"],
                non_compliant=data["non_compliant"],
                not_assessed=data["not_assessed"],
                score=round(score, 2),
            ))

    # Get breakdown by priority
    by_priority = []
    if latest_assessment:
        pri_result = await db.execute(
            select(
                ClientRequirement.priority,
                RequirementCompliance.status,
                func.count(RequirementCompliance.id)
            )
            .join(ClientRequirement)
            .where(RequirementCompliance.assessment_id == latest_assessment.id)
            .group_by(ClientRequirement.priority, RequirementCompliance.status)
        )
        pri_data = {}
        for row in pri_result:
            pri = row[0].value
            status_val = row[1].value
            count = row[2]
            if pri not in pri_data:
                pri_data[pri] = {"total": 0, "compliant": 0, "non_compliant": 0}
            pri_data[pri]["total"] += count
            if status_val == "compliant":
                pri_data[pri]["compliant"] += count
            elif status_val == "non_compliant":
                pri_data[pri]["non_compliant"] += count

        priority_labels = {
            "critical": "Critique",
            "high": "Haute",
            "medium": "Moyenne",
            "low": "Basse",
        }

        for pri, data in pri_data.items():
            score = (data["compliant"] / data["total"] * 100) if data["total"] > 0 else 0
            by_priority.append(PriorityScore(
                priority=pri,
                priority_label=priority_labels.get(pri, pri),
                total=data["total"],
                compliant=data["compliant"],
                non_compliant=data["non_compliant"],
                score=round(score, 2),
            ))

    # Get action stats
    action_counts = await db.execute(
        select(
            RemediationAction.status,
            func.count(RemediationAction.id)
        )
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(ComplianceAssessment.client_id == client_id)
        .group_by(RemediationAction.status)
    )
    action_status_counts = {row[0]: row[1] for row in action_counts}

    total_actions = sum(action_status_counts.values())
    completed_actions = action_status_counts.get(ActionStatus.COMPLETED, 0)
    open_actions = (
        action_status_counts.get(ActionStatus.PLANNED, 0) +
        action_status_counts.get(ActionStatus.IN_PROGRESS, 0)
    )

    overdue_actions = await db.scalar(
        select(func.count(RemediationAction.id))
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            RemediationAction.status.in_([ActionStatus.PLANNED, ActionStatus.IN_PROGRESS]),
            RemediationAction.due_date < datetime.utcnow()
        )
    ) or 0

    action_completion_rate = (completed_actions / total_actions * 100) if total_actions > 0 else 0

    # Get evidence stats
    evidence_result = await db.execute(
        select(
            Evidence.evidence_type,
            Evidence.is_verified,
            Evidence.is_expired,
            func.count(Evidence.id)
        )
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(ComplianceAssessment.client_id == client_id)
        .group_by(Evidence.evidence_type, Evidence.is_verified, Evidence.is_expired)
    )

    total_evidence = 0
    verified_evidence = 0
    pending_verification = 0
    expired_evidence = 0
    evidence_by_type = {}

    for row in evidence_result:
        ev_type = row[0].value
        is_verified = row[1]
        is_expired = row[2]
        count = row[3]

        total_evidence += count
        if is_verified:
            verified_evidence += count
        else:
            pending_verification += count
        if is_expired:
            expired_evidence += count

        if ev_type not in evidence_by_type:
            evidence_by_type[ev_type] = 0
        evidence_by_type[ev_type] += count

    evidence_stats = EvidenceStats(
        total_evidence=total_evidence,
        verified_evidence=verified_evidence,
        pending_verification=pending_verification,
        expired_evidence=expired_evidence,
        by_type=evidence_by_type,
    )

    # Get critical non-compliant count
    critical_non_compliant = 0
    if latest_assessment:
        critical_non_compliant = await db.scalar(
            select(func.count(RequirementCompliance.id))
            .join(ClientRequirement)
            .where(
                RequirementCompliance.assessment_id == latest_assessment.id,
                RequirementCompliance.status == ComplianceStatus.NON_COMPLIANT,
                ClientRequirement.priority == RequirementPriority.CRITICAL
            )
        ) or 0

    # Get high priority open actions
    high_priority_actions = await db.scalar(
        select(func.count(RemediationAction.id))
        .join(RequirementCompliance)
        .join(ComplianceAssessment)
        .where(
            ComplianceAssessment.client_id == client_id,
            RemediationAction.status.in_([ActionStatus.PLANNED, ActionStatus.IN_PROGRESS]),
            RemediationAction.priority.in_([RequirementPriority.CRITICAL, RequirementPriority.HIGH])
        )
    ) or 0

    # Calculate days since last assessment
    days_since_last_assessment = None
    if latest_assessment:
        days_since_last_assessment = (datetime.utcnow() - latest_assessment.assessment_date).days

    return ClientDashboard(
        client_id=client_id,
        client_name=client.name,
        client_code=client.code,
        total_requirements=total_requirements,
        current_compliance_score=current_score or 0,
        previous_compliance_score=previous_score,
        score_change=round(score_change, 2) if score_change is not None else None,
        compliant_count=compliant_count,
        partially_compliant_count=partially_compliant_count,
        non_compliant_count=non_compliant_count,
        not_assessed_count=not_assessed_count,
        not_applicable_count=not_applicable_count,
        total_actions=total_actions,
        open_actions=open_actions,
        overdue_actions=overdue_actions,
        completed_actions=completed_actions,
        action_completion_rate=round(action_completion_rate, 2),
        evidence_stats=evidence_stats,
        assessment_trend=assessment_trend,
        by_category=by_category,
        by_priority=by_priority,
        last_assessment_date=latest_assessment.assessment_date if latest_assessment else None,
        next_review_date=None,  # Could be calculated based on review_frequency
        critical_non_compliant=critical_non_compliant,
        high_priority_actions=high_priority_actions,
        days_since_last_assessment=days_since_last_assessment,
    )
