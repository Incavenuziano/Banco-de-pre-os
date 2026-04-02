"""Schemas Pydantic para a API de busca."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemBusca(BaseModel):
    """Item retornado na busca."""

    id: int
    descricao: str
    categoria: str | None = None
    preco_mediano: float | None = None
    n_amostras: int = 0
    uf: str | None = None
    data_ultima_atualizacao: str | None = None


class BuscaResponse(BaseModel):
    """Resposta paginada da busca de itens."""

    total: int
    page: int
    page_size: int
    itens: list[ItemBusca]


class CategoriaResponse(BaseModel):
    """Categoria retornada na listagem."""

    id: int
    nome: str
    familia: str
    descricao: str
