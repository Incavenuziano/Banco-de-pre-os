"""Testes para o serviço e API de dashboard."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.dashboard_service import DashboardService

client = TestClient(app)
service = DashboardService()


class TestDashboardService:
    """Testes do DashboardService."""

    def test_resumo_retorna_dict(self) -> None:
        """obter_resumo retorna dicionário."""
        resultado = service.obter_resumo("t1")
        assert isinstance(resultado, dict)

    def test_resumo_tem_campos_obrigatorios(self) -> None:
        """Resumo contém todos os campos esperados."""
        resultado = service.obter_resumo("t1")
        for campo in [
            "total_consultas",
            "total_relatorios",
            "categorias_mais_buscadas",
            "cobertura_ufs",
            "media_score_confianca",
        ]:
            assert campo in resultado

    def test_historico_retorna_lista(self) -> None:
        """obter_historico_consultas retorna lista."""
        resultado = service.obter_historico_consultas("t1", dias=7)
        assert isinstance(resultado, list)

    def test_historico_tamanho_correto(self) -> None:
        """Histórico com dias=7 retorna exatamente 7 entradas."""
        resultado = service.obter_historico_consultas("t1", dias=7)
        assert len(resultado) == 7

    def test_cobertura_tem_total(self) -> None:
        """Cobertura contém campo total_categorias."""
        resultado = service.obter_cobertura_categorias()
        assert "total_categorias" in resultado
        assert resultado["total_categorias"] > 0

    def test_cobertura_categorias_nao_vazia(self) -> None:
        """Lista de categorias na cobertura não é vazia."""
        resultado = service.obter_cobertura_categorias()
        assert len(resultado["por_categoria"]) > 0


class TestDashboardAPI:
    """Testes dos endpoints de dashboard."""

    def test_api_resumo_ok(self) -> None:
        """GET /dashboard/resumo retorna 200."""
        resp = client.get("/api/v1/dashboard/resumo?tenant_id=t1")
        assert resp.status_code == 200
        assert "total_consultas" in resp.json()

    def test_api_historico_ok(self) -> None:
        """GET /dashboard/historico retorna 200."""
        resp = client.get("/api/v1/dashboard/historico?tenant_id=t1&dias=7")
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    def test_api_cobertura_ok(self) -> None:
        """GET /dashboard/cobertura retorna 200."""
        resp = client.get("/api/v1/dashboard/cobertura")
        assert resp.status_code == 200
        assert "total_categorias" in resp.json()

    def test_api_admin_status_ok(self) -> None:
        """GET /dashboard/admin/status retorna 200 com versão."""
        resp = client.get("/api/v1/dashboard/admin/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "versao" in data
        assert data["testes_ok"] is True
