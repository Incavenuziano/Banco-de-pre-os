"""Classificador tipo_objeto: regras em DB, overrides manuais e auditoria.

Revision ID: 010
Revises: 009
Create Date: 2026-04-14

Mudanças:
- tipo_objeto_regras: regras regex configuráveis por prioridade para
  classificar automaticamente itens como material/servico/obra.
- tipo_objeto_overrides: substituições manuais realizadas por revisores,
  com rastreabilidade de usuário e motivo.
- tipo_objeto_auditoria: log imutável de cada classificação e correção
  para treinamento futuro e rastreabilidade de qualidade.
- Seed inicial de ~35 regras cobrindo obras, serviços e materiais.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────
    # 1. tipo_objeto_regras — regras regex gerenciáveis
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tipo_objeto_regras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "padrao",
            sa.Text(),
            nullable=False,
            comment="Regex Python aplicada sobre descrição normalizada (sem acentos, maiúscula)",
        ),
        sa.Column(
            "tipo",
            sa.String(20),
            nullable=False,
            comment="material | servico | obra",
        ),
        sa.Column(
            "prioridade",
            sa.Integer(),
            nullable=False,
            server_default="50",
            comment="Ordem de avaliação — maior prioridade é verificada primeiro",
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "descricao",
            sa.Text(),
            nullable=True,
            comment="Explicação em linguagem natural do que a regra detecta",
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("tipo IN ('material', 'servico', 'obra')", name="ck_regras_tipo"),
    )
    op.create_index("ix_regras_tipo", "tipo_objeto_regras", ["tipo"])
    op.create_index("ix_regras_prioridade", "tipo_objeto_regras", ["prioridade"])
    op.create_index(
        "ix_regras_ativo_prioridade",
        "tipo_objeto_regras",
        ["ativo", "prioridade"],
    )

    # ─────────────────────────────────────────────────────────────────
    # 2. tipo_objeto_overrides — substituições manuais com rastreabilidade
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tipo_objeto_overrides",
        sa.Column(
            "item_id",
            sa.dialects.postgresql.UUID(as_uuid=True) if _pg_dialect() else sa.Text(),
            sa.ForeignKey("itens.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tipo_override",
            sa.String(20),
            nullable=False,
            comment="material | servico | obra",
        ),
        sa.Column("usuario", sa.String(100), nullable=False, server_default="admin"),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "tipo_override IN ('material', 'servico', 'obra')",
            name="ck_overrides_tipo",
        ),
    )
    op.create_index("ix_overrides_tipo", "tipo_objeto_overrides", ["tipo_override"])

    # ─────────────────────────────────────────────────────────────────
    # 3. tipo_objeto_auditoria — log imutável de classificações
    # ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tipo_objeto_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "item_id",
            sa.dialects.postgresql.UUID(as_uuid=True) if _pg_dialect() else sa.Text(),
            nullable=True,
            comment="NULL aceito — auditoria pode ocorrer antes do insert em itens",
        ),
        sa.Column(
            "descricao_trecho",
            sa.Text(),
            nullable=False,
            comment="Primeiros 200 chars da descrição usada na classificação",
        ),
        sa.Column(
            "tipo_inferido",
            sa.String(20),
            nullable=False,
            comment="Resultado da classificação automática",
        ),
        sa.Column(
            "tipo_correto",
            sa.String(20),
            nullable=True,
            comment="Preenchido quando um revisor corrige o valor",
        ),
        sa.Column(
            "metodo",
            sa.String(30),
            nullable=False,
            server_default="builtin",
            comment="builtin | db_regras | override",
        ),
        sa.Column(
            "score",
            sa.Float(),
            nullable=True,
            comment="Confiança da classificação (0.0–1.0)",
        ),
        sa.Column(
            "auditado_em",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_auditoria_item_id", "tipo_objeto_auditoria", ["item_id"])
    op.create_index("ix_auditoria_tipo_inferido", "tipo_objeto_auditoria", ["tipo_inferido"])
    op.create_index("ix_auditoria_auditado_em", "tipo_objeto_auditoria", ["auditado_em"])

    # ─────────────────────────────────────────────────────────────────
    # 4. Seed — regras iniciais
    #
    # Estratégia de prioridades:
    #   90 → obras (maior especificidade — erros de classificação graves)
    #   80 → serviços
    #   10 → material (não inserido — é o default quando nenhuma regra casa)
    #
    # Padrões aplicados sobre texto normalizado: sem acentos + maiúsculas.
    # Usar \b (word boundary) para evitar falsos positivos.
    # ─────────────────────────────────────────────────────────────────
    op.execute(
        """
        INSERT INTO tipo_objeto_regras (padrao, tipo, prioridade, descricao) VALUES

        -- ── OBRAS (prioridade 90) ──────────────────────────────────────────
        (E'\\\\bOBRA\\\\b',                   'obra', 90, 'Palavra OBRA isolada'),
        (E'\\\\bENGENHARIA\\\\b',              'obra', 90, 'Engenharia (projeto/execução)'),
        (E'\\\\bREFORMA\\\\b',                 'obra', 90, 'Reforma de edificação'),
        (E'\\\\bPAVIMENTA',                    'obra', 90, 'Pavimentação / asfalto / calçamento'),
        (E'\\\\bCALCAMENTO\\\\b',              'obra', 90, 'Calçamento de vias'),
        (E'\\\\bCONSTRU',                      'obra', 90, 'Construção de edificação ou infraestrutura'),
        (E'\\\\bEDIFICA',                      'obra', 90, 'Edificação (construção)'),
        (E'\\\\bDRENAGEM\\\\b',                'obra', 90, 'Drenagem pluvial ou sanitária'),
        (E'\\\\bTERRAPLANAGEM\\\\b',           'obra', 90, 'Terraplanagem'),
        (E'\\\\bFUNDACAO\\\\b',                'obra', 90, 'Fundação de edificação'),
        (E'\\\\bESTRUTURA\\\\s+DE\\\\s+CONCRETO\\\\b', 'obra', 90, 'Estrutura de concreto armado'),
        (E'\\\\bSANEAMENTO\\\\b',              'obra', 90, 'Obras de saneamento básico'),
        (E'\\\\bGALERIA\\\\s+DE\\\\s+AGUA',   'obra', 90, 'Galeria de águas pluviais'),

        -- ── SERVIÇOS (prioridade 80) ──────────────────────────────────────
        (E'\\\\bSERVICO\\\\b',                 'servico', 80, 'Palavra SERVICO isolada'),
        (E'\\\\bSERVICOS\\\\b',                'servico', 80, 'Palavra SERVICOS isolada'),
        (E'\\\\bMANUTENCAO\\\\b',              'servico', 80, 'Manutenção (preventiva ou corretiva)'),
        (E'\\\\bLOCACAO\\\\b',                 'servico', 80, 'Locação de equipamento, veículo ou imóvel'),
        (E'\\\\bCONSULTORIA\\\\b',             'servico', 80, 'Consultoria técnica ou administrativa'),
        (E'\\\\bSUPORTE\\\\s+TECNICO\\\\b',    'servico', 80, 'Suporte técnico de TI ou equipamentos'),
        (E'\\\\bLIMPEZA\\\\b',                 'servico', 80, 'Serviço de limpeza / conservação'),
        (E'\\\\bTRANSPORTE\\\\b',              'servico', 80, 'Serviço de transporte de pessoas ou cargas'),
        (E'\\\\bVIGILANCIA\\\\b',              'servico', 80, 'Vigilância / segurança patrimonial'),
        (E'\\\\bSEGURANCA\\\\s+PATRIMONIAL\\\\b', 'servico', 80, 'Segurança patrimonial'),
        (E'\\\\bPORTARIA\\\\b',                'servico', 80, 'Serviço de portaria / recepção'),
        (E'\\\\bDEDETIZACAO\\\\b',             'servico', 80, 'Dedetização / controle de pragas'),
        (E'\\\\bCONTROLE\\\\s+DE\\\\s+PRAGA',  'servico', 80, 'Controle de pragas e vetores'),
        (E'\\\\bREPROGRAFIA\\\\b',             'servico', 80, 'Reprografia / cópias / digitalização'),
        (E'\\\\bTELEFONIA\\\\b',               'servico', 80, 'Serviços de telefonia'),
        (E'\\\\bINTERNET\\\\b',                'servico', 80, 'Serviços de acesso à internet'),
        (E'\\\\bASSESSORIA\\\\b',              'servico', 80, 'Assessoria técnica ou jurídica'),
        (E'\\\\bTREINAMENTO\\\\b',             'servico', 80, 'Treinamento de pessoal'),
        (E'\\\\bCAPACITACAO\\\\b',             'servico', 80, 'Capacitação e formação profissional'),
        (E'\\\\bJARDINAGEM\\\\b',              'servico', 80, 'Serviço de jardinagem e paisagismo'),
        (E'\\\\bCOLETA\\\\s+DE\\\\s+LIXO\\\\b','servico', 80, 'Coleta e destinação de resíduos sólidos'),
        (E'\\\\bCOPEIRAGEM\\\\b',              'servico', 80, 'Copeiragem / copa e cozinha'),
        (E'\\\\bRECEPCAO\\\\b',                'servico', 80, 'Serviço de recepção / atendimento')
        """
    )


def downgrade() -> None:
    op.drop_index("ix_auditoria_auditado_em", table_name="tipo_objeto_auditoria")
    op.drop_index("ix_auditoria_tipo_inferido", table_name="tipo_objeto_auditoria")
    op.drop_index("ix_auditoria_item_id", table_name="tipo_objeto_auditoria")
    op.drop_table("tipo_objeto_auditoria")

    op.drop_index("ix_overrides_tipo", table_name="tipo_objeto_overrides")
    op.drop_table("tipo_objeto_overrides")

    op.drop_index("ix_regras_ativo_prioridade", table_name="tipo_objeto_regras")
    op.drop_index("ix_regras_prioridade", table_name="tipo_objeto_regras")
    op.drop_index("ix_regras_tipo", table_name="tipo_objeto_regras")
    op.drop_table("tipo_objeto_regras")


def _pg_dialect() -> bool:
    """Retorna True se estiver conectado a PostgreSQL."""
    try:
        bind = op.get_bind()
        return bind.dialect.name == "postgresql"
    except Exception:
        return False
