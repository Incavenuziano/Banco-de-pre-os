"""Cálculo de score de confiança para fontes de preço.

O score (0-100) avalia a qualidade e confiabilidade de uma amostra
de preço com base em completude, fonte, evidência, normalização,
classificação e — com Fase 4 — decaimento temporal.

Decaimento temporal:
    Preços antigos têm menor relevância para pesquisa de mercado.
    Um fator multiplicativo (0.10–1.00) penaliza fontes com
    data_referencia distante da data base de consulta.

    Use calcular_score_fonte(fonte, data_base=date.today()) para
    aplicar o decaimento. Sem data_base (default None) o comportamento
    é idêntico à versão anterior (sem decaimento).
"""

from __future__ import annotations

from datetime import date
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Tabelas de referência
# ─────────────────────────────────────────────────────────────────────────────

_CONFIABILIDADE_FONTE: dict[str, int] = {
    "HOMOLOGADO":    30,
    "TABELA_OFICIAL": 25,
    "ESTIMADO":      15,
    "MERCADO":       10,
}

# (dias_max_inclusive, fator) — ordenados do mais recente ao mais antigo.
# Preços com mais de 5 anos recebem fator mínimo.
_TABELA_DECAIMENTO: list[tuple[int, float]] = [
    (30,   1.00),   # ≤ 30 dias: sem penalidade
    (90,   0.95),   # 31–90 dias: penalidade leve
    (180,  0.85),   # 91–180 dias: penalidade moderada
    (365,  0.70),   # 181–365 dias: penalidade significativa
    (730,  0.50),   # 1–2 anos: penalidade alta
    (1825, 0.30),   # 2–5 anos: penalidade severa
]
_FATOR_MUITO_ANTIGO: float = 0.10   # > 5 anos


# ─────────────────────────────────────────────────────────────────────────────
# Componentes individuais (expostos para calcular_score_detalhado)
# ─────────────────────────────────────────────────────────────────────────────

def _score_completude(fonte: dict[str, Any]) -> int:
    """Completude de campos — máx 20."""
    s = 0
    if fonte.get("url_origem"):
        s += 10
    if fonte.get("data_referencia"):
        s += 5
    if fonte.get("quantidade"):
        s += 5
    return s


def _score_confiabilidade(fonte: dict[str, Any]) -> int:
    """Confiabilidade da fonte — máx 30."""
    qualidade = str(fonte.get("qualidade_tipo") or "").upper()
    return _CONFIABILIDADE_FONTE.get(qualidade, 0)


def _score_evidencia(fonte: dict[str, Any]) -> int:
    """Evidência documental — máx 20."""
    s = 0
    if fonte.get("storage_path"):
        s += 10
    if fonte.get("hash_sha256"):
        s += 10
    return s


def _score_unidade(fonte: dict[str, Any]) -> int:
    """Unidade de medida normalizada — máx 15."""
    unidade = fonte.get("unidade_normalizada")
    if unidade and str(unidade).strip() and str(unidade).upper() != "OUTRO":
        return 15
    return 0


def _score_categoria(fonte: dict[str, Any]) -> int:
    """Categoria classificada — máx 15."""
    s = 0
    if fonte.get("categoria_id") is not None:
        s += 10
    score_class = fonte.get("score_classificacao")
    if score_class is not None and float(score_class) > 0.8:
        s += 5
    return s


# ─────────────────────────────────────────────────────────────────────────────
# Decaimento temporal
# ─────────────────────────────────────────────────────────────────────────────

def _parse_data(data_referencia: Any) -> date | None:
    """Converte string 'YYYY-MM-DD' ou objeto date para date. None se inválido."""
    if data_referencia is None:
        return None
    if isinstance(data_referencia, date):
        return data_referencia
    try:
        partes = str(data_referencia)[:10].split("-")
        return date(int(partes[0]), int(partes[1]), int(partes[2]))
    except (ValueError, IndexError):
        return None


def calcular_fator_temporal(
    data_referencia: Any,
    data_base: date | None = None,
) -> float:
    """Calcula o fator de decaimento temporal (0.10–1.00).

    Args:
        data_referencia: Data de referência do preço (str 'YYYY-MM-DD' ou date).
        data_base:       Data de comparação (default: date.today()).

    Returns:
        Fator multiplicativo:
            1.00  ≤ 30 dias
            0.95  31–90 dias
            0.85  91–180 dias
            0.70  181–365 dias
            0.50  1–2 anos
            0.30  2–5 anos
            0.10  > 5 anos
        Se data_referencia for None ou inválida, retorna 1.0 (sem penalidade).
        Se data_referencia for futura (> data_base), retorna 1.0.
    """
    dr = _parse_data(data_referencia)
    if dr is None:
        return 1.0

    if data_base is None:
        data_base = date.today()

    dias = (data_base - dr).days
    if dias < 0:
        return 1.0  # data futura — sem penalidade

    for dias_max, fator in _TABELA_DECAIMENTO:
        if dias <= dias_max:
            return fator

    return _FATOR_MUITO_ANTIGO


# ─────────────────────────────────────────────────────────────────────────────
# Funções públicas
# ─────────────────────────────────────────────────────────────────────────────

def calcular_score_fonte(
    fonte_preco: dict[str, Any],
    *,
    data_base: date | None = None,
) -> int:
    """Calcula score de confiança (0-100) de uma fonte de preço.

    Componentes com pesos:
    - Completude de campos (máx 20): url_origem +10, data_referencia +5, quantidade +5
    - Confiabilidade da fonte (máx 30): baseado em qualidade_tipo
    - Evidência (máx 20): storage_path +10, hash_sha256 +10
    - Unidade normalizada (máx 15): unidade válida +15
    - Categoria (máx 15): categoria_id +10, score_classificacao > 0.8 +5

    Decaimento temporal (opcional):
        Quando data_base é fornecida, aplica fator multiplicativo
        (calcular_fator_temporal) sobre o score base. Preços mais
        antigos recebem score menor.

    Args:
        fonte_preco: Dicionário com campos da fonte de preço.
        data_base:   Se fornecida, aplica decaimento temporal relativo
                     a esta data. Default None = sem decaimento
                     (comportamento idêntico à versão anterior).

    Returns:
        Inteiro entre 0 e 100.
    """
    score = (
        _score_completude(fonte_preco)
        + _score_confiabilidade(fonte_preco)
        + _score_evidencia(fonte_preco)
        + _score_unidade(fonte_preco)
        + _score_categoria(fonte_preco)
    )
    score = min(score, 100)

    if data_base is not None:
        fator = calcular_fator_temporal(
            fonte_preco.get("data_referencia"), data_base
        )
        score = round(score * fator)

    return score


def calcular_score_detalhado(
    fonte_preco: dict[str, Any],
    data_base: date | None = None,
) -> dict[str, Any]:
    """Retorna breakdown completo do score com todos os componentes.

    Útil para auditoria, debugging e exibição na interface de gestão.

    Args:
        fonte_preco: Dicionário com campos da fonte de preço.
        data_base:   Data base para cálculo de decaimento. Se None,
                     usa date.today() apenas para calcular os dias
                     decorridos — não penaliza o score.

    Returns:
        Dict com:
          score_final       int    Score aplicado (com ou sem decaimento)
          score_base        int    Score antes do decaimento temporal
          fator_temporal    float  Multiplicador aplicado (1.0 = sem decaimento)
          dias_referencia   int|None  Dias desde a data_referencia até data_base
          componentes       dict   Pontuação por dimensão
    """
    score_base = min(
        _score_completude(fonte_preco)
        + _score_confiabilidade(fonte_preco)
        + _score_evidencia(fonte_preco)
        + _score_unidade(fonte_preco)
        + _score_categoria(fonte_preco),
        100,
    )

    # Decaimento: aplica somente quando data_base é explicitamente passada
    if data_base is not None:
        fator = calcular_fator_temporal(
            fonte_preco.get("data_referencia"), data_base
        )
        score_final = round(score_base * fator)
    else:
        fator = calcular_fator_temporal(
            fonte_preco.get("data_referencia"), date.today()
        )
        score_final = score_base  # sem penalidade, mas informa o fator

    # Dias desde a referência (informativo)
    dr = _parse_data(fonte_preco.get("data_referencia"))
    base_para_dias = data_base or date.today()
    dias = (base_para_dias - dr).days if dr else None

    return {
        "score_final": score_final,
        "score_base": score_base,
        "fator_temporal": fator,
        "dias_referencia": dias,
        "componentes": {
            "completude":      _score_completude(fonte_preco),
            "confiabilidade":  _score_confiabilidade(fonte_preco),
            "evidencia":       _score_evidencia(fonte_preco),
            "unidade":         _score_unidade(fonte_preco),
            "categoria":       _score_categoria(fonte_preco),
        },
    }
