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


# ─────────────────────────────────────────────────────────────────────────────
# Classificador tipo_objeto — gestão de regras, overrides e auditoria
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/tipo-objeto/regras")
def listar_regras_tipo_objeto(
    tipo: str | None = Query(None, description="material | servico | obra"),
    ativo: bool | None = Query(None, description="Filtrar por status ativo/inativo"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    """Lista regras de classificação de tipo_objeto.

    Regras são regex aplicadas sobre descrições normalizadas (sem acentos,
    maiúsculas) para classificar itens em material/servico/obra.
    Avaliadas em ordem decrescente de prioridade.
    """
    try:
        params: dict = {"offset": (pagina - 1) * por_pagina, "limit": por_pagina}
        filtros = []
        if tipo:
            filtros.append("tipo = :tipo")
            params["tipo"] = tipo
        if ativo is not None:
            filtros.append("ativo = :ativo")
            params["ativo"] = ativo
        where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

        total = db.execute(
            text(f"SELECT COUNT(*) FROM tipo_objeto_regras {where}"), params
        ).scalar() or 0

        rows = db.execute(
            text(
                f"""
                SELECT id, padrao, tipo, prioridade, ativo, descricao, criado_em
                FROM tipo_objeto_regras {where}
                ORDER BY prioridade DESC, id
                OFFSET :offset LIMIT :limit
                """
            ),
            params,
        ).fetchall()

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "regras": [
                {
                    "id": r[0],
                    "padrao": r[1],
                    "tipo": r[2],
                    "prioridade": r[3],
                    "ativo": r[4],
                    "descricao": r[5],
                    "criado_em": r[6].isoformat() if r[6] else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"total": 0, "pagina": pagina, "por_pagina": por_pagina, "regras": [], "aviso": str(e)}


@router.post("/tipo-objeto/regras", status_code=201)
def criar_regra_tipo_objeto(
    padrao: str = Body(..., description="Regex Python (aplicada sobre texto sem acentos + maiúsculas)"),
    tipo: str = Body(..., description="material | servico | obra"),
    prioridade: int = Body(50, ge=1, le=99, description="Prioridade de avaliação (maior = primeiro)"),
    descricao: str | None = Body(None, description="Descrição em linguagem natural"),
    db: Session = Depends(get_db),
) -> dict:
    """Cria uma nova regra de classificação de tipo_objeto.

    A regra entra ativa imediatamente. O cache do classificador é TTL de 5 min,
    portanto pode demorar até 5 min para ser aplicada nas próximas ingestões.
    """
    import re as _re

    if tipo not in ("material", "servico", "obra"):
        raise HTTPException(status_code=422, detail="tipo deve ser material, servico ou obra")

    try:
        _re.compile(padrao)
    except _re.error as exc:
        raise HTTPException(status_code=422, detail=f"Regex inválida: {exc}") from exc

    try:
        row = db.execute(
            text(
                """
                INSERT INTO tipo_objeto_regras (padrao, tipo, prioridade, descricao)
                VALUES (:padrao, :tipo, :prioridade, :descricao)
                RETURNING id, criado_em
                """
            ),
            {"padrao": padrao, "tipo": tipo, "prioridade": prioridade, "descricao": descricao},
        ).fetchone()
        db.commit()
        return {
            "id": row[0],
            "padrao": padrao,
            "tipo": tipo,
            "prioridade": prioridade,
            "ativo": True,
            "descricao": descricao,
            "criado_em": row[1].isoformat() if row[1] else None,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tipo-objeto/regras/{regra_id}")
def atualizar_regra_tipo_objeto(
    regra_id: int,
    ativo: bool | None = Body(None, description="Ativar/desativar regra"),
    prioridade: int | None = Body(None, ge=1, le=99, description="Nova prioridade"),
    descricao: str | None = Body(None, description="Nova descrição"),
    db: Session = Depends(get_db),
) -> dict:
    """Atualiza campos de uma regra (ativo, prioridade ou descrição)."""
    campos = []
    params: dict = {"id": regra_id}

    if ativo is not None:
        campos.append("ativo = :ativo")
        params["ativo"] = ativo
    if prioridade is not None:
        campos.append("prioridade = :prioridade")
        params["prioridade"] = prioridade
    if descricao is not None:
        campos.append("descricao = :descricao")
        params["descricao"] = descricao

    if not campos:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar")

    try:
        result = db.execute(
            text(
                f"UPDATE tipo_objeto_regras SET {', '.join(campos)} WHERE id = :id RETURNING id"
            ),
            params,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Regra {regra_id} não encontrada")
        return {"id": regra_id, "atualizado": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tipo-objeto/regras/{regra_id}", status_code=204)
def excluir_regra_tipo_objeto(
    regra_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Exclui permanentemente uma regra.

    Prefira desativar (PATCH ativo=false) a deletar, para manter histórico.
    """
    try:
        result = db.execute(
            text("DELETE FROM tipo_objeto_regras WHERE id = :id"), {"id": regra_id}
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Regra {regra_id} não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tipo-objeto/override")
def registrar_override_tipo_objeto(
    item_id: str = Body(..., description="UUID do item em itens"),
    tipo: str = Body(..., description="material | servico | obra"),
    usuario: str = Body("admin", description="Identificador do revisor"),
    motivo: str | None = Body(None, description="Justificativa da correção"),
    db: Session = Depends(get_db),
) -> dict:
    """Registra override manual de tipo_objeto para um item.

    Substitui permanentemente a classificação automática. O override tem
    precedência máxima em toda classificação futura do item.
    """
    if tipo not in ("material", "servico", "obra"):
        raise HTTPException(status_code=422, detail="tipo deve ser material, servico ou obra")

    try:
        db.execute(
            text(
                """
                INSERT INTO tipo_objeto_overrides (item_id, tipo_override, usuario, motivo)
                VALUES (:item_id, :tipo, :usuario, :motivo)
                ON CONFLICT (item_id) DO UPDATE
                    SET tipo_override = EXCLUDED.tipo_override,
                        usuario       = EXCLUDED.usuario,
                        motivo        = EXCLUDED.motivo,
                        criado_em     = NOW()
                """
            ),
            {"item_id": item_id, "tipo": tipo, "usuario": usuario, "motivo": motivo},
        )
        # Propagar para coluna tipo_objeto em itens (keep in sync)
        db.execute(
            text("UPDATE itens SET tipo_objeto = :tipo WHERE id = :item_id"),
            {"tipo": tipo, "item_id": item_id},
        )
        db.commit()
        return {"item_id": item_id, "tipo_override": tipo, "usuario": usuario}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipo-objeto/auditoria")
def listar_auditoria_tipo_objeto(
    item_id: str | None = Query(None, description="Filtrar por item específico"),
    tipo_inferido: str | None = Query(None, description="Filtrar por tipo inferido"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    """Lista registros de auditoria do classificador tipo_objeto."""
    try:
        params: dict = {"offset": (pagina - 1) * por_pagina, "limit": por_pagina}
        filtros = []
        if item_id:
            filtros.append("item_id = :item_id")
            params["item_id"] = item_id
        if tipo_inferido:
            filtros.append("tipo_inferido = :tipo_inferido")
            params["tipo_inferido"] = tipo_inferido
        where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

        total = db.execute(
            text(f"SELECT COUNT(*) FROM tipo_objeto_auditoria {where}"), params
        ).scalar() or 0

        rows = db.execute(
            text(
                f"""
                SELECT id, item_id, descricao_trecho, tipo_inferido,
                       tipo_correto, metodo, score, auditado_em
                FROM tipo_objeto_auditoria {where}
                ORDER BY auditado_em DESC
                OFFSET :offset LIMIT :limit
                """
            ),
            params,
        ).fetchall()

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "registros": [
                {
                    "id": r[0],
                    "item_id": str(r[1]) if r[1] else None,
                    "descricao_trecho": r[2],
                    "tipo_inferido": r[3],
                    "tipo_correto": r[4],
                    "metodo": r[5],
                    "score": r[6],
                    "auditado_em": r[7].isoformat() if r[7] else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        return {"total": 0, "pagina": pagina, "por_pagina": por_pagina, "registros": [], "aviso": str(e)}


@router.get("/tipo-objeto/resumo")
def resumo_tipo_objeto(db: Session = Depends(get_db)) -> dict:
    """Resumo da distribuição de tipo_objeto nos itens e saúde das regras."""
    try:
        dist_itens = db.execute(
            text(
                """
                SELECT tipo_objeto, COUNT(*) as total
                FROM itens
                WHERE tipo_objeto IS NOT NULL
                GROUP BY tipo_objeto
                ORDER BY total DESC
                """
            )
        ).fetchall()

        total_regras = db.execute(
            text("SELECT COUNT(*) FROM tipo_objeto_regras WHERE ativo = TRUE")
        ).scalar() or 0

        total_overrides = db.execute(
            text("SELECT COUNT(*) FROM tipo_objeto_overrides")
        ).scalar() or 0

        return {
            "distribuicao_itens": {r[0]: r[1] for r in dist_itens},
            "total_regras_ativas": total_regras,
            "total_overrides": total_overrides,
        }
    except Exception as e:
        return {"distribuicao_itens": {}, "total_regras_ativas": 0, "total_overrides": 0, "aviso": str(e)}


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
