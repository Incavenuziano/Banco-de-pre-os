"""Modelo de uso mensal por tenant."""

from datetime import date, datetime
import uuid

from sqlalchemy import String, Date, DateTime, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsoMensal(Base):
    """Registro de uso mensal de um tenant em relação ao seu plano."""

    __tablename__ = "uso_mensal"
    __table_args__ = (
        UniqueConstraint("tenant_id", "mes_referencia", name="uq_uso_mensal_tenant_mes"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False)
    plano_id: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    consultas_utilizadas: Mapped[int] = mapped_column(Integer, default=0)
    relatorios_utilizados: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
