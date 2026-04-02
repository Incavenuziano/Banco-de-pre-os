"""Motor estatístico para cálculo de preços referenciais.

Utiliza apenas stdlib + statistics (sem numpy/scipy/pandas).
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any


def calcular_estatisticas(precos: list[float]) -> dict[str, Any]:
    """Calcula estatísticas descritivas para uma lista de preços.

    Retorna dict com n, media, mediana, desvio_padrao, variancia,
    q1, q3, iqr, min, max, coeficiente_variacao.
    Se n < 2, campos estatísticos ficam None (exceto n e mediana).
    """
    n = len(precos)

    if n == 0:
        return {
            "n": 0,
            "media": None,
            "mediana": None,
            "desvio_padrao": None,
            "variancia": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "min": None,
            "max": None,
            "coeficiente_variacao": None,
        }

    if n == 1:
        return {
            "n": 1,
            "media": precos[0],
            "mediana": precos[0],
            "desvio_padrao": None,
            "variancia": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "min": precos[0],
            "max": precos[0],
            "coeficiente_variacao": None,
        }

    ordenados = sorted(precos)
    media = statistics.mean(ordenados)
    mediana = statistics.median(ordenados)
    desvio = statistics.stdev(ordenados)
    variancia = statistics.variance(ordenados)
    q1 = statistics.median(ordenados[: n // 2])
    q3 = statistics.median(ordenados[(n + 1) // 2 :])
    iqr = q3 - q1
    cv = desvio / media if media != 0 else None

    return {
        "n": n,
        "media": round(media, 4),
        "mediana": round(mediana, 4),
        "desvio_padrao": round(desvio, 4),
        "variancia": round(variancia, 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "min": round(ordenados[0], 4),
        "max": round(ordenados[-1], 4),
        "coeficiente_variacao": round(cv, 4) if cv is not None else None,
    }


def _percentil(ordenados: list[float], p: float) -> float:
    """Calcula o percentil p (0-100) usando interpolação linear."""
    n = len(ordenados)
    if n == 1:
        return ordenados[0]
    k = (n - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= n:
        return ordenados[-1]
    return ordenados[f] + (k - f) * (ordenados[c] - ordenados[f])


def marcar_outliers(precos: list[float], metodo: str = "iqr") -> list[dict[str, Any]]:
    """Marca outliers em uma lista de preços.

    Métodos disponíveis:
    - 'iqr': outlier se preco < Q1 - 1.5*IQR ou preco > Q3 + 1.5*IQR
    - 'percentil': outlier se preco < p5 ou preco > p95
    - 'desvio': outlier se |preco - media| > 2 * desvio_padrao

    Retorna lista de dicts {preco, outlier, motivo}.
    """
    if not precos:
        return []

    ordenados = sorted(precos)
    n = len(ordenados)
    resultados: list[dict[str, Any]] = []

    if metodo == "iqr":
        q1 = statistics.median(ordenados[: n // 2]) if n >= 2 else ordenados[0]
        q3 = statistics.median(ordenados[(n + 1) // 2 :]) if n >= 2 else ordenados[0]
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr

        for p in precos:
            if p < limite_inferior:
                resultados.append({"preco": p, "outlier": True, "motivo": f"Abaixo de Q1 - 1.5*IQR ({limite_inferior:.2f})"})
            elif p > limite_superior:
                resultados.append({"preco": p, "outlier": True, "motivo": f"Acima de Q3 + 1.5*IQR ({limite_superior:.2f})"})
            else:
                resultados.append({"preco": p, "outlier": False, "motivo": None})

    elif metodo == "percentil":
        p5 = _percentil(ordenados, 5)
        p95 = _percentil(ordenados, 95)

        for p in precos:
            if p < p5:
                resultados.append({"preco": p, "outlier": True, "motivo": f"Abaixo do percentil 5 ({p5:.2f})"})
            elif p > p95:
                resultados.append({"preco": p, "outlier": True, "motivo": f"Acima do percentil 95 ({p95:.2f})"})
            else:
                resultados.append({"preco": p, "outlier": False, "motivo": None})

    elif metodo == "desvio":
        media = statistics.mean(precos)
        desvio = statistics.stdev(precos) if n >= 2 else 0.0

        for p in precos:
            if n >= 2 and abs(p - media) > 2 * desvio:
                resultados.append({"preco": p, "outlier": True, "motivo": f"|{p} - {media:.2f}| > 2 * {desvio:.2f}"})
            else:
                resultados.append({"preco": p, "outlier": False, "motivo": None})

    else:
        raise ValueError(f"Método desconhecido: {metodo}")

    return resultados


def calcular_preco_referencial(
    precos: list[float],
    excluir_outliers: bool = True,
) -> dict[str, Any]:
    """Calcula o preço referencial a partir de uma lista de preços.

    Retorna dict com preco_referencial, metodo_usado, n_amostras,
    n_outliers_excluidos, estatisticas, confianca.
    """
    if not precos:
        return {
            "preco_referencial": None,
            "metodo_usado": "mediana",
            "n_amostras": 0,
            "n_outliers_excluidos": 0,
            "estatisticas": calcular_estatisticas([]),
            "confianca": "INSUFICIENTE",
        }

    n_outliers = 0
    precos_usados = precos

    if excluir_outliers and len(precos) >= 2:
        marcados = marcar_outliers(precos, metodo="iqr")
        precos_usados = [m["preco"] for m in marcados if not m["outlier"]]
        n_outliers = len(precos) - len(precos_usados)
        if not precos_usados:
            precos_usados = precos
            n_outliers = 0

    stats = calcular_estatisticas(precos_usados)
    n = stats["n"]

    # Determinar confiança
    cv = stats.get("coeficiente_variacao")
    if n >= 10 and cv is not None and cv < 0.3:
        confianca = "ALTA"
    elif n >= 5:
        confianca = "MEDIA"
    elif n >= 2:
        confianca = "BAIXA"
    else:
        confianca = "INSUFICIENTE"

    return {
        "preco_referencial": stats["mediana"],
        "metodo_usado": "mediana",
        "n_amostras": n,
        "n_outliers_excluidos": n_outliers,
        "estatisticas": stats,
        "confianca": confianca,
    }


def gerar_sumario_categoria(fontes: list[dict[str, Any]]) -> dict[str, Any]:
    """Gera sumário estatístico agrupado por unidade normalizada.

    Filtra fontes com score_confianca >= 30 e preco_unitario > 0.
    Agrupa por unidade_normalizada e calcula estatísticas por grupo.

    Retorna dict com total_amostras, amostras_validas, por_unidade, distribuicao_uf.
    """
    total = len(fontes)

    validas = [
        f for f in fontes
        if f.get("score_confianca", 0) >= 30 and f.get("preco_unitario", 0) > 0
    ]

    # Agrupar por unidade
    por_unidade: dict[str, list[float]] = defaultdict(list)
    distribuicao_uf: dict[str, int] = defaultdict(int)

    for f in validas:
        unidade = f.get("unidade_normalizada") or "SEM_UNIDADE"
        por_unidade[unidade].append(f["preco_unitario"])
        uf = f.get("uf") or "DESCONHECIDA"
        distribuicao_uf[uf] += 1

    resultado_unidades: dict[str, Any] = {}
    for unidade, precos_lista in por_unidade.items():
        resultado_unidades[unidade] = {
            "estatisticas": calcular_estatisticas(precos_lista),
            "preco_referencial": calcular_preco_referencial(precos_lista),
        }

    return {
        "total_amostras": total,
        "amostras_validas": len(validas),
        "por_unidade": resultado_unidades,
        "distribuicao_uf": dict(distribuicao_uf),
    }


def calibrar_limiar_outlier(
    precos: list[float], categoria: str | None = None
) -> dict[str, Any]:
    """Calibra o limiar ideal de detecção de outliers para uma amostra de preços.

    Analisa a distribuição dos preços e recomenda o método mais adequado
    de detecção de outliers, junto com os limiares correspondentes.

    Args:
        precos: Lista de preços para calibração.
        categoria: Categoria do item (reservado para uso futuro).

    Returns:
        Dict com metodo_recomendado, limiar_iqr, limiar_percentil,
        limiar_desvio e justificativa.
    """
    n = len(precos)
    resultado: dict[str, Any] = {
        "metodo_recomendado": "iqr",
        "limiar_iqr": 1.5,
        "limiar_percentil": (5.0, 95.0),
        "limiar_desvio": 2.0,
        "justificativa": "",
    }

    if n < 5:
        resultado["metodo_recomendado"] = "desvio"
        resultado["justificativa"] = "amostra pequena"
        return resultado

    media = statistics.mean(precos)
    desvio = statistics.stdev(precos)
    cv = desvio / media if media != 0 else 0.0

    if cv > 0.5:
        resultado["metodo_recomendado"] = "iqr"
        resultado["justificativa"] = (
            f"coeficiente de variação alto ({cv:.2f}), IQR é mais robusto"
        )
    elif cv <= 0.3:
        resultado["metodo_recomendado"] = "percentil"
        resultado["justificativa"] = (
            f"coeficiente de variação baixo ({cv:.2f}), percentil é adequado"
        )
    else:
        resultado["metodo_recomendado"] = "iqr"
        resultado["justificativa"] = (
            f"coeficiente de variação moderado ({cv:.2f}), IQR como padrão"
        )

    return resultado


def relatorio_qualidade_amostras(precos: list[float]) -> dict[str, Any]:
    """Gera relatório de qualidade de uma amostra de preços.

    Avalia a suficiência e confiabilidade da amostra, retornando
    métricas de qualidade e recomendações de melhoria.

    Args:
        precos: Lista de preços para avaliação.

    Returns:
        Dict com n, n_outliers, pct_outliers, coeficiente_variacao,
        nivel_qualidade e recomendacoes.
    """
    n = len(precos)
    recomendacoes: list[str] = []

    if n < 2:
        return {
            "n": n,
            "n_outliers": 0,
            "pct_outliers": 0.0,
            "coeficiente_variacao": None,
            "nivel_qualidade": "INSUFICIENTE" if n < 3 else "REGULAR",
            "recomendacoes": ["Fonte insuficiente para relatório", "Ampliar período de pesquisa"],
        }

    marcados = marcar_outliers(precos, metodo="iqr")
    n_outliers = sum(1 for m in marcados if m["outlier"])
    pct_outliers = round(n_outliers / n * 100, 2) if n > 0 else 0.0

    media = statistics.mean(precos)
    desvio = statistics.stdev(precos)
    cv = round(desvio / media, 4) if media != 0 else None

    # Determinar nível de qualidade
    if cv is not None and cv < 0.15 and n >= 10:
        nivel = "EXCELENTE"
    elif cv is not None and cv < 0.3 and n >= 5:
        nivel = "BOM"
    elif n >= 3:
        nivel = "REGULAR"
    else:
        nivel = "INSUFICIENTE"

    # Gerar recomendações
    if n < 3:
        recomendacoes.append("Fonte insuficiente para relatório")
    if n < 10:
        recomendacoes.append("Ampliar período de pesquisa")
    if pct_outliers > 20:
        recomendacoes.append("Verificar outliers manualmente")
    if cv is not None and cv > 0.5:
        recomendacoes.append("Alta dispersão — verificar compatibilidade das amostras")

    return {
        "n": n,
        "n_outliers": n_outliers,
        "pct_outliers": pct_outliers,
        "coeficiente_variacao": cv,
        "nivel_qualidade": nivel,
        "recomendacoes": recomendacoes,
    }
