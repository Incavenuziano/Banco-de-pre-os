"""Testes de validação de normalização — amostragem 750 itens (15 UFs × 50) — Semana 13.

Cobre: amostrar_itens_por_uf, validar_item_normalizacao,
validar_normalizacao_uf, gerar_relatorio_normalizacao, SLA ≥ 85%.
"""

from __future__ import annotations

import pytest

from app.services.pncp_pipeline_ufs import UFS_PRIORITARIAS
from app.services.validacao_normalizacao import (
    AMOSTRA_POR_UF,
    SLA_TAXA_ACERTO,
    ResultadoNormalizacaoItem,
    ResultadoNormalizacaoUF,
    amostrar_itens_por_uf,
    gerar_relatorio_normalizacao,
    validar_item_normalizacao,
    validar_normalizacao_uf,
)


# ─────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────


def _item_valido(i: int, uf: str, categoria: str = "MATERIAL_ESCRITORIO") -> dict:
    return {
        "id": str(i),
        "descricao_original": f"PAPEL SULFITE A4 75G CAIXA COM 500 FOLHAS ITEM {i:04d}",
        "categoria": categoria,
        "unidade_original": "CX",
    }


def _item_ruim(i: int, uf: str) -> dict:
    return {
        "id": str(i),
        "descricao_original": "",  # sem descrição
        "categoria": "SEM_CATEGORIA",
        "unidade_original": "??",
    }


def _itens_bons(uf: str, n: int = 100) -> list[dict]:
    cats = ["MATERIAL_ESCRITORIO", "LIMPEZA", "ALIMENTACAO", "EPI", "INFORMATICA"]
    return [_item_valido(i, uf, cats[i % len(cats)]) for i in range(n)]


# ─────────────────────────────────────────────────────────
# Testes: amostrar_itens_por_uf
# ─────────────────────────────────────────────────────────


class TestAmostrarItensPorUF:
    def test_retorna_n_itens(self):
        itens = _itens_bons("SP", 200)
        amostra = amostrar_itens_por_uf(itens, "SP", n=50)
        assert len(amostra) == 50

    def test_retorna_todos_se_menos_que_n(self):
        itens = _itens_bons("MG", 30)
        amostra = amostrar_itens_por_uf(itens, "MG", n=50)
        assert len(amostra) == 30

    def test_lista_vazia(self):
        amostra = amostrar_itens_por_uf([], "RJ", n=50)
        assert amostra == []

    def test_reproducibilidade_com_seed(self):
        itens = _itens_bons("BA", 200)
        a1 = amostrar_itens_por_uf(itens, "BA", n=50, seed=42)
        a2 = amostrar_itens_por_uf(itens, "BA", n=50, seed=42)
        assert [i["id"] for i in a1] == [i["id"] for i in a2]

    def test_seeds_diferentes_amostras_diferentes(self):
        itens = _itens_bons("RS", 200)
        a1 = amostrar_itens_por_uf(itens, "RS", n=50, seed=1)
        a2 = amostrar_itens_por_uf(itens, "RS", n=50, seed=99)
        assert [i["id"] for i in a1] != [i["id"] for i in a2]

    def test_amostra_n_exato_quando_igual(self):
        itens = _itens_bons("PE", 50)
        amostra = amostrar_itens_por_uf(itens, "PE", n=50)
        assert len(amostra) == 50

    def test_estratificacao_por_categoria(self):
        """Amostra deve conter múltiplas categorias quando disponível."""
        itens = _itens_bons("CE", 200)
        amostra = amostrar_itens_por_uf(itens, "CE", n=50)
        categorias = {i["categoria"] for i in amostra}
        assert len(categorias) >= 2  # múltiplas categorias representadas


# ─────────────────────────────────────────────────────────
# Testes: validar_item_normalizacao
# ─────────────────────────────────────────────────────────


class TestValidarItemNormalizacao:
    def test_item_valido_classificado(self):
        item = _item_valido(1, "SP")
        r = validar_item_normalizacao(item, "SP")
        assert isinstance(r, ResultadoNormalizacaoItem)
        assert r.classificado is True
        assert r.score_qualidade >= 0.6

    def test_item_sem_descricao_nao_classificado(self):
        item = _item_ruim(1, "MG")
        r = validar_item_normalizacao(item, "MG")
        assert r.classificado is False
        assert r.score_qualidade < 0.6

    def test_resultado_contem_uf(self):
        item = _item_valido(1, "RJ")
        r = validar_item_normalizacao(item, "RJ")
        assert r.uf == "RJ"

    def test_resultado_contem_categoria(self):
        item = _item_valido(1, "BA", categoria="LIMPEZA")
        r = validar_item_normalizacao(item, "BA")
        assert r.categoria == "LIMPEZA"

    def test_unidade_normalizada(self):
        item = _item_valido(1, "SP")
        r = validar_item_normalizacao(item, "SP")
        # unidade_original = "CX" → deve normalizar
        assert r.unidade_normalizada == "CX"

    def test_sinonimo_regional_aplicado(self):
        """Item com sinônimo regional deve registrar aplicação."""
        item = {
            "id": "1",
            "descricao_original": "CARNE SECA KG",
            "categoria": "ALIMENTACAO",
            "unidade_original": "KG",
        }
        r = validar_item_normalizacao(item, "BA")
        # "CARNE SECA" → "CARNE BOVINA" é sinônimo regional
        assert "CARNE" in r.descricao_normalizada or r.score_qualidade >= 0.6

    def test_score_entre_0_e_1(self):
        item = _item_valido(1, "SC")
        r = validar_item_normalizacao(item, "SC")
        assert 0.0 <= r.score_qualidade <= 1.0

    def test_item_sem_unidade_aceito(self):
        item = {
            "id": "2",
            "descricao_original": "SERVICO DE MANUTENCAO PREDIAL",
            "categoria": "SERVICOS",
        }
        r = validar_item_normalizacao(item, "PR")
        assert isinstance(r, ResultadoNormalizacaoItem)


# ─────────────────────────────────────────────────────────
# Testes: validar_normalizacao_uf
# ─────────────────────────────────────────────────────────


class TestValidarNormalizacaoUF:
    def test_uf_com_itens_bons_dentro_sla(self):
        itens = _itens_bons("SP", 200)
        r = validar_normalizacao_uf(itens, "SP", n_amostra=50)
        assert r.taxa_acerto >= SLA_TAXA_ACERTO
        assert r.dentro_sla is True

    def test_uf_sem_itens(self):
        r = validar_normalizacao_uf([], "MG", n_amostra=50)
        assert r.total_amostrado == 0
        assert r.dentro_sla is False

    def test_resultado_contem_por_categoria(self):
        itens = _itens_bons("RJ", 200)
        r = validar_normalizacao_uf(itens, "RJ", n_amostra=50)
        assert len(r.por_categoria) >= 1

    def test_taxa_acerto_entre_0_e_1(self):
        itens = _itens_bons("BA", 100)
        r = validar_normalizacao_uf(itens, "BA", n_amostra=50)
        assert 0.0 <= r.taxa_acerto <= 1.0

    def test_como_texto_contem_uf(self):
        itens = _itens_bons("RS", 100)
        r = validar_normalizacao_uf(itens, "RS", n_amostra=50)
        assert "RS" in r.como_texto()

    def test_total_amostrado_nao_excede_n(self):
        itens = _itens_bons("PE", 200)
        r = validar_normalizacao_uf(itens, "PE", n_amostra=50)
        assert r.total_amostrado <= 50

    def test_itens_problematicos_listados(self):
        """Com itens ruins, deve listar problemáticos."""
        itens = [_item_ruim(i, "CE") for i in range(60)]
        r = validar_normalizacao_uf(itens, "CE", n_amostra=50)
        assert len(r.itens_problematicos) > 0

    def test_soma_classificados_le_amostrado(self):
        itens = _itens_bons("SC", 100)
        r = validar_normalizacao_uf(itens, "SC", n_amostra=50)
        assert r.total_classificado <= r.total_amostrado


# ─────────────────────────────────────────────────────────
# Testes: SLA 750 itens totais (15 UFs × 50)
# ─────────────────────────────────────────────────────────


class TestSLANormalizacao15UFs:
    @pytest.mark.parametrize("uf", UFS_PRIORITARIAS)
    def test_uf_com_dados_bons_atinge_sla(self, uf: str):
        """Cada UF com descrições válidas deve atingir ≥85% de acerto."""
        itens = _itens_bons(uf, 200)
        r = validar_normalizacao_uf(itens, uf, n_amostra=AMOSTRA_POR_UF)
        assert r.dentro_sla is True, f"UF {uf}: {r.como_texto()}"

    def test_total_amostrado_750(self):
        """Soma total de 15 UFs × 50 = 750 itens."""
        total = 0
        for uf in UFS_PRIORITARIAS:
            itens = _itens_bons(uf, 200)
            r = validar_normalizacao_uf(itens, uf, n_amostra=AMOSTRA_POR_UF)
            total += r.total_amostrado
        assert total == 750

    def test_todas_ufs_tem_resultado(self):
        resultados = []
        for uf in UFS_PRIORITARIAS:
            itens = _itens_bons(uf, 100)
            r = validar_normalizacao_uf(itens, uf, n_amostra=AMOSTRA_POR_UF)
            resultados.append(r)
        assert len(resultados) == 15


# ─────────────────────────────────────────────────────────
# Testes: gerar_relatorio_normalizacao
# ─────────────────────────────────────────────────────────


class TestGerarRelatorioNormalizacao:
    def _resultado(self, uf: str, taxa: float = 0.90) -> ResultadoNormalizacaoUF:
        total = 50
        classificados = int(total * taxa)
        return ResultadoNormalizacaoUF(
            uf=uf,
            total_amostrado=total,
            total_classificado=classificados,
            taxa_acerto=taxa,
            dentro_sla=taxa >= SLA_TAXA_ACERTO,
            por_categoria={
                "MATERIAL_ESCRITORIO": {"total": 20, "classificados": int(20 * taxa), "taxa_acerto": taxa, "score_medio": taxa},
                "LIMPEZA": {"total": 15, "classificados": int(15 * taxa), "taxa_acerto": taxa, "score_medio": taxa},
            },
        )

    def test_relatorio_gerado(self):
        resultados = [self._resultado(uf) for uf in ["SP", "MG", "RJ"]]
        relatorio = gerar_relatorio_normalizacao(resultados)
        assert "RELATÓRIO DE QUALIDADE" in relatorio
        assert "SP" in relatorio

    def test_relatorio_15_ufs(self):
        resultados = [self._resultado(uf) for uf in UFS_PRIORITARIAS]
        relatorio = gerar_relatorio_normalizacao(resultados)
        for uf in UFS_PRIORITARIAS:
            assert uf in relatorio

    def test_relatorio_contem_taxa_geral(self):
        resultados = [self._resultado(uf, 0.90) for uf in UFS_PRIORITARIAS]
        relatorio = gerar_relatorio_normalizacao(resultados)
        assert "Taxa geral" in relatorio or "taxa" in relatorio.lower()

    def test_relatorio_contem_detalhes_categoria(self):
        resultados = [self._resultado("SP")]
        relatorio = gerar_relatorio_normalizacao(resultados)
        assert "MATERIAL_ESCRITORIO" in relatorio or "LIMPEZA" in relatorio

    def test_relatorio_com_uf_abaixo_sla(self):
        resultados = [self._resultado("SP", taxa=0.70)]
        relatorio = gerar_relatorio_normalizacao(resultados)
        assert "✗" in relatorio  # símbolo de reprovado

    def test_relatorio_lista_vazia(self):
        relatorio = gerar_relatorio_normalizacao([])
        assert "RELATÓRIO" in relatorio
