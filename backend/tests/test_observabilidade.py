"""Testes para o serviço de observabilidade e endpoints de health/metrics."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.observabilidade_service import ObservabilidadeService

client = TestClient(app)


class TestObservabilidadeService:
    """Testes do ObservabilidadeService."""

    def test_registrar_consulta_incrementa(self) -> None:
        """registrar_consulta incrementa o contador."""
        svc = ObservabilidadeService()
        svc.registrar_consulta(50.0, True)
        assert svc.METRICAS["consultas_total"] == 1

    def test_registrar_relatorio_incrementa(self) -> None:
        """registrar_relatorio incrementa o contador."""
        svc = ObservabilidadeService()
        svc.registrar_relatorio(200.0, True)
        assert svc.METRICAS["relatorios_total"] == 1

    def test_registrar_erro_incrementa(self) -> None:
        """Consulta com sucesso=False incrementa erros."""
        svc = ObservabilidadeService()
        svc.registrar_consulta(100.0, False)
        assert svc.METRICAS["erros_total"] == 1

    def test_health_check_status_ok(self) -> None:
        """health_check retorna status 'ok'."""
        svc = ObservabilidadeService()
        resultado = svc.health_check()
        assert resultado["status"] == "ok"

    def test_health_check_tem_versao(self) -> None:
        """health_check contém campo versao."""
        svc = ObservabilidadeService()
        resultado = svc.health_check()
        assert "versao" in resultado

    def test_metricas_tempo_medio(self) -> None:
        """Tempo médio é calculado corretamente."""
        svc = ObservabilidadeService()
        svc.registrar_consulta(100.0, True)
        svc.registrar_consulta(200.0, True)
        assert svc.METRICAS["tempo_medio_ms"] == 150.0


class TestObservabilidadeAPI:
    """Testes dos endpoints de health e metrics."""

    def test_api_health_ok(self) -> None:
        """GET /health retorna 200."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_api_metrics_ok(self) -> None:
        """GET /metrics retorna 200 com métricas."""
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "consultas_total" in data
