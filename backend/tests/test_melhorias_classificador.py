"""Testes das melhorias do classificador regex — sinônimos e sugestão de correção."""

import pytest

from app.services.classificador_regex import ClassificadorRegex


@pytest.fixture
def classificador() -> ClassificadorRegex:
    """Instância do classificador."""
    return ClassificadorRegex()


class TestSinonimos:
    """Testes de sinônimos adicionados."""

    def test_sinonimo_papel_sulfite(self, classificador: ClassificadorRegex) -> None:
        """'papel sulfite 75g' deve ser classificado como Papel A4."""
        r = classificador.classificar("papel sulfite 75g")
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"

    def test_sinonimo_combustivel(self, classificador: ClassificadorRegex) -> None:
        """'oleo diesel s-10' deve ser classificado como Diesel S10."""
        r = classificador.classificar("oleo diesel s-10")
        assert r is not None
        assert r["categoria_nome"] == "Diesel S10"

    def test_sinonimo_papel_xerox(self, classificador: ClassificadorRegex) -> None:
        """'papel xerox' deve ser classificado como Papel A4."""
        r = classificador.classificar("papel xerox")
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"

    def test_sinonimo_limpador(self, classificador: ClassificadorRegex) -> None:
        """'limpador multiuso' deve ser classificado como Detergente."""
        r = classificador.classificar("limpador multiuso")
        assert r is not None
        assert r["categoria_nome"] == "Detergente"

    def test_sinonimo_cartucho_hp(self, classificador: ClassificadorRegex) -> None:
        """'cartucho hp 662' deve ser classificado como Cartucho de Tinta."""
        r = classificador.classificar("cartucho hp 662")
        assert r is not None
        assert r["categoria_nome"] == "Cartucho de Tinta"


class TestSugerirCorrecao:
    """Testes do método sugerir_correcao."""

    def test_sugerir_correcao_sem_categoria(self, classificador: ClassificadorRegex) -> None:
        """Sem resultado → sugere revisão manual."""
        r = classificador.sugerir_correcao("item genérico", None)
        assert r["sugestao"] == "revisão manual"
        assert r["motivo"] == "sem categoria identificada"
        assert r["confianca_esperada"] == 0.0

    def test_sugerir_correcao_score_baixo(self, classificador: ClassificadorRegex) -> None:
        """Score < 0.8 → sugere verificar manualmente."""
        resultado = {"categoria_nome": "Teste", "score": 0.5}
        r = classificador.sugerir_correcao("item", resultado)
        assert r["sugestao"] == "verificar categoria manualmente"
        assert r["motivo"] == "score baixo"

    def test_sugerir_correcao_ok(self, classificador: ClassificadorRegex) -> None:
        """Score >= 0.8 → sem sugestão (ok)."""
        resultado = {"categoria_nome": "Papel A4", "score": 1.0}
        r = classificador.sugerir_correcao("papel a4", resultado)
        assert r["sugestao"] is None
        assert r["motivo"] is None
        assert r["confianca_esperada"] == 1.0
