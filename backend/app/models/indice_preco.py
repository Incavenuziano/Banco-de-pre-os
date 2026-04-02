"""Modelo SQLAlchemy para índices de preço (IPCA/IBGE)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, UniqueConstraint

from app.db.base import Base


class IndicePreco(Base):
    """Índice de preço mensal (IPCA ou outro índice econômico)."""

    __tablename__ = "indices_preco"
    __table_args__ = (
        UniqueConstraint("fonte", "ano", "mes", name="uq_indices_preco_fonte_ano_mes"),
    )

    id = Column(Integer, primary_key=True)
    fonte = Column(String(20), nullable=False, default="IPCA")
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    variacao_mensal = Column(Numeric(8, 4))
    variacao_acumulada_ano = Column(Numeric(8, 4))
    indice_acumulado = Column(Numeric(12, 6))
    fonte_url = Column(Text)
    coletado_em = Column(DateTime, default=datetime.utcnow)
