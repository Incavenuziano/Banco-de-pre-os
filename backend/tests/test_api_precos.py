"""Testes da API de preços usando TestClient."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGetEstatisticas:
    """Testes do endpoint GET /api/v1/precos/estatisticas."""

    def test_get_estatisticas_ok(self) -> None:
        """Retorna estatísticas para lista válida."""
        resp = client.get("/api/v1/precos/estatisticas", params={"precos": [10, 20, 30, 40, 50]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["estatisticas"]["n"] == 5
        assert data["estatisticas"]["mediana"] == 30

    def test_get_estatisticas_lista_vazia(self) -> None:
        """Lista vazia retorna n=0."""
        resp = client.get("/api/v1/precos/estatisticas", params={"precos": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["estatisticas"]["n"] == 0

    def test_estatisticas_dois_elementos(self) -> None:
        """Dois elementos retorna estatísticas válidas."""
        resp = client.get("/api/v1/precos/estatisticas", params={"precos": [10, 20]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["estatisticas"]["n"] == 2
        assert data["estatisticas"]["desvio_padrao"] is not None


class TestGetReferencial:
    """Testes do endpoint GET /api/v1/precos/referencial."""

    def test_get_referencial_ok(self) -> None:
        """Retorna preço referencial para lista válida."""
        resp = client.get("/api/v1/precos/referencial", params={"precos": [10, 20, 30, 40, 50]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["preco_referencial"] is not None
        assert data["confianca"] in ("ALTA", "MEDIA", "BAIXA", "INSUFICIENTE")

    def test_get_referencial_sem_excluir_outliers(self) -> None:
        """excluir_outliers=False funciona via query param."""
        resp = client.get(
            "/api/v1/precos/referencial",
            params={"precos": [10, 20, 30, 40, 50], "excluir_outliers": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["n_outliers_excluidos"] == 0

    def test_referencial_um_elemento_insuficiente(self) -> None:
        """Um elemento retorna INSUFICIENTE."""
        resp = client.get("/api/v1/precos/referencial", params={"precos": [42]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["confianca"] == "INSUFICIENTE"


class TestPostSumario:
    """Testes do endpoint POST /api/v1/precos/sumario."""

    def test_post_sumario_ok(self) -> None:
        """Sumário com fontes válidas funciona."""
        body = {
            "fontes": [
                {"preco_unitario": 10, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "SP"},
                {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
            ]
        }
        resp = client.post("/api/v1/precos/sumario", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_amostras"] == 2
        assert data["amostras_validas"] == 2

    def test_post_sumario_vazio(self) -> None:
        """Lista de fontes vazia retorna zeros."""
        resp = client.post("/api/v1/precos/sumario", json={"fontes": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_amostras"] == 0
        assert data["amostras_validas"] == 0

    def test_sumario_ignora_score_baixo(self) -> None:
        """Fonte com score < 30 é filtrada."""
        body = {
            "fontes": [
                {"preco_unitario": 10, "unidade_normalizada": "UN", "score_confianca": 10, "uf": "SP"},
                {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
            ]
        }
        resp = client.post("/api/v1/precos/sumario", json=body)
        assert resp.status_code == 200
        data = resp.json()
        assert data["amostras_validas"] == 1


class TestHealthCheck:
    """Teste do endpoint de health check."""

    def test_health_check(self) -> None:
        """GET /health retorna status ok."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
