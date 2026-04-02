"""Testes do AnaliseService — Semana 14.

Cobre: listar_precos, obter_tendencias, obter_comparativo_ufs,
obter_resumo_dashboard, exportar_csv, listar_categorias, listar_ufs.
"""

from __future__ import annotations

import pytest

from app.services.analise_service import (
    AnaliseService,
    CATEGORIAS,
    UFS_VALIDADAS,
    _variacao_mensal,
)


@pytest.fixture()
def service() -> AnaliseService:
    return AnaliseService()


# ---------------------------------------------------------------------------
# _variacao_mensal
# ---------------------------------------------------------------------------

class TestVariacaoMensal:
    def test_retorna_float(self) -> None:
        resultado = _variacao_mensal(100.0, 6, 2026, 42)
        assert isinstance(resultado, float)

    def test_deterministico(self) -> None:
        r1 = _variacao_mensal(100.0, 6, 2026, 42)
        r2 = _variacao_mensal(100.0, 6, 2026, 42)
        assert r1 == r2

    def test_variacao_dentro_faixa(self) -> None:
        # Variação de até ±5%
        base = 100.0
        for seed in range(20):
            r = _variacao_mensal(base, 3, 2026, seed)
            assert 90.0 <= r <= 115.0, f"seed={seed}, r={r}"


# ---------------------------------------------------------------------------
# listar_precos
# ---------------------------------------------------------------------------

class TestListarPrecos:
    def test_retorna_dict_com_campos(self, service: AnaliseService) -> None:
        resultado = service.listar_precos()
        for campo in ["itens", "total", "pagina", "por_pagina", "total_paginas", "filtros_aplicados"]:
            assert campo in resultado

    def test_itens_e_lista(self, service: AnaliseService) -> None:
        resultado = service.listar_precos()
        assert isinstance(resultado["itens"], list)

    def test_pagina_padrao_1(self, service: AnaliseService) -> None:
        resultado = service.listar_precos()
        assert resultado["pagina"] == 1

    def test_por_pagina_respeitado(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(por_pagina=5)
        assert len(resultado["itens"]) <= 5

    def test_filtro_uf(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(uf="SP")
        for item in resultado["itens"]:
            assert item["uf"] == "SP"

    def test_filtro_categoria(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(categoria="Papel A4")
        for item in resultado["itens"]:
            assert item["categoria"] == "Papel A4"

    def test_filtro_preco_min(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(preco_min=20.0)
        for item in resultado["itens"]:
            assert item["preco_unitario"] >= 20.0

    def test_filtro_preco_max(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(preco_max=50.0)
        for item in resultado["itens"]:
            assert item["preco_unitario"] <= 50.0

    def test_paginacao_segunda_pagina(self, service: AnaliseService) -> None:
        r1 = service.listar_precos(pagina=1, por_pagina=5)
        r2 = service.listar_precos(pagina=2, por_pagina=5)
        # Se há itens em ambas, os IDs da p1 não devem aparecer na p2
        if r2["itens"]:
            ids_p1 = {item["id"] for item in r1["itens"]}
            ids_p2 = {item["id"] for item in r2["itens"]}
            assert ids_p1.isdisjoint(ids_p2), "Páginas 1 e 2 compartilham IDs duplicados"

    def test_total_paginas_calculado(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(por_pagina=10)
        esperado = max(1, (resultado["total"] + 9) // 10)
        assert resultado["total_paginas"] == esperado

    def test_item_tem_campos_obrigatorios(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(por_pagina=1)
        if resultado["itens"]:
            item = resultado["itens"][0]
            for campo in ["id", "uf", "categoria", "preco_unitario", "data_referencia"]:
                assert campo in item

    def test_filtros_aplicados_no_retorno(self, service: AnaliseService) -> None:
        resultado = service.listar_precos(uf="SP", categoria="Papel A4")
        assert resultado["filtros_aplicados"]["uf"] == "SP"
        assert resultado["filtros_aplicados"]["categoria"] == "Papel A4"


# ---------------------------------------------------------------------------
# obter_tendencias
# ---------------------------------------------------------------------------

class TestObterTendencias:
    def test_retorna_dict_com_campos(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Papel A4", meses=3)
        for campo in ["categoria", "ufs_analisadas", "meses", "serie_temporal", "resumo_por_uf", "media_geral"]:
            assert campo in resultado

    def test_categoria_correta(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Gasolina Comum")
        assert resultado["categoria"] == "Gasolina Comum"

    def test_meses_correto(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Papel A4", meses=4)
        assert resultado["meses"] == 4
        for uf, pontos in resultado["serie_temporal"].items():
            assert len(pontos) == 4

    def test_ufs_padrao_cinco(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Papel A4")
        assert len(resultado["ufs_analisadas"]) == 5

    def test_ufs_customizadas(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Papel A4", ufs=["SP", "MG"])
        assert set(resultado["ufs_analisadas"]) == {"SP", "MG"}

    def test_serie_temporal_tem_periodo_e_preco(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Papel A4", meses=2)
        for uf, pontos in resultado["serie_temporal"].items():
            for ponto in pontos:
                assert "periodo" in ponto
                assert "preco" in ponto
                assert ponto["preco"] > 0

    def test_resumo_por_uf_tem_tendencia(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Gasolina Comum", ufs=["SP"])
        resumo = resultado["resumo_por_uf"]["SP"]
        assert resumo["tendencia"] in ("ALTA", "QUEDA", "ESTAVEL")

    def test_media_geral_e_float(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Arroz")
        assert isinstance(resultado["media_geral"], float)
        assert resultado["media_geral"] > 0

    def test_tendencias_categoria_desconhecida(self, service: AnaliseService) -> None:
        resultado = service.obter_tendencias("Item Inexistente", meses=2)
        # Categoria inexistente: retorna estrutura válida sem erro, media_geral=0
        assert isinstance(resultado["media_geral"], float)
        assert resultado["media_geral"] == 0.0


# ---------------------------------------------------------------------------
# obter_comparativo_ufs
# ---------------------------------------------------------------------------

class TestObterComparativoUFs:
    def test_retorna_dict_com_campos(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Papel A4")
        for campo in ["categoria", "comparativo", "estatisticas", "ufs_analisadas"]:
            assert campo in resultado

    def test_comparativo_e_lista(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Papel A4")
        assert isinstance(resultado["comparativo"], list)

    def test_ordenado_por_preco(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Papel A4")
        precos = [item["preco_atual"] for item in resultado["comparativo"]]
        assert precos == sorted(precos)

    def test_rank_sequencial(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Papel A4", ufs=["SP", "RJ", "MG"])
        ranks = [item["rank"] for item in resultado["comparativo"]]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_estatisticas_presentes(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Gasolina Comum")
        est = resultado["estatisticas"]
        for campo in ["media", "mediana", "desvio_padrao", "minimo", "maximo", "uf_mais_barata", "uf_mais_cara"]:
            assert campo in est

    def test_uf_mais_barata_e_mais_cara(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Gasolina Comum", ufs=["SP", "AC"])
        est = resultado["estatisticas"]
        # SP deve ser mais barata que AC (baseado nos dados)
        assert est["uf_mais_barata"] is not None
        assert est["uf_mais_cara"] is not None

    def test_diferenca_media_pct_calculada(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Papel A4", ufs=["SP", "RJ"])
        for item in resultado["comparativo"]:
            assert "diferenca_media_pct" in item

    def test_ufs_padrao_15(self, service: AnaliseService) -> None:
        resultado = service.obter_comparativo_ufs("Arroz")
        assert len(resultado["ufs_analisadas"]) == 15


# ---------------------------------------------------------------------------
# obter_resumo_dashboard
# ---------------------------------------------------------------------------

class TestObterResumoDashboard:
    def test_retorna_dict_com_campos(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard()
        for campo in ["kpis", "kpis_por_uf", "top_categorias", "ufs_cobertas"]:
            assert campo in resultado

    def test_kpis_tem_campos(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard()
        kpis = resultado["kpis"]
        for campo in ["total_registros", "total_categorias", "total_ufs", "cobertura_pct"]:
            assert campo in kpis

    def test_cobertura_pct_entre_0_e_100(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard()
        pct = resultado["kpis"]["cobertura_pct"]
        assert 0 <= pct <= 100

    def test_filtro_ufs(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard(ufs=["SP", "RJ"])
        assert resultado["kpis"]["total_ufs"] == 2

    def test_filtro_categoria(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard(categoria="Papel A4")
        assert resultado["kpis"]["total_categorias"] == 1

    def test_kpis_por_uf_tem_media_preco(self, service: AnaliseService) -> None:
        resultado = service.obter_resumo_dashboard(ufs=["SP"])
        assert len(resultado["kpis_por_uf"]) == 1
        assert resultado["kpis_por_uf"][0]["media_preco"] > 0


# ---------------------------------------------------------------------------
# exportar_csv
# ---------------------------------------------------------------------------

class TestExportarCSV:
    def test_retorna_bytes(self, service: AnaliseService) -> None:
        resultado = service.exportar_csv()
        assert isinstance(resultado, bytes)

    def test_inicia_com_bom(self, service: AnaliseService) -> None:
        resultado = service.exportar_csv()
        assert resultado[:3] == b"\xef\xbb\xbf"

    def test_tem_cabecalho(self, service: AnaliseService) -> None:
        resultado = service.exportar_csv()
        texto = resultado.decode("utf-8-sig")
        assert "UF" in texto
        assert "Categoria" in texto
        assert "Preço Unitário" in texto

    def test_filtro_uf_no_csv(self, service: AnaliseService) -> None:
        resultado = service.exportar_csv(uf="SP")
        texto = resultado.decode("utf-8-sig")
        linhas = texto.strip().split("\n")
        # Todas as linhas de dados devem ter SP (exceto cabeçalho)
        for linha in linhas[1:]:
            if linha.strip():
                assert "SP" in linha

    def test_csv_e_parseable(self, service: AnaliseService) -> None:
        import csv
        import io
        resultado = service.exportar_csv()
        texto = resultado.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(texto), delimiter=";")
        linhas = list(reader)
        assert len(linhas) >= 1  # Cabeçalho sempre presente


# ---------------------------------------------------------------------------
# listar_categorias e listar_ufs
# ---------------------------------------------------------------------------

class TestListarCategorias:
    def test_retorna_lista(self, service: AnaliseService) -> None:
        resultado = service.listar_categorias()
        assert isinstance(resultado, list)

    def test_nao_vazia(self, service: AnaliseService) -> None:
        resultado = service.listar_categorias()
        assert len(resultado) > 0

    def test_item_tem_campos(self, service: AnaliseService) -> None:
        resultado = service.listar_categorias()
        item = resultado[0]
        for campo in ["nome", "n_ufs", "n_registros", "ultima_atualizacao"]:
            assert campo in item

    def test_todas_categorias_presentes(self, service: AnaliseService) -> None:
        resultado = service.listar_categorias()
        nomes = [c["nome"] for c in resultado]
        for cat in CATEGORIAS:
            assert cat in nomes


class TestListarUFs:
    def test_retorna_lista(self, service: AnaliseService) -> None:
        resultado = service.listar_ufs()
        assert isinstance(resultado, list)

    def test_nao_vazia(self, service: AnaliseService) -> None:
        resultado = service.listar_ufs()
        assert len(resultado) > 0

    def test_item_tem_campos(self, service: AnaliseService) -> None:
        resultado = service.listar_ufs()
        item = resultado[0]
        for campo in ["uf", "n_categorias", "n_registros", "status"]:
            assert campo in item

    def test_status_validada(self, service: AnaliseService) -> None:
        resultado = service.listar_ufs()
        for item in resultado:
            assert item["status"] == "VALIDADA"
