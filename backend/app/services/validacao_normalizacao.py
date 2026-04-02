"""Validação de normalização — Semana 13.

Amostragem estratificada (50 itens por UF = 750 total),
cálculo de taxa de acerto por UF e categoria, e relatório
de qualidade por UF × categoria.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Any

from app.services.normalizacao import (
    limpar_descricao,
    normalizar_sinonimo_regional,
    normalizar_unidade,
)

logger = logging.getLogger(__name__)

# SLA de taxa de acerto de normalização
SLA_TAXA_ACERTO: float = 0.85  # 85%

# Tamanho da amostra por UF
AMOSTRA_POR_UF: int = 50

# UFs prioritárias Semana 13
UFS_PRIORITARIAS: list[str] = [
    "DF", "SP", "MG", "RJ", "BA", "RS", "PE", "CE",
    "SC", "PR", "ES", "MT", "GO", "PI", "AL",
]


@dataclass
class ResultadoNormalizacaoItem:
    """Resultado de validação de normalização de um item."""

    item_id: str
    uf: str
    categoria: str
    descricao_original: str
    descricao_normalizada: str
    unidade_normalizada: str | None
    sinonimos_aplicados: list[str]
    classificado: bool  # True se passou pelo pipeline sem erro
    score_qualidade: float  # 0.0 – 1.0


@dataclass
class ResultadoNormalizacaoUF:
    """Resultado agregado de validação de normalização para uma UF."""

    uf: str
    total_amostrado: int
    total_classificado: int
    taxa_acerto: float
    dentro_sla: bool
    por_categoria: dict[str, dict[str, Any]] = field(default_factory=dict)
    itens_problematicos: list[dict[str, Any]] = field(default_factory=list)

    def como_texto(self) -> str:
        status = "✓ OK" if self.dentro_sla else "✗ ABAIXO DO SLA"
        return (
            f"UF={self.uf} | amostrado={self.total_amostrado} | "
            f"classificado={self.total_classificado} | "
            f"taxa={self.taxa_acerto:.1%} | {status}"
        )


def amostrar_itens_por_uf(
    itens: list[dict[str, Any]],
    uf: str,
    n: int = AMOSTRA_POR_UF,
    seed: int | None = 42,
) -> list[dict[str, Any]]:
    """Retorna amostra estratificada de itens por UF.

    Se houver menos de n itens disponíveis, retorna todos.
    A estratificação é por categoria (proporção aproximada).

    Args:
        itens: Lista de dicts com ao menos 'descricao' e 'categoria'.
        uf: Sigla da UF (para logging).
        n: Tamanho da amostra (default 50).
        seed: Seed para reproducibilidade (default 42).

    Returns:
        Lista de itens amostrados.
    """
    if not itens:
        return []

    rng = random.Random(seed)

    if len(itens) <= n:
        logger.debug("UF %s: apenas %d itens, retornando todos", uf, len(itens))
        return list(itens)

    # Estratificação por categoria
    por_categoria: dict[str, list[dict[str, Any]]] = {}
    for item in itens:
        cat = item.get("categoria", "SEM_CATEGORIA")
        por_categoria.setdefault(cat, []).append(item)

    amostra: list[dict[str, Any]] = []
    cats = list(por_categoria.keys())
    total = len(itens)

    for cat in cats:
        itens_cat = por_categoria[cat]
        proporcao = len(itens_cat) / total
        qtd_cat = max(1, round(n * proporcao))
        amostrados = rng.sample(itens_cat, min(qtd_cat, len(itens_cat)))
        amostra.extend(amostrados)

    # Completar até n se sobrar espaço (ou truncar se passou)
    if len(amostra) > n:
        rng.shuffle(amostra)
        amostra = amostra[:n]
    elif len(amostra) < n:
        restantes = [i for i in itens if i not in amostra]
        extras = rng.sample(restantes, min(n - len(amostra), len(restantes)))
        amostra.extend(extras)

    logger.debug("UF %s: amostra=%d itens (de %d)", uf, len(amostra), len(itens))
    return amostra


def validar_item_normalizacao(
    item: dict[str, Any],
    uf: str,
) -> ResultadoNormalizacaoItem:
    """Valida a qualidade de normalização de um item.

    Critérios de sucesso:
    - descricao normalizada não vazia
    - unidade normalizada válida (ou None se não disponível)
    - sinônimos regionais aplicados quando detectável

    Args:
        item: Dict com campos 'descricao', 'categoria', 'unidade' (opcional).
        uf: Sigla da UF.

    Returns:
        ResultadoNormalizacaoItem com score calculado.
    """
    item_id = str(item.get("id", item.get("numero_item", "?")))
    descricao_orig = item.get("descricao_original", item.get("descricao", ""))
    categoria = item.get("categoria", "SEM_CATEGORIA")
    unidade_orig = item.get("unidade_original", item.get("unidade", ""))

    # Score parcial
    score = 0.0
    sinonimos_aplicados: list[str] = []
    classificado = False

    try:
        # Passo 1: limpeza básica
        desc_limpa = limpar_descricao(descricao_orig)
        if desc_limpa:
            score += 0.4

        # Passo 2: sinônimos regionais
        desc_com_sinonimos = normalizar_sinonimo_regional(desc_limpa, uf)
        if desc_com_sinonimos != desc_limpa:
            sinonimos_aplicados.append(f"{desc_limpa[:20]}→{desc_com_sinonimos[:20]}")
            score += 0.2

        # Passo 3: unidade normalizada
        unidade_norm = normalizar_unidade(unidade_orig) if unidade_orig else None
        if unidade_orig and unidade_norm:
            score += 0.2  # unidade reconhecida
        elif not unidade_orig:
            score += 0.1  # sem unidade original (não penaliza totalmente)

        # Passo 4: descrição mínima útil (> 5 chars após limpeza)
        if len(desc_limpa.strip()) > 5:
            score += 0.2

        classificado = score >= 0.6

        return ResultadoNormalizacaoItem(
            item_id=item_id,
            uf=uf,
            categoria=categoria,
            descricao_original=descricao_orig,
            descricao_normalizada=desc_com_sinonimos or desc_limpa,
            unidade_normalizada=unidade_norm,
            sinonimos_aplicados=sinonimos_aplicados,
            classificado=classificado,
            score_qualidade=min(score, 1.0),
        )

    except Exception as exc:
        logger.warning("Erro ao normalizar item %s da UF %s: %s", item_id, uf, exc)
        return ResultadoNormalizacaoItem(
            item_id=item_id,
            uf=uf,
            categoria=categoria,
            descricao_original=descricao_orig,
            descricao_normalizada="",
            unidade_normalizada=None,
            sinonimos_aplicados=[],
            classificado=False,
            score_qualidade=0.0,
        )


def validar_normalizacao_uf(
    itens: list[dict[str, Any]],
    uf: str,
    n_amostra: int = AMOSTRA_POR_UF,
) -> ResultadoNormalizacaoUF:
    """Valida normalização de uma amostra de itens de uma UF.

    Args:
        itens: Lista de itens da UF.
        uf: Sigla da UF.
        n_amostra: Tamanho da amostra a validar.

    Returns:
        ResultadoNormalizacaoUF com estatísticas e SLA.
    """
    amostra = amostrar_itens_por_uf(itens, uf, n_amostra)

    if not amostra:
        return ResultadoNormalizacaoUF(
            uf=uf,
            total_amostrado=0,
            total_classificado=0,
            taxa_acerto=0.0,
            dentro_sla=False,
        )

    resultados = [validar_item_normalizacao(item, uf) for item in amostra]
    total = len(resultados)
    classificados = sum(1 for r in resultados if r.classificado)
    taxa = classificados / total if total > 0 else 0.0

    # Agrega por categoria
    por_categoria: dict[str, dict[str, Any]] = {}
    for r in resultados:
        cat = r.categoria
        if cat not in por_categoria:
            por_categoria[cat] = {"total": 0, "classificados": 0, "score_medio": 0.0, "_scores": []}
        por_categoria[cat]["total"] += 1
        if r.classificado:
            por_categoria[cat]["classificados"] += 1
        por_categoria[cat]["_scores"].append(r.score_qualidade)

    for cat, dados in por_categoria.items():
        scores = dados.pop("_scores")
        dados["taxa_acerto"] = dados["classificados"] / dados["total"] if dados["total"] > 0 else 0.0
        dados["score_medio"] = sum(scores) / len(scores) if scores else 0.0

    # Itens problemáticos (score < 0.6)
    problematicos = [
        {
            "item_id": r.item_id,
            "uf": r.uf,
            "categoria": r.categoria,
            "descricao_original": r.descricao_original[:80],
            "score": r.score_qualidade,
        }
        for r in resultados
        if not r.classificado
    ]

    return ResultadoNormalizacaoUF(
        uf=uf,
        total_amostrado=total,
        total_classificado=classificados,
        taxa_acerto=taxa,
        dentro_sla=taxa >= SLA_TAXA_ACERTO,
        por_categoria=por_categoria,
        itens_problematicos=problematicos,
    )


def gerar_relatorio_normalizacao(
    resultados: list[ResultadoNormalizacaoUF],
) -> str:
    """Gera relatório textual de qualidade de normalização por UF × categoria.

    Args:
        resultados: Lista de ResultadoNormalizacaoUF (uma por UF).

    Returns:
        String formatada com ~75 linhas de relatório.
    """
    linhas: list[str] = [
        "=" * 65,
        "RELATÓRIO DE QUALIDADE — NORMALIZAÇÃO — SEMANA 13",
        "=" * 65,
    ]

    dentro_sla = [r for r in resultados if r.dentro_sla]
    fora_sla = [r for r in resultados if not r.dentro_sla]

    total_amostrado = sum(r.total_amostrado for r in resultados)
    total_classificado = sum(r.total_classificado for r in resultados)
    taxa_geral = total_classificado / total_amostrado if total_amostrado > 0 else 0.0

    linhas += [
        f"UFs dentro do SLA (≥85%): {len(dentro_sla)}/{len(resultados)}",
        f"UFs fora do SLA: {len(fora_sla)}",
        f"Total amostrado: {total_amostrado} itens",
        f"Taxa geral de acerto: {taxa_geral:.1%}",
        "",
        "DETALHE POR UF:",
        "-" * 50,
    ]

    for r in sorted(resultados, key=lambda x: x.taxa_acerto, reverse=True):
        linhas.append(f"  {r.como_texto()}")

    linhas += [
        "",
        "DETALHE POR UF × CATEGORIA:",
        "-" * 50,
    ]

    for r in sorted(resultados, key=lambda x: x.uf):
        if not r.por_categoria:
            linhas.append(f"  {r.uf}: sem categorias na amostra")
            continue
        for cat, dados in sorted(r.por_categoria.items()):
            taxa_cat = dados.get("taxa_acerto", 0.0)
            score_med = dados.get("score_medio", 0.0)
            total_cat = dados.get("total", 0)
            status = "✓" if taxa_cat >= SLA_TAXA_ACERTO else "✗"
            linhas.append(
                f"  {status} {r.uf:<4} | {cat:<25} | "
                f"n={total_cat:>3} | taxa={taxa_cat:.0%} | score={score_med:.2f}"
            )

    if fora_sla:
        linhas += [
            "",
            "ITENS PROBLEMÁTICOS (sample):",
            "-" * 50,
        ]
        count = 0
        for r in fora_sla:
            for p in r.itens_problematicos[:3]:
                linhas.append(
                    f"  UF={p['uf']} cat={p['categoria'][:20]} "
                    f"score={p['score']:.2f} desc='{p['descricao_original'][:40]}'"
                )
                count += 1
                if count >= 10:
                    break
            if count >= 10:
                break

    linhas.append("=" * 65)
    return "\n".join(linhas)
