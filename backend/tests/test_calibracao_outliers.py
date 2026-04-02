"""Testes de calibração de outliers e relatório de qualidade."""

import pytest

from app.services.motor_estatistico import (
    calibrar_limiar_outlier,
    relatorio_qualidade_amostras,
)


# ---------- calibrar_limiar_outlier ----------


class TestCalibrarLimiarOutlier:
    """Testes para calibrar_limiar_outlier."""

    def test_calibrar_amostra_pequena(self) -> None:
        """Amostra com n < 5 recomenda 'desvio'."""
        r = calibrar_limiar_outlier([10.0, 20.0, 30.0])
        assert r["metodo_recomendado"] == "desvio"
        assert r["justificativa"] == "amostra pequena"

    def test_calibrar_alta_variacao(self) -> None:
        """CV > 0.5 recomenda 'iqr'."""
        # Preços com alta dispersão
        precos = [1.0, 2.0, 3.0, 100.0, 200.0, 300.0]
        r = calibrar_limiar_outlier(precos)
        assert r["metodo_recomendado"] == "iqr"
        assert "IQR" in r["justificativa"] or "iqr" in r["justificativa"].lower()

    def test_calibrar_baixa_variacao(self) -> None:
        """CV <= 0.3 recomenda 'percentil'."""
        precos = [10.0, 10.5, 11.0, 10.2, 10.8, 10.3]
        r = calibrar_limiar_outlier(precos)
        assert r["metodo_recomendado"] == "percentil"

    def test_limiares_padrao(self) -> None:
        """Verifica que limiares padrão são retornados."""
        r = calibrar_limiar_outlier([10.0, 20.0, 30.0])
        assert r["limiar_iqr"] == 1.5
        assert r["limiar_percentil"] == (5.0, 95.0)
        assert r["limiar_desvio"] == 2.0


# ---------- relatorio_qualidade_amostras ----------


class TestRelatorioQualidadeAmostras:
    """Testes para relatorio_qualidade_amostras."""

    def test_relatorio_qualidade_excelente(self) -> None:
        """CV < 0.15 e n >= 10 → EXCELENTE."""
        precos = [10.0, 10.1, 10.2, 9.9, 10.0, 10.05, 9.95, 10.1, 10.0, 9.98]
        r = relatorio_qualidade_amostras(precos)
        assert r["nivel_qualidade"] == "EXCELENTE"
        assert r["n"] == 10

    def test_relatorio_qualidade_bom(self) -> None:
        """CV < 0.3 e n >= 5 → BOM."""
        precos = [10.0, 11.0, 12.0, 9.0, 10.5]
        r = relatorio_qualidade_amostras(precos)
        assert r["nivel_qualidade"] == "BOM"

    def test_relatorio_qualidade_regular(self) -> None:
        """n >= 3 mas CV alto → REGULAR."""
        precos = [5.0, 50.0, 500.0]
        r = relatorio_qualidade_amostras(precos)
        assert r["nivel_qualidade"] == "REGULAR"

    def test_relatorio_qualidade_insuficiente(self) -> None:
        """n < 3 → INSUFICIENTE."""
        precos = [10.0, 20.0]
        r = relatorio_qualidade_amostras(precos)
        assert r["nivel_qualidade"] == "INSUFICIENTE"

    def test_relatorio_tem_recomendacoes(self) -> None:
        """Relatório deve conter lista de recomendações."""
        precos = [10.0, 20.0]
        r = relatorio_qualidade_amostras(precos)
        assert isinstance(r["recomendacoes"], list)
        assert len(r["recomendacoes"]) > 0

    def test_relatorio_campos_completos(self) -> None:
        """Relatório tem todos os campos obrigatórios."""
        precos = [10.0, 20.0, 30.0, 40.0, 50.0]
        r = relatorio_qualidade_amostras(precos)
        assert "n" in r
        assert "n_outliers" in r
        assert "pct_outliers" in r
        assert "coeficiente_variacao" in r
        assert "nivel_qualidade" in r
        assert "recomendacoes" in r

    def test_relatorio_amostra_vazia(self) -> None:
        """Amostra vazia retorna INSUFICIENTE."""
        r = relatorio_qualidade_amostras([])
        assert r["nivel_qualidade"] == "INSUFICIENTE"
        assert r["n"] == 0

    def test_relatorio_amostra_unica(self) -> None:
        """Amostra com 1 elemento retorna INSUFICIENTE."""
        r = relatorio_qualidade_amostras([10.0])
        assert r["nivel_qualidade"] == "INSUFICIENTE"
        assert r["n"] == 1
