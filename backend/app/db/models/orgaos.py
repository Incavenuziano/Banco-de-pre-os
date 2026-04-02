"""Modelo de órgãos públicos."""

from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Orgao(Base):
    """Órgão público contratante."""

    __tablename__ = "orgaos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(500), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    esfera: Mapped[str] = mapped_column(String(20), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contratacoes: Mapped[list["Contratacao"]] = relationship(back_populates="orgao")  # noqa: F821
