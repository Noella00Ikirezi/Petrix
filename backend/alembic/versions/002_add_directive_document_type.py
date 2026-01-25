"""Add directive to DocumentType enum

Revision ID: 002_add_directive
Revises: 001_initial_schema
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_directive'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add 'directive' value to documenttype enum."""
    # PostgreSQL requires special handling for adding enum values
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'directive'")


def downgrade():
    """Remove 'directive' value from documenttype enum.

    Note: PostgreSQL doesn't support removing enum values directly.
    This would require recreating the enum and updating all references.
    For safety, we leave this as a no-op.
    """
    pass
