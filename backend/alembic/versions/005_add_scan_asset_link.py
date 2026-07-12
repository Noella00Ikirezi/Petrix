"""Add last_scan_id to assets — tracks which scan last discovered each asset

Revision ID: 005_add_scan_asset_link
Revises: 004_add_pentest
Create Date: 2026-06-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005_add_scan_asset_link"
down_revision = "004_add_pentest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column(
            "last_scan_id",
            UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_assets_last_scan_id", "assets", ["last_scan_id"])


def downgrade() -> None:
    op.drop_index("idx_assets_last_scan_id", table_name="assets")
    op.drop_column("assets", "last_scan_id")
