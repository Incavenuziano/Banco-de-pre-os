"""Model SQLAlchemy para a tabela convites."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Convite(Base):
    """Convites enviados a novos usuários durante o beta fechado."""

    __tablename__ = "convites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    plano = Column(String(50), nullable=False, default="free")
    aceito = Column(Boolean, nullable=False, default=False)
    criado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    aceito_em = Column(DateTime(timezone=True), nullable=True)
