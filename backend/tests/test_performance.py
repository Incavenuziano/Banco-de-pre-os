"""Testes de performance — endpoints críticos devem responder < 2s."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

HEADERS_ADMIN = {"Authorization": "Bearer admin-token-test"}


def _duracao(func) -> float:
    t0 = time.perf_counter()
    func()
    return time.perf_counter() - t0


# ── Endpoints de análise ──────────────────────────────────────────────────────

class TestPerformanceAnalise:
    def test_listar_precos_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/precos"))
        assert d < 5.0, f"listar_precos demorou {d:.3f}s"

    def test_listar_precos_com_filtro_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/precos?categoria=Papel+A4"))
        assert d < 5.0, f"listar_precos filtrado demorou {d:.3f}s"

    def test_tendencias_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/tendencias"))
        assert d < 5.0, f"tendencias demorou {d:.3f}s"

    def test_comparativo_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/comparativo"))
        assert d < 5.0, f"comparativo demorou {d:.3f}s"

    def test_dashboard_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/dashboard"))
        assert d < 5.0, f"dashboard demorou {d:.3f}s"

    def test_categorias_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/categorias"))
        assert d < 5.0, f"categorias demorou {d:.3f}s"

    def test_ufs_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/analise/ufs"))
        assert d < 5.0, f"ufs demorou {d:.3f}s"


# ── Endpoints de correção monetária ──────────────────────────────────────────

class TestPerformanceCorrecao:
    def test_fator_ipca_rapido(self) -> None:
        d = _duracao(lambda: client.get(
            "/api/v1/correcao/fator?data_inicio=2020-01-01&data_fim=2025-01-01"
        ))
        assert d < 5.0, f"fator_ipca demorou {d:.3f}s"

    def test_serie_ipca_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/correcao/ipca"))
        assert d < 5.0, f"serie_ipca demorou {d:.3f}s"

    def test_corrigir_preco_rapido(self) -> None:
        d = _duracao(lambda: client.post(
            "/api/v1/correcao/preco",
            json={"valor": 100.0, "data_origem": "2020-01-01", "data_destino": "2025-01-01"},
        ))
        assert d < 5.0, f"corrigir_preco demorou {d:.3f}s"


# ── Endpoints públicos ────────────────────────────────────────────────────────

class TestPerformancePublico:
    def _gerar_key(self) -> str:
        r = client.post("/api/v1/public/keys/gerar?nome=perf-test&tenant_id=perf")
        assert r.status_code == 200, f"Falha ao gerar key: {r.text}"
        return r.json()["key"]

    def test_precos_publicos_rapido(self) -> None:
        key = self._gerar_key()
        d = _duracao(lambda: client.get(
            "/api/v1/public/precos", headers={"x-api-key": key}
        ))
        assert d < 5.0, f"precos_publicos demorou {d:.3f}s"

    def test_categorias_publicas_rapido(self) -> None:
        key = self._gerar_key()
        d = _duracao(lambda: client.get(
            "/api/v1/public/categorias", headers={"x-api-key": key}
        ))
        assert d < 5.0, f"categorias_publicas demorou {d:.3f}s"

    def test_ipca_fator_publico_rapido(self) -> None:
        key = self._gerar_key()
        d = _duracao(lambda: client.get(
            "/api/v1/public/ipca/fator?data_inicio=2020-01-01&data_fim=2025-01-01",
            headers={"x-api-key": key},
        ))
        assert d < 5.0, f"ipca_fator_publico demorou {d:.3f}s"


# ── Endpoints de busca ────────────────────────────────────────────────────────

class TestPerformanceBusca:
    def test_busca_full_text_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/busca/full-text?q=papel"))
        assert d < 5.0, f"busca_full_text demorou {d:.3f}s"

    def test_busca_semantica_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/busca/semantica?q=caneta"))
        assert d < 5.0, f"busca_semantica demorou {d:.3f}s"

    def test_busca_combinada_rapido(self) -> None:
        d = _duracao(lambda: client.get("/api/v1/busca/combinada?q=detergente"))
        assert d < 5.0, f"busca_combinada demorou {d:.3f}s"
