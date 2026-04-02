"""Schemas Pydantic para a API de relatórios."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AmostraRelatorio(BaseModel):
    """Amostra individual para composição do relatório."""

    numero_controle: str | None = None
    orgao_origem: str | None = None
    data_referencia: str | None = None
    preco_unitario: float
    unidade: str | None = None
    uf: str | None = None
    qualidade: str | None = None
    url_origem: str | None = None
    outlier: bool = False


# Alias para compatibilidade com código de testes S18
AmostraInput = AmostraRelatorio


class RelatorioInput(BaseModel):
    """Dados de entrada para geração de relatório PDF."""

    orgao_nome: str
    orgao_cnpj: str | None = None
    item_descricao: str
    categoria_nome: str | None = None
    # Aceita YYYY-MM-DD ou YYYY-MM
    periodo_inicio: str
    periodo_fim: str
    uf_filtro: str | None = None
    amostras: list[AmostraRelatorio] = []
    estatisticas: dict = {}
    preco_referencial: float | None = None
    confianca: str = "INSUFICIENTE"
    n_outliers_excluidos: int = 0
    id_relatorio: str
    emitido_em: str


class RelatorioPreviewResponse(BaseModel):
    """Resposta de preview do relatório."""

    id_relatorio: str
    dados: RelatorioInput
