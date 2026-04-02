"""Testes do router de correção monetária — Semana 15.

Cobre: endpoints /api/v1/correcao/ipca, /fator, /preco, /sincronizar.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/v1/correcao/ipca
# ---------------------------------------------------------------------------
class TestSerieIPCA:
    def test_status_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/correcao/ipca")
        assert resp.status_code == 200

    def test_retorna_indice_ipca(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/ipca").json()
        assert data["indice"] == "IPCA"

    def test_retorna_dados_nao_vazios(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/ipca").json()
        assert len(data["dados"]) > 0

    def test_filtro_ano(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/ipca", params={"ano_inicio": 2023, "ano_fim": 2023}).json()
        assert all(d["ano"] == 2023 for d in data["dados"])

    def test_total_meses(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/ipca", params={"ano_inicio": 2021, "ano_fim": 2021}).json()
        assert data["total_meses"] == 12

    def test_campos_dados(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/ipca").json()
        primeiro = data["dados"][0]
        assert "ano" in primeiro
        assert "mes" in primeiro
        assert "variacao_mensal" in primeiro
        assert "variacao_acumulada_ano" in primeiro
        assert "indice_acumulado" in primeiro


# ---------------------------------------------------------------------------
# GET /api/v1/correcao/fator
# ---------------------------------------------------------------------------
class TestFatorCorrecao:
    def test_status_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/correcao/fator", params={
            "data_inicio": "2020-01-01", "data_fim": "2023-01-01"
        })
        assert resp.status_code == 200

    def test_retorna_fator(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/fator", params={
            "data_inicio": "2020-01-01", "data_fim": "2023-01-01"
        }).json()
        assert "fator" in data
        assert data["fator"] > 1.0

    def test_retorna_variacao(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/fator", params={
            "data_inicio": "2020-01-01", "data_fim": "2023-01-01"
        }).json()
        assert data["variacao_percentual"] > 0

    def test_datas_preservadas(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/fator", params={
            "data_inicio": "2022-06-01", "data_fim": "2024-06-01"
        }).json()
        assert data["data_inicio"] == "2022-06-01"
        assert data["data_fim"] == "2024-06-01"

    def test_indice_ipca(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/fator", params={
            "data_inicio": "2021-01-01", "data_fim": "2021-12-01"
        }).json()
        assert data["indice"] == "IPCA"

    def test_sem_params_retorna_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/correcao/fator")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/correcao/preco
# ---------------------------------------------------------------------------
class TestCorrigirPreco:
    def test_status_200(self, client: TestClient) -> None:
        resp = client.post("/api/v1/correcao/preco", json={
            "valor": 100, "data_origem": "2020-01-01", "data_destino": "2023-01-01"
        })
        assert resp.status_code == 200

    def test_valor_corrigido_maior(self, client: TestClient) -> None:
        data = client.post("/api/v1/correcao/preco", json={
            "valor": 100, "data_origem": "2020-01-01", "data_destino": "2023-01-01"
        }).json()
        assert data["valor_corrigido"] > 100

    def test_campos_resposta(self, client: TestClient) -> None:
        data = client.post("/api/v1/correcao/preco", json={
            "valor": 100, "data_origem": "2020-01-01", "data_destino": "2023-01-01"
        }).json()
        for campo in ["valor_original", "valor_corrigido", "fator", "variacao_percentual"]:
            assert campo in data

    def test_valor_zero_ou_negativo_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/correcao/preco", json={
            "valor": -10, "data_origem": "2020-01-01", "data_destino": "2023-01-01"
        })
        assert resp.status_code == 422

    def test_body_vazio_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/correcao/preco", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/correcao/sincronizar
# ---------------------------------------------------------------------------
class TestSincronizar:
    def test_status_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/correcao/sincronizar")
        assert resp.status_code == 200

    def test_status_ok(self, client: TestClient) -> None:
        data = client.get("/api/v1/correcao/sincronizar").json()
        assert data["status"] == "ok"


# ---------------------------------------------------------------------------
# GET /api/v1/analise/precos-corrigidos
# ---------------------------------------------------------------------------
class TestPrecosCorrigidos:
    def test_status_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analise/precos-corrigidos")
        assert resp.status_code == 200

    def test_campo_preco_corrigido_hoje(self, client: TestClient) -> None:
        data = client.get("/api/v1/analise/precos-corrigidos").json()
        if data["itens"]:
            assert "preco_corrigido_hoje" in data["itens"][0]

    def test_campo_fator_correcao(self, client: TestClient) -> None:
        data = client.get("/api/v1/analise/precos-corrigidos").json()
        if data["itens"]:
            assert "fator_correcao_ipca" in data["itens"][0]

    def test_indice_ipca(self, client: TestClient) -> None:
        data = client.get("/api/v1/analise/precos-corrigidos").json()
        assert data["indice"] == "IPCA"
