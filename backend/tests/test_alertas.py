"""Testes para o serviço e API de alertas de sobrepreço."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.alerta_service import AlertaService

client = TestClient(app)
service = AlertaService()


class TestAlertaService:
    """Testes do AlertaService."""

    def test_alerta_critico(self) -> None:
        """Preço 2x a mediana → CRITICO."""
        resultado = service.analisar_preco(200.0, {"mediana": 100.0})
        assert resultado["alerta"] is True
        assert resultado["nivel"] == "CRITICO"

    def test_alerta_atencao(self) -> None:
        """Preço 1.3x a mediana → ATENCAO."""
        resultado = service.analisar_preco(130.0, {"mediana": 100.0})
        assert resultado["alerta"] is True
        assert resultado["nivel"] == "ATENCAO"

    def test_alerta_ok(self) -> None:
        """Preço igual à mediana → OK."""
        resultado = service.analisar_preco(100.0, {"mediana": 100.0})
        assert resultado["alerta"] is False
        assert resultado["nivel"] == "OK"

    def test_alerta_preco_abaixo(self) -> None:
        """Preço 0.8x mediana → OK."""
        resultado = service.analisar_preco(80.0, {"mediana": 100.0})
        assert resultado["alerta"] is False
        assert resultado["nivel"] == "OK"

    def test_relatorio_alertas_conta_criticos(self) -> None:
        """Relatório conta corretamente os críticos."""
        itens = [
            {"descricao": "Item A", "preco_proposto": 200.0, "estatisticas": {"mediana": 100.0}},
            {"descricao": "Item B", "preco_proposto": 100.0, "estatisticas": {"mediana": 100.0}},
        ]
        resultado = service.gerar_relatorio_alertas(itens)
        assert resultado["criticos"] == 1
        assert resultado["ok"] == 1
        assert resultado["total"] == 2

    def test_relatorio_alertas_lista_vazia(self) -> None:
        """Relatório com lista vazia retorna totais zerados."""
        resultado = service.gerar_relatorio_alertas([])
        assert resultado["total"] == 0
        assert resultado["criticos"] == 0

    def test_economia_positiva(self) -> None:
        """Economia positiva quando proposto > referencial."""
        resultado = service.calcular_economia_potencial(150.0, 100.0, 10)
        assert resultado["economia_total"] == 500.0
        assert resultado["viavel"] is True

    def test_economia_nula(self) -> None:
        """Economia zero quando proposto == referencial."""
        resultado = service.calcular_economia_potencial(100.0, 100.0, 10)
        assert resultado["economia_total"] == 0.0
        assert resultado["viavel"] is False


class TestAlertasAPI:
    """Testes dos endpoints de alertas."""

    def test_api_analisar_ok(self) -> None:
        """POST /alertas/analisar retorna 200."""
        resp = client.post(
            "/api/v1/alertas/analisar",
            json={"preco_proposto": 150.0, "estatisticas": {"mediana": 100.0}},
        )
        assert resp.status_code == 200
        assert "nivel" in resp.json()

    def test_api_economia_ok(self) -> None:
        """POST /alertas/economia retorna 200."""
        resp = client.post(
            "/api/v1/alertas/economia",
            json={"preco_proposto": 150.0, "preco_referencial": 100.0, "quantidade": 10},
        )
        assert resp.status_code == 200
        assert resp.json()["economia_total"] == 500.0
