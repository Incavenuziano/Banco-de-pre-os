"""Testes de auth aprimorado — Semana 17.

Cobre: refresh token, blacklist, expiração configurável.
"""

from __future__ import annotations

from app.services.auth_service import (
    gerar_refresh_token,
    gerar_token,
    limpar_blacklist,
    revogar_token,
    token_revogado,
    verificar_token,
)


class TestRefreshToken:
    """Testes do refresh token."""

    def test_gerar_refresh_retorna_string(self) -> None:
        token = gerar_refresh_token("user1", "tenant1")
        assert isinstance(token, str)

    def test_refresh_tem_3_partes(self) -> None:
        token = gerar_refresh_token("user1", "tenant1")
        assert len(token.split(".")) == 3

    def test_refresh_decodifica(self) -> None:
        token = gerar_refresh_token("user1", "tenant1")
        payload = verificar_token(token)
        assert payload is not None

    def test_refresh_tipo_correto(self) -> None:
        token = gerar_refresh_token("user1", "tenant1")
        payload = verificar_token(token)
        assert payload["tipo"] == "refresh"

    def test_refresh_usuario_correto(self) -> None:
        token = gerar_refresh_token("user42", "tenant7")
        payload = verificar_token(token)
        assert payload["sub"] == "user42"
        assert payload["tenant"] == "tenant7"


class TestBlacklist:
    """Testes da blacklist de tokens."""

    def setup_method(self) -> None:
        limpar_blacklist()

    def test_token_nao_revogado(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        assert not token_revogado(token)

    def test_revogar_token(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        revogar_token(token)
        assert token_revogado(token)

    def test_verificar_token_revogado_retorna_none(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        revogar_token(token)
        assert verificar_token(token) is None

    def test_token_nao_revogado_valida(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        assert verificar_token(token) is not None

    def test_limpar_blacklist(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        revogar_token(token)
        limpar_blacklist()
        assert not token_revogado(token)

    def test_multiplos_tokens_revogados(self) -> None:
        t1 = gerar_token("user1", "tenant1", "admin")
        t2 = gerar_token("user2", "tenant1", "viewer")
        revogar_token(t1)
        revogar_token(t2)
        assert token_revogado(t1)
        assert token_revogado(t2)

    def test_revogar_retorna_true(self) -> None:
        token = gerar_token("user1", "tenant1", "admin")
        assert revogar_token(token) is True
