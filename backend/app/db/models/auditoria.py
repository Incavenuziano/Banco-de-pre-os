"""Modelo de eventos de auditoria."""

from datetime import datetime

from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditoriaEvento(Base):
    """Evento de auditoria para rastreabilidade de alterações."""

    __tablename__ = "auditoria_eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    entidade: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[str | None] = mapped_column(String(100))
    acao: Mapped[str] = mapped_column(String(50), nullable=False)
    usuario_id: Mapped[str | None] = mapped_column(String(100))
    payload_before: Mapped[dict | None] = mapped_column(JSON)
    payload_after: Mapped[dict | None] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
