"""Adicionar tipo_objeto em itens.

Revision ID: 007
Revises: 006
Create Date: 2026-04-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE itens ADD COLUMN IF NOT EXISTS tipo_objeto VARCHAR(20)")
    op.execute(
        """
        UPDATE itens
        SET tipo_objeto = CASE
            WHEN LOWER(COALESCE(descricao, '')) ~
                 '(servi[c?]o|manuten[c?][a?]o|loca[c?][a?]o|consultoria|suporte|limpeza|transporte|vigil[?a]ncia|portaria|dedetiza[c?][a?]o|reprografia|telefonia|internet)'
                THEN 'servico'
            WHEN LOWER(COALESCE(descricao, '')) ~
                 '(obra|engenharia|reforma|pavimenta[c?][a?]o|constru[c?][a?]o|edifica[c?][a?]o|drenagem|terraplanagem)'
                THEN 'obra'
            ELSE 'material'
        END
        WHERE tipo_objeto IS NULL
        """
    )
    op.alter_column(
        "itens",
        "tipo_objeto",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default="material",
    )
    op.create_index("ix_itens_tipo_objeto", "itens", ["tipo_objeto"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_itens_tipo_objeto", table_name="itens")
    op.drop_column("itens", "tipo_objeto")
