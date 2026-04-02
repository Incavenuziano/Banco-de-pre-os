"""Testes de deduplicação para as 15 UFs prioritárias — Semana 13.

Cobre: calcular_hash_item, calcular_hash_conteudo,
analisar_duplicidade_lista, detectar_duplicatas_cross_uf,
gerar_relatorio_deduplicacao, SLA < 5%.
"""

from __future__ import annotations

import pytest

from app.services.deduplicacao_validacao import (
    SLA_TAXA_DUPLICIDADE,
    ResultadoDeduplicacao,
    analisar_duplicidade_lista,
    calcular_hash_conteudo,
    calcular_hash_item,
    detectar_duplicatas_cross_uf,
    gerar_relatorio_deduplicacao,
)
from app.services.pncp_pipeline_ufs import UFS_PRIORITARIAS


# ─────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────


def _item(descricao: str, uf: str, preco: float = 10.0, data: str = "2025-01-01") -> dict:
    return {
        "descricao_normalizada": descricao,
        "preco_unitario": preco,
        "data_referencia": data,
        "uf": uf,
    }


def _itens_sem_duplicatas(uf: str, n: int = 100) -> list[dict]:
    return [_item(f"ITEM UNICO {i:04d}", uf, preco=float(i + 1)) for i in range(n)]


def _itens_com_duplicatas(uf: str, n: int = 100, taxa: float = 0.10) -> list[dict]:
    """Cria lista com ~taxa% de duplicatas."""
    itens = _itens_sem_duplicatas(uf, n)
    n_dup = int(n * taxa)
    duplicatas = [itens[i % len(itens)].copy() for i in range(n_dup)]
    return itens + duplicatas


# ─────────────────────────────────────────────────────────
# Testes: calcular_hash_item
# ─────────────────────────────────────────────────────────


class TestCalcularHashItem:
    def test_retorna_string_hex(self):
        h = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA256 = 64 chars hex

    def test_mesma_entrada_mesmo_hash(self):
        h1 = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        h2 = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        assert h1 == h2

    def test_descricao_diferente_hash_diferente(self):
        h1 = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        h2 = calcular_hash_item("PAPEL A3", "SP", 10.0, "2025-01-01")
        assert h1 != h2

    def test_uf_diferente_hash_diferente(self):
        h1 = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        h2 = calcular_hash_item("PAPEL A4", "MG", 10.0, "2025-01-01")
        assert h1 != h2

    def test_preco_diferente_hash_diferente(self):
        h1 = calcular_hash_item("PAPEL A4", "SP", 10.0, "2025-01-01")
        h2 = calcular_hash_item("PAPEL A4", "SP", 11.0, "2025-01-01")
        assert h1 != h2

    def test_preco_none_aceito(self):
        h = calcular_hash_item("PAPEL A4", "SP")
        assert len(h) == 64

    def test_descricao_case_insensitive(self):
        h1 = calcular_hash_item("papel a4", "SP")
        h2 = calcular_hash_item("PAPEL A4", "SP")
        assert h1 == h2  # normaliza para uppercase internamente

    def test_descricao_vazia(self):
        h = calcular_hash_item("", "SP")
        assert len(h) == 64


# ─────────────────────────────────────────────────────────
# Testes: calcular_hash_conteudo
# ─────────────────────────────────────────────────────────


class TestCalcularHashConteudo:
    def test_ignora_uf(self):
        """Hash de conteúdo não considera UF."""
        h_sp = calcular_hash_conteudo("PAPEL A4", 10.0)
        h_mg = calcular_hash_conteudo("PAPEL A4", 10.0)
        assert h_sp == h_mg

    def test_descricao_diferente(self):
        h1 = calcular_hash_conteudo("PAPEL A4", 10.0)
        h2 = calcular_hash_conteudo("PAPEL A3", 10.0)
        assert h1 != h2

    def test_retorna_hex_64(self):
        h = calcular_hash_conteudo("QUALQUER COISA")
        assert len(h) == 64


# ─────────────────────────────────────────────────────────
# Testes: analisar_duplicidade_lista
# ─────────────────────────────────────────────────────────


class TestAnalisarDuplicidadeLista:
    def test_lista_vazia(self):
        r = analisar_duplicidade_lista([], "SP")
        assert r.total_registros == 0
        assert r.taxa_duplicidade == 0.0
        assert r.dentro_sla is True

    def test_sem_duplicatas(self):
        itens = _itens_sem_duplicatas("SP", 50)
        r = analisar_duplicidade_lista(itens, "SP")
        assert r.total_registros == 50
        assert r.total_duplicados == 0
        assert r.taxa_duplicidade == 0.0
        assert r.dentro_sla is True

    def test_com_duplicatas_abaixo_sla(self):
        """Taxa de ~4% deve ficar dentro do SLA (<5%)."""
        itens = _itens_sem_duplicatas("MG", 100)
        # Adiciona 3 duplicatas (3%)
        itens += [itens[0].copy(), itens[1].copy(), itens[2].copy()]
        r = analisar_duplicidade_lista(itens, "MG")
        assert r.taxa_duplicidade < SLA_TAXA_DUPLICIDADE
        assert r.dentro_sla is True

    def test_com_duplicatas_acima_sla(self):
        """Taxa de 10% deve estar fora do SLA."""
        itens = _itens_com_duplicatas("RJ", 100, taxa=0.10)
        r = analisar_duplicidade_lista(itens, "RJ")
        assert r.taxa_duplicidade > SLA_TAXA_DUPLICIDADE
        assert r.dentro_sla is False

    def test_resultado_tem_campo_uf(self):
        r = analisar_duplicidade_lista(_itens_sem_duplicatas("BA"), "BA")
        assert r.uf == "BA"

    def test_amostras_suspeitas_coletadas(self):
        itens = _itens_com_duplicatas("RS", 50, taxa=0.20)
        r = analisar_duplicidade_lista(itens, "RS")
        assert len(r.amostras_suspeitas) > 0

    def test_campo_hash_existente(self):
        """Se campo hash_dedup já existe, usa diretamente."""
        itens = [{"hash_dedup": f"hash_{i}"} for i in range(20)]
        # Adiciona 5 duplicatas do hash_0
        itens += [{"hash_dedup": "hash_0"} for _ in range(5)]
        r = analisar_duplicidade_lista(itens, "SC")
        assert r.total_duplicados == 5

    def test_como_texto_contem_uf(self):
        r = analisar_duplicidade_lista(_itens_sem_duplicatas("DF"), "DF")
        texto = r.como_texto()
        assert "DF" in texto


# ─────────────────────────────────────────────────────────
# Testes: SLA por UF — 15 UFs
# ─────────────────────────────────────────────────────────


class TestSLADeduplicacao15UFs:
    @pytest.mark.parametrize("uf", UFS_PRIORITARIAS)
    def test_uf_sem_duplicatas_dentro_sla(self, uf: str):
        """Cada UF com dados limpos deve estar dentro do SLA."""
        itens = _itens_sem_duplicatas(uf, 50)
        r = analisar_duplicidade_lista(itens, uf)
        assert r.dentro_sla is True, f"UF {uf}: {r.como_texto()}"

    @pytest.mark.parametrize("uf", UFS_PRIORITARIAS)
    def test_uf_com_3pct_duplicatas_dentro_sla(self, uf: str):
        """3% de duplicatas deve estar dentro do SLA de 5%."""
        itens = _itens_sem_duplicatas(uf, 100)
        itens += [itens[0].copy(), itens[1].copy(), itens[2].copy()]
        r = analisar_duplicidade_lista(itens, uf)
        assert r.dentro_sla is True, f"UF {uf}: {r.como_texto()}"


# ─────────────────────────────────────────────────────────
# Testes: detectar_duplicatas_cross_uf
# ─────────────────────────────────────────────────────────


class TestDetectarDuplicatasCrossUF:
    def test_sem_cross_uf(self):
        """Itens distintos por UF → sem suspeitos."""
        itens_por_uf = {
            "SP": [_item(f"ITEM SP {i}", "SP") for i in range(10)],
            "MG": [_item(f"ITEM MG {i}", "MG") for i in range(10)],
        }
        suspeitos = detectar_duplicatas_cross_uf(itens_por_uf)
        assert len(suspeitos) == 0

    def test_com_cross_uf(self):
        """Mesmo item em SP e MG → detectado como cross-UF."""
        itens_por_uf = {
            "SP": [_item("PAPEL A4 75G", "SP", 10.0)],
            "MG": [_item("PAPEL A4 75G", "MG", 10.0)],  # mesmo conteúdo
        }
        suspeitos = detectar_duplicatas_cross_uf(itens_por_uf)
        assert len(suspeitos) >= 1
        ufs_detectadas = suspeitos[0]["ufs"]
        assert "SP" in ufs_detectadas
        assert "MG" in ufs_detectadas

    def test_retorna_lista_com_campos_obrigatorios(self):
        itens_por_uf = {
            "SP": [_item("CANETA BIC", "SP", 5.0)],
            "RJ": [_item("CANETA BIC", "RJ", 5.0)],
        }
        suspeitos = detectar_duplicatas_cross_uf(itens_por_uf)
        for s in suspeitos:
            assert "hash_conteudo" in s
            assert "ufs" in s
            assert "exemplo" in s

    def test_cross_uf_multiplos_estados(self):
        """Item idêntico em 3 UFs."""
        itens_por_uf = {uf: [_item("CANETA PRETA", uf, 3.0)] for uf in ["SP", "MG", "RJ"]}
        suspeitos = detectar_duplicatas_cross_uf(itens_por_uf)
        assert len(suspeitos) >= 1
        assert len(suspeitos[0]["ufs"]) == 3

    def test_dict_vazio(self):
        suspeitos = detectar_duplicatas_cross_uf({})
        assert suspeitos == []


# ─────────────────────────────────────────────────────────
# Testes: gerar_relatorio_deduplicacao
# ─────────────────────────────────────────────────────────


class TestGerarRelatorioDeduplicacao:
    def _resultado(self, uf: str, taxa: float) -> ResultadoDeduplicacao:
        total = 100
        distintos = int(total * (1 - taxa))
        duplicados = total - distintos
        return ResultadoDeduplicacao(
            uf=uf,
            total_registros=total,
            total_distintos=distintos,
            total_duplicados=duplicados,
            taxa_duplicidade=taxa,
            dentro_sla=taxa <= SLA_TAXA_DUPLICIDADE,
        )

    def test_relatorio_gerado(self):
        resultados = [self._resultado(uf, 0.02) for uf in ["SP", "MG", "RJ"]]
        relatorio = gerar_relatorio_deduplicacao(resultados)
        assert "RELATÓRIO DE DEDUPLICAÇÃO" in relatorio
        assert "SP" in relatorio
        assert "MG" in relatorio

    def test_relatorio_15_ufs(self):
        resultados = [self._resultado(uf, 0.01) for uf in UFS_PRIORITARIAS]
        relatorio = gerar_relatorio_deduplicacao(resultados)
        assert "15/15" in relatorio

    def test_relatorio_com_cross_uf(self):
        resultados = [self._resultado("SP", 0.02)]
        cross_uf = [{"ufs": ["SP", "MG"], "exemplo": {"descricao_normalizada": "PAPEL A4"}}]
        relatorio = gerar_relatorio_deduplicacao(resultados, cross_uf)
        assert "CROSS-UF" in relatorio
        assert "SP" in relatorio

    def test_relatorio_com_uf_fora_sla(self):
        resultados = [
            self._resultado("SP", 0.02),
            self._resultado("MG", 0.08),  # acima do SLA
        ]
        relatorio = gerar_relatorio_deduplicacao(resultados)
        assert "fora do SLA" in relatorio.lower() or "ACIMA DO SLA" in relatorio

    def test_relatorio_lista_vazia(self):
        relatorio = gerar_relatorio_deduplicacao([])
        assert "RELATÓRIO" in relatorio
