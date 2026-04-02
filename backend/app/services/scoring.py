"""Cálculo de score de confiança para fontes de preço.

O score (0-100) avalia a qualidade e confiabilidade de uma amostra
de preço com base em completude, fonte, evidência, normalização
e classificação.
"""

from typing import Any


# Mapeamento de qualidade_tipo para pontuação de confiabilidade
_CONFIABILIDADE_FONTE: dict[str, int] = {
    "HOMOLOGADO": 30,
    "TABELA_OFICIAL": 25,
    "ESTIMADO": 15,
    "MERCADO": 10,
}


def calcular_score_fonte(fonte_preco: dict[str, Any]) -> int:
    """Calcula score de confiança (0-100) de uma fonte de preço.

    Componentes com pesos:
    - Completude de campos (máx 20): url_origem +10, data_referencia +5, quantidade +5
    - Confiabilidade da fonte (máx 30): baseado em qualidade_tipo
    - Evidência (máx 20): storage_path +10, hash_sha256 +10
    - Unidade normalizada (máx 15): unidade válida +15
    - Categoria (máx 15): categoria_id +10, score_classificacao > 0.8 +5

    Args:
        fonte_preco: dicionário com campos da fonte de preço. Campos
            esperados: url_origem, data_referencia, quantidade,
            qualidade_tipo, storage_path, hash_sha256,
            unidade_normalizada, categoria_id, score_classificacao.

    Retorna inteiro entre 0 e 100.
    """
    score = 0

    # Completude de campos (máx 20)
    if fonte_preco.get("url_origem"):
        score += 10
    if fonte_preco.get("data_referencia"):
        score += 5
    if fonte_preco.get("quantidade"):
        score += 5

    # Confiabilidade da fonte (máx 30)
    qualidade = fonte_preco.get("qualidade_tipo", "")
    score += _CONFIABILIDADE_FONTE.get(str(qualidade).upper(), 0)

    # Evidência (máx 20)
    if fonte_preco.get("storage_path"):
        score += 10
    if fonte_preco.get("hash_sha256"):
        score += 10

    # Unidade normalizada (máx 15)
    unidade = fonte_preco.get("unidade_normalizada")
    if unidade and str(unidade).strip() and str(unidade).upper() != "OUTRO":
        score += 15

    # Categoria (máx 15)
    if fonte_preco.get("categoria_id") is not None:
        score += 10
    score_class = fonte_preco.get("score_classificacao")
    if score_class is not None and float(score_class) > 0.8:
        score += 5

    return min(score, 100)
