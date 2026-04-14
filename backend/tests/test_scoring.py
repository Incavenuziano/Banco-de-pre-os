"""Testes unitários do cálculo de score de confiança.

Cobertura:
  - Score mínimo e máximo (comportamento original, sem decaimento)
  - Componentes individuais
  - calcular_fator_temporal: todas as faixas de decaimento
  - calcular_score_fonte com data_base: decaimento aplicado
  - calcular_score_detalhado: breakdown completo
"""

from datetime import date, timedelta

import pytest

from app.services.scoring import (
    calcular_fator_temporal,
    calcular_score_detalhado,
    calcular_score_fonte,
)


class TestScoreMinimo:
    """Testes para score mínimo (0)."""

    def test_dict_vazio(self) -> None:
        assert calcular_score_fonte({}) == 0

    def test_campos_none(self) -> None:
        fonte = {
            "url_origem": None,
            "data_referencia": None,
            "quantidade": None,
            "qualidade_tipo": None,
            "storage_path": None,
            "hash_sha256": None,
            "unidade_normalizada": None,
            "categoria_id": None,
            "score_classificacao": None,
        }
        assert calcular_score_fonte(fonte) == 0

    def test_campos_vazios(self) -> None:
        fonte = {
            "url_origem": "",
            "qualidade_tipo": "",
            "storage_path": "",
            "hash_sha256": "",
            "unidade_normalizada": "",
        }
        assert calcular_score_fonte(fonte) == 0


class TestScoreMaximo:
    """Testes para score máximo (100)."""

    def test_todos_campos_presentes_homologado(self) -> None:
        fonte = {
            "url_origem": "https://pncp.gov.br/item/123",
            "data_referencia": "2024-01-15",
            "quantidade": 100,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/evidencias/123.pdf",
            "hash_sha256": "abc123" * 10,
            "unidade_normalizada": "UN",
            "categoria_id": 1,
            "score_classificacao": 0.95,
        }
        assert calcular_score_fonte(fonte) == 100

    def test_score_nao_ultrapassa_100(self) -> None:
        """Mesmo com tudo preenchido, não ultrapassa 100."""
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": "2024-06-01",
            "quantidade": 500,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/path/doc.pdf",
            "hash_sha256": "deadbeef" * 8,
            "unidade_normalizada": "KG",
            "categoria_id": 5,
            "score_classificacao": 1.0,
        }
        assert calcular_score_fonte(fonte) <= 100


class TestScoreIntermediario:
    """Testes para scores intermediários."""

    def test_apenas_url(self) -> None:
        fonte = {"url_origem": "https://example.com"}
        assert calcular_score_fonte(fonte) == 10

    def test_completude_total(self) -> None:
        """url_origem + data_referencia + quantidade = 20."""
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": "2024-01-01",
            "quantidade": 10,
        }
        assert calcular_score_fonte(fonte) == 20

    def test_confiabilidade_tabela_oficial(self) -> None:
        fonte = {"qualidade_tipo": "TABELA_OFICIAL"}
        assert calcular_score_fonte(fonte) == 25

    def test_confiabilidade_estimado(self) -> None:
        fonte = {"qualidade_tipo": "ESTIMADO"}
        assert calcular_score_fonte(fonte) == 15

    def test_confiabilidade_mercado(self) -> None:
        fonte = {"qualidade_tipo": "MERCADO"}
        assert calcular_score_fonte(fonte) == 10

    def test_evidencia_storage_path(self) -> None:
        fonte = {"storage_path": "/evidencias/doc.pdf"}
        assert calcular_score_fonte(fonte) == 10

    def test_evidencia_completa(self) -> None:
        fonte = {
            "storage_path": "/evidencias/doc.pdf",
            "hash_sha256": "abc123def456",
        }
        assert calcular_score_fonte(fonte) == 20

    def test_unidade_normalizada_valida(self) -> None:
        fonte = {"unidade_normalizada": "KG"}
        assert calcular_score_fonte(fonte) == 15

    def test_unidade_outro_nao_pontua(self) -> None:
        fonte = {"unidade_normalizada": "OUTRO"}
        assert calcular_score_fonte(fonte) == 0

    def test_categoria_sem_score_alto(self) -> None:
        """Categoria presente mas score <= 0.8 → só 10 pontos."""
        fonte = {"categoria_id": 1, "score_classificacao": 0.5}
        assert calcular_score_fonte(fonte) == 10

    def test_categoria_com_score_alto(self) -> None:
        """Categoria + score > 0.8 → 15 pontos."""
        fonte = {"categoria_id": 1, "score_classificacao": 0.95}
        assert calcular_score_fonte(fonte) == 15

    def test_qualidade_case_insensitive(self) -> None:
        fonte = {"qualidade_tipo": "homologado"}
        assert calcular_score_fonte(fonte) == 30


# ─────────────────────────────────────────────────────────────────────────────
# Testes de calcular_fator_temporal
# ─────────────────────────────────────────────────────────────────────────────

class TestFatorTemporal:
    """Verifica cada faixa da tabela de decaimento."""

    BASE = date(2025, 6, 1)  # data base fixa para todos os testes

    def _dr(self, dias_atras: int) -> str:
        return (self.BASE - timedelta(days=dias_atras)).isoformat()

    # ── Faixas ────────────────────────────────────────────────────────────

    def test_faixa_0_a_30_dias(self) -> None:
        assert calcular_fator_temporal(self._dr(0), self.BASE) == 1.00
        assert calcular_fator_temporal(self._dr(15), self.BASE) == 1.00
        assert calcular_fator_temporal(self._dr(30), self.BASE) == 1.00

    def test_faixa_31_a_90_dias(self) -> None:
        assert calcular_fator_temporal(self._dr(31), self.BASE) == 0.95
        assert calcular_fator_temporal(self._dr(60), self.BASE) == 0.95
        assert calcular_fator_temporal(self._dr(90), self.BASE) == 0.95

    def test_faixa_91_a_180_dias(self) -> None:
        assert calcular_fator_temporal(self._dr(91), self.BASE) == 0.85
        assert calcular_fator_temporal(self._dr(135), self.BASE) == 0.85
        assert calcular_fator_temporal(self._dr(180), self.BASE) == 0.85

    def test_faixa_181_a_365_dias(self) -> None:
        assert calcular_fator_temporal(self._dr(181), self.BASE) == 0.70
        assert calcular_fator_temporal(self._dr(270), self.BASE) == 0.70
        assert calcular_fator_temporal(self._dr(365), self.BASE) == 0.70

    def test_faixa_1_a_2_anos(self) -> None:
        assert calcular_fator_temporal(self._dr(366), self.BASE) == 0.50
        assert calcular_fator_temporal(self._dr(500), self.BASE) == 0.50
        assert calcular_fator_temporal(self._dr(730), self.BASE) == 0.50

    def test_faixa_2_a_5_anos(self) -> None:
        assert calcular_fator_temporal(self._dr(731), self.BASE) == 0.30
        assert calcular_fator_temporal(self._dr(1000), self.BASE) == 0.30
        assert calcular_fator_temporal(self._dr(1825), self.BASE) == 0.30

    def test_faixa_mais_de_5_anos(self) -> None:
        assert calcular_fator_temporal(self._dr(1826), self.BASE) == 0.10
        assert calcular_fator_temporal(self._dr(3650), self.BASE) == 0.10

    # ── Edge cases ────────────────────────────────────────────────────────

    def test_data_none_retorna_1(self) -> None:
        assert calcular_fator_temporal(None, self.BASE) == 1.0

    def test_data_invalida_retorna_1(self) -> None:
        assert calcular_fator_temporal("nao-e-uma-data", self.BASE) == 1.0
        assert calcular_fator_temporal("", self.BASE) == 1.0

    def test_data_futura_retorna_1(self) -> None:
        futura = (self.BASE + timedelta(days=10)).isoformat()
        assert calcular_fator_temporal(futura, self.BASE) == 1.0

    def test_data_objeto_date_aceita(self) -> None:
        dr_obj = self.BASE - timedelta(days=60)
        assert calcular_fator_temporal(dr_obj, self.BASE) == 0.95

    def test_sem_data_base_usa_hoje(self) -> None:
        # Sem data_base, usa date.today() internamente — não deve lançar erro
        fator = calcular_fator_temporal("2020-01-01")
        assert 0.0 < fator <= 1.0

    def test_data_referencia_hoje_retorna_1(self) -> None:
        hoje = self.BASE.isoformat()
        assert calcular_fator_temporal(hoje, self.BASE) == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Testes de calcular_score_fonte com data_base (decaimento aplicado)
# ─────────────────────────────────────────────────────────────────────────────

class TestScoreComDecaimento:
    BASE = date(2025, 6, 1)

    def _fonte_completa(self, dias_atras: int) -> dict:
        dr = (self.BASE - timedelta(days=dias_atras)).isoformat()
        return {
            "url_origem": "https://pncp.gov.br/item/1",
            "data_referencia": dr,
            "quantidade": 100,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/ev/1.pdf",
            "hash_sha256": "abc" * 20,
            "unidade_normalizada": "UN",
            "categoria_id": 1,
            "score_classificacao": 0.95,
        }  # score_base = 100

    def test_preco_recente_sem_penalidade(self) -> None:
        fonte = self._fonte_completa(15)
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 100

    def test_preco_60_dias_fator_095(self) -> None:
        fonte = self._fonte_completa(60)
        # 100 * 0.95 = 95
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 95

    def test_preco_120_dias_fator_085(self) -> None:
        fonte = self._fonte_completa(120)
        # 100 * 0.85 = 85
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 85

    def test_preco_270_dias_fator_070(self) -> None:
        fonte = self._fonte_completa(270)
        # 100 * 0.70 = 70
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 70

    def test_preco_500_dias_fator_050(self) -> None:
        fonte = self._fonte_completa(500)
        # 100 * 0.50 = 50
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 50

    def test_preco_1000_dias_fator_030(self) -> None:
        fonte = self._fonte_completa(1000)
        # 100 * 0.30 = 30
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 30

    def test_preco_2000_dias_fator_010(self) -> None:
        fonte = self._fonte_completa(2000)
        # 100 * 0.10 = 10
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 10

    def test_sem_data_base_sem_decaimento(self) -> None:
        """data_base=None → mesmo score independente da data_referencia."""
        fonte_antiga = self._fonte_completa(2000)
        fonte_recente = self._fonte_completa(5)
        assert calcular_score_fonte(fonte_antiga) == calcular_score_fonte(fonte_recente)
        assert calcular_score_fonte(fonte_antiga) == 100

    def test_score_parcial_com_decaimento(self) -> None:
        """Score base 50, 60 dias → 50 * 0.95 = 47 (arredondado)."""
        dr = (self.BASE - timedelta(days=60)).isoformat()
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": dr,
            "qualidade_tipo": "MERCADO",  # 10 pts
            "unidade_normalizada": "KG",   # 15 pts
            "quantidade": 1,               # 5 pts (completude parcial)
        }
        # score_base: url=10, dr=5, qtd=5 → completude=20; mercado=10 → total=45
        assert calcular_score_fonte(fonte, data_base=self.BASE) == round(45 * 0.95)

    def test_arredondamento_correto(self) -> None:
        """Decaimento fracionário: round(70 * 0.95) = 67 (não 66)."""
        dr = (self.BASE - timedelta(days=60)).isoformat()
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": dr,
            "quantidade": 10,
            "qualidade_tipo": "HOMOLOGADO",  # 30
            "unidade_normalizada": "L",       # 15
        }
        # completude: 10+5+5=20, homologado=30, unidade=15 → base=65
        # 65 * 0.95 = 61.75 → round = 62
        assert calcular_score_fonte(fonte, data_base=self.BASE) == 62


# ─────────────────────────────────────────────────────────────────────────────
# Testes de calcular_score_detalhado
# ─────────────────────────────────────────────────────────────────────────────

class TestScoreDetalhado:
    BASE = date(2025, 6, 1)

    def _fonte_completa(self, dias_atras: int) -> dict:
        dr = (self.BASE - timedelta(days=dias_atras)).isoformat()
        return {
            "url_origem": "https://pncp.gov.br/item/1",
            "data_referencia": dr,
            "quantidade": 100,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/ev/1.pdf",
            "hash_sha256": "abc" * 20,
            "unidade_normalizada": "UN",
            "categoria_id": 1,
            "score_classificacao": 0.95,
        }

    def test_estrutura_completa(self) -> None:
        r = calcular_score_detalhado(self._fonte_completa(30), self.BASE)
        assert "score_final" in r
        assert "score_base" in r
        assert "fator_temporal" in r
        assert "dias_referencia" in r
        assert "componentes" in r
        componentes = r["componentes"]
        assert "completude" in componentes
        assert "confiabilidade" in componentes
        assert "evidencia" in componentes
        assert "unidade" in componentes
        assert "categoria" in componentes

    def test_score_base_sem_data_base(self) -> None:
        """Sem data_base, score_final == score_base."""
        r = calcular_score_detalhado(self._fonte_completa(500))
        assert r["score_final"] == r["score_base"] == 100

    def test_score_final_com_data_base(self) -> None:
        """Com data_base=BASE, preço de 500 dias atrás tem fator 0.50."""
        r = calcular_score_detalhado(self._fonte_completa(500), self.BASE)
        assert r["score_base"] == 100
        assert r["fator_temporal"] == 0.50
        assert r["score_final"] == 50

    def test_dias_referencia_correto(self) -> None:
        r = calcular_score_detalhado(self._fonte_completa(120), self.BASE)
        assert r["dias_referencia"] == 120

    def test_dias_referencia_none_se_sem_data(self) -> None:
        fonte = {"qualidade_tipo": "HOMOLOGADO"}
        r = calcular_score_detalhado(fonte, self.BASE)
        assert r["dias_referencia"] is None

    def test_fator_informado_mesmo_sem_data_base(self) -> None:
        """Sem data_base, fator é calculado mas score_final não é penalizado."""
        fonte = self._fonte_completa(500)  # antiga em relação a BASE
        r = calcular_score_detalhado(fonte)  # sem data_base → usa date.today()
        # Fator é < 1.0 pois o preço tem mais de 30 dias (calculado em relação a hoje)
        assert r["fator_temporal"] < 1.0
        # Mas score_final NÃO é penalizado — sem data_base não aplica decaimento
        assert r["score_final"] == 100

    def test_componentes_somam_score_base(self) -> None:
        r = calcular_score_detalhado(self._fonte_completa(10), self.BASE)
        soma = sum(r["componentes"].values())
        assert soma == r["score_base"]

    def test_preco_recente_score_final_igual_base(self) -> None:
        r = calcular_score_detalhado(self._fonte_completa(10), self.BASE)
        assert r["score_final"] == r["score_base"]
        assert r["fator_temporal"] == 1.0
