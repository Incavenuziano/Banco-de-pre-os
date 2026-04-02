"""Otimizador de queries e validação de performance — Semana 13.

Provê estratégias de índices, planos de query e benchmarking
de latência para os cenários críticos do Banco de Preços.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

# SLA de latência por cenário (segundos)
SLA_LATENCIA: dict[str, float] = {
    "busca_item_uf": 0.5,
    "agregacao_uf_categoria": 1.0,
    "estatistica_completa": 2.0,
    "export_csv_10k": 5.0,
}

# Índices recomendados para a Semana 13
INDICES_RECOMENDADOS: list[dict[str, Any]] = [
    {
        "nome": "idx_itens_descricao_limpa",
        "tabela": "itens",
        "colunas": ["descricao_limpa"],
        "tipo": "btree",
        "razao": "Busca textual por item normalizado",
        "query_beneficiada": "busca_item_uf",
    },
    {
        "nome": "idx_orgaos_uf",
        "tabela": "orgaos",
        "colunas": ["uf"],
        "tipo": "btree",
        "razao": "Filtro por UF em queries de agregação",
        "query_beneficiada": "agregacao_uf_categoria",
    },
    {
        "nome": "idx_contratacoes_data_publicacao",
        "tabela": "contratacoes",
        "colunas": ["data_publicacao"],
        "tipo": "btree",
        "razao": "Queries por período de publicação",
        "query_beneficiada": "estatistica_completa",
    },
    {
        "nome": "idx_fontes_preco_item_data",
        "tabela": "fontes_preco",
        "colunas": ["item_id", "data_referencia"],
        "tipo": "btree",
        "razao": "Busca de preços por item e período",
        "query_beneficiada": "estatistica_completa",
    },
    {
        "nome": "idx_itens_categoria",
        "tabela": "itens",
        "colunas": ["categoria_id"],
        "tipo": "btree",
        "razao": "Agregação por categoria",
        "query_beneficiada": "agregacao_uf_categoria",
    },
    {
        "nome": "idx_contratacoes_orgao_data",
        "tabela": "contratacoes",
        "colunas": ["orgao_id", "data_publicacao"],
        "tipo": "btree",
        "razao": "Queries por órgão + período",
        "query_beneficiada": "export_csv_10k",
    },
    {
        "nome": "idx_fontes_preco_qualidade",
        "tabela": "fontes_preco",
        "colunas": ["qualidade_tipo"],
        "tipo": "btree",
        "razao": "Filtro por qualidade de fonte",
        "query_beneficiada": "estatistica_completa",
    },
]


@dataclass
class ResultadoBenchmark:
    """Resultado de benchmark de uma query."""

    nome: str
    latencia_ms: float
    sla_ms: float
    dentro_sla: bool
    amostras: list[float] = field(default_factory=list)
    erro: str | None = None

    @property
    def latencia_p99_ms(self) -> float | None:
        if not self.amostras:
            return None
        s = sorted(self.amostras)
        idx = int(len(s) * 0.99)
        return s[min(idx, len(s) - 1)]

    def como_texto(self) -> str:
        status = "✓ OK" if self.dentro_sla else "✗ ACIMA DO SLA"
        p99 = f"p99={self.latencia_p99_ms:.1f}ms" if self.latencia_p99_ms else ""
        return (
            f"{self.nome:<30} | {self.latencia_ms:>7.1f}ms "
            f"(SLA {self.sla_ms:.0f}ms) | {p99} | {status}"
        )


def medir_latencia(
    fn: Callable[[], Any],
    n_repeticoes: int = 5,
) -> tuple[float, list[float]]:
    """Mede latência média de uma função em milissegundos.

    Args:
        fn: Função a medir (sem argumentos).
        n_repeticoes: Número de execuções para média.

    Returns:
        Tupla (latencia_media_ms, lista_de_amostras_ms).
    """
    amostras: list[float] = []
    for _ in range(n_repeticoes):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        amostras.append((t1 - t0) * 1000)
    media = sum(amostras) / len(amostras)
    return media, amostras


def benchmark_query(
    nome: str,
    fn: Callable[[], Any],
    n_repeticoes: int = 5,
) -> ResultadoBenchmark:
    """Executa benchmark de uma query e compara ao SLA.

    Args:
        nome: Nome do cenário (deve existir em SLA_LATENCIA).
        fn: Função que executa a query.
        n_repeticoes: Número de repetições para média.

    Returns:
        ResultadoBenchmark com latência e status de SLA.
    """
    sla_s = SLA_LATENCIA.get(nome, 2.0)
    sla_ms = sla_s * 1000

    try:
        latencia_ms, amostras = medir_latencia(fn, n_repeticoes)
        return ResultadoBenchmark(
            nome=nome,
            latencia_ms=latencia_ms,
            sla_ms=sla_ms,
            dentro_sla=latencia_ms <= sla_ms,
            amostras=amostras,
        )
    except Exception as exc:
        logger.error("Benchmark %s falhou: %s", nome, exc)
        return ResultadoBenchmark(
            nome=nome,
            latencia_ms=float("inf"),
            sla_ms=sla_ms,
            dentro_sla=False,
            erro=str(exc),
        )


def gerar_sql_indices() -> list[str]:
    """Gera statements SQL para criação dos índices recomendados.

    Returns:
        Lista de strings SQL CREATE INDEX.
    """
    sqls: list[str] = []
    for idx in INDICES_RECOMENDADOS:
        cols = ", ".join(idx["colunas"])
        sql = (
            f"CREATE INDEX IF NOT EXISTS {idx['nome']} "
            f"ON {idx['tabela']} USING {idx['tipo']} ({cols});"
        )
        sqls.append(sql)
    return sqls


def gerar_relatorio_performance(
    benchmarks: list[ResultadoBenchmark],
    indices_aplicados: list[str] | None = None,
) -> str:
    """Gera relatório textual de performance de queries.

    Args:
        benchmarks: Lista de ResultadoBenchmark por cenário.
        indices_aplicados: Lista de nomes de índices já aplicados.

    Returns:
        String formatada com relatório de performance.
    """
    linhas: list[str] = [
        "=" * 65,
        "RELATÓRIO DE PERFORMANCE — SEMANA 13",
        "=" * 65,
    ]

    dentro_sla = [b for b in benchmarks if b.dentro_sla and not b.erro]
    fora_sla = [b for b in benchmarks if not b.dentro_sla or b.erro]

    linhas += [
        f"Cenários dentro do SLA: {len(dentro_sla)}/{len(benchmarks)}",
        "",
        "LATÊNCIAS POR CENÁRIO:",
        "-" * 50,
    ]

    for b in benchmarks:
        linhas.append(f"  {b.como_texto()}")
        if b.erro:
            linhas.append(f"    ERRO: {b.erro}")

    linhas += [
        "",
        "ÍNDICES RECOMENDADOS:",
        "-" * 50,
    ]

    for idx in INDICES_RECOMENDADOS:
        cols = ", ".join(idx["colunas"])
        aplicado = ""
        if indices_aplicados and idx["nome"] in indices_aplicados:
            aplicado = " [APLICADO]"
        linhas.append(
            f"  {idx['tabela']}.({cols}) → {idx['razao']}{aplicado}"
        )

    linhas += [
        "",
        "SQL DE CRIAÇÃO DE ÍNDICES:",
        "-" * 50,
    ]
    for sql in gerar_sql_indices():
        linhas.append(f"  {sql}")

    linhas.append("=" * 65)
    return "\n".join(linhas)
