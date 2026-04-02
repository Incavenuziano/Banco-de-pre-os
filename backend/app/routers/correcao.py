"""Router FastAPI para correção monetária IPCA."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.correcao_monetaria import CorrecaoMonetariaService
from app.services.ibge_service import IBGEService

router = APIRouter(prefix="/api/v1/correcao", tags=["correcao"])

_ibge = IBGEService()
_correcao = CorrecaoMonetariaService(_ibge)


class CorrecaoPrecoRequest(BaseModel):
    """Body para correção de preço."""

    valor: float = Field(..., gt=0, description="Valor a corrigir")
    data_origem: str = Field(..., description="Data de origem (YYYY-MM-DD)")
    data_destino: str = Field(..., description="Data de destino (YYYY-MM-DD)")


@router.get("/ipca", summary="Série histórica IPCA")
def serie_ipca(
    ano_inicio: int = Query(2020, ge=2020, description="Ano inicial"),
    ano_fim: int = Query(2026, le=2030, description="Ano final"),
) -> dict:
    """Retorna série histórica do IPCA entre os anos especificados."""
    serie = _ibge.get_serie(ano_inicio, ano_fim)
    return {
        "indice": "IPCA",
        "periodo": {"ano_inicio": ano_inicio, "ano_fim": ano_fim},
        "total_meses": len(serie),
        "dados": [
            {
                "ano": s.ano,
                "mes": s.mes,
                "variacao_mensal": s.variacao_mensal,
                "variacao_acumulada_ano": s.variacao_acumulada_ano,
                "indice_acumulado": s.indice_acumulado,
            }
            for s in serie
        ],
    }


@router.get("/fator", summary="Fator de correção entre duas datas")
def fator_correcao(
    data_inicio: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="Data final (YYYY-MM-DD)"),
) -> dict:
    """Calcula fator de correção IPCA entre duas datas."""
    fator = _correcao.fator_correcao(data_inicio, data_fim)
    variacao = _correcao.variacao_periodo(data_inicio, data_fim)
    return {
        "fator": round(fator, 6),
        "variacao_percentual": variacao,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "indice": "IPCA",
    }


@router.post("/preco", summary="Corrigir preço pelo IPCA")
def corrigir_preco(body: CorrecaoPrecoRequest) -> dict:
    """Corrige um preço pela inflação IPCA entre duas datas."""
    return _correcao.corrigir_preco_detalhado(
        body.valor, body.data_origem, body.data_destino
    )


@router.get("/sincronizar", summary="Sincronizar dados IPCA")
def sincronizar() -> dict:
    """Sincroniza dados IPCA com a fonte (IBGE SIDRA)."""
    return _ibge.sincronizar()
