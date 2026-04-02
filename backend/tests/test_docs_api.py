"""Testes para a API de documentação técnica."""

from __future__ import annotations

import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_DOCS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "docs"
)


class TestDocsAPI:
    """Testes dos endpoints de documentação."""

    def test_get_changelog_retorna_lista(self) -> None:
        """GET /docs/changelog retorna lista."""
        resp = client.get("/api/v1/docs/changelog")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_changelog_tem_versao(self) -> None:
        """Changelog contém entrada com campo versao."""
        resp = client.get("/api/v1/docs/changelog")
        data = resp.json()
        assert len(data) > 0
        assert "versao" in data[0]

    def test_get_metodologia_retorna_string(self) -> None:
        """GET /docs/metodologia retorna string com conteúdo."""
        resp = client.get("/api/v1/docs/metodologia")
        assert resp.status_code == 200
        assert "Metodologia" in resp.json()

    def test_get_compliance_retorna_dict(self) -> None:
        """GET /docs/compliance retorna dict com normas."""
        resp = client.get("/api/v1/docs/compliance")
        assert resp.status_code == 200
        data = resp.json()
        assert "normas_aplicaveis" in data
        assert len(data["normas_aplicaveis"]) >= 2


class TestDocsArquivos:
    """Testes de existência dos arquivos de documentação."""

    def test_metodologia_md_existe(self) -> None:
        """Arquivo METODOLOGIA.md existe."""
        caminho = os.path.join(_DOCS_DIR, "METODOLOGIA.md")
        assert os.path.isfile(caminho)

    def test_playbook_md_existe(self) -> None:
        """Arquivo PLAYBOOK_OPERACIONAL.md existe."""
        caminho = os.path.join(_DOCS_DIR, "PLAYBOOK_OPERACIONAL.md")
        assert os.path.isfile(caminho)
