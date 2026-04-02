"""Testes de performance — Semana 20.

Verifica que endpoints críticos respondem em tempo aceitável.
"""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _medir_tempo(fn) -> float:
    """Mede tempo de execução em segundos."""
    inicio = time.perf_counter()
    fn()
    return time.perf_counter() - inicio


class TestPerformanceEndpoints:
    """Testes de performance — endpoints devem responder < 2s."""

    def test_health_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/health"))
        assert t < 2.0

    def test_precos_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/analise/precos"))
        assert t < 2.0

    def test_categorias_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/analise/categorias"))
        assert t < 2.0

    def test_tendencias_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get(
            "/api/v1/analise/tendencias", params={"categoria": "Papel A4"}
        ))
        assert t < 2.0

    def test_comparativo_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get(
            "/api/v1/analise/comparativo", params={"categoria": "Papel A4"}
        ))
        assert t < 2.0

    def test_ipca_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/correcao/ipca"))
        assert t < 2.0

    def test_fator_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get(
            "/api/v1/correcao/fator",
            params={"data_inicio": "2020-01-01", "data_fim": "2025-01-01"}
        ))
        assert t < 2.0

    def test_benchmark_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get(
            "/api/v1/analise/benchmark/uf", params={"categoria": "Papel A4"}
        ))
        assert t < 2.0

    def test_busca_semantica_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get(
            "/api/v1/busca/semantica", params={"q": "papel sulfite"}
        ))
        assert t < 2.0

    def test_dashboard_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/analise/dashboard"))
        assert t < 2.0

    def test_export_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/admin/export"))
        assert t < 2.0

    def test_precos_corrigidos_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/analise/precos-corrigidos"))
        assert t < 2.0

    def test_public_precos_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/public/precos"))
        assert t < 2.0

    def test_metricas_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/admin/metricas"))
        assert t < 2.0

    def test_saude_rapido(self) -> None:
        t = _medir_tempo(lambda: client.get("/api/v1/admin/saude"))
        assert t < 2.0
