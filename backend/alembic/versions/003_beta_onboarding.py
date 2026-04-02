"""003_beta_onboarding: tabelas feedbacks, convites, checklist_tenant.

Revision ID: 003
Revises: 002
Create Date: 2026-03-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tabelas feedbacks, convites e checklist_tenant."""
    op.create_table(
        "feedbacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("nota", sa.Integer(), nullable=False),
        sa.Column(
            "registrado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("nota >= 1 AND nota <= 5", name="ck_feedback_nota"),
    )

    op.create_table(
        "convites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("plano", sa.String(50), nullable=False, server_default="free"),
        sa.Column("aceito", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("aceito_em", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "checklist_tenant",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("etapa", sa.String(100), nullable=False),
        sa.Column("concluida", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("concluida_em", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "etapa", name="uq_checklist_tenant_etapa"),
    )


def downgrade() -> None:
    """Remove tabelas feedbacks, convites e checklist_tenant."""
    op.drop_table("checklist_tenant")
    op.drop_table("convites")
    op.drop_table("feedbacks")
