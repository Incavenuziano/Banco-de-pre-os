"""Testes para o serviço e API de cobertura de UFs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.cobertura_service import CoberturaService

client = TestClient(app)
service = CoberturaService()


class TestCoberturaService:
    """Testes do CoberturaService."""

    def test_obter_municipios_go_nao_vazio(self) -> None:
        """GO tem pelo menos 10 municípios prioritários."""
        municipios = service.obter_municipios_por_uf("GO")
        assert len(municipios) >= 10

    def test_obter_ufs_cobertas_tem_df(self) -> None:
        """Lista de UFs cobertas inclui DF."""
        ufs = service.obter_ufs_cobertas()
        assert "DF" in ufs

    def test_indice_alto(self) -> None:
        """n_amostras=1000, n_categorias=50 → ALTO."""
        resultado = service.calcular_indice_cobertura("SP", 1000, 50)
        assert resultado["nivel"] == "ALTO"
        assert resultado["indice"] == 1.0

    def test_indice_medio(self) -> None:
        """n_amostras=500, n_categorias=25 → MEDIO."""
        resultado = service.calcular_indice_cobertura("GO", 500, 25)
        assert resultado["nivel"] == "MEDIO"

    def test_indice_baixo(self) -> None:
        """n_amostras=100, n_categorias=10 → BAIXO."""
        resultado = service.calcular_indice_cobertura("BA", 100, 10)
        assert resultado["nivel"] == "BAIXO"


class TestCoberturaAPI:
    """Testes dos endpoints de cobertura."""

    def test_api_ufs_ok(self) -> None:
        """GET /cobertura/ufs retorna 200."""
        resp = client.get("/api/v1/cobertura/ufs")
        assert resp.status_code == 200
        assert "DF" in resp.json()

    def test_api_municipios_ok(self) -> None:
        """GET /cobertura/municipios retorna 200."""
        resp = client.get("/api/v1/cobertura/municipios?uf=GO")
        assert resp.status_code == 200
        assert len(resp.json()) >= 10

    def test_api_indice_ok(self) -> None:
        """GET /cobertura/indice retorna 200 com nível."""
        resp = client.get("/api/v1/cobertura/indice?uf=SP&n_amostras=1000&n_categorias=50")
        assert resp.status_code == 200
        assert resp.json()["nivel"] == "ALTO"
