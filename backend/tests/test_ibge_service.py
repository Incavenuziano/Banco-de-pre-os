"""Testes do serviço IBGE/IPCA — Semana 15.

Cobre: IBGEService — get_serie, get_variacao_mensal, get_meses_disponiveis,
sincronizar, get_indice_acumulado_entre.
"""

from __future__ import annotations

import pytest

from app.services.ibge_service import IBGEService, IndicePrecoDTO


@pytest.fixture
def ibge() -> IBGEService:
    return IBGEService()


class TestGetSerie:
    """Testes de get_serie()."""

    def test_retorna_lista(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert isinstance(serie, list)

    def test_retorna_dtos(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert all(isinstance(s, IndicePrecoDTO) for s in serie)

    def test_doze_meses_2020(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert len(serie) == 12

    def test_fonte_ipca(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert all(s.fonte == "IPCA" for s in serie)

    def test_anos_corretos(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert all(s.ano == 2020 for s in serie)

    def test_meses_1_a_12(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        meses = [s.mes for s in serie]
        assert meses == list(range(1, 13))

    def test_indice_acumulado_crescente(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        # Geralmente crescente (pode ter deflação pontual mas acumulado sobe)
        assert serie[-1].indice_acumulado > serie[0].indice_acumulado

    def test_periodo_multi_ano(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2021)
        assert len(serie) == 24  # 12 + 12

    def test_periodo_parcial_2026(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2026, 2026)
        assert len(serie) == 3  # jan, fev, mar 2026

    def test_ano_sem_dados_retorna_vazio(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2030, 2030)
        assert serie == []

    def test_variacao_acumulada_ano_janeiro(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        jan = serie[0]
        # Em janeiro, acumulado_ano == variacao_mensal
        assert abs(jan.variacao_acumulada_ano - jan.variacao_mensal) < 0.01

    def test_fonte_url_presente(self, ibge: IBGEService) -> None:
        serie = ibge.get_serie(2020, 2020)
        assert all(s.fonte_url is not None for s in serie)


class TestGetVariacaoMensal:
    """Testes de get_variacao_mensal()."""

    def test_retorna_float(self, ibge: IBGEService) -> None:
        v = ibge.get_variacao_mensal(2020, 1)
        assert isinstance(v, float)

    def test_janeiro_2020(self, ibge: IBGEService) -> None:
        v = ibge.get_variacao_mensal(2020, 1)
        assert v == 0.21

    def test_mes_inexistente(self, ibge: IBGEService) -> None:
        v = ibge.get_variacao_mensal(2030, 1)
        assert v is None

    def test_deflacao_abril_2020(self, ibge: IBGEService) -> None:
        v = ibge.get_variacao_mensal(2020, 4)
        assert v is not None
        assert v < 0


class TestGetMesesDisponiveis:
    """Testes de get_meses_disponiveis()."""

    def test_retorna_lista(self, ibge: IBGEService) -> None:
        meses = ibge.get_meses_disponiveis()
        assert isinstance(meses, list)

    def test_ordenados(self, ibge: IBGEService) -> None:
        meses = ibge.get_meses_disponiveis()
        assert meses == sorted(meses)

    def test_primeiro_mes(self, ibge: IBGEService) -> None:
        meses = ibge.get_meses_disponiveis()
        assert meses[0] == (2020, 1)

    def test_ultimo_mes(self, ibge: IBGEService) -> None:
        meses = ibge.get_meses_disponiveis()
        assert meses[-1] == (2026, 3)

    def test_total_meses(self, ibge: IBGEService) -> None:
        meses = ibge.get_meses_disponiveis()
        # 2020: 12, 2021: 12, 2022: 12, 2023: 12, 2024: 12, 2025: 12, 2026: 3
        assert len(meses) == 75


class TestSincronizar:
    """Testes de sincronizar()."""

    def test_retorna_dict(self, ibge: IBGEService) -> None:
        resultado = ibge.sincronizar()
        assert isinstance(resultado, dict)

    def test_status_ok(self, ibge: IBGEService) -> None:
        resultado = ibge.sincronizar()
        assert resultado["status"] == "ok"

    def test_fonte_ipca(self, ibge: IBGEService) -> None:
        resultado = ibge.sincronizar()
        assert resultado["fonte"] == "IPCA"

    def test_total_meses(self, ibge: IBGEService) -> None:
        resultado = ibge.sincronizar()
        assert resultado["total_meses"] == 75

    def test_periodo(self, ibge: IBGEService) -> None:
        resultado = ibge.sincronizar()
        assert resultado["periodo"]["inicio"] == "2020-01"
        assert resultado["periodo"]["fim"] == "2026-03"


class TestGetIndiceAcumuladoEntre:
    """Testes de get_indice_acumulado_entre()."""

    def test_mesmo_mes_retorna_fator(self, ibge: IBGEService) -> None:
        fator = ibge.get_indice_acumulado_entre(2020, 1, 2020, 1)
        assert fator > 1.0  # Inclui variação do próprio mês

    def test_periodo_invalido_erro(self, ibge: IBGEService) -> None:
        with pytest.raises(ValueError):
            ibge.get_indice_acumulado_entre(2022, 1, 2020, 1)

    def test_inflacao_positiva_2020(self, ibge: IBGEService) -> None:
        fator = ibge.get_indice_acumulado_entre(2020, 1, 2020, 12)
        assert fator > 1.0

    def test_inflacao_acumulada_2020_2025(self, ibge: IBGEService) -> None:
        fator = ibge.get_indice_acumulado_entre(2020, 1, 2025, 12)
        # Inflação acumulada ~35-45% (plausível para 6 anos)
        assert fator > 1.30
        assert fator < 1.60
