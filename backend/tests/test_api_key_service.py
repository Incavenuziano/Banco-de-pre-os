"""Testes do serviço de API keys — Semana 19."""

from __future__ import annotations

import pytest

from app.services.api_key_service import ApiKeyService


@pytest.fixture
def svc() -> ApiKeyService:
    s = ApiKeyService()
    s.limpar()
    return s


class TestGerar:
    """Testes de gerar()."""

    def test_retorna_dict(self, svc: ApiKeyService) -> None:
        r = svc.gerar("Teste")
        assert isinstance(r, dict)

    def test_key_prefixo(self, svc: ApiKeyService) -> None:
        r = svc.gerar("Teste")
        assert r["key"].startswith("laas_")

    def test_key_unica(self, svc: ApiKeyService) -> None:
        r1 = svc.gerar("A")
        r2 = svc.gerar("B")
        assert r1["key"] != r2["key"]

    def test_nome_preservado(self, svc: ApiKeyService) -> None:
        r = svc.gerar("Minha App")
        assert r["nome"] == "Minha App"

    def test_tenant_id(self, svc: ApiKeyService) -> None:
        r = svc.gerar("App", tenant_id="t1")
        assert r["tenant_id"] == "t1"

    def test_id_presente(self, svc: ApiKeyService) -> None:
        r = svc.gerar("App")
        assert "id" in r

    def test_scopes_padrao(self, svc: ApiKeyService) -> None:
        r = svc.gerar("App")
        assert "read" in r["scopes"]


class TestValidar:
    """Testes de validar()."""

    def test_key_valida(self, svc: ApiKeyService) -> None:
        key = svc.gerar("App")["key"]
        r = svc.validar(key)
        assert r is not None

    def test_key_inexistente(self, svc: ApiKeyService) -> None:
        r = svc.validar("inexistente")
        assert r is None

    def test_key_revogada_invalida(self, svc: ApiKeyService) -> None:
        data = svc.gerar("App")
        svc.revogar(data["id"])
        r = svc.validar(data["key"])
        assert r is None

    def test_incrementa_uso(self, svc: ApiKeyService) -> None:
        data = svc.gerar("App")
        svc.validar(data["key"])
        svc.validar(data["key"])
        meta = svc.obter(data["id"])
        assert meta["uso_total"] == 2

    def test_retorna_nome(self, svc: ApiKeyService) -> None:
        data = svc.gerar("MeuApp")
        r = svc.validar(data["key"])
        assert r["nome"] == "MeuApp"


class TestRevogar:
    """Testes de revogar()."""

    def test_revogar_existente(self, svc: ApiKeyService) -> None:
        data = svc.gerar("App")
        assert svc.revogar(data["id"]) is True

    def test_revogar_inexistente(self, svc: ApiKeyService) -> None:
        assert svc.revogar("xxx") is False


class TestListar:
    """Testes de listar()."""

    def test_lista_vazia_inicial(self, svc: ApiKeyService) -> None:
        assert svc.listar() == []

    def test_lista_apos_gerar(self, svc: ApiKeyService) -> None:
        svc.gerar("App1")
        svc.gerar("App2")
        assert len(svc.listar()) == 2

    def test_filtro_tenant(self, svc: ApiKeyService) -> None:
        svc.gerar("A", tenant_id="t1")
        svc.gerar("B", tenant_id="t2")
        assert len(svc.listar("t1")) == 1


class TestObter:
    """Testes de obter()."""

    def test_key_existente(self, svc: ApiKeyService) -> None:
        data = svc.gerar("App")
        r = svc.obter(data["id"])
        assert r is not None
        assert r["nome"] == "App"

    def test_key_inexistente(self, svc: ApiKeyService) -> None:
        r = svc.obter("xxx")
        assert r is None
