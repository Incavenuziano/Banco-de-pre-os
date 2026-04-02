"""Tabelas iniciais do Banco de Preços.

Revision ID: 001
Revises: None
Create Date: 2026-03-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensão pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # orgaos
    op.create_table(
        "orgaos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(500), nullable=False),
        sa.Column("cnpj", sa.String(18), nullable=False),
        sa.Column("uf", sa.String(2), nullable=False),
        sa.Column("esfera", sa.String(20), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    # categorias
    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text()),
        sa.Column("familia", sa.String(100)),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    # contratacoes
    op.create_table(
        "contratacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero_controle_pncp", sa.String(100), nullable=False, unique=True),
        sa.Column("data_publicacao", sa.Date()),
        sa.Column("modalidade", sa.String(100)),
        sa.Column("orgao_id", sa.Integer(), sa.ForeignKey("orgaos.id"), nullable=False),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_contratacoes_numero_pncp", "contratacoes", ["numero_controle_pncp"], unique=True)

    # itens
    op.create_table(
        "itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero_item", sa.Integer(), nullable=False),
        sa.Column("descricao_original", sa.Text(), nullable=False),
        sa.Column("descricao_limpa", sa.Text()),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id")),
        sa.Column("contratacao_id", sa.Integer(), sa.ForeignKey("contratacoes.id"), nullable=False),
        sa.Column("unidade_original", sa.String(50)),
        sa.Column("unidade_normalizada", sa.String(20)),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_itens_contratacao_numero", "itens", ["contratacao_id", "numero_item"])

    # fontes_preco
    op.create_table(
        "fontes_preco",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fonte_tipo", sa.String(50), nullable=False),
        sa.Column("fonte_referencia", sa.String(200)),
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), nullable=False),
        sa.Column("preco_unitario", sa.Numeric(18, 4)),
        sa.Column("preco_total", sa.Numeric(18, 4)),
        sa.Column("quantidade", sa.Numeric(18, 4)),
        sa.Column("unidade_original", sa.String(50)),
        sa.Column("unidade_normalizada", sa.String(20)),
        sa.Column("data_referencia", sa.Date()),
        sa.Column("municipio", sa.String(200)),
        sa.Column("uf", sa.String(2)),
        sa.Column("esfera", sa.String(20)),
        sa.Column("url_origem", sa.Text()),
        sa.Column("qualidade_tipo", sa.String(30)),
        sa.Column("score_confianca", sa.Integer()),
        sa.Column("outlier_flag", sa.Boolean(), server_default="false"),
        sa.Column("ativo", sa.Boolean(), server_default="true"),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        "uq_fontes_preco_dedup",
        "fontes_preco",
        ["fonte_tipo", "fonte_referencia", "item_id", "data_referencia", "preco_unitario", "quantidade"],
    )

    # evidencias
    op.create_table(
        "evidencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fonte_preco_id", sa.Integer(), sa.ForeignKey("fontes_preco.id"), nullable=False),
        sa.Column("tipo_evidencia", sa.String(30), nullable=False),
        sa.Column("storage_path", sa.Text()),
        sa.Column("hash_sha256", sa.String(64)),
        sa.Column("capturado_em", sa.DateTime()),
        sa.Column("metadados_json", sa.JSON()),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )

    # auditoria_eventos
    op.create_table(
        "auditoria_eventos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entidade", sa.String(100), nullable=False),
        sa.Column("entidade_id", sa.String(100)),
        sa.Column("acao", sa.String(50), nullable=False),
        sa.Column("usuario_id", sa.String(100)),
        sa.Column("payload_before", sa.JSON()),
        sa.Column("payload_after", sa.JSON()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

    # item_categoria
    op.create_table(
        "item_categoria",
        sa.Column("item_id", sa.Integer(), sa.ForeignKey("itens.id"), primary_key=True),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categorias.id"), primary_key=True),
        sa.Column("score_classificacao", sa.Numeric(5, 4)),
        sa.Column("metodo", sa.String(50)),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("item_categoria")
    op.drop_table("auditoria_eventos")
    op.drop_table("evidencias")
    op.drop_table("fontes_preco")
    op.drop_table("itens")
    op.drop_table("contratacoes")
    op.drop_table("categorias")
    op.drop_table("orgaos")
    op.execute("DROP EXTENSION IF EXISTS vector")
