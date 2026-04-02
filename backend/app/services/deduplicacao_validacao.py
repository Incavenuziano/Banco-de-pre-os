"""Validação e análise de deduplicação — Semana 13.

Provê funções para calcular taxa de duplicidade por UF,
detectar duplicatas cross-UF e gerar fila de revisão manual.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# SLA de duplicidade máxima por UF
SLA_TAXA_DUPLICIDADE: float = 0.05  # 5%


@dataclass
class ResultadoDeduplicacao:
    """Resultado de análise de deduplicação para uma UF."""

    uf: str
    total_registros: int
    total_distintos: int
    total_duplicados: int
    taxa_duplicidade: float
    dentro_sla: bool
    amostras_suspeitas: list[dict[str, Any]] = field(default_factory=list)

    def como_texto(self) -> str:
        status = "✓ OK" if self.dentro_sla else "✗ ACIMA DO SLA"
        return (
            f"UF={self.uf} | total={self.total_registros} | "
            f"distintos={self.total_distintos} | "
            f"duplicados={self.total_duplicados} | "
            f"taxa={self.taxa_duplicidade:.1%} | {status}"
        )


def calcular_hash_item(
    descricao: str,
    uf: str,
    preco: float | None = None,
    data_ref: str | None = None,
) -> str:
    """Calcula hash SHA256 para deduplicação de item.

    Args:
        descricao: Descrição normalizada do item.
        uf: Sigla da UF.
        preco: Preço unitário (opcional).
        data_ref: Data de referência ISO (opcional).

    Returns:
        Hash hexadecimal SHA256.
    """
    partes = [
        descricao.upper().strip() if descricao else "",
        uf.upper() if uf else "",
        f"{preco:.4f}" if preco is not None else "",
        str(data_ref or ""),
    ]
    payload = "|".join(partes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def calcular_hash_conteudo(
    descricao: str,
    preco: float | None = None,
) -> str:
    """Calcula hash de conteúdo para detectar duplicatas cross-UF.

    Ignora a UF — detecta mesma publicação replicada em múltiplas UFs.

    Args:
        descricao: Descrição normalizada do item.
        preco: Preço unitário (opcional).

    Returns:
        Hash hexadecimal SHA256.
    """
    partes = [
        descricao.upper().strip() if descricao else "",
        f"{preco:.4f}" if preco is not None else "",
    ]
    payload = "|".join(partes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def analisar_duplicidade_lista(
    itens: list[dict[str, Any]],
    uf: str,
    campo_hash: str = "hash_dedup",
) -> ResultadoDeduplicacao:
    """Analisa taxa de duplicidade em uma lista de itens.

    Args:
        itens: Lista de dicts com campo de hash ou dados brutos.
        uf: Sigla da UF.
        campo_hash: Nome do campo de hash no dict (default 'hash_dedup').

    Returns:
        ResultadoDeduplicacao com estatísticas.
    """
    if not itens:
        return ResultadoDeduplicacao(
            uf=uf,
            total_registros=0,
            total_distintos=0,
            total_duplicados=0,
            taxa_duplicidade=0.0,
            dentro_sla=True,
        )

    total = len(itens)
    hashes_vistos: dict[str, int] = {}
    amostras_suspeitas: list[dict[str, Any]] = []

    for item in itens:
        # Calcula hash se não presente
        if campo_hash in item:
            h = item[campo_hash]
        else:
            descricao = item.get("descricao_normalizada", item.get("descricao", ""))
            preco = item.get("preco_unitario")
            data = item.get("data_referencia")
            h = calcular_hash_item(descricao, uf, preco, data)

        if h in hashes_vistos:
            hashes_vistos[h] += 1
            if len(amostras_suspeitas) < 100:
                amostras_suspeitas.append({
                    "hash": h,
                    "item": item,
                    "ocorrencias": hashes_vistos[h],
                })
        else:
            hashes_vistos[h] = 1

    distintos = len(hashes_vistos)
    duplicados = total - distintos
    taxa = duplicados / total if total > 0 else 0.0

    return ResultadoDeduplicacao(
        uf=uf,
        total_registros=total,
        total_distintos=distintos,
        total_duplicados=duplicados,
        taxa_duplicidade=taxa,
        dentro_sla=taxa <= SLA_TAXA_DUPLICIDADE,
        amostras_suspeitas=amostras_suspeitas,
    )


def detectar_duplicatas_cross_uf(
    itens_por_uf: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Detecta itens duplicados entre UFs diferentes.

    Calcula hash de conteúdo (sem UF) e identifica hashes que aparecem
    em mais de uma UF.

    Args:
        itens_por_uf: Dict {uf: lista_de_itens}.

    Returns:
        Lista de suspeitos de duplicação cross-UF com detalhes.
    """
    hash_para_ufs: dict[str, list[str]] = {}
    hash_para_exemplos: dict[str, dict[str, Any]] = {}

    for uf, itens in itens_por_uf.items():
        for item in itens:
            descricao = item.get("descricao_normalizada", item.get("descricao", ""))
            preco = item.get("preco_unitario")
            h = calcular_hash_conteudo(descricao, preco)

            if h not in hash_para_ufs:
                hash_para_ufs[h] = []
                hash_para_exemplos[h] = item

            if uf not in hash_para_ufs[h]:
                hash_para_ufs[h].append(uf)

    suspeitos: list[dict[str, Any]] = []
    for h, ufs in hash_para_ufs.items():
        if len(ufs) > 1:
            suspeitos.append({
                "hash_conteudo": h,
                "ufs": sorted(ufs),
                "exemplo": hash_para_exemplos.get(h, {}),
            })

    logger.info(
        "Detecção cross-UF: %d hashes únicos, %d suspeitos de replicação",
        len(hash_para_ufs),
        len(suspeitos),
    )
    return suspeitos


def gerar_relatorio_deduplicacao(
    resultados: list[ResultadoDeduplicacao],
    cross_uf: list[dict[str, Any]] | None = None,
) -> str:
    """Gera relatório textual de deduplicação consolidado.

    Args:
        resultados: Lista de ResultadoDeduplicacao por UF.
        cross_uf: Lista de suspeitos cross-UF (opcional).

    Returns:
        String formatada com relatório completo.
    """
    linhas: list[str] = [
        "=" * 60,
        "RELATÓRIO DE DEDUPLICAÇÃO — SEMANA 13",
        "=" * 60,
    ]

    dentro_sla = [r for r in resultados if r.dentro_sla]
    fora_sla = [r for r in resultados if not r.dentro_sla]

    linhas += [
        f"UFs dentro do SLA (<5%): {len(dentro_sla)}/{len(resultados)}",
        f"UFs fora do SLA: {len(fora_sla)}",
        "",
        "DETALHE POR UF:",
        "-" * 40,
    ]

    for r in sorted(resultados, key=lambda x: x.taxa_duplicidade, reverse=True):
        linhas.append(f"  {r.como_texto()}")

    if cross_uf is not None:
        linhas += [
            "",
            f"DUPLICATAS CROSS-UF: {len(cross_uf)} suspeitos",
        ]
        for item in cross_uf[:10]:
            ufs_str = ", ".join(item["ufs"])
            exemplo = item.get("exemplo", {})
            desc = exemplo.get("descricao_normalizada", exemplo.get("descricao", "N/A"))[:50]
            linhas.append(f"  UFs={ufs_str} | '{desc}'")

    linhas.append("=" * 60)
    return "\n".join(linhas)
