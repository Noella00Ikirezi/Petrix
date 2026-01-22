"""Initial schema with client requirements management

Revision ID: 001
Revises:
Create Date: 2024-01-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('contact_name', sa.String(100), nullable=True),
        sa.Column('contact_email', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(30), nullable=True),
        sa.Column('contract_start', sa.DateTime, nullable=True),
        sa.Column('contract_end', sa.DateTime, nullable=True),
        sa.Column('contract_reference', sa.String(100), nullable=True),
        sa.Column('industry_sector', sa.String(100), nullable=True),
        sa.Column('criticality', sa.String(20), default='medium'),
        sa.Column('metadata', postgresql.JSONB, default=dict),
        sa.Column('tags', postgresql.JSONB, default=list),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_clients_code', 'clients', ['code'])
    op.create_index('idx_clients_active', 'clients', ['is_active'])

    # Create client_requirements table
    op.create_table(
        'client_requirements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(30), default='security'),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('source', sa.String(200), nullable=True),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('framework_mappings', postgresql.JSONB, default=list),
        sa.Column('acceptance_criteria', sa.Text, nullable=True),
        sa.Column('evidence_required', postgresql.JSONB, default=list),
        sa.Column('sla_target', sa.String(100), nullable=True),
        sa.Column('review_frequency', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_mandatory', sa.Boolean, default=True),
        sa.Column('effective_date', sa.DateTime, nullable=True),
        sa.Column('expiry_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_requirements_client', 'client_requirements', ['client_id'])
    op.create_index('idx_requirements_category', 'client_requirements', ['category'])
    op.create_index('idx_requirements_priority', 'client_requirements', ['priority'])

    # Create compliance_assessments table
    op.create_table(
        'compliance_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('assessment_date', sa.DateTime, default=sa.func.now()),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('period_start', sa.DateTime, nullable=True),
        sa.Column('period_end', sa.DateTime, nullable=True),
        sa.Column('total_requirements', sa.Integer, default=0),
        sa.Column('compliant_count', sa.Integer, default=0),
        sa.Column('partially_compliant_count', sa.Integer, default=0),
        sa.Column('non_compliant_count', sa.Integer, default=0),
        sa.Column('not_applicable_count', sa.Integer, default=0),
        sa.Column('not_assessed_count', sa.Integer, default=0),
        sa.Column('compliance_score', sa.Float, nullable=True),
        sa.Column('maturity_level', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), default='in_progress'),
        sa.Column('is_final', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('finalized_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_assessments_client', 'compliance_assessments', ['client_id'])
    op.create_index('idx_assessments_date', 'compliance_assessments', ['assessment_date'])

    # Create requirement_compliance table
    op.create_table(
        'requirement_compliance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('compliance_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('client_requirements.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(30), default='not_assessed'),
        sa.Column('previous_status', sa.String(30), nullable=True),
        sa.Column('compliance_level', sa.Integer, nullable=True),
        sa.Column('gap_description', sa.Text, nullable=True),
        sa.Column('findings', sa.Text, nullable=True),
        sa.Column('recommendations', sa.Text, nullable=True),
        sa.Column('evidence_provided', postgresql.JSONB, default=list),
        sa.Column('evidence_files', postgresql.JSONB, default=list),
        sa.Column('ai_assessment', sa.Text, nullable=True),
        sa.Column('ai_confidence', sa.Float, nullable=True),
        sa.Column('ai_recommendations', sa.Text, nullable=True),
        sa.Column('assessed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_compliance_assessment', 'requirement_compliance', ['assessment_id'])
    op.create_index('idx_compliance_requirement', 'requirement_compliance', ['requirement_id'])
    op.create_index('idx_compliance_status', 'requirement_compliance', ['status'])

    # Create remediation_actions table
    op.create_table(
        'remediation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('compliance_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requirement_compliance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('action_type', sa.String(30), default='technical'),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('status', sa.String(20), default='planned'),
        sa.Column('progress_percentage', sa.Integer, default=0),
        sa.Column('estimated_effort', sa.String(50), nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('actual_effort', sa.String(50), nullable=True),
        sa.Column('actual_cost', sa.Float, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('implementation_steps', postgresql.JSONB, default=list),
        sa.Column('deliverables', postgresql.JSONB, default=list),
        sa.Column('blockers', sa.Text, nullable=True),
        sa.Column('ai_generated', sa.Boolean, default=False),
        sa.Column('ai_prompt_used', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_actions_compliance', 'remediation_actions', ['compliance_record_id'])
    op.create_index('idx_actions_status', 'remediation_actions', ['status'])
    op.create_index('idx_actions_due_date', 'remediation_actions', ['due_date'])


def downgrade() -> None:
    op.drop_table('remediation_actions')
    op.drop_table('requirement_compliance')
    op.drop_table('compliance_assessments')
    op.drop_table('client_requirements')
    op.drop_table('clients')
