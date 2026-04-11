"""Router FastAPI para administração — auditoria, rate limiting, métricas, saúde."""

from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
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


# ─────────────────────────────────────────────────────────
# Quarentena de itens suspeitos
# ─────────────────────────────────────────────────────────

@router.get("/quarentena")
def listar_quarentena(
    status: str = Query("pendente", description="pendente | aprovado | rejeitado"),
    uf: str | None = Query(None, description="Filtro por UF (ex: GO)"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    """Lista itens em quarentena aguardando revisão manual.

    Itens em quarentena são aqueles que passaram pela ingestão mas
    apresentaram características suspeitas (preço redondo, unidade
    ausente, preço improvável para a categoria, etc.).
    """
    try:
        params: dict = {"status": status, "offset": (pagina - 1) * por_pagina, "limit": por_pagina}
        uf_clause = "AND uf = :uf" if uf else ""
        if uf:
            params["uf"] = uf.upper()

        total_row = db.execute(
            text(f"SELECT COUNT(*) FROM itens_quarentena WHERE status = :status {uf_clause}"),
            params,
        ).fetchone()
        total = total_row[0] if total_row else 0

        rows = db.execute(
            text(
                f"""
                SELECT id, uf, cnpj, item_raw, motivo, status,
                       revisado_por, revisado_em, criado_em
                FROM itens_quarentena
                WHERE status = :status {uf_clause}
                ORDER BY criado_em DESC
                OFFSET :offset LIMIT :limit
                """
            ),
            params,
        ).fetchall()

        itens = [
            {
                "id": r[0],
                "uf": r[1],
                "cnpj": r[2],
                "item_raw": r[3],
                "motivo": r[4],
                "status": r[5],
                "revisado_por": r[6],
                "revisado_em": r[7].isoformat() if r[7] else None,
                "criado_em": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "itens": itens,
        }
    except Exception as e:
        # Tabela pode não existir antes da migration 009
        return {"total": 0, "pagina": pagina, "por_pagina": por_pagina, "itens": [], "aviso": str(e)}


@router.patch("/quarentena/{item_id}")
def revisar_quarentena(
    item_id: int,
    decisao: str = Body(..., description="'aprovar' ou 'rejeitar'"),
    usuario: str = Body("admin", description="Identificador do revisor"),
    db: Session = Depends(get_db),
) -> dict:
    """Revisa um item em quarentena, aprovando ou rejeitando-o.

    - **aprovar**: marca o item como aprovado para reprocessamento manual.
    - **rejeitar**: descarta o item definitivamente.

    Após aprovação, o item pode ser reinserido manualmente via
    o endpoint de ingestão com os dados corrigidos.
    """
    if decisao not in ("aprovar", "rejeitar"):
        raise HTTPException(
            status_code=422,
            detail="decisao deve ser 'aprovar' ou 'rejeitar'",
        )

    novo_status = "aprovado" if decisao == "aprovar" else "rejeitado"
    agora = datetime.now(timezone.utc)

    try:
        result = db.execute(
            text(
                """
                UPDATE itens_quarentena
                SET status = :status,
                    revisado_por = :usuario,
                    revisado_em = :agora
                WHERE id = :id AND status = 'pendente'
                RETURNING id
                """
            ),
            {"status": novo_status, "usuario": usuario, "agora": agora, "id": item_id},
        )
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Item {item_id} não encontrado ou já foi revisado.",
            )

        return {"id": item_id, "status": novo_status, "revisado_por": usuario}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quarentena/resumo")
def resumo_quarentena(
    db: Session = Depends(get_db),
) -> dict:
    """Resumo agregado da quarentena: totais por status, UF e motivo mais frequente."""
    try:
        por_status = db.execute(
            text("SELECT status, COUNT(*) FROM itens_quarentena GROUP BY status ORDER BY status")
        ).fetchall()

        por_uf = db.execute(
            text(
                """
                SELECT uf, COUNT(*) as total
                FROM itens_quarentena
                WHERE status = 'pendente'
                GROUP BY uf
                ORDER BY total DESC
                LIMIT 10
                """
            )
        ).fetchall()

        return {
            "por_status": {r[0]: r[1] for r in por_status},
            "pendentes_por_uf": [{"uf": r[0], "total": r[1]} for r in por_uf],
        }
    except Exception as e:
        return {"por_status": {}, "pendentes_por_uf": [], "aviso": str(e)}
