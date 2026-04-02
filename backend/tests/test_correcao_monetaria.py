"""Testes do serviço de correção monetária IPCA — Semana 15.

Cobre: CorrecaoMonetariaService — fator_correcao, corrigir_preco,
variacao_periodo, corrigir_preco_detalhado, _parse_data, edge cases.
"""

from __future__ import annotations

import pytest

from app.services.correcao_monetaria import CorrecaoMonetariaService
from app.services.ibge_service import IBGEService


@pytest.fixture
def svc() -> CorrecaoMonetariaService:
    return CorrecaoMonetariaService(IBGEService())


# ---------------------------------------------------------------------------
# _parse_data
# ---------------------------------------------------------------------------
class TestParseData:
    def test_formato_yyyy_mm_dd(self, svc: CorrecaoMonetariaService) -> None:
        ano, mes = svc._parse_data("2023-06-15")
        assert ano == 2023
        assert mes == 6

    def test_formato_yyyy_mm(self, svc: CorrecaoMonetariaService) -> None:
        ano, mes = svc._parse_data("2023-06")
        assert ano == 2023
        assert mes == 6

    def test_formato_invalido(self, svc: CorrecaoMonetariaService) -> None:
        with pytest.raises(ValueError, match="inválido"):
            svc._parse_data("2023")

    def test_mes_invalido_zero(self, svc: CorrecaoMonetariaService) -> None:
        with pytest.raises(ValueError, match="Mês inválido"):
            svc._parse_data("2023-00-01")

    def test_mes_invalido_treze(self, svc: CorrecaoMonetariaService) -> None:
        with pytest.raises(ValueError, match="Mês inválido"):
            svc._parse_data("2023-13-01")


# ---------------------------------------------------------------------------
# fator_correcao
# ---------------------------------------------------------------------------
class TestFatorCorrecao:
    def test_mesma_data_retorna_um(self, svc: CorrecaoMonetariaService) -> None:
        assert svc.fator_correcao("2023-06-01", "2023-06-15") == 1.0

    def test_datas_invertidas_erro(self, svc: CorrecaoMonetariaService) -> None:
        with pytest.raises(ValueError, match="posterior"):
            svc.fator_correcao("2025-01-01", "2020-01-01")

    def test_fator_maior_que_um(self, svc: CorrecaoMonetariaService) -> None:
        fator = svc.fator_correcao("2020-01-01", "2023-12-01")
        assert fator > 1.0

    def test_fator_um_mes_adjacente(self, svc: CorrecaoMonetariaService) -> None:
        fator = svc.fator_correcao("2020-01-01", "2020-02-01")
        assert fator > 1.0
        assert fator < 1.05

    def test_fator_retorna_float(self, svc: CorrecaoMonetariaService) -> None:
        fator = svc.fator_correcao("2021-01-01", "2021-12-01")
        assert isinstance(fator, float)


# ---------------------------------------------------------------------------
# corrigir_preco
# ---------------------------------------------------------------------------
class TestCorrigirPreco:
    def test_preco_corrigido_maior(self, svc: CorrecaoMonetariaService) -> None:
        corrigido = svc.corrigir_preco(100.0, "2020-01-01", "2025-12-01")
        assert corrigido > 130

    def test_mesma_data_retorna_mesmo_valor(self, svc: CorrecaoMonetariaService) -> None:
        assert svc.corrigir_preco(100.0, "2023-06-01", "2023-06-15") == 100.0

    def test_valor_negativo_erro(self, svc: CorrecaoMonetariaService) -> None:
        with pytest.raises(ValueError, match="negativo"):
            svc.corrigir_preco(-50.0, "2020-01-01", "2023-01-01")

    def test_valor_zero(self, svc: CorrecaoMonetariaService) -> None:
        assert svc.corrigir_preco(0.0, "2020-01-01", "2023-01-01") == 0.0

    def test_retorna_float(self, svc: CorrecaoMonetariaService) -> None:
        resultado = svc.corrigir_preco(100.0, "2022-01-01", "2023-01-01")
        assert isinstance(resultado, float)

    def test_arredondamento_2_casas(self, svc: CorrecaoMonetariaService) -> None:
        resultado = svc.corrigir_preco(99.99, "2020-01-01", "2023-06-01")
        casas = str(resultado).split(".")[-1]
        assert len(casas) <= 2

    def test_preco_grande(self, svc: CorrecaoMonetariaService) -> None:
        resultado = svc.corrigir_preco(1_000_000.0, "2020-01-01", "2023-01-01")
        assert resultado > 1_000_000.0


# ---------------------------------------------------------------------------
# variacao_periodo
# ---------------------------------------------------------------------------
class TestVariacaoPeriodo:
    def test_variacao_positiva(self, svc: CorrecaoMonetariaService) -> None:
        v = svc.variacao_periodo("2020-01-01", "2023-12-01")
        assert v > 0

    def test_variacao_zero_mesmo_mes(self, svc: CorrecaoMonetariaService) -> None:
        v = svc.variacao_periodo("2022-06-01", "2022-06-01")
        assert v == 0.0

    def test_variacao_retorna_percentual(self, svc: CorrecaoMonetariaService) -> None:
        v = svc.variacao_periodo("2020-01-01", "2025-12-01")
        assert 30 < v < 60

    def test_variacao_arredondada_2_casas(self, svc: CorrecaoMonetariaService) -> None:
        v = svc.variacao_periodo("2020-01-01", "2023-01-01")
        casas = str(v).split(".")[-1]
        assert len(casas) <= 2


# ---------------------------------------------------------------------------
# corrigir_preco_detalhado
# ---------------------------------------------------------------------------
class TestCorrigirPrecoDetalhado:
    def test_retorna_dict(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(100.0, "2020-01-01", "2023-01-01")
        assert isinstance(r, dict)

    def test_campos_obrigatorios(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(100.0, "2020-01-01", "2023-01-01")
        campos = {"valor_original", "valor_corrigido", "fator", "variacao_percentual",
                  "data_origem", "data_destino", "indice"}
        assert campos.issubset(r.keys())

    def test_valor_original_preservado(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(250.0, "2021-01-01", "2023-01-01")
        assert r["valor_original"] == 250.0

    def test_indice_ipca(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(100.0, "2020-01-01", "2023-01-01")
        assert r["indice"] == "IPCA"

    def test_fator_consistente_com_variacao(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(100.0, "2020-01-01", "2023-01-01")
        variacao_esperada = (r["fator"] - 1) * 100
        assert abs(r["variacao_percentual"] - variacao_esperada) < 0.1

    def test_valor_corrigido_consistente(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(200.0, "2021-06-01", "2024-06-01")
        esperado = round(200.0 * r["fator"], 2)
        assert r["valor_corrigido"] == esperado

    def test_datas_preservadas(self, svc: CorrecaoMonetariaService) -> None:
        r = svc.corrigir_preco_detalhado(100.0, "2022-03-01", "2024-03-01")
        assert r["data_origem"] == "2022-03-01"
        assert r["data_destino"] == "2024-03-01"
