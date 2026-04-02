"""Testes para o router de busca de itens e categorias."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestApiBusca:
    """Testes para os endpoints de busca."""

    def test_get_itens_q_obrigatorio(self) -> None:
        """Verifica que o parâmetro q é obrigatório."""
        resp = client.get("/api/v1/busca/itens")
        assert resp.status_code == 422

    def test_get_itens_retorna_lista(self) -> None:
        """Verifica que a busca retorna uma lista de itens."""
        resp = client.get("/api/v1/busca/itens", params={"q": "papel"})
        assert resp.status_code == 200
        data = resp.json()
        assert "itens" in data
        assert "total" in data
        assert isinstance(data["itens"], list)

    def test_get_itens_filtra_por_texto(self) -> None:
        """Verifica que a busca filtra corretamente por texto."""
        resp = client.get("/api/v1/busca/itens", params={"q": "gasolina"})
        data = resp.json()
        assert data["total"] >= 1
        for item in data["itens"]:
            assert "gasolina" in item["descricao"].lower()

    def test_get_itens_paginacao(self) -> None:
        """Verifica que a paginação funciona corretamente."""
        resp = client.get("/api/v1/busca/itens", params={"q": "papel", "page": 1, "page_size": 2})
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["itens"]) <= 2

    def test_get_itens_q_curto_erro(self) -> None:
        """Verifica que q com menos de 3 caracteres retorna 422."""
        resp = client.get("/api/v1/busca/itens", params={"q": "ab"})
        assert resp.status_code == 422

    def test_get_categorias_retorna_lista(self) -> None:
        """Verifica que /categorias retorna uma lista."""
        resp = client.get("/api/v1/busca/categorias")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_categorias_tem_50_itens(self) -> None:
        """Verifica que /categorias retorna exatamente 50 categorias."""
        resp = client.get("/api/v1/busca/categorias")
        data = resp.json()
        assert len(data) == 51

    def test_get_itens_uf_filtro(self) -> None:
        """Verifica que o filtro por UF funciona."""
        resp = client.get("/api/v1/busca/itens", params={"q": "litro", "uf": "SP"})
        data = resp.json()
        for item in data["itens"]:
            assert item["uf"] == "SP"
