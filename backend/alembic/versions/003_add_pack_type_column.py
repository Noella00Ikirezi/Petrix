"""Add pack_type column to smsi_projects

Revision ID: 003_add_pack_type
Revises: 002_add_directive
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_pack_type'
down_revision = '002_add_directive'
branch_labels = None
depends_on = None


def upgrade():
    """Add pack_type column to smsi_projects table."""
    op.add_column(
        'smsi_projects',
        sa.Column('pack_type', sa.String(20), nullable=False, server_default='standard')
    )


def downgrade():
    """Remove pack_type column from smsi_projects table."""
    op.drop_column('smsi_projects', 'pack_type')
