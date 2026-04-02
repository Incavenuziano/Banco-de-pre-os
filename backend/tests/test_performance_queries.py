"""Testes de performance de queries — Semana 13.

Cobre: medir_latencia, benchmark_query, gerar_sql_indices,
gerar_relatorio_performance, SLA de latência.
"""

from __future__ import annotations

import time

import pytest

from app.services.query_optimizer import (
    INDICES_RECOMENDADOS,
    SLA_LATENCIA,
    ResultadoBenchmark,
    benchmark_query,
    gerar_relatorio_performance,
    gerar_sql_indices,
    medir_latencia,
)


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────


def _fn_rapida():
    """Simula query rápida (~0ms)."""
    return sum(range(100))


def _fn_lenta(ms: float = 600):
    """Simula query com latência específica em ms."""
    time.sleep(ms / 1000)


# ─────────────────────────────────────────────────────────
# Testes: medir_latencia
# ─────────────────────────────────────────────────────────


class TestMedirLatencia:
    def test_retorna_media_e_amostras(self):
        media, amostras = medir_latencia(_fn_rapida, n_repeticoes=3)
        assert isinstance(media, float)
        assert len(amostras) == 3

    def test_media_e_media_das_amostras(self):
        media, amostras = medir_latencia(_fn_rapida, n_repeticoes=5)
        esperado = sum(amostras) / len(amostras)
        assert abs(media - esperado) < 1e-9

    def test_latencia_positiva(self):
        media, _ = medir_latencia(_fn_rapida, n_repeticoes=3)
        assert media >= 0

    def test_n_repeticoes_1(self):
        media, amostras = medir_latencia(_fn_rapida, n_repeticoes=1)
        assert len(amostras) == 1
        assert amostras[0] == pytest.approx(media)


# ─────────────────────────────────────────────────────────
# Testes: benchmark_query
# ─────────────────────────────────────────────────────────


class TestBenchmarkQuery:
    def test_retorna_resultado_benchmark(self):
        b = benchmark_query("busca_item_uf", _fn_rapida, n_repeticoes=3)
        assert isinstance(b, ResultadoBenchmark)

    def test_query_rapida_dentro_sla(self):
        """Função < 1ms deve estar dentro de qualquer SLA razoável."""
        b = benchmark_query("busca_item_uf", _fn_rapida, n_repeticoes=3)
        assert b.dentro_sla is True

    def test_nome_preservado(self):
        b = benchmark_query("agregacao_uf_categoria", _fn_rapida, n_repeticoes=2)
        assert b.nome == "agregacao_uf_categoria"

    def test_sla_correto_para_cenario(self):
        b = benchmark_query("estatistica_completa", _fn_rapida, n_repeticoes=2)
        assert b.sla_ms == SLA_LATENCIA["estatistica_completa"] * 1000

    def test_erro_capturado(self):
        def fn_quebrada():
            raise RuntimeError("erro simulado")

        b = benchmark_query("busca_item_uf", fn_quebrada, n_repeticoes=2)
        assert b.dentro_sla is False
        assert b.erro is not None
        assert "erro simulado" in b.erro

    def test_amostras_coletadas(self):
        b = benchmark_query("busca_item_uf", _fn_rapida, n_repeticoes=5)
        assert len(b.amostras) == 5

    def test_como_texto(self):
        b = benchmark_query("busca_item_uf", _fn_rapida, n_repeticoes=3)
        texto = b.como_texto()
        assert "busca_item_uf" in texto
        assert "ms" in texto

    def test_p99_latencia(self):
        b = benchmark_query("busca_item_uf", _fn_rapida, n_repeticoes=10)
        assert b.latencia_p99_ms is not None
        assert b.latencia_p99_ms >= b.latencia_ms * 0.5  # p99 >= metade da média

    def test_cenario_desconhecido_usa_sla_default(self):
        b = benchmark_query("cenario_inexistente", _fn_rapida, n_repeticoes=2)
        assert b.sla_ms == 2000  # default 2s


# ─────────────────────────────────────────────────────────
# Testes: SLA_LATENCIA — constantes corretas
# ─────────────────────────────────────────────────────────


class TestSLALatenciaConstantes:
    def test_busca_item_uf_sla(self):
        assert SLA_LATENCIA["busca_item_uf"] == 0.5

    def test_agregacao_uf_categoria_sla(self):
        assert SLA_LATENCIA["agregacao_uf_categoria"] == 1.0

    def test_estatistica_completa_sla(self):
        assert SLA_LATENCIA["estatistica_completa"] == 2.0

    def test_export_csv_sla(self):
        assert SLA_LATENCIA["export_csv_10k"] == 5.0


# ─────────────────────────────────────────────────────────
# Testes: gerar_sql_indices
# ─────────────────────────────────────────────────────────


class TestGerarSQLIndices:
    def test_retorna_lista_de_strings(self):
        sqls = gerar_sql_indices()
        assert isinstance(sqls, list)
        assert all(isinstance(s, str) for s in sqls)

    def test_quantidade_indices(self):
        sqls = gerar_sql_indices()
        assert len(sqls) == len(INDICES_RECOMENDADOS)

    def test_sql_cria_index(self):
        sqls = gerar_sql_indices()
        for sql in sqls:
            assert "CREATE INDEX" in sql.upper()

    def test_sql_if_not_exists(self):
        sqls = gerar_sql_indices()
        for sql in sqls:
            assert "IF NOT EXISTS" in sql.upper()

    def test_sql_contem_nome_indice(self):
        sqls = gerar_sql_indices()
        for idx, sql in zip(INDICES_RECOMENDADOS, sqls):
            assert idx["nome"] in sql

    def test_sql_contem_tabela(self):
        sqls = gerar_sql_indices()
        for idx, sql in zip(INDICES_RECOMENDADOS, sqls):
            assert idx["tabela"] in sql

    def test_sql_contem_coluna(self):
        sqls = gerar_sql_indices()
        for idx, sql in zip(INDICES_RECOMENDADOS, sqls):
            for col in idx["colunas"]:
                assert col in sql


# ─────────────────────────────────────────────────────────
# Testes: INDICES_RECOMENDADOS — estrutura
# ─────────────────────────────────────────────────────────


class TestIndicesRecomendados:
    def test_tem_indices_suficientes(self):
        assert len(INDICES_RECOMENDADOS) >= 5

    def test_cada_indice_tem_campos_obrigatorios(self):
        campos = ["nome", "tabela", "colunas", "tipo", "razao"]
        for idx in INDICES_RECOMENDADOS:
            for campo in campos:
                assert campo in idx, f"Índice {idx.get('nome')} sem campo '{campo}'"

    def test_colunas_e_lista(self):
        for idx in INDICES_RECOMENDADOS:
            assert isinstance(idx["colunas"], list)
            assert len(idx["colunas"]) >= 1

    def test_tipos_validos(self):
        tipos_validos = {"btree", "hash", "gin", "gist"}
        for idx in INDICES_RECOMENDADOS:
            assert idx["tipo"].lower() in tipos_validos


# ─────────────────────────────────────────────────────────
# Testes: gerar_relatorio_performance
# ─────────────────────────────────────────────────────────


class TestGerarRelatorioPerformance:
    def _benchmark(self, nome: str, latencia_ms: float) -> ResultadoBenchmark:
        sla_ms = SLA_LATENCIA.get(nome, 2.0) * 1000
        return ResultadoBenchmark(
            nome=nome,
            latencia_ms=latencia_ms,
            sla_ms=sla_ms,
            dentro_sla=latencia_ms <= sla_ms,
            amostras=[latencia_ms] * 5,
        )

    def test_relatorio_gerado(self):
        benchmarks = [
            self._benchmark("busca_item_uf", 100),
            self._benchmark("agregacao_uf_categoria", 500),
        ]
        relatorio = gerar_relatorio_performance(benchmarks)
        assert "RELATÓRIO DE PERFORMANCE" in relatorio

    def test_relatorio_contem_todos_cenarios(self):
        benchmarks = [self._benchmark(nome, 100) for nome in SLA_LATENCIA]
        relatorio = gerar_relatorio_performance(benchmarks)
        for nome in SLA_LATENCIA:
            assert nome in relatorio

    def test_relatorio_contem_indices_recomendados(self):
        benchmarks = [self._benchmark("busca_item_uf", 100)]
        relatorio = gerar_relatorio_performance(benchmarks)
        assert "ÍNDICES RECOMENDADOS" in relatorio

    def test_relatorio_contem_sql(self):
        benchmarks = [self._benchmark("busca_item_uf", 100)]
        relatorio = gerar_relatorio_performance(benchmarks)
        assert "CREATE INDEX" in relatorio.upper()

    def test_relatorio_indices_aplicados(self):
        benchmarks = [self._benchmark("busca_item_uf", 100)]
        indices_aplicados = ["idx_itens_descricao_limpa"]
        relatorio = gerar_relatorio_performance(benchmarks, indices_aplicados)
        assert "APLICADO" in relatorio

    def test_relatorio_lista_vazia(self):
        relatorio = gerar_relatorio_performance([])
        assert "RELATÓRIO" in relatorio
