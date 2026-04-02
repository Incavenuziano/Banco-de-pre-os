"""Testes para autenticação — hash, JWT, login, refresh, /me."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import (
    gerar_token,
    hash_senha,
    verificar_senha,
    verificar_token,
)

client = TestClient(app)


class TestHashSenha:
    """Testes para hash e verificação de senha."""

    def test_hash_senha_deterministico(self) -> None:
        """Mesmo input gera mesmo hash."""
        assert hash_senha("abc") == hash_senha("abc")

    def test_verificar_senha_correta(self) -> None:
        """Senha correta é aceita."""
        h = hash_senha("minha_senha")
        assert verificar_senha("minha_senha", h) is True

    def test_verificar_senha_incorreta(self) -> None:
        """Senha incorreta é rejeitada."""
        h = hash_senha("minha_senha")
        assert verificar_senha("outra_senha", h) is False


class TestJWT:
    """Testes para geração e verificação de tokens JWT."""

    def test_gerar_token_retorna_string(self) -> None:
        """gerar_token retorna string com 3 partes separadas por ponto."""
        token = gerar_token("u1", "t1", "admin")
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_verificar_token_valido(self) -> None:
        """Token recém-gerado é validado com sucesso."""
        token = gerar_token("u1", "t1", "admin")
        payload = verificar_token(token)
        assert payload is not None
        assert payload["sub"] == "u1"
        assert payload["tenant"] == "t1"
        assert payload["papel"] == "admin"

    def test_verificar_token_invalido(self) -> None:
        """Token adulterado retorna None."""
        assert verificar_token("abc.def.ghi") is None

    def test_token_expirado(self) -> None:
        """Token com expiração no passado retorna None."""
        import time

        with patch("app.services.auth_service.time") as mock_time:
            # Gerar token "no passado"
            mock_time.time.return_value = 1000000.0
            token = gerar_token("u1", "t1", "admin")

        # Verificar "no presente" (muito depois da expiração)
        payload = verificar_token(token)
        assert payload is None


class TestLoginEndpoint:
    """Testes para o endpoint POST /api/v1/auth/login."""

    def test_login_sucesso(self) -> None:
        """Login com credenciais válidas retorna token e dados."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@teste.com", "senha": "senha123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["usuario"]["email"] == "admin@teste.com"
        assert data["usuario"]["papel"] == "admin"

    def test_login_senha_errada(self) -> None:
        """Login com senha errada retorna 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@teste.com", "senha": "errada"},
        )
        assert resp.status_code == 401

    def test_login_email_inexistente(self) -> None:
        """Login com e-mail inexistente retorna 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "naoexiste@teste.com", "senha": "qualquer"},
        )
        assert resp.status_code == 401


class TestRefreshEndpoint:
    """Testes para o endpoint POST /api/v1/auth/refresh."""

    def test_refresh_token_valido(self) -> None:
        """Refresh com token válido retorna novo token."""
        token = gerar_token("u1", "t1", "admin")
        resp = client.post("/api/v1/auth/refresh", json={"token": token})
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_refresh_token_invalido(self) -> None:
        """Refresh com token inválido retorna 401."""
        resp = client.post("/api/v1/auth/refresh", json={"token": "invalido"})
        assert resp.status_code == 401


class TestMeEndpoint:
    """Testes para o endpoint GET /api/v1/auth/me."""

    def test_get_me_com_token(self) -> None:
        """GET /me com token válido retorna dados do usuário."""
        token = gerar_token("u1", "t1", "admin")
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "u1"
        assert data["nome"] == "Admin Teste"

    def test_get_me_sem_token(self) -> None:
        """GET /me sem token retorna 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_token_invalido(self) -> None:
        """GET /me com token inválido retorna 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token_falso_xyz"},
        )
        assert resp.status_code == 401
