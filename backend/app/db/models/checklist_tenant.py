"""Model SQLAlchemy para a tabela checklist_tenant."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ChecklistTenant(Base):
    """Etapas de onboarding por tenant, com status de conclusão."""

    __tablename__ = "checklist_tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), nullable=False)
    etapa = Column(String(100), nullable=False)
    concluida = Column(Boolean, nullable=False, default=False)
    concluida_em = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("tenant_id", "etapa", name="uq_checklist_tenant_etapa"),)
