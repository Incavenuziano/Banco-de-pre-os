"""Router FastAPI para administração — auditoria, rate limiting, métricas, saúde."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

import io

from app.services.auditoria_service import auditoria
from app.services.backup_service import BackupService
from app.services.observabilidade_service import observabilidade
from app.services.rate_limiter import rate_limiter

_backup = BackupService()

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/auditoria")
def listar_auditoria(
    entidade: str | None = Query(None, description="Filtro por entidade"),
    usuario_id: str | None = Query(None, description="Filtro por usuário"),
    pagina: int = Query(1, ge=1, description="Página"),
    por_pagina: int = Query(50, ge=1, le=200, description="Itens por página"),
) -> dict:
    """Lista eventos de auditoria com filtros opcionais e paginação."""
    todos = auditoria.listar(entidade=entidade, usuario_id=usuario_id)
    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina
    return {
        "total": len(todos),
        "pagina": pagina,
        "por_pagina": por_pagina,
        "eventos": todos[inicio:fim],
    }


@router.get("/auditoria/export")
def exportar_auditoria() -> StreamingResponse:
    """Exporta eventos de auditoria como CSV."""
    csv_content = auditoria.exportar_csv()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=auditoria.csv"},
    )


@router.get("/rate-limit/status")
def rate_limit_status(
    key: str = Query(..., description="Chave do rate limiter"),
) -> dict:
    """Retorna status do rate limiter para uma chave."""
    return rate_limiter.verificar(key)


@router.get("/metricas")
def metricas_admin() -> dict:
    """Retorna métricas detalhadas de uso do sistema."""
    return observabilidade.obter_metricas_detalhadas()


@router.get("/saude")
def saude_admin() -> dict:
    """Health check detalhado (DB, pgvector, IBGE API, filesystem)."""
    return observabilidade.health_check_detalhado()


@router.get("/export")
def exportar_dados() -> StreamingResponse:
    """Export completo dos dados em JSON (admin only)."""
    json_bytes = _backup.exportar_json_bytes()
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=banco_precos_export.json"},
    )


@router.get("/integridade")
def verificar_integridade() -> dict:
    """Verifica integridade dos dados do sistema."""
    return _backup.validar_integridade()
