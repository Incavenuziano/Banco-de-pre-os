"""005: Tabela api_keys para acesso à API pública.

Revision ID: 005
Revises: 004
Create Date: 2026-04-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("tenant_id", sa.String(100)),
        sa.Column("ativa", sa.Boolean(), server_default="true"),
        sa.Column("limite_diario", sa.Integer(), server_default="1000"),
        sa.Column("usos_hoje", sa.Integer(), server_default="0"),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ultimo_uso", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
