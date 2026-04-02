"""Router FastAPI para dashboard e métricas de uso."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
_service = DashboardService()


@router.get("/resumo")
def resumo(tenant_id: str = Query(..., description="ID do tenant")) -> dict:
    """Retorna resumo geral do tenant para o dashboard."""
    return _service.obter_resumo(tenant_id)


@router.get("/historico")
def historico(
    tenant_id: str = Query(..., description="ID do tenant"),
    dias: int = Query(30, ge=1, le=365, description="Número de dias"),
) -> list[dict]:
    """Retorna histórico de consultas e relatórios por dia."""
    return _service.obter_historico_consultas(tenant_id, dias)


@router.get("/cobertura")
def cobertura() -> dict:
    """Retorna cobertura de categorias com amostras."""
    return _service.obter_cobertura_categorias()


@router.get("/admin/status")
def admin_status() -> dict:
    """Retorna status geral do sistema para administração."""
    return _service.admin_status()
