"""Testes para o router de administração (/api/v1/admin)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMetricas:
    """Testes do endpoint /api/v1/admin/metricas."""

    def test_get_metricas_ok(self) -> None:
        resp = client.get("/api/v1/admin/metricas")
        assert resp.status_code == 200

    def test_metricas_tem_campos_detalhados(self) -> None:
        resp = client.get("/api/v1/admin/metricas")
        data = resp.json()
        assert "total_requests" in data or "consultas_total" in data

    def test_metricas_retorna_json(self) -> None:
        resp = client.get("/api/v1/admin/metricas")
        assert resp.headers.get("content-type", "").startswith("application/json")


class TestSaude:
    """Testes do endpoint /api/v1/admin/saude."""

    def test_get_saude_ok(self) -> None:
        resp = client.get("/api/v1/admin/saude")
        assert resp.status_code == 200

    def test_saude_tem_componentes(self) -> None:
        resp = client.get("/api/v1/admin/saude")
        data = resp.json()
        assert "componentes" in data or "status" in data

    def test_saude_retorna_status(self) -> None:
        resp = client.get("/api/v1/admin/saude")
        data = resp.json()
        assert "status" in data


class TestAuditoria:
    """Testes do endpoint /api/v1/admin/auditoria."""

    def test_get_auditoria_ok(self) -> None:
        resp = client.get("/api/v1/admin/auditoria")
        assert resp.status_code == 200

    def test_auditoria_paginacao(self) -> None:
        resp = client.get("/api/v1/admin/auditoria", params={"pagina": 1, "por_pagina": 10})
        data = resp.json()
        assert "total" in data
        assert "eventos" in data
        assert data["pagina"] == 1

    def test_auditoria_export_csv(self) -> None:
        resp = client.get("/api/v1/admin/auditoria/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_auditoria_export_filename(self) -> None:
        resp = client.get("/api/v1/admin/auditoria/export")
        cd = resp.headers.get("content-disposition", "")
        assert "auditoria.csv" in cd

    def test_auditoria_filtro_entidade(self) -> None:
        resp = client.get("/api/v1/admin/auditoria", params={"entidade": "usuario"})
        assert resp.status_code == 200


class TestRateLimit:
    """Testes do endpoint /api/v1/admin/rate-limit/status."""

    def test_get_rate_limit_status_ok(self) -> None:
        resp = client.get("/api/v1/admin/rate-limit/status", params={"key": "teste_admin"})
        assert resp.status_code == 200

    def test_rate_limit_retorna_campos(self) -> None:
        resp = client.get("/api/v1/admin/rate-limit/status", params={"key": "teste_campos"})
        data = resp.json()
        assert "permitido" in data
        assert "restante" in data

    def test_rate_limit_key_obrigatorio(self) -> None:
        resp = client.get("/api/v1/admin/rate-limit/status")
        assert resp.status_code == 422
