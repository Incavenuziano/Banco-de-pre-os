"""Modelo de evidências documentais."""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Evidencia(Base):
    """Evidência documental vinculada a uma fonte de preço."""

    __tablename__ = "evidencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    fonte_preco_id: Mapped[int] = mapped_column(ForeignKey("fontes_preco.id"), nullable=False)
    tipo_evidencia: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text)
    hash_sha256: Mapped[str | None] = mapped_column(String(64))
    capturado_em: Mapped[datetime | None] = mapped_column(DateTime)
    metadados_json: Mapped[dict | None] = mapped_column(JSON)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    fonte_preco: Mapped["FontePreco"] = relationship(back_populates="evidencias")  # noqa: F821
