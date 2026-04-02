"""Tabela uso_mensal para controle de uso por tenant.

Revision ID: 002
Revises: 001
Create Date: 2026-03-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uso_mensal",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("tenant_id", sa.String(100), nullable=False),
        sa.Column("plano_id", sa.String(50), nullable=False, server_default="free"),
        sa.Column("mes_referencia", sa.Date(), nullable=False),
        sa.Column("consultas_utilizadas", sa.Integer(), server_default="0"),
        sa.Column("relatorios_utilizados", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "mes_referencia", name="uq_uso_mensal_tenant_mes"),
    )


def downgrade() -> None:
    op.drop_table("uso_mensal")
