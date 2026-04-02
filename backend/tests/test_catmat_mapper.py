"""Testes unitários do mapeamento CATMAT/CATSER."""

import pytest

from app.services.catmat_mapper import mapear_catmat, listar_codigos


class TestMapearCatmat:
    """Testes para mapear_catmat."""

    def test_codigo_valido_papel(self) -> None:
        r = mapear_catmat(16884)
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"
        assert r["confianca"] == 0.95

    def test_codigo_valido_gasolina(self) -> None:
        r = mapear_catmat(15121)
        assert r is not None
        assert r["categoria_nome"] == "Gasolina Comum"

    def test_codigo_valido_como_string(self) -> None:
        r = mapear_catmat("21181")
        assert r is not None
        assert r["categoria_nome"] == "Detergente"

    def test_codigo_invalido(self) -> None:
        r = mapear_catmat(99999999)
        assert r is None

    def test_codigo_none(self) -> None:
        r = mapear_catmat(None)
        assert r is None

    def test_codigo_texto_invalido(self) -> None:
        r = mapear_catmat("abc")
        assert r is None

    def test_com_resolucao_categoria_id(self) -> None:
        cats = [{"id": 42, "nome": "Papel A4"}]
        r = mapear_catmat(16884, categorias=cats)
        assert r is not None
        assert r["categoria_id"] == 42

    def test_sem_resolucao_categoria_id(self) -> None:
        r = mapear_catmat(16884)
        assert r is not None
        assert r["categoria_id"] is None

    def test_retorna_confianca(self) -> None:
        r = mapear_catmat(22632)  # Medicamento Genérico — confiança menor
        assert r is not None
        assert r["confianca"] == 0.80


class TestListarCodigos:
    """Testes para listar_codigos."""

    def test_retorna_dict(self) -> None:
        codigos = listar_codigos()
        assert isinstance(codigos, dict)

    def test_quantidade_minima(self) -> None:
        """Deve ter pelo menos 30 códigos mapeados."""
        codigos = listar_codigos()
        assert len(codigos) >= 30
