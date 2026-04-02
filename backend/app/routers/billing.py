"""Router FastAPI para billing — planos, uso e upgrades."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.billing_service import BillingService

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
_service = BillingService()


class UpgradeRequest(BaseModel):
    """Corpo da requisição de upgrade de plano."""

    tenant_id: str
    novo_plano: str


class IncrementarUsoRequest(BaseModel):
    """Corpo da requisição de incremento de uso."""

    tenant_id: str
    plano_id: str
    tipo: str


@router.get("/planos")
def listar_planos() -> list[dict]:
    """Lista todos os planos disponíveis com preços."""
    return _service.listar_planos()


@router.get("/plano/{plano_id}")
def obter_plano(plano_id: str) -> dict:
    """Retorna detalhes de um plano específico."""
    plano = _service.obter_plano(plano_id)
    if plano is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plano


@router.get("/uso")
def uso_tenant(
    tenant_id: str = Query(..., description="ID do tenant"),
    db: Session = Depends(get_db),
) -> dict:
    """Retorna uso atual do tenant em relação aos limites do plano."""
    return {
        "consultas": _service.verificar_limite(tenant_id, "free", "consulta", db=db),
        "relatorios": _service.verificar_limite(tenant_id, "free", "relatorio", db=db),
    }


@router.post("/upgrade")
def upgrade(body: UpgradeRequest, db: Session = Depends(get_db)) -> dict:
    """Realiza upgrade do plano de um tenant."""
    plano_novo = _service.obter_plano(body.novo_plano)
    if plano_novo is None:
        raise HTTPException(status_code=400, detail="Plano inválido")
    return _service.upgrade_tenant(db, body.tenant_id, body.novo_plano)


@router.post("/uso/incrementar")
def incrementar_uso(body: IncrementarUsoRequest, db: Session = Depends(get_db)) -> dict:
    """Registra incremento de uso de um recurso pelo tenant."""
    if body.tipo not in ("consulta", "relatorio"):
        raise HTTPException(status_code=400, detail="Tipo deve ser 'consulta' ou 'relatorio'")
    return _service.incrementar_uso(db, body.tenant_id, body.plano_id, body.tipo)
