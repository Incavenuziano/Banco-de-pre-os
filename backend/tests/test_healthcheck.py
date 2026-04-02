"""Testes de healthcheck — endpoint de saúde e verificações do sistema."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Testes do endpoint GET /health (root health check)."""

    def test_health_status_200(self) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_retorna_status(self) -> None:
        data = client.get("/health").json()
        assert "status" in data

    def test_health_status_ok(self) -> None:
        data = client.get("/health").json()
        assert data["status"] in ("ok", "healthy", "up")


class TestAdminSaudeEndpoint:
    """Testes do endpoint GET /api/v1/admin/saude."""

    def test_saude_status_200(self) -> None:
        resp = client.get("/api/v1/admin/saude")
        assert resp.status_code == 200

    def test_saude_retorna_dict(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert isinstance(data, dict)

    def test_saude_tem_status(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert "status" in data

    def test_saude_status_valido(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        assert data["status"] in ("ok", "degraded", "error", "healthy")

    def test_saude_tem_componentes(self) -> None:
        data = client.get("/api/v1/admin/saude").json()
        # deve ter algum campo além de status
        assert len(data) > 1

    def test_saude_resposta_rapida(self) -> None:
        import time
        t0 = time.perf_counter()
        client.get("/api/v1/admin/saude")
        assert time.perf_counter() - t0 < 2.0


class TestAdminMetricasEndpoint:
    """Testes do endpoint GET /api/v1/admin/metricas."""

    def test_metricas_status_200(self) -> None:
        resp = client.get("/api/v1/admin/metricas")
        assert resp.status_code == 200

    def test_metricas_retorna_dict(self) -> None:
        data = client.get("/api/v1/admin/metricas").json()
        assert isinstance(data, dict)

    def test_metricas_resposta_rapida(self) -> None:
        import time
        t0 = time.perf_counter()
        client.get("/api/v1/admin/metricas")
        assert time.perf_counter() - t0 < 2.0


class TestIntegridadeEndpoint:
    """Testes do endpoint GET /api/v1/admin/integridade."""

    def test_integridade_status_200(self) -> None:
        resp = client.get("/api/v1/admin/integridade")
        assert resp.status_code == 200

    def test_integridade_retorna_status(self) -> None:
        data = client.get("/api/v1/admin/integridade").json()
        assert "status" in data

    def test_integridade_campos_esperados(self) -> None:
        data = client.get("/api/v1/admin/integridade").json()
        assert "total_precos" in data or "problemas" in data
