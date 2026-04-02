"""Router FastAPI para consulta de preços e estatísticas."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.precos import (
    EstatisticasComOutliersResponse,
    EstatisticasResponse,
    OutlierItem,
    ReferencialResponse,
    SumarioRequest,
    SumarioResponse,
)
from app.services.motor_estatistico import (
    calcular_estatisticas,
    calcular_preco_referencial,
    gerar_sumario_categoria,
    marcar_outliers,
)

router = APIRouter(prefix="/api/v1/precos", tags=["precos"])


@router.get("/estatisticas", response_model=EstatisticasComOutliersResponse)
def get_estatisticas(
    precos: list[float] = Query(default=[]),
    metodo_outlier: str = Query(default="iqr"),
) -> EstatisticasComOutliersResponse:
    """Retorna estatísticas descritivas e marcação de outliers para uma lista de preços."""
    stats = calcular_estatisticas(precos)
    outliers_raw = marcar_outliers(precos, metodo=metodo_outlier)

    return EstatisticasComOutliersResponse(
        estatisticas=EstatisticasResponse(**stats),
        outliers=[OutlierItem(**o) for o in outliers_raw],
    )


@router.get("/referencial", response_model=ReferencialResponse)
def get_referencial(
    precos: list[float] = Query(default=[]),
    excluir_outliers: bool = Query(default=True),
) -> ReferencialResponse:
    """Calcula o preço referencial a partir de uma lista de preços."""
    resultado = calcular_preco_referencial(precos, excluir_outliers=excluir_outliers)

    return ReferencialResponse(
        preco_referencial=resultado["preco_referencial"],
        metodo_usado=resultado["metodo_usado"],
        n_amostras=resultado["n_amostras"],
        n_outliers_excluidos=resultado["n_outliers_excluidos"],
        confianca=resultado["confianca"],
        estatisticas=EstatisticasResponse(**resultado["estatisticas"]),
    )


@router.post("/sumario", response_model=SumarioResponse)
def post_sumario(body: SumarioRequest) -> SumarioResponse:
    """Gera sumário estatístico agrupado por unidade normalizada."""
    fontes_dicts = [f.model_dump() for f in body.fontes]
    resultado = gerar_sumario_categoria(fontes_dicts)

    return SumarioResponse(
        total_amostras=resultado["total_amostras"],
        amostras_validas=resultado["amostras_validas"],
        por_unidade=resultado["por_unidade"],
        distribuicao_uf=resultado["distribuicao_uf"],
    )
