"""Testes para os endpoints de busca semântica, full-text e combinada."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestBuscaSemantica:
    """Testes do endpoint /api/v1/busca/semantica."""

    def test_get_semantica_ok(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "papel sulfite"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["metodo"] == "semantica"
        assert "resultados" in data

    def test_semantica_retorna_score(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "papel sulfite a4"})
        data = resp.json()
        for item in data["resultados"]:
            assert "score_similaridade" in item

    def test_semantica_top_n(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "papel", "top_n": 3})
        data = resp.json()
        assert len(data["resultados"]) <= 3

    def test_semantica_q_curto_422(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "ab"})
        assert resp.status_code == 422

    def test_semantica_q_obrigatorio(self) -> None:
        resp = client.get("/api/v1/busca/semantica")
        assert resp.status_code == 422

    def test_semantica_ordenado_por_score(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "gasolina litro"})
        data = resp.json()
        scores = [r["score_similaridade"] for r in data["resultados"]]
        assert scores == sorted(scores, reverse=True)


class TestBuscaFullText:
    """Testes do endpoint /api/v1/busca/full-text."""

    def test_get_fulltext_ok(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "papel"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["metodo"] == "full_text"

    def test_fulltext_retorna_score_relevancia(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "papel sulfite"})
        data = resp.json()
        for item in data["resultados"]:
            assert "score_relevancia" in item

    def test_fulltext_filtra_por_uf(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "litro", "uf": "SP"})
        data = resp.json()
        for item in data["resultados"]:
            assert item["uf"] == "SP"

    def test_fulltext_q_curto_422(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "a"})
        assert resp.status_code == 422

    def test_fulltext_q_obrigatorio(self) -> None:
        resp = client.get("/api/v1/busca/full-text")
        assert resp.status_code == 422

    def test_fulltext_sem_resultado(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "xyzwqkjm"})
        data = resp.json()
        assert data["total"] == 0


class TestBuscaCombinada:
    """Testes do endpoint /api/v1/busca/combinada."""

    def test_get_combinada_ok(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "papel sulfite"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["metodo"] == "combinada"

    def test_combinada_scores_duplos(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "papel sulfite"})
        data = resp.json()
        for item in data["resultados"]:
            assert "score_combinado" in item
            assert "score_semantica" in item
            assert "score_textual" in item

    def test_combinada_peso_semantica(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "papel sulfite", "peso_semantica": 0.8})
        data = resp.json()
        assert data["pesos"]["semantica"] == 0.8
        assert abs(data["pesos"]["textual"] - 0.2) < 0.01

    def test_combinada_top_n(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "papel", "top_n": 2})
        data = resp.json()
        assert len(data["resultados"]) <= 2

    def test_combinada_q_obrigatorio(self) -> None:
        resp = client.get("/api/v1/busca/combinada")
        assert resp.status_code == 422

    def test_combinada_q_curto_422(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "ab"})
        assert resp.status_code == 422
