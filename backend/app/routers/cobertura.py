"""Router FastAPI para cobertura de UFs e municípios."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.cobertura_service import CoberturaService

router = APIRouter(prefix="/api/v1/cobertura", tags=["cobertura"])
_service = CoberturaService()


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints originais (compatibilidade)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ufs")
def listar_ufs() -> list[str]:
    """Lista UFs com cobertura de municípios prioritários."""
    return _service.obter_ufs_cobertas()


@router.get("/municipios")
def municipios(uf: str = Query(..., description="Sigla da UF")) -> list[str]:
    """Retorna municípios prioritários de uma UF."""
    return _service.obter_municipios_por_uf(uf)


@router.get("/indice")
def indice(
    uf: str = Query(..., description="Sigla da UF"),
    n_amostras: int = Query(..., ge=0, description="Número de amostras"),
    n_categorias: int = Query(..., ge=0, description="Número de categorias"),
) -> dict:
    """Calcula índice de cobertura de uma UF."""
    return _service.calcular_indice_cobertura(uf, n_amostras, n_categorias)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints novos: cobertura por município goiano
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/go/municipios",
    summary="Lista municípios goianos monitorados",
    response_description="Lista com os 50 principais municípios de GO",
)
def municipios_go() -> list[str]:
    """Retorna a lista completa dos municípios goianos monitorados pelo banco de preços."""
    return _service.obter_todos_municipios_go()


@router.get(
    "/go/mapa",
    summary="Mapa de cobertura de dados por município em Goiás",
    response_description="Lista de municípios com nível de cobertura (ALTA/MEDIA/BAIXA/INSUFICIENTE)",
)
def mapa_cobertura_go(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Retorna a cobertura de dados do PNCP para cada município goiano monitorado.

    Consulta o banco de preços para contar amostras e categorias por município
    e classifica o nível de cobertura:

    - **ALTA**: ≥50 amostras e ≥5 categorias
    - **MEDIA**: ≥20 amostras e ≥3 categorias
    - **BAIXA**: ≥5 amostras e ≥1 categoria
    - **INSUFICIENTE**: dados insuficientes para referência confiável
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT fp.municipio,
                       COUNT(*)                 AS n_amostras,
                       COUNT(DISTINCT c.id)     AS n_categorias
                FROM fontes_preco fp
                JOIN itens i ON i.id = fp.item_id
                LEFT JOIN categorias c ON c.id = i.categoria_id
                WHERE fp.uf = 'GO'
                  AND fp.ativo = TRUE
                GROUP BY fp.municipio
                """
            )
        ).fetchall()

        contagens = {
            r.municipio: {"n_amostras": r.n_amostras, "n_categorias": r.n_categorias}
            for r in rows
            if r.municipio
        }
    except Exception:
        # Se o banco não estiver disponível (ex: testes sem DB), retorna tudo INSUFICIENTE
        contagens = {}

    return _service.obter_mapa_cobertura_go(contagens)


@router.get(
    "/go/resumo",
    summary="Resumo estatístico da cobertura em Goiás",
    response_description="Totais por nível de cobertura e percentual coberto",
)
def resumo_cobertura_go(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Retorna estatísticas agregadas de cobertura para todo o estado de Goiás.

    Útil para monitorar evolução da qualidade dos dados ao longo do tempo.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT fp.municipio,
                       COUNT(*)             AS n_amostras,
                       COUNT(DISTINCT c.id) AS n_categorias
                FROM fontes_preco fp
                JOIN itens i ON i.id = fp.item_id
                LEFT JOIN categorias c ON c.id = i.categoria_id
                WHERE fp.uf = 'GO'
                  AND fp.ativo = TRUE
                GROUP BY fp.municipio
                """
            )
        ).fetchall()

        contagens = {
            r.municipio: {"n_amostras": r.n_amostras, "n_categorias": r.n_categorias}
            for r in rows
            if r.municipio
        }
    except Exception:
        contagens = {}

    return _service.resumo_cobertura_go(contagens)
