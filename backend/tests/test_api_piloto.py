"""Testes para a API do piloto controlado.

Chamadas externas ao PNCP são mockadas — nenhuma requisição HTTP real.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPostExecutar:
    """Testes para POST /api/v1/piloto/executar."""

    @patch("app.routers.piloto.PNCPConector")
    def test_post_executar_aceita(self, mock_conector_cls: MagicMock) -> None:
        """Endpoint aceita requisição válida e retorna status 'accepted'."""
        mock_conector = MagicMock()
        mock_conector.buscar_contratacoes.return_value = {"data": [], "totalRegistros": 0}
        mock_conector_cls.return_value = mock_conector

        resp = client.post("/api/v1/piloto/executar", json={
            "uf": "GO",
            "municipio": "Anápolis",
            "data_inicio": "20250101",
            "data_fim": "20250331",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "Anápolis" in data["message"]

    def test_post_executar_campos_obrigatorios(self) -> None:
        """Retorna 422 quando campos obrigatórios estão ausentes."""
        resp = client.post("/api/v1/piloto/executar", json={
            "uf": "GO",
        })

        assert resp.status_code == 422

    @patch("app.routers.piloto.PNCPConector")
    def test_post_executar_resposta_tem_task_id(self, mock_conector_cls: MagicMock) -> None:
        """Resposta deve conter task_id como string UUID."""
        mock_conector = MagicMock()
        mock_conector.buscar_contratacoes.return_value = {"data": [], "totalRegistros": 0}
        mock_conector_cls.return_value = mock_conector

        resp = client.post("/api/v1/piloto/executar", json={
            "uf": "GO",
            "municipio": "Santo Antônio do Descoberto",
            "data_inicio": "20250101",
            "data_fim": "20250331",
        })

        data = resp.json()
        assert "task_id" in data
        assert isinstance(data["task_id"], str)
        assert len(data["task_id"]) > 0


class TestGetTopItens:
    """Testes para GET /api/v1/piloto/top-itens."""

    def test_get_top_itens_retorna_lista(self) -> None:
        """Endpoint retorna lista de itens mock."""
        resp = client.get("/api/v1/piloto/top-itens", params={
            "uf": "GO",
            "municipio": "Anápolis",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 20

        primeiro = data[0]
        assert "descricao_normalizada" in primeiro
        assert "categoria" in primeiro
        assert "ocorrencias" in primeiro
        assert "preco_mediano" in primeiro

    def test_get_top_itens_parametro_n(self) -> None:
        """Parâmetro n limita o número de itens retornados."""
        resp = client.get("/api/v1/piloto/top-itens", params={
            "uf": "GO",
            "municipio": "Anápolis",
            "n": 5,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5
