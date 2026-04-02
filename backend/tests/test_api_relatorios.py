"""Testes para o router de relatórios."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload_basico(**kwargs) -> dict:
    """Cria payload mínimo para geração de relatório."""
    defaults = {
        "orgao_nome": "Prefeitura de Teste",
        "item_descricao": "Papel A4",
        "periodo_inicio": "2025-01-01",
        "periodo_fim": "2025-12-31",
        "id_relatorio": str(uuid.uuid4()),
        "emitido_em": "2025-06-01T10:00:00",
        "confianca": "ALTA",
        "estatisticas": {"n": 0},
    }
    defaults.update(kwargs)
    return defaults


class TestApiRelatorios:
    """Testes para os endpoints de relatórios."""

    def test_post_gerar_retorna_pdf(self) -> None:
        """Verifica que POST /gerar retorna status 200 com conteúdo PDF."""
        resp = client.post("/api/v1/relatorios/gerar", json=_payload_basico())
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"

    def test_post_gerar_content_type_pdf(self) -> None:
        """Verifica que o content-type da resposta é application/pdf."""
        resp = client.post("/api/v1/relatorios/gerar", json=_payload_basico())
        assert resp.headers["content-type"] == "application/pdf"

    def test_post_gerar_campos_minimos(self) -> None:
        """Verifica que o endpoint aceita payload com apenas campos obrigatórios."""
        payload = {
            "orgao_nome": "Órgão Mínimo",
            "item_descricao": "Item teste",
            "periodo_inicio": "2025-01-01",
            "periodo_fim": "2025-12-31",
            "id_relatorio": str(uuid.uuid4()),
            "emitido_em": "2025-06-01T10:00:00",
        }
        resp = client.post("/api/v1/relatorios/gerar", json=payload)
        assert resp.status_code == 200

    def test_get_preview_retorna_json(self) -> None:
        """Verifica que GET /preview/{id} retorna JSON com dados do relatório."""
        id_rel = str(uuid.uuid4())
        resp = client.get(f"/api/v1/relatorios/preview/{id_rel}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id_relatorio"] == id_rel
        assert "dados" in data

    def test_post_gerar_sem_amostras(self) -> None:
        """Verifica que gerar relatório sem amostras funciona corretamente."""
        payload = _payload_basico(amostras=[])
        resp = client.post("/api/v1/relatorios/gerar", json=payload)
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"
