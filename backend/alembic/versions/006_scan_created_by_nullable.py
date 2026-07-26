"""make scan.created_by_id nullable with SET NULL on user delete

Revision ID: 006_scan_created_by_nullable
Revises: 005_add_scan_asset_link
Create Date: 2026-07-26
"""
from alembic import op
import sqlalchemy as sa

revision = '006_scan_created_by_nullable'
down_revision = '005_add_scan_asset_link'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old NOT NULL FK constraint and recreate as nullable with SET NULL
    op.drop_constraint('scans_created_by_id_fkey', 'scans', type_='foreignkey')
    op.alter_column('scans', 'created_by_id', nullable=True)
    op.create_foreign_key(
        'scans_created_by_id_fkey',
        'scans', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('scans_created_by_id_fkey', 'scans', type_='foreignkey')
    op.alter_column('scans', 'created_by_id', nullable=False)
    op.create_foreign_key(
        'scans_created_by_id_fkey',
        'scans', 'users',
        ['created_by_id'], ['id'],
    )
