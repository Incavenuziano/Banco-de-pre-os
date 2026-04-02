"""Testes para o serviço de auditoria."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.auditoria_service import AuditoriaService

client = TestClient(app)


class TestAuditoriaService:
    """Testes do AuditoriaService."""

    def test_registrar_evento(self) -> None:
        """registrar cria evento com todos os campos."""
        svc = AuditoriaService()
        evento = svc.registrar("usuario", "criar", "u1", {"nome": "Teste"})
        assert evento["entidade"] == "usuario"
        assert evento["acao"] == "criar"
        assert "id" in evento
        assert "timestamp" in evento

    def test_listar_todos(self) -> None:
        """listar sem filtros retorna todos os eventos."""
        svc = AuditoriaService()
        svc.registrar("usuario", "criar", "u1")
        svc.registrar("relatorio", "gerar", "u2")
        assert len(svc.listar()) == 2

    def test_listar_por_entidade(self) -> None:
        """listar com filtro de entidade retorna apenas matching."""
        svc = AuditoriaService()
        svc.registrar("usuario", "criar", "u1")
        svc.registrar("relatorio", "gerar", "u2")
        resultado = svc.listar(entidade="usuario")
        assert len(resultado) == 1
        assert resultado[0]["entidade"] == "usuario"

    def test_listar_por_usuario(self) -> None:
        """listar com filtro de usuario_id retorna apenas matching."""
        svc = AuditoriaService()
        svc.registrar("usuario", "criar", "u1")
        svc.registrar("usuario", "atualizar", "u2")
        resultado = svc.listar(usuario_id="u1")
        assert len(resultado) == 1

    def test_exportar_csv_tem_cabecalho(self) -> None:
        """exportar_csv inclui cabeçalho CSV."""
        svc = AuditoriaService()
        svc.registrar("usuario", "criar", "u1")
        csv = svc.exportar_csv()
        assert csv.startswith("id,entidade,acao,usuario_id,payload,timestamp")


class TestAuditoriaAPI:
    """Testes dos endpoints de auditoria."""

    def test_api_auditoria_ok(self) -> None:
        """GET /admin/auditoria retorna 200."""
        resp = client.get("/api/v1/admin/auditoria")
        assert resp.status_code == 200

    def test_api_export_csv(self) -> None:
        """GET /admin/auditoria/export retorna CSV."""
        resp = client.get("/api/v1/admin/auditoria/export")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
