"""Portão de qualidade: quarentena, índices de performance e constraint tipo_objeto.

Revision ID: 009
Revises: 008
Create Date: 2026-04-11

Mudanças:
- itens_quarentena: tabela de quarentena para itens suspeitos/inválidos detectados
  durante a ingestão, aguardando revisão manual.
- Índices FK faltantes: PostgreSQL não cria índices automáticos em FKs.
  fontes_preco(item_id), evidencias(fonte_preco_id), itens(contratacao_id),
  item_categoria(categoria_id)
- Índices compostos para os padrões de query mais frequentes:
  fontes_preco(uf, data_referencia), fontes_preco(ativo, outlier_flag), orgaos(uf)
- CHECK constraint em itens.tipo_objeto para garantir integridade dos valores
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────
    # 1. Tabela de quarentena
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "itens_quarentena",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column("cnpj", sa.String(20), nullable=True),
        sa.Column(
            "item_raw",
            sa.JSON(),
            nullable=False,
            comment="Payload original do item (serializado) para reprocessamento",
        ),
        sa.Column(
            "motivo",
            sa.Text(),
            nullable=False,
            comment="Motivos de rejeição/quarentena separados por ponto-e-vírgula",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pendente",
            comment="pendente | aprovado | rejeitado",
        ),
        sa.Column("revisado_por", sa.String(100), nullable=True),
        sa.Column("revisado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_quarentena_uf", "itens_quarentena", ["uf"])
    op.create_index("ix_quarentena_status", "itens_quarentena", ["status"])
    op.create_index("ix_quarentena_criado_em", "itens_quarentena", ["criado_em"])

    # ─────────────────────────────────────────────────────────────────
    # 2. CHECK constraint em itens.tipo_objeto
    #    Garante apenas valores do domínio (material|servico|obra)
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_itens_tipo_objeto'
                  AND conrelid = 'itens'::regclass
            ) THEN
                ALTER TABLE itens
                    ADD CONSTRAINT ck_itens_tipo_objeto
                    CHECK (tipo_objeto IN ('material', 'servico', 'obra'));
            END IF;
        END
        $$;
        """
    )

    # ─────────────────────────────────────────────────────────────────
    # 3. Índices FK faltantes
    #    PostgreSQL NÃO cria índices automáticos em foreign keys.
    #    Esses joins ocorrem em todas as queries principais do sistema.
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            -- fontes_preco.item_id (JOIN mais frequente do sistema)
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'fontes_preco'
                  AND indexname = 'ix_fontes_preco_item_id'
            ) THEN
                CREATE INDEX ix_fontes_preco_item_id
                    ON fontes_preco(item_id);
            END IF;

            -- evidencias.fonte_preco_id
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'evidencias'
                  AND indexname = 'ix_evidencias_fonte_preco_id'
            ) THEN
                CREATE INDEX ix_evidencias_fonte_preco_id
                    ON evidencias(fonte_preco_id);
            END IF;

            -- itens.contratacao_id
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'itens'
                  AND indexname = 'ix_itens_contratacao_id'
            ) THEN
                CREATE INDEX ix_itens_contratacao_id
                    ON itens(contratacao_id);
            END IF;

            -- item_categoria.categoria_id (lookup reverso por categoria)
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'item_categoria'
                  AND indexname = 'ix_item_categoria_categoria_id'
            ) THEN
                CREATE INDEX ix_item_categoria_categoria_id
                    ON item_categoria(categoria_id);
            END IF;
        END
        $$;
        """
    )

    # ─────────────────────────────────────────────────────────────────
    # 4. Índices compostos para padrões de query mais frequentes
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            -- Pattern: listar_precos — filtra por UF + data + ativo + sem outlier
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'fontes_preco'
                  AND indexname = 'ix_fp_uf_data_ativo'
            ) THEN
                CREATE INDEX ix_fp_uf_data_ativo
                    ON fontes_preco(uf, data_referencia DESC)
                    WHERE ativo = TRUE AND outlier_flag = FALSE;
            END IF;

            -- Pattern: busca regional — filtra por UF + preço
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'fontes_preco'
                  AND indexname = 'ix_fp_uf_preco'
            ) THEN
                CREATE INDEX ix_fp_uf_preco
                    ON fontes_preco(uf, preco_unitario)
                    WHERE preco_unitario > 0 AND ativo = TRUE;
            END IF;

            -- Pattern: filtra orgaos por UF (JOIN frequente em listar_precos)
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'orgaos'
                  AND indexname = 'ix_orgaos_uf'
            ) THEN
                CREATE INDEX ix_orgaos_uf ON orgaos(uf);
            END IF;

            -- Pattern: contratações por data (export, histórico)
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'contratacoes'
                  AND indexname = 'ix_contratacoes_data_publicacao'
            ) THEN
                CREATE INDEX ix_contratacoes_data_publicacao
                    ON contratacoes(data_publicacao DESC);
            END IF;
        END
        $$;
        """
    )

    # ─────────────────────────────────────────────────────────────────
    # 5. Full-Text Search em itens.descricao_limpa
    #    Substitui ILIKE para busca textual (~100x mais rápido)
    #    Usa dicionário 'portuguese' para stemming básico
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            -- Coluna tsvector gerada automaticamente (PostgreSQL 12+)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'itens'
                  AND column_name = 'descricao_tsv'
            ) THEN
                ALTER TABLE itens
                    ADD COLUMN descricao_tsv tsvector
                    GENERATED ALWAYS AS (
                        to_tsvector(
                            'portuguese',
                            coalesce(descricao_limpa, '') || ' ' ||
                            coalesce(descricao_original, '')
                        )
                    ) STORED;
            END IF;

            -- Índice GIN sobre a coluna gerada
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'itens'
                  AND indexname = 'ix_itens_descricao_fts'
            ) THEN
                CREATE INDEX ix_itens_descricao_fts
                    ON itens USING gin(descricao_tsv);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_itens_descricao_fts")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'itens' AND column_name = 'descricao_tsv'
            ) THEN
                ALTER TABLE itens DROP COLUMN descricao_tsv;
            END IF;
        END
        $$;
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_contratacoes_data_publicacao")
    op.execute("DROP INDEX IF EXISTS ix_orgaos_uf")
    op.execute("DROP INDEX IF EXISTS ix_fp_uf_preco")
    op.execute("DROP INDEX IF EXISTS ix_fp_uf_data_ativo")
    op.execute("DROP INDEX IF EXISTS ix_item_categoria_categoria_id")
    op.execute("DROP INDEX IF EXISTS ix_itens_contratacao_id")
    op.execute("DROP INDEX IF EXISTS ix_evidencias_fonte_preco_id")
    op.execute("DROP INDEX IF EXISTS ix_fontes_preco_item_id")
    op.execute(
        """
        ALTER TABLE itens
            DROP CONSTRAINT IF EXISTS ck_itens_tipo_objeto;
        """
    )
    op.drop_index("ix_quarentena_criado_em", table_name="itens_quarentena")
    op.drop_index("ix_quarentena_status", table_name="itens_quarentena")
    op.drop_index("ix_quarentena_uf", table_name="itens_quarentena")
    op.drop_table("itens_quarentena")
