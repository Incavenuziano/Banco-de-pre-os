"""Adicionar coluna embedding em itens e tabela cobertura_municipios.

Revision ID: 008
Revises: 007
Create Date: 2026-04-07

Mudanças:
- itens.embedding: vetor de 384 dimensões para classificação semântica.
  Dimensão 384 é compatível com EmbeddingGemma-300M e multilingual-e5-small.
- cobertura_municipios: tabela de cache com nível de cobertura de dados
  por município (atualizada pelo job semanal do scheduler).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Garante que a extensão vector está ativa (idempotente)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Coluna de embedding semântico em itens (nullable — preenchida na ingestão)
    op.execute(
        "ALTER TABLE itens ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )

    # Índice HNSW para busca por vizinhos mais próximos (cosine distance)
    # Criado apenas se ainda não existir para permitir re-execução segura
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'itens'
                  AND indexname = 'ix_itens_embedding_hnsw'
            ) THEN
                CREATE INDEX ix_itens_embedding_hnsw
                ON itens
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            END IF;
        END
        $$;
        """
    )

    # Tabela de cache de cobertura por município
    op.create_table(
        "cobertura_municipios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("municipio", sa.String(200), nullable=False),
        sa.Column("uf", sa.String(2), nullable=False),
        sa.Column("n_amostras", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_categorias", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "nivel",
            sa.String(20),
            nullable=False,
            server_default="INSUFICIENTE",
            comment="ALTA | MEDIA | BAIXA | INSUFICIENTE",
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Constraint unique para permitir ON CONFLICT DO UPDATE no scheduler
    op.create_unique_constraint(
        "uq_cobertura_municipio_uf",
        "cobertura_municipios",
        ["municipio", "uf"],
    )

    # Índices para consultas frequentes
    op.create_index("ix_cobertura_uf", "cobertura_municipios", ["uf"])
    op.create_index("ix_cobertura_nivel", "cobertura_municipios", ["nivel"])

    # Pré-popula GO com todos os municípios em INSUFICIENTE
    # (será sobrescrito pela primeira execução do job semanal)
    from app.services.cobertura_service import MUNICIPIOS_GOIAS

    municipios_values = ", ".join(
        f"('{m.replace(chr(39), chr(39) + chr(39))}', 'GO', 0, 0, 'INSUFICIENTE', NOW())"
        for m in MUNICIPIOS_GOIAS
    )
    if municipios_values:
        op.execute(
            f"""
            INSERT INTO cobertura_municipios
                (municipio, uf, n_amostras, n_categorias, nivel, atualizado_em)
            VALUES {municipios_values}
            ON CONFLICT (municipio, uf) DO NOTHING
            """
        )


def downgrade() -> None:
    op.drop_index("ix_cobertura_nivel", table_name="cobertura_municipios")
    op.drop_index("ix_cobertura_uf", table_name="cobertura_municipios")
    op.drop_constraint("uq_cobertura_municipio_uf", "cobertura_municipios")
    op.drop_table("cobertura_municipios")
    op.execute(
        "DROP INDEX IF EXISTS ix_itens_embedding_hnsw"
    )
    op.execute("ALTER TABLE itens DROP COLUMN IF EXISTS embedding")
