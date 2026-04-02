"""Testes para o conector PNCP.

Todas as chamadas HTTP são mockadas — nenhuma requisição real é feita.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.pncp_conector import PNCPConector


@pytest.fixture
def conector() -> PNCPConector:
    """Fixture para o conector PNCP."""
    return PNCPConector()


class TestBuscarContratacoes:
    """Testes para buscar_contratacoes."""

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_contratacoes_sucesso(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna JSON quando a API responde 200."""
        dados_esperados = {
            "data": [{"cnpjOrgao": "12345678000190", "anoCompra": 2025}],
            "totalRegistros": 1,
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = dados_esperados
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        resultado = conector.buscar_contratacoes(uf="GO", municipio="Anápolis", data_inicio="20250101", data_fim="20250331")

        assert resultado == dados_esperados
        mock_get.assert_called_once()

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_contratacoes_timeout(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna fallback vazio em caso de Timeout persistente."""
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        resultado = conector.buscar_contratacoes(uf="GO", municipio="Anápolis", data_inicio="20250101", data_fim="20250331")

        assert resultado == {"data": [], "totalRegistros": 0}

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_contratacoes_erro_http(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna fallback vazio quando API retorna 500."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_get.return_value = mock_resp

        resultado = conector.buscar_contratacoes(uf="GO", data_inicio="20250101", data_fim="20250331")

        assert resultado == {"data": [], "totalRegistros": 0}


class TestBuscarItens:
    """Testes para buscar_itens_contratacao."""

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_itens_sucesso(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna lista de itens quando API responde 200."""
        itens = [
            {"descricao": "PAPEL A4", "valorUnitarioEstimado": 22.50},
            {"descricao": "DETERGENTE 500ML", "valorUnitarioEstimado": 2.80},
        ]
        mock_resp = MagicMock()
        mock_resp.json.return_value = itens
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        resultado = conector.buscar_itens_contratacao("12345678000190", 2025, 1)

        assert resultado == itens
        assert len(resultado) == 2

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_itens_erro(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna lista vazia em caso de exceção."""
        mock_get.side_effect = Exception("erro genérico")

        resultado = conector.buscar_itens_contratacao("12345678000190", 2025, 1)

        assert resultado == []


class TestBuscarResultado:
    """Testes para buscar_resultado_item."""

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_resultado_sucesso(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna dicionário de resultado quando API responde 200."""
        resultado_esperado = {"valorHomologado": 22.50, "situacao": "HOMOLOGADO"}
        mock_resp = MagicMock()
        mock_resp.json.return_value = resultado_esperado
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        resultado = conector.buscar_resultado_item("12345678000190", 2025, 1, 1)

        assert resultado == resultado_esperado

    @patch("app.services.pncp_conector.requests.get")
    def test_buscar_resultado_none(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Retorna None quando API retorna 404."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_get.return_value = mock_resp

        resultado = conector.buscar_resultado_item("12345678000190", 2025, 1, 1)

        assert resultado is None


class TestRetry:
    """Testes para mecanismo de retry."""

    @patch("app.services.pncp_conector.requests.get")
    def test_retry_em_timeout(self, mock_get: MagicMock, conector: PNCPConector) -> None:
        """Na 1ª chamada dá Timeout, na 2ª retorna sucesso."""
        dados_ok = {"data": [{"id": 1}], "totalRegistros": 1}
        mock_resp_ok = MagicMock()
        mock_resp_ok.json.return_value = dados_ok
        mock_resp_ok.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.exceptions.Timeout("timeout"),
            mock_resp_ok,
        ]

        resultado = conector.buscar_contratacoes(uf="GO", data_inicio="20250101", data_fim="20250331")

        assert resultado == dados_ok
        assert mock_get.call_count == 2
