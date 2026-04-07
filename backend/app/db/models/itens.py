"""Modelo de itens de contratação."""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Item(Base):
    """Item individual de uma contratação."""

    __tablename__ = "itens"
    __table_args__ = (
        UniqueConstraint("contratacao_id", "numero_item", name="uq_itens_contratacao_numero"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_item: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao_original: Mapped[str] = mapped_column(Text, nullable=False)
    descricao_limpa: Mapped[str | None] = mapped_column(Text)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))
    contratacao_id: Mapped[int] = mapped_column(ForeignKey("contratacoes.id"), nullable=False)
    unidade_original: Mapped[str | None] = mapped_column(String(50))
    unidade_normalizada: Mapped[str | None] = mapped_column(String(20))
    tipo_objeto: Mapped[str | None] = mapped_column(String(20), default="material")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contratacao: Mapped["Contratacao"] = relationship(back_populates="itens")  # noqa: F821
    fontes_preco: Mapped[list["FontePreco"]] = relationship(back_populates="item")  # noqa: F821
