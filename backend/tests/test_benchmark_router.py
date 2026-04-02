"""Testes dos endpoints de benchmark regional — Semana 18."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestBenchmarkUF:
    """Testes do endpoint GET /api/v1/analise/benchmark/uf."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"})
        assert resp.status_code == 200

    def test_ranking_presente(self) -> None:
        data = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"}).json()
        assert "ranking" in data
        assert len(data["ranking"]) > 0

    def test_estatisticas(self) -> None:
        data = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"}).json()
        assert "media" in data["estatisticas"]
        assert "mediana" in data["estatisticas"]

    def test_ranking_ordenado(self) -> None:
        data = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"}).json()
        precos = [item["preco_medio"] for item in data["ranking"]]
        assert precos == sorted(precos)

    def test_categoria_inexistente(self) -> None:
        data = client.get("/api/v1/analise/benchmark/uf", params={"categoria": "XYZ"}).json()
        assert data["total_ufs"] == 0


class TestBenchmarkPercentil:
    """Testes do endpoint GET /api/v1/analise/benchmark/percentil."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/percentil", params={
            "categoria": "Papel A4", "uf": "SP"
        })
        assert resp.status_code == 200

    def test_rank_presente(self) -> None:
        data = client.get("/api/v1/analise/benchmark/percentil", params={
            "categoria": "Papel A4", "uf": "SP"
        }).json()
        assert data["rank"] is not None

    def test_percentil_range(self) -> None:
        data = client.get("/api/v1/analise/benchmark/percentil", params={
            "categoria": "Papel A4", "uf": "SP"
        }).json()
        assert 1 <= data["percentil"] <= 100


class TestBenchmarkEvolucao:
    """Testes do endpoint GET /api/v1/analise/benchmark/evolucao."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/evolucao", params={
            "categoria": "Papel A4"
        })
        assert resp.status_code == 200

    def test_serie_presente(self) -> None:
        data = client.get("/api/v1/analise/benchmark/evolucao", params={
            "categoria": "Papel A4"
        }).json()
        assert "serie" in data
        assert len(data["serie"]) > 0

    def test_meses_param(self) -> None:
        data = client.get("/api/v1/analise/benchmark/evolucao", params={
            "categoria": "Papel A4", "meses": 3
        }).json()
        for pontos in data["serie"].values():
            assert len(pontos) == 3


class TestBenchmarkResumo:
    """Testes do endpoint GET /api/v1/analise/benchmark/resumo."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/analise/benchmark/resumo")
        assert resp.status_code == 200

    def test_total_categorias(self) -> None:
        data = client.get("/api/v1/analise/benchmark/resumo").json()
        assert data["total_categorias"] > 0

    def test_resumos_presentes(self) -> None:
        data = client.get("/api/v1/analise/benchmark/resumo").json()
        assert len(data["resumos"]) > 0
