"""Schemas Pydantic para a API de preços."""

from __future__ import annotations

from pydantic import BaseModel


class FontePreco(BaseModel):
    """Fonte de preço individual."""

    preco_unitario: float
    unidade_normalizada: str | None = None
    score_confianca: int = 0
    data_referencia: str | None = None
    uf: str | None = None


class EstatisticasResponse(BaseModel):
    """Resposta com estatísticas descritivas."""

    n: int
    media: float | None = None
    mediana: float | None = None
    desvio_padrao: float | None = None
    variancia: float | None = None
    q1: float | None = None
    q3: float | None = None
    iqr: float | None = None
    min: float | None = None
    max: float | None = None
    coeficiente_variacao: float | None = None


class OutlierItem(BaseModel):
    """Item com marcação de outlier."""

    preco: float
    outlier: bool
    motivo: str | None = None


class EstatisticasComOutliersResponse(BaseModel):
    """Resposta completa com estatísticas e outliers."""

    estatisticas: EstatisticasResponse
    outliers: list[OutlierItem]


class ReferencialResponse(BaseModel):
    """Resposta com preço referencial."""

    preco_referencial: float | None = None
    metodo_usado: str
    n_amostras: int
    n_outliers_excluidos: int
    confianca: str
    estatisticas: EstatisticasResponse


class SumarioRequest(BaseModel):
    """Requisição para sumário de categoria."""

    fontes: list[FontePreco]


class SumarioResponse(BaseModel):
    """Resposta com sumário de categoria."""

    total_amostras: int
    amostras_validas: int
    por_unidade: dict
    distribuicao_uf: dict
