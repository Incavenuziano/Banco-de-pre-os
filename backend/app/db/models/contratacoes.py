"""Modelo de contratações públicas."""

from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Contratacao(Base):
    """Contratação pública registrada no PNCP ou outra fonte."""

    __tablename__ = "contratacoes"
    __table_args__ = (
        UniqueConstraint("numero_controle_pncp", name="uq_contratacoes_numero_pncp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_controle_pncp: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    modalidade: Mapped[str | None] = mapped_column(String(100))
    orgao_id: Mapped[int] = mapped_column(ForeignKey("orgaos.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orgao: Mapped["Orgao"] = relationship(back_populates="contratacoes")  # noqa: F821
    itens: Mapped[list["Item"]] = relationship(back_populates="contratacao")  # noqa: F821
