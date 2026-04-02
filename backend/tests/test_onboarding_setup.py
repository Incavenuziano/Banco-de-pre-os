"""Testes do endpoint de setup wizard — Semana 19."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSetupWizard:
    """Testes do endpoint POST /api/v1/onboarding/setup."""

    def test_status_200(self) -> None:
        resp = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Prefeitura Teste",
            "email_admin": "admin@teste.gov.br",
        })
        assert resp.status_code == 200

    def test_retorna_status_ok(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org Test",
            "email_admin": "test@org.br",
        }).json()
        assert data["status"] == "ok"

    def test_retorna_tenant(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
        }).json()
        assert "tenant" in data

    def test_retorna_configuracoes(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
        }).json()
        assert "configuracoes" in data
        assert "ufs_interesse" in data["configuracoes"]

    def test_retorna_proximos_passos(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
        }).json()
        assert "proximos_passos" in data
        assert len(data["proximos_passos"]) > 0

    def test_ufs_customizadas(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
            "ufs_interesse": ["BA", "PE"],
        }).json()
        assert data["configuracoes"]["ufs_interesse"] == ["BA", "PE"]

    def test_plano_customizado(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
            "plano": "pro",
        }).json()
        assert data["tenant"]["plano"] == "pro"

    def test_categorias_interesse(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
            "categorias_interesse": ["Papel A4"],
        }).json()
        assert data["configuracoes"]["categorias_interesse"] == ["Papel A4"]

    def test_mensagem_sucesso(self) -> None:
        data = client.post("/api/v1/onboarding/setup", json={
            "nome_organizacao": "Org",
            "email_admin": "a@b.com",
        }).json()
        assert "concluído" in data["mensagem"] or "sucesso" in data["mensagem"]

    def test_sem_body_422(self) -> None:
        resp = client.post("/api/v1/onboarding/setup", json={})
        assert resp.status_code == 422
