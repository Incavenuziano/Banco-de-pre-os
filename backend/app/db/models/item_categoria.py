"""Modelo de associação item-categoria com score."""

from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ItemCategoria(Base):
    """Associação entre item e categoria com score de classificação."""

    __tablename__ = "item_categoria"

    item_id: Mapped[int] = mapped_column(ForeignKey("itens.id"), primary_key=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"), primary_key=True)
    score_classificacao: Mapped[float | None] = mapped_column(Numeric(5, 4))
    metodo: Mapped[str | None] = mapped_column(String(50))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
