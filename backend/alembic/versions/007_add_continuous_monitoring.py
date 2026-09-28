"""Add continuous monitoring fields to hardening_targets (real-time agent daemon)

Revision ID: 007_add_continuous_monitoring
Revises: 006_scan_created_by_nullable
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = '007_add_continuous_monitoring'
down_revision = '006_scan_created_by_nullable'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hardening_targets",
        sa.Column("mode", sa.String(20), nullable=False, server_default="on_demand"),
    )
    op.add_column(
        "hardening_targets",
        sa.Column("monitor_interval_seconds", sa.Integer(), nullable=False, server_default="300"),
    )
    op.add_column(
        "hardening_targets",
        sa.Column("agent_token_hash", sa.String(100), nullable=True),
    )
    op.add_column(
        "hardening_targets",
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("hardening_targets", "last_heartbeat_at")
    op.drop_column("hardening_targets", "agent_token_hash")
    op.drop_column("hardening_targets", "monitor_interval_seconds")
    op.drop_column("hardening_targets", "mode")
