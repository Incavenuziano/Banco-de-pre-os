"""006: Índices de performance para queries críticas.

Revision ID: 006
Revises: 005
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Índice composto para queries de preço por categoria/UF/data
    op.create_index(
        "ix_fontes_preco_uf_data",
        "fontes_preco",
        ["uf", "data_referencia"],
    )

    # Índice para queries de alertas por status
    op.create_index(
        "ix_auditoria_timestamp",
        "auditoria_eventos",
        ["timestamp"],
    )

    # Índice para API keys
    op.create_index(
        "ix_api_keys_ativa",
        "api_keys",
        ["ativa"],
    )


def downgrade() -> None:
    op.drop_index("ix_api_keys_ativa", table_name="api_keys")
    op.drop_index("ix_auditoria_timestamp", table_name="auditoria_eventos")
    op.drop_index("ix_fontes_preco_uf_data", table_name="fontes_preco")
