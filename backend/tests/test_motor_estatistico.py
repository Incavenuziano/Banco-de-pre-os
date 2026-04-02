"""Testes do motor estatístico."""

import pytest

from app.services.motor_estatistico import (
    calcular_estatisticas,
    calcular_preco_referencial,
    gerar_sumario_categoria,
    marcar_outliers,
)


# ---------- calcular_estatisticas ----------


class TestCalcularEstatisticas:
    """Testes para calcular_estatisticas."""

    def test_estatisticas_lista_normal(self) -> None:
        """Lista [10,20,30,40,50] retorna mediana=30, n=5."""
        r = calcular_estatisticas([10, 20, 30, 40, 50])
        assert r["n"] == 5
        assert r["mediana"] == 30
        assert r["media"] == 30
        assert r["min"] == 10
        assert r["max"] == 50

    def test_estatisticas_lista_vazia(self) -> None:
        """Lista vazia retorna n=0, mediana=None."""
        r = calcular_estatisticas([])
        assert r["n"] == 0
        assert r["mediana"] is None
        assert r["media"] is None
        assert r["desvio_padrao"] is None

    def test_estatisticas_lista_um_elemento(self) -> None:
        """Lista com 1 elemento retorna n=1, mediana=42, desvio=None."""
        r = calcular_estatisticas([42])
        assert r["n"] == 1
        assert r["mediana"] == 42
        assert r["desvio_padrao"] is None
        assert r["variancia"] is None

    def test_q1_q3_corretos(self) -> None:
        """Para [1,2,3,4,5,6,7,8] Q1 e Q3 são valores esperados."""
        r = calcular_estatisticas([1, 2, 3, 4, 5, 6, 7, 8])
        assert r["q1"] == 2.5
        assert r["q3"] == 6.5
        assert r["iqr"] == 4.0

    def test_coeficiente_variacao(self) -> None:
        """Coeficiente de variação é calculado corretamente."""
        r = calcular_estatisticas([100, 100, 100, 100])
        assert r["coeficiente_variacao"] == 0.0

    def test_dois_elementos(self) -> None:
        """Lista com 2 elementos retorna estatísticas válidas."""
        r = calcular_estatisticas([10, 20])
        assert r["n"] == 2
        assert r["mediana"] == 15.0
        assert r["desvio_padrao"] is not None


# ---------- marcar_outliers ----------


class TestMarcarOutliers:
    """Testes para marcar_outliers."""

    def test_outliers_iqr_detecta_outlier(self) -> None:
        """Valor muito alto é marcado como outlier pelo método IQR."""
        precos = [10, 11, 12, 13, 14, 15, 100]
        resultado = marcar_outliers(precos, metodo="iqr")
        outliers = [r for r in resultado if r["outlier"]]
        assert len(outliers) >= 1
        assert any(r["preco"] == 100 for r in outliers)

    def test_outliers_iqr_sem_outliers(self) -> None:
        """Lista uniforme não tem outliers."""
        precos = [10, 11, 12, 13, 14]
        resultado = marcar_outliers(precos, metodo="iqr")
        outliers = [r for r in resultado if r["outlier"]]
        assert len(outliers) == 0

    def test_outliers_percentil(self) -> None:
        """Método percentil funciona corretamente."""
        precos = list(range(1, 101))  # 1 a 100
        resultado = marcar_outliers(precos, metodo="percentil")
        outliers = [r for r in resultado if r["outlier"]]
        # Valores extremos devem ser outliers
        assert any(r["preco"] <= 5 for r in outliers)

    def test_outliers_desvio(self) -> None:
        """Método desvio detecta valores distantes da média."""
        precos = [10, 10, 10, 10, 10, 50]
        resultado = marcar_outliers(precos, metodo="desvio")
        outliers = [r for r in resultado if r["outlier"]]
        assert any(r["preco"] == 50 for r in outliers)

    def test_outliers_lista_vazia(self) -> None:
        """Lista vazia retorna lista vazia."""
        assert marcar_outliers([]) == []

    def test_outliers_metodo_invalido(self) -> None:
        """Método inválido levanta ValueError."""
        with pytest.raises(ValueError, match="Método desconhecido"):
            marcar_outliers([1, 2, 3], metodo="invalido")


# ---------- calcular_preco_referencial ----------


class TestCalcularPrecoReferencial:
    """Testes para calcular_preco_referencial."""

    def test_referencial_confianca_alta(self) -> None:
        """n>=10 e cv<0.3 resulta em confiança ALTA."""
        precos = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        r = calcular_preco_referencial(precos)
        assert r["confianca"] == "ALTA"

    def test_referencial_confianca_media(self) -> None:
        """n=5 resulta em confiança MEDIA."""
        precos = [10, 20, 30, 40, 50]
        r = calcular_preco_referencial(precos)
        assert r["confianca"] == "MEDIA"

    def test_referencial_confianca_baixa(self) -> None:
        """n=2 resulta em confiança BAIXA."""
        precos = [10, 20]
        r = calcular_preco_referencial(precos)
        assert r["confianca"] == "BAIXA"

    def test_referencial_insuficiente(self) -> None:
        """n=1 resulta em confiança INSUFICIENTE."""
        precos = [42]
        r = calcular_preco_referencial(precos)
        assert r["confianca"] == "INSUFICIENTE"

    def test_referencial_exclui_outliers(self) -> None:
        """Preço referencial com exclusão difere de sem em lista contaminada."""
        precos = [10, 11, 12, 13, 14, 15, 500]
        com_exclusao = calcular_preco_referencial(precos, excluir_outliers=True)
        sem_exclusao = calcular_preco_referencial(precos, excluir_outliers=False)
        assert com_exclusao["preco_referencial"] != sem_exclusao["preco_referencial"]
        assert com_exclusao["n_outliers_excluidos"] > 0

    def test_referencial_sem_excluir_outliers(self) -> None:
        """excluir_outliers=False usa todos os preços."""
        precos = [10, 11, 12, 13, 14, 15, 500]
        r = calcular_preco_referencial(precos, excluir_outliers=False)
        assert r["n_outliers_excluidos"] == 0
        assert r["n_amostras"] == 7

    def test_referencial_lista_vazia(self) -> None:
        """Lista vazia retorna INSUFICIENTE."""
        r = calcular_preco_referencial([])
        assert r["confianca"] == "INSUFICIENTE"
        assert r["preco_referencial"] is None

    def test_calcular_preco_lista_com_outlier_severo(self) -> None:
        """Outlier severo é removido e reduz o preço referencial."""
        precos = [10, 11, 12, 13, 14, 15, 10000]
        r = calcular_preco_referencial(precos, excluir_outliers=True)
        assert r["preco_referencial"] is not None
        assert r["preco_referencial"] < 100  # Sem o outlier, mediana fica baixa


# ---------- gerar_sumario_categoria ----------


class TestGerarSumarioCategoria:
    """Testes para gerar_sumario_categoria."""

    def test_sumario_agrupa_por_unidade(self) -> None:
        """Fontes com 2 unidades distintas geram 2 grupos."""
        fontes = [
            {"preco_unitario": 10, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "SP"},
            {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
            {"preco_unitario": 5, "unidade_normalizada": "KG", "score_confianca": 50, "uf": "MG"},
        ]
        r = gerar_sumario_categoria(fontes)
        assert len(r["por_unidade"]) == 2
        assert "UN" in r["por_unidade"]
        assert "KG" in r["por_unidade"]

    def test_sumario_filtra_score_baixo(self) -> None:
        """Fonte com score < 30 é ignorada."""
        fontes = [
            {"preco_unitario": 10, "unidade_normalizada": "UN", "score_confianca": 29, "uf": "SP"},
            {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
        ]
        r = gerar_sumario_categoria(fontes)
        assert r["total_amostras"] == 2
        assert r["amostras_validas"] == 1

    def test_sumario_filtra_preco_zero(self) -> None:
        """Fonte com preco=0 é ignorada."""
        fontes = [
            {"preco_unitario": 0, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "SP"},
            {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
        ]
        r = gerar_sumario_categoria(fontes)
        assert r["amostras_validas"] == 1

    def test_sumario_distribuicao_uf(self) -> None:
        """distribuicao_uf conta corretamente por UF."""
        fontes = [
            {"preco_unitario": 10, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "SP"},
            {"preco_unitario": 20, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "SP"},
            {"preco_unitario": 30, "unidade_normalizada": "UN", "score_confianca": 50, "uf": "RJ"},
        ]
        r = gerar_sumario_categoria(fontes)
        assert r["distribuicao_uf"]["SP"] == 2
        assert r["distribuicao_uf"]["RJ"] == 1

    def test_sumario_vazio(self) -> None:
        """Lista vazia retorna amostras_validas=0."""
        r = gerar_sumario_categoria([])
        assert r["total_amostras"] == 0
        assert r["amostras_validas"] == 0
        assert r["por_unidade"] == {}
        assert r["distribuicao_uf"] == {}
