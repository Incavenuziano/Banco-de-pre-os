"""Testes para o serviço de benchmark regional."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.benchmark_regional import BenchmarkRegionalService

client = TestClient(app)
svc = BenchmarkRegionalService()


class TestCompararPorUF:
    """Testes do método comparar_por_uf."""

    def test_retorna_ranking(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        assert "ranking" in resultado
        assert len(resultado["ranking"]) > 0

    def test_ranking_ordenado(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        precos = [item["preco_medio"] for item in resultado["ranking"]]
        assert precos == sorted(precos)

    def test_ranking_tem_campos(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        for item in resultado["ranking"]:
            assert "uf" in item
            assert "preco_medio" in item
            assert "rank" in item

    def test_estatisticas_presentes(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        stats = resultado["estatisticas"]
        assert "media" in stats
        assert "mediana" in stats
        assert "uf_mais_barata" in stats
        assert "uf_mais_cara" in stats

    def test_categoria_inexistente(self) -> None:
        resultado = svc.comparar_por_uf("CategoriaInexistente")
        assert resultado["ranking"] == []
        assert resultado["total_ufs"] == 0

    def test_total_ufs(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        assert resultado["total_ufs"] == len(resultado["ranking"])

    def test_media_coerente(self) -> None:
        resultado = svc.comparar_por_uf("Papel A4")
        stats = resultado["estatisticas"]
        assert stats["minimo"] <= stats["media"] <= stats["maximo"]


class TestPercentilUF:
    """Testes do método percentil_uf."""

    def test_uf_existente(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "SP")
        assert resultado["rank"] is not None
        assert resultado["percentil"] is not None

    def test_percentil_entre_0_e_100(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "SP")
        assert 0 <= resultado["percentil"] <= 100

    def test_uf_inexistente(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "XX")
        assert resultado["rank"] is None
        assert resultado["percentil"] is None

    def test_diferenca_media(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "SP")
        assert "diferenca_media_pct" in resultado

    def test_preco_medio_retornado(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "SP")
        assert "preco_medio" in resultado
        assert resultado["preco_medio"] > 0

    def test_media_nacional_retornada(self) -> None:
        resultado = svc.percentil_uf("Papel A4", "SP")
        assert "media_nacional" in resultado

    def test_categoria_inexistente(self) -> None:
        resultado = svc.percentil_uf("Inexistente", "SP")
        assert resultado["rank"] is None


class TestEvolucaoRegional:
    """Testes do método evolucao_regional."""

    def test_retorna_serie(self) -> None:
        resultado = svc.evolucao_regional("Papel A4")
        assert "serie" in resultado
        assert len(resultado["serie"]) > 0

    def test_meses_parametro(self) -> None:
        resultado = svc.evolucao_regional("Papel A4", meses=3)
        for uf, pontos in resultado["serie"].items():
            assert len(pontos) == 3

    def test_ufs_filtradas(self) -> None:
        resultado = svc.evolucao_regional("Papel A4", ufs=["SP", "RJ"])
        assert set(resultado["serie"].keys()) <= {"SP", "RJ"}

    def test_pontos_tem_campos(self) -> None:
        resultado = svc.evolucao_regional("Papel A4", meses=2)
        for uf, pontos in resultado["serie"].items():
            for p in pontos:
                assert "periodo" in p
                assert "preco" in p
                assert "variacao_pct" in p

    def test_categoria_inexistente(self) -> None:
        resultado = svc.evolucao_regional("CategoriaInexistente")
        assert resultado["serie"] == {}


class TestResumoBenchmark:
    """Testes do método resumo_benchmark."""

    def test_retorna_resumos(self) -> None:
        resultado = svc.resumo_benchmark()
        assert "resumos" in resultado
        assert resultado["total_categorias"] > 0

    def test_resumo_campos(self) -> None:
        resultado = svc.resumo_benchmark()
        for r in resultado["resumos"]:
            assert "categoria" in r
            assert "media_nacional" in r
            assert "uf_mais_barata" in r
            assert "uf_mais_cara" in r

    def test_resumo_categorias_especificas(self) -> None:
        resultado = svc.resumo_benchmark(["Papel A4"])
        assert resultado["total_categorias"] == 1


class TestBenchmarkAPI:
    """Testes dos endpoints REST de benchmark."""

    def test_get_benchmark_uf_ok(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"})
        assert resp.status_code == 200
        data = resp.json()
        assert "ranking" in data

    def test_get_benchmark_percentil(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/percentil", params={"categoria": "Papel A4", "uf": "SP"})
        assert resp.status_code == 200

    def test_get_benchmark_evolucao(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/evolucao", params={"categoria": "Papel A4"})
        assert resp.status_code == 200
        data = resp.json()
        assert "serie" in data

    def test_get_benchmark_resumo(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/resumo")
        assert resp.status_code == 200
