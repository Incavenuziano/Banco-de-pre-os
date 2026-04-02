"""Testes do serviço de backup e exportação — Semana 20."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.backup_service import BackupService

client = TestClient(app)


class TestBackupService:
    """Testes do BackupService."""

    def setup_method(self) -> None:
        self.svc = BackupService()

    def test_exportar_completo_retorna_dict(self) -> None:
        r = self.svc.exportar_completo()
        assert isinstance(r, dict)

    def test_exportar_tem_metadados(self) -> None:
        r = self.svc.exportar_completo()
        assert "metadados" in r
        assert "exportado_em" in r["metadados"]
        assert "versao" in r["metadados"]

    def test_exportar_tem_dados(self) -> None:
        r = self.svc.exportar_completo()
        assert "dados" in r
        assert "precos" in r["dados"]
        assert "categorias" in r["dados"]
        assert "ufs" in r["dados"]

    def test_exportar_tem_estatisticas(self) -> None:
        r = self.svc.exportar_completo()
        assert "estatisticas" in r
        assert "total_precos" in r["estatisticas"]

    def test_exportar_json_bytes(self) -> None:
        b = self.svc.exportar_json_bytes()
        assert isinstance(b, bytes)
        assert len(b) > 0

    def test_json_bytes_valido(self) -> None:
        b = self.svc.exportar_json_bytes()
        dados = json.loads(b)
        assert "metadados" in dados

    def test_validar_integridade(self) -> None:
        r = self.svc.validar_integridade()
        assert "status" in r
        assert r["status"] in ("ok", "problemas")

    def test_integridade_campos(self) -> None:
        r = self.svc.validar_integridade()
        assert "total_precos" in r
        assert "total_categorias" in r
        assert "total_ufs" in r
        assert "verificado_em" in r


class TestExportEndpoint:
    """Testes do endpoint GET /api/v1/admin/export."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/admin/export")
        assert resp.status_code == 200

    def test_content_type_json(self) -> None:
        resp = client.get("/api/v1/admin/export")
        assert "json" in resp.headers.get("content-type", "")

    def test_content_disposition(self) -> None:
        resp = client.get("/api/v1/admin/export")
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_body_valido(self) -> None:
        resp = client.get("/api/v1/admin/export")
        dados = resp.json()
        assert "metadados" in dados


class TestIntegridadeEndpoint:
    """Testes do endpoint GET /api/v1/admin/integridade."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/admin/integridade")
        assert resp.status_code == 200

    def test_retorna_status(self) -> None:
        data = client.get("/api/v1/admin/integridade").json()
        assert "status" in data
