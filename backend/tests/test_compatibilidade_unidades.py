"""Testes do serviço de compatibilidade de unidades."""

import pytest

from app.services.compatibilidade_unidades import CompatibilidadeUnidades


@pytest.fixture
def compat() -> CompatibilidadeUnidades:
    """Instância do serviço de compatibilidade."""
    return CompatibilidadeUnidades()


class TestConverterUnidades:
    """Testes para conversão de unidades."""

    def test_converter_ml_para_l(self, compat: CompatibilidadeUnidades) -> None:
        """500 ML → 0.5 L."""
        resultado = compat.converter(500.0, "ML", "L")
        assert resultado is not None
        assert abs(resultado - 0.5) < 1e-9

    def test_converter_l_para_ml(self, compat: CompatibilidadeUnidades) -> None:
        """2 L → 2000 ML."""
        resultado = compat.converter(2.0, "L", "ML")
        assert resultado is not None
        assert abs(resultado - 2000.0) < 1e-9

    def test_converter_g_para_kg(self, compat: CompatibilidadeUnidades) -> None:
        """1500 G → 1.5 KG."""
        resultado = compat.converter(1500.0, "G", "KG")
        assert resultado is not None
        assert abs(resultado - 1.5) < 1e-9

    def test_converter_kg_para_g(self, compat: CompatibilidadeUnidades) -> None:
        """3 KG → 3000 G."""
        resultado = compat.converter(3.0, "KG", "G")
        assert resultado is not None
        assert abs(resultado - 3000.0) < 1e-9

    def test_converter_incompativel_retorna_none(self, compat: CompatibilidadeUnidades) -> None:
        """L e KG são de grandezas diferentes → None."""
        resultado = compat.converter(1.0, "L", "KG")
        assert resultado is None


class TestSaoComparaveis:
    """Testes para verificação de compatibilidade."""

    def test_sao_comparaveis_mesmo_tipo(self, compat: CompatibilidadeUnidades) -> None:
        """L e ML são da mesma grandeza → True."""
        assert compat.sao_comparaveis("L", "ML") is True

    def test_nao_comparaveis_tipos_diferentes(self, compat: CompatibilidadeUnidades) -> None:
        """KG e L são de grandezas diferentes → False."""
        assert compat.sao_comparaveis("KG", "L") is False


class TestNormalizarParaBase:
    """Testes para normalização para unidade base."""

    def test_normalizar_ml_para_base(self, compat: CompatibilidadeUnidades) -> None:
        """(500, ML) → (0.5, L)."""
        resultado = compat.normalizar_para_base(500.0, "ML")
        assert resultado is not None
        valor, unidade = resultado
        assert abs(valor - 0.5) < 1e-9
        assert unidade == "L"

    def test_normalizar_unidade_desconhecida(self, compat: CompatibilidadeUnidades) -> None:
        """Unidade desconhecida 'CAIXA' → None."""
        resultado = compat.normalizar_para_base(1.0, "CAIXA")
        assert resultado is None


class TestCompararPrecos:
    """Testes para comparação de preços."""

    def test_comparar_precos_comparaveis(self, compat: CompatibilidadeUnidades) -> None:
        """Preços em ML e L são comparáveis."""
        resultado = compat.comparar_precos(10.0, "ML", 5.0, "L")
        assert resultado is not None
        assert resultado["comparavel"] is True
        assert resultado["unidade_base"] == "L"
        assert resultado["razao"] is not None

    def test_comparar_precos_incompativeis(self, compat: CompatibilidadeUnidades) -> None:
        """Preços em KG e L não são comparáveis."""
        resultado = compat.comparar_precos(10.0, "KG", 5.0, "L")
        assert resultado is not None
        assert resultado["comparavel"] is False

    def test_comparar_precos_unidade_desconhecida(self, compat: CompatibilidadeUnidades) -> None:
        """Unidade desconhecida retorna None."""
        resultado = compat.comparar_precos(10.0, "CAIXA", 5.0, "L")
        assert resultado is None
