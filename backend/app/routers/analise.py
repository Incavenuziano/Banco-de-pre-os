"""Router FastAPI para análise de preços — Semana 14.

Endpoints para dashboard de análise, tendências, comparativo por UF,
filtros avançados e exportação de dados.
"""

from __future__ import annotations

import io
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.analise_service import AnaliseService
from app.services.benchmark_regional import BenchmarkRegionalService
from app.services.correcao_monetaria import CorrecaoMonetariaService

router = APIRouter(prefix="/api/v1/analise", tags=["analise"])

_service = AnaliseService()
_correcao = CorrecaoMonetariaService()
_benchmark = BenchmarkRegionalService()


@router.get(
    "/precos",
    summary="Lista preços com filtros avançados",
    response_description="Lista paginada de preços com metadados",
)
def listar_precos(
    uf: Annotated[str | None, Query(description="Filtrar por UF (ex: SP, RJ)")] = None,
    categoria: Annotated[str | None, Query(description="Filtrar por categoria")] = None,
    municipio: Annotated[str | None, Query(description="Filtrar por município (ex: Goiânia)")] = None,
    data_inicio: Annotated[
        str | None, Query(description="Data inicial (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    ] = None,
    data_fim: Annotated[
        str | None, Query(description="Data final (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    ] = None,
    preco_min: Annotated[float | None, Query(description="Preço mínimo", ge=0)] = None,
    preco_max: Annotated[float | None, Query(description="Preço máximo", ge=0)] = None,
    pagina: Annotated[int, Query(description="Página (começa em 1)", ge=1)] = 1,
    por_pagina: Annotated[int, Query(description="Itens por página", ge=1, le=100)] = 20,
    ordenar_por: Annotated[str, Query(description="Campo de ordenação: 'data' ou 'preco'", pattern=r"^(data|preco)$")] = "data",
    ordem: Annotated[str, Query(description="Direção: 'asc' ou 'desc'", pattern=r"^(asc|desc)$")] = "desc",
) -> dict:
    """Lista preços com filtros avançados: UF, categoria, município, data e faixa de preço.

    Retorna lista paginada com metadados de paginação e filtros aplicados.
    Combina dados de fontes_preco (seed/pipeline) e itens PNCP diretos.
    Suporta ordenação por data ou preço (asc/desc).
    """
    return _service.listar_precos(
        uf=uf,
        categoria=categoria,
        municipio=municipio,
        data_inicio=data_inicio,
        data_fim=data_fim,
        preco_min=preco_min,
        preco_max=preco_max,
        pagina=pagina,
        por_pagina=por_pagina,
        ordenar_por=ordenar_por,
        ordem=ordem,
    )


@router.get(
    "/tendencias",
    summary="Tendências de preço por categoria e UF",
    response_description="Série temporal de preços por UF",
)
def obter_tendencias(
    categoria: Annotated[str, Query(description="Categoria para análise de tendência")],
    ufs: Annotated[
        list[str] | None,
        Query(description="UFs para comparar (ex: SP, RJ, MG)"),
    ] = None,
    meses: Annotated[int, Query(description="Meses de histórico (1-24)", ge=1, le=24)] = 6,
) -> dict:
    """Retorna tendências de preço ao longo do tempo por categoria e UF.

    Inclui série temporal mensal, variação percentual e indicador de tendência
    (ALTA, QUEDA, ESTAVEL) para cada UF selecionada.
    """
    return _service.obter_tendencias(categoria=categoria, ufs=ufs, meses=meses)


@router.get(
    "/comparativo",
    summary="Comparativo de preços entre UFs",
    response_description="Ranking de preços por UF para a categoria",
)
def obter_comparativo(
    categoria: Annotated[str, Query(description="Categoria para comparar entre UFs")],
    ufs: Annotated[
        list[str] | None,
        Query(description="UFs para comparar. Se omitido, usa todas as 15 validadas"),
    ] = None,
) -> dict:
    """Compara preços de uma categoria entre múltiplas UFs.

    Retorna ranking por preço, diferença percentual em relação à média e
    estatísticas descritivas do comparativo.
    """
    return _service.obter_comparativo_ufs(categoria=categoria, ufs=ufs)


@router.get(
    "/dashboard",
    summary="Resumo do dashboard de análise",
    response_description="KPIs e métricas agregadas para o dashboard",
)
def dashboard_analise(
    ufs: Annotated[
        list[str] | None,
        Query(description="UFs para incluir no dashboard"),
    ] = None,
    categoria: Annotated[str | None, Query(description="Filtrar por categoria")] = None,
) -> dict:
    """Retorna KPIs e métricas agregadas para o dashboard principal.

    Inclui totais, distribuição por UF, top categorias e cobertura.
    Otimizado para latência < 1s.
    """
    return _service.obter_resumo_dashboard(ufs=ufs, categoria=categoria)


@router.get(
    "/exportar/csv",
    summary="Exportar dados em CSV",
    response_description="Arquivo CSV com dados filtrados",
)
def exportar_csv(
    uf: Annotated[str | None, Query(description="Filtrar por UF")] = None,
    categoria: Annotated[str | None, Query(description="Filtrar por categoria")] = None,
    municipio: Annotated[str | None, Query(description="Filtrar por município")] = None,
    data_inicio: Annotated[
        str | None, Query(description="Data inicial (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    ] = None,
    data_fim: Annotated[
        str | None, Query(description="Data final (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    ] = None,
    preco_min: Annotated[float | None, Query(description="Preço mínimo", ge=0)] = None,
    preco_max: Annotated[float | None, Query(description="Preço máximo", ge=0)] = None,
) -> StreamingResponse:
    """Exporta preços filtrados em formato CSV (UTF-8-BOM, compatível com Excel).

    Aplicáveis todos os filtros avançados. Máximo de 1000 registros por exportação.
    """
    csv_bytes = _service.exportar_csv(
        uf=uf,
        categoria=categoria,
        municipio=municipio,
        data_inicio=data_inicio,
        data_fim=data_fim,
        preco_min=preco_min,
        preco_max=preco_max,
    )

    nome_arquivo = "precos_banco"
    if uf:
        nome_arquivo += f"_{uf}"
    if municipio:
        nome_arquivo += f"_{municipio.replace(' ', '_')}"
    if categoria:
        nome_arquivo += f"_{categoria.replace(' ', '_')}"
    nome_arquivo += ".csv"

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )


@router.get(
    "/comparativo-item",
    summary="Comparativo de preço de um item por UF",
    response_description="Histórico local + benchmark por UF",
)
def comparativo_item(
    descricao: Annotated[str, Query(description="Descrição do item")],
    uf: Annotated[str | None, Query(description="Filtrar histórico por UF")] = None,
) -> dict:
    """Compara preços de um item: histórico local e benchmark por UF."""
    return _service.get_comparativo_item(descricao=descricao, uf=uf)


@router.get(
    "/historico",
    summary="Histórico de preços de um item",
    response_description="Lista cronológica de preços para uma descrição",
)
def historico_item(
    descricao: Annotated[str, Query(description="Descrição do item para buscar histórico")],
    uf: Annotated[str | None, Query(description="Filtrar por UF")] = None,
    limite: Annotated[int, Query(description="Limite de registros", ge=1, le=500)] = 100,
) -> dict:
    """Retorna histórico cronológico de preços para um item.

    Busca todas as ocorrências de itens com descrição similar (ILIKE),
    retornando dados de múltiplas contratações ordenados por data.
    """
    return _service.get_historico_item(descricao=descricao, uf=uf, limite=limite)


@router.get(
    "/categorias",
    summary="Lista categorias disponíveis",
    response_description="Lista de categorias com metadados",
)
def listar_categorias() -> list[dict]:
    """Lista todas as categorias disponíveis no banco de preços com metadados."""
    return _service.listar_categorias()


@router.get(
    "/ufs",
    summary="Lista UFs validadas",
    response_description="Lista de UFs com status e contagem de registros",
)
def listar_ufs() -> list[dict]:
    """Lista todas as UFs validadas no sistema com status e contagem de registros."""
    return _service.listar_ufs()


@router.get(
    "/municipios",
    summary="Lista municípios disponíveis",
    response_description="Lista de municípios com dados reais no banco",
)
def listar_municipios(
    uf: Annotated[str | None, Query(description="Filtrar por UF")] = None,
) -> list[dict]:
    """Lista municípios com dados reais no banco, opcionalmente filtrados por UF."""
    return _service.listar_municipios(uf=uf)


@router.get(
    "/mapa/precos",
    summary="Dados de preço para visualização em mapa",
    response_description="Preços por UF para renderizar no mapa do Brasil",
)
def mapa_precos(
    categoria: Annotated[str, Query(description="Categoria para o mapa")],
) -> dict:
    """Retorna preços por UF em formato otimizado para renderização em mapa.

    Ideal para componentes de mapa coroplético no frontend.
    """
    comparativo = _service.obter_comparativo_ufs(categoria=categoria)
    return {
        "categoria": categoria,
        "dados_mapa": {
            item["uf"]: {
                "preco": item["preco_atual"],
                "rank": item["rank"],
                "diferenca_media_pct": item["diferenca_media_pct"],
            }
            for item in comparativo["comparativo"]
        },
        "escala": {
            "minimo": comparativo["estatisticas"]["minimo"],
            "maximo": comparativo["estatisticas"]["maximo"],
            "media": comparativo["estatisticas"]["media"],
        },
    }


@router.get(
    "/precos-corrigidos",
    summary="Preços com correção monetária IPCA",
    response_description="Lista de preços com campo preco_corrigido_hoje",
)
def precos_corrigidos(
    uf: Annotated[str | None, Query(description="Filtrar por UF")] = None,
    categoria: Annotated[str | None, Query(description="Filtrar por categoria")] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """Retorna preços com campo adicional `preco_corrigido_hoje`.

    Aplica correção monetária IPCA da data de referência até o mês atual.
    """
    from datetime import date

    dados = _service.listar_precos(
        uf=uf, categoria=categoria, pagina=pagina, por_pagina=por_pagina
    )

    hoje = date.today()
    data_destino = f"{hoje.year}-{hoje.month:02d}-01"

    itens_corrigidos = []
    for item in dados.get("itens", []):
        item_corrigido = dict(item)
        data_ref = item.get("data_referencia", "2025-01-01")
        preco = item.get("preco_unitario", 0)
        try:
            corrigido = _correcao.corrigir_preco(preco, data_ref, data_destino)
            fator = _correcao.fator_correcao(data_ref, data_destino)
        except (ValueError, KeyError):
            corrigido = preco
            fator = 1.0
        item_corrigido["preco_corrigido_hoje"] = corrigido
        item_corrigido["fator_correcao_ipca"] = round(fator, 6)
        itens_corrigidos.append(item_corrigido)

    return {
        "itens": itens_corrigidos,
        "total": dados.get("total", 0),
        "pagina": dados.get("pagina", 1),
        "total_paginas": dados.get("total_paginas", 1),
        "data_correcao": data_destino,
        "indice": "IPCA",
    }


# --- Benchmark Regional (S18) ---


@router.get(
    "/benchmark/uf",
    summary="Ranking de preços por UF",
)
def benchmark_uf(
    categoria: Annotated[str, Query(description="Categoria para benchmark")],
) -> dict:
    """Retorna ranking de preço médio por UF para uma categoria."""
    return _benchmark.comparar_por_uf(categoria)


@router.get(
    "/benchmark/percentil",
    summary="Percentil de uma UF no ranking nacional",
)
def benchmark_percentil(
    categoria: Annotated[str, Query(description="Categoria")],
    uf: Annotated[str, Query(description="UF para consultar")],
) -> dict:
    """Retorna posição e percentil de uma UF no ranking nacional."""
    return _benchmark.percentil_uf(categoria, uf)


@router.get(
    "/benchmark/evolucao",
    summary="Série temporal regional",
)
def benchmark_evolucao(
    categoria: Annotated[str, Query(description="Categoria para evolução")],
    ufs: Annotated[list[str] | None, Query(description="UFs para comparar")] = None,
    meses: Annotated[int, Query(ge=1, le=24)] = 6,
) -> dict:
    """Retorna série temporal de preços por UF."""
    return _benchmark.evolucao_regional(categoria, ufs, meses)


@router.get(
    "/benchmark/resumo",
    summary="Resumo de benchmark para múltiplas categorias",
)
def benchmark_resumo() -> dict:
    """Resumo do benchmark para todas as categorias disponíveis."""
    return _benchmark.resumo_benchmark()
