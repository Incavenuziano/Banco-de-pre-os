"""Testes dos endpoints admin aprimorados — Semana 17."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAdminMetricas:
    """Testes do endpoint GET /api/v1/admin/metricas."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/admin/metricas")
        assert resp.status_code == 200

    def test_retorna_consultas_total(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert "consultas_total" in data

    def test_retorna_p50(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert "p50_ms" in data

    def test_retorna_p95(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert "p95_ms" in data

    def test_retorna_total_requests(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert "total_requests" in data

    def test_retorna_erros_total(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert "erros_total" in data


class TestAdminSaude:
    """Testes do endpoint GET /api/v1/admin/saude."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/admin/saude")
        assert resp.status_code == 200

    def test_status_ok(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert data["status"] == "ok"

    def test_componentes_presentes(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert "componentes" in data
        assert "database" in data["componentes"]
        assert "pgvector" in data["componentes"]
        assert "ibge_api" in data["componentes"]
        assert "filesystem" in data["componentes"]

    def test_uptime_presente(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert "uptime_segundos" in data
        assert data["uptime_segundos"] > 0

    def test_versao_presente(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert "versao" in data

    def test_database_ok(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert data["componentes"]["database"]["status"] == "ok"

    def test_pgvector_ok(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert data["componentes"]["pgvector"]["status"] == "ok"


class TestAdminAuditoriaPaginada:
    """Testes da auditoria paginada."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/admin/auditoria")
        assert resp.status_code == 200

    def test_retorna_estrutura_paginada(self) -> None:
        data = client.get("/api/v1/admin/auditoria").json()
        assert "total" in data
        assert "pagina" in data
        assert "eventos" in data
