"""Modelo de fontes de preço."""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String, Text, DateTime, Date, ForeignKey, Numeric, Boolean, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FontePreco(Base):
    """Amostra de preço proveniente de uma fonte rastreável."""

    __tablename__ = "fontes_preco"
    __table_args__ = (
        UniqueConstraint(
            "fonte_tipo", "fonte_referencia", "item_id",
            "data_referencia", "preco_unitario", "quantidade",
            name="uq_fontes_preco_dedup",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fonte_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    fonte_referencia: Mapped[str | None] = mapped_column(String(200))
    item_id: Mapped[int] = mapped_column(ForeignKey("itens.id"), nullable=False)
    preco_unitario: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    unidade_original: Mapped[str | None] = mapped_column(String(50))
    unidade_normalizada: Mapped[str | None] = mapped_column(String(20))
    data_referencia: Mapped[date | None] = mapped_column(Date)
    municipio: Mapped[str | None] = mapped_column(String(200))
    uf: Mapped[str | None] = mapped_column(String(2))
    esfera: Mapped[str | None] = mapped_column(String(20))
    url_origem: Mapped[str | None] = mapped_column(Text)
    qualidade_tipo: Mapped[str | None] = mapped_column(String(30))
    score_confianca: Mapped[int | None] = mapped_column()
    outlier_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped["Item"] = relationship(back_populates="fontes_preco")  # noqa: F821
    evidencias: Mapped[list["Evidencia"]] = relationship(back_populates="fonte_preco")  # noqa: F821
