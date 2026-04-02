"""Model SQLAlchemy para a tabela feedbacks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Feedback(Base):
    """Registros de feedback dos tenants no beta fechado."""

    __tablename__ = "feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False)
    texto = Column(Text, nullable=False)
    nota = Column(Integer, nullable=False)
    registrado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (CheckConstraint("nota >= 1 AND nota <= 5", name="ck_feedback_nota"),)
