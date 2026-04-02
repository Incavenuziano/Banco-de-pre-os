"""Modelos SQLAlchemy para autenticação e tenants."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tenant(Base):
    """Tenant (organização) do sistema multi-tenant."""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plano = Column(String(50), nullable=False, default="free")
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuarios = relationship("Usuario", back_populates="tenant")


class Usuario(Base):
    """Usuário do sistema com papel (role) e vínculo a tenant."""

    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(String(50), nullable=False, default="viewer")
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    ultimo_acesso = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="usuarios")
