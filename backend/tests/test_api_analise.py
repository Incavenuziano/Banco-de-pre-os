"""Testes dos endpoints da API de análise — Semana 14.

Cobre: GET /api/v1/analise/precos, /tendencias, /comparativo,
/dashboard, /exportar/csv, /categorias, /ufs, /mapa/precos.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPIListarPrecos:
    """Testes do endpoint GET /api/v1/analise/precos."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/precos")
        assert resp.status_code == 200

    def test_retorna_estrutura(self) -> None:
        resp = client.get("/api/v1/analise/precos")
        data = resp.json()
        assert "itens" in data
        assert "total" in data
        assert "pagina" in data
        assert "total_paginas" in data

    def test_filtro_uf(self) -> None:
        resp = client.get("/api/v1/analise/precos", params={"uf": "SP"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["itens"]:
            assert item["uf"] == "SP"

    def test_filtro_categoria(self) -> None:
        resp = client.get("/api/v1/analise/precos", params={"categoria": "Papel A4"})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["itens"]:
            assert item["categoria"] == "Papel A4"

    def test_paginacao(self) -> None:
        resp = client.get("/api/v1/analise/precos", params={"por_pagina": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["itens"]) <= 5

    def test_filtro_preco_min(self) -> None:
        resp = client.get("/api/v1/analise/precos", params={"preco_min": 20.0})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["itens"]:
            assert item["preco_unitario"] >= 20.0

    def test_filtro_data(self) -> None:
        resp = client.get(
            "/api/v1/analise/precos",
            params={"data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
        )
        assert resp.status_code == 200

    def test_por_pagina_invalido(self) -> None:
        resp = client.get("/api/v1/analise/precos", params={"por_pagina": 200})
        assert resp.status_code == 422  # Validation error

    def test_performance_rapida(self) -> None:
        import time
        inicio = time.time()
        resp = client.get("/api/v1/analise/precos")
        duracao = time.time() - inicio
        assert resp.status_code == 200
        assert duracao < 2.0, f"Query demorou {duracao:.3f}s (> 1s)"


class TestAPITendencias:
    """Testes do endpoint GET /api/v1/analise/tendencias."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/tendencias", params={"categoria": "Papel A4"})
        assert resp.status_code == 200

    def test_categoria_obrigatoria(self) -> None:
        resp = client.get("/api/v1/analise/tendencias")
        assert resp.status_code == 422

    def test_retorna_serie_temporal(self) -> None:
        resp = client.get("/api/v1/analise/tendencias", params={"categoria": "Papel A4", "meses": 3})
        data = resp.json()
        assert "serie_temporal" in data
        assert data["meses"] == 3

    def test_ufs_customizadas(self) -> None:
        resp = client.get(
            "/api/v1/analise/tendencias",
            params={"categoria": "Gasolina Comum", "ufs": ["SP", "RJ"], "meses": 2},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["ufs_analisadas"]) == {"SP", "RJ"}

    def test_meses_invalido(self) -> None:
        resp = client.get(
            "/api/v1/analise/tendencias",
            params={"categoria": "Papel A4", "meses": 30},
        )
        assert resp.status_code == 422

    def test_resumo_por_uf_presente(self) -> None:
        resp = client.get(
            "/api/v1/analise/tendencias",
            params={"categoria": "Arroz", "meses": 2},
        )
        data = resp.json()
        assert "resumo_por_uf" in data
        for uf, resumo in data["resumo_por_uf"].items():
            assert resumo["tendencia"] in ("ALTA", "QUEDA", "ESTAVEL")

    def test_performance_rapida(self) -> None:
        import time
        inicio = time.time()
        resp = client.get("/api/v1/analise/tendencias", params={"categoria": "Gasolina Comum", "meses": 12})
        duracao = time.time() - inicio
        assert resp.status_code == 200
        assert duracao < 2.0, f"Query demorou {duracao:.3f}s"


class TestAPIComparativo:
    """Testes do endpoint GET /api/v1/analise/comparativo."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/comparativo", params={"categoria": "Papel A4"})
        assert resp.status_code == 200

    def test_categoria_obrigatoria(self) -> None:
        resp = client.get("/api/v1/analise/comparativo")
        assert resp.status_code == 422

    def test_retorna_ranking(self) -> None:
        resp = client.get("/api/v1/analise/comparativo", params={"categoria": "Papel A4"})
        data = resp.json()
        assert "comparativo" in data
        assert len(data["comparativo"]) > 0

    def test_ordenado_por_preco(self) -> None:
        resp = client.get("/api/v1/analise/comparativo", params={"categoria": "Papel A4"})
        data = resp.json()
        precos = [item["preco_atual"] for item in data["comparativo"]]
        assert precos == sorted(precos)

    def test_estatisticas_presentes(self) -> None:
        resp = client.get("/api/v1/analise/comparativo", params={"categoria": "Gasolina Comum"})
        data = resp.json()
        assert "estatisticas" in data
        assert "media" in data["estatisticas"]
        assert "uf_mais_barata" in data["estatisticas"]

    def test_performance_rapida(self) -> None:
        import time
        inicio = time.time()
        resp = client.get("/api/v1/analise/comparativo", params={"categoria": "Diesel S10"})
        duracao = time.time() - inicio
        assert resp.status_code == 200
        assert duracao < 2.0


class TestAPIDashboard:
    """Testes do endpoint GET /api/v1/analise/dashboard."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/dashboard")
        assert resp.status_code == 200

    def test_retorna_kpis(self) -> None:
        resp = client.get("/api/v1/analise/dashboard")
        data = resp.json()
        assert "kpis" in data
        kpis = data["kpis"]
        assert "total_registros" in kpis
        assert "cobertura_pct" in kpis

    def test_filtro_ufs(self) -> None:
        resp = client.get("/api/v1/analise/dashboard", params={"ufs": ["SP", "RJ"]})
        data = resp.json()
        assert data["kpis"]["total_ufs"] == 2

    def test_performance_rapida(self) -> None:
        import time
        inicio = time.time()
        resp = client.get("/api/v1/analise/dashboard")
        duracao = time.time() - inicio
        assert resp.status_code == 200
        assert duracao < 2.0


class TestAPIExportarCSV:
    """Testes do endpoint GET /api/v1/analise/exportar/csv."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/exportar/csv")
        assert resp.status_code == 200

    def test_content_type_csv(self) -> None:
        resp = client.get("/api/v1/analise/exportar/csv")
        assert "text/csv" in resp.headers["content-type"]

    def test_content_disposition(self) -> None:
        resp = client.get("/api/v1/analise/exportar/csv")
        assert "attachment" in resp.headers["content-disposition"]
        assert ".csv" in resp.headers["content-disposition"]

    def test_filtro_uf_no_nome_arquivo(self) -> None:
        resp = client.get("/api/v1/analise/exportar/csv", params={"uf": "SP"})
        assert "SP" in resp.headers["content-disposition"]

    def test_conteudo_e_csv_valido(self) -> None:
        import csv
        import io
        resp = client.get("/api/v1/analise/exportar/csv")
        texto = resp.content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(texto), delimiter=";")
        linhas = list(reader)
        assert len(linhas) >= 1  # Cabeçalho sempre presente


class TestAPICategorias:
    """Testes do endpoint GET /api/v1/analise/categorias."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/categorias")
        assert resp.status_code == 200

    def test_retorna_lista(self) -> None:
        resp = client.get("/api/v1/analise/categorias")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_item_tem_campos(self) -> None:
        resp = client.get("/api/v1/analise/categorias")
        item = resp.json()[0]
        assert "nome" in item
        assert "n_registros" in item


class TestAPIUFs:
    """Testes do endpoint GET /api/v1/analise/ufs."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/ufs")
        assert resp.status_code == 200

    def test_retorna_lista(self) -> None:
        resp = client.get("/api/v1/analise/ufs")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_item_tem_status_validada(self) -> None:
        resp = client.get("/api/v1/analise/ufs")
        for item in resp.json():
            assert item["status"] == "VALIDADA"


class TestAPIMapaPrecos:
    """Testes do endpoint GET /api/v1/analise/mapa/precos."""

    def test_retorna_200(self) -> None:
        resp = client.get("/api/v1/analise/mapa/precos", params={"categoria": "Papel A4"})
        assert resp.status_code == 200

    def test_categoria_obrigatoria(self) -> None:
        resp = client.get("/api/v1/analise/mapa/precos")
        assert resp.status_code == 422

    def test_retorna_dados_mapa(self) -> None:
        resp = client.get("/api/v1/analise/mapa/precos", params={"categoria": "Gasolina Comum"})
        data = resp.json()
        assert "dados_mapa" in data
        assert "escala" in data
        assert "minimo" in data["escala"]
        assert "maximo" in data["escala"]

    def test_performance_rapida(self) -> None:
        import time
        inicio = time.time()
        resp = client.get("/api/v1/analise/mapa/precos", params={"categoria": "Arroz"})
        duracao = time.time() - inicio
        assert resp.status_code == 200
        assert duracao < 2.0
