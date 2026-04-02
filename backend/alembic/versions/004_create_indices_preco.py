"""004: Tabela indices_preco para séries IPCA/IBGE.

Revision ID: 004
Revises: 003
Create Date: 2026-04-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "indices_preco",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fonte", sa.String(20), nullable=False, server_default="IPCA"),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("variacao_mensal", sa.Numeric(8, 4)),
        sa.Column("variacao_acumulada_ano", sa.Numeric(8, 4)),
        sa.Column("indice_acumulado", sa.Numeric(12, 6)),
        sa.Column("fonte_url", sa.Text()),
        sa.Column("coletado_em", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("fonte", "ano", "mes", name="uq_indices_preco_fonte_ano_mes"),
    )


def downgrade() -> None:
    op.drop_table("indices_preco")
