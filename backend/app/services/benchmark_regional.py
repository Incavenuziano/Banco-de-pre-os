"""Serviço de benchmark regional — comparação de preços por UF."""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any

# Dados sintéticos realistas para benchmark regional
_PRECOS_UF: dict[str, dict[str, float]] = {
    "Papel A4": {
        "AC": 32.50, "AL": 28.90, "AM": 34.20, "AP": 35.10, "BA": 27.80,
        "CE": 27.50, "DF": 25.90, "ES": 26.80, "GO": 26.50, "MA": 29.40,
        "MG": 25.20, "MS": 27.10, "MT": 28.30, "PA": 31.60, "PB": 29.10,
        "PE": 27.90, "PI": 30.20, "PR": 24.80, "RJ": 25.60, "RN": 29.50,
        "RO": 32.80, "RR": 36.40, "RS": 24.20, "SC": 23.90, "SE": 28.70,
        "SP": 23.50, "TO": 31.20,
    },
    "Gasolina Comum": {
        "AC": 6.89, "AL": 5.78, "AM": 6.45, "AP": 6.92, "BA": 5.62,
        "CE": 5.55, "DF": 5.89, "ES": 5.72, "GO": 5.48, "MA": 5.95,
        "MG": 5.52, "MS": 5.61, "MT": 5.67, "PA": 6.21, "PB": 5.71,
        "PE": 5.58, "PI": 5.84, "PR": 5.38, "RJ": 5.69, "RN": 5.63,
        "RO": 6.31, "RR": 6.78, "RS": 5.34, "SC": 5.29, "SE": 5.73,
        "SP": 5.42, "TO": 6.05,
    },
    "Detergente": {
        "AC": 5.20, "AL": 4.10, "AM": 5.50, "AP": 5.80, "BA": 3.90,
        "CE": 3.85, "DF": 3.80, "ES": 3.90, "GO": 3.75, "MA": 4.30,
        "MG": 3.60, "MS": 3.95, "MT": 4.10, "PA": 4.80, "PB": 4.20,
        "PE": 3.95, "PI": 4.40, "PR": 3.50, "RJ": 3.70, "RN": 4.15,
        "RO": 4.90, "RR": 5.30, "RS": 3.40, "SC": 3.35, "SE": 4.05,
        "SP": 3.30, "TO": 4.55,
    },
}


def _get_categoria(categoria: str) -> dict[str, float] | None:
    """Retorna mapa UF→preço se a categoria existir (match exato ou parcial), None caso contrário."""
    for key, data in _PRECOS_UF.items():
        if key.lower() == categoria.lower() or key.lower() in categoria.lower() or categoria.lower() in key.lower():
            return data
    return None


class BenchmarkRegionalService:
    """Comparação de preços entre UFs."""

    def comparar_por_uf(
        self,
        categoria: str,
        periodo: str | None = None,
    ) -> dict[str, Any]:
        """Ranking de preço médio por UF para uma categoria."""
        precos = _get_categoria(categoria)
        if not precos:
            return {
                "categoria": categoria,
                "periodo": periodo or "geral",
                "ranking": [],
                "estatisticas": {"media": 0, "mediana": 0, "minimo": 0, "maximo": 0, "uf_mais_barata": None, "uf_mais_cara": None},
                "total_ufs": 0,
            }

        ranking_sorted = sorted(precos.items(), key=lambda x: x[1])
        valores = list(precos.values())

        return {
            "categoria": categoria,
            "periodo": periodo or "geral",
            "ranking": [
                {"rank": i + 1, "uf": uf, "preco_medio": preco, "n_amostras": 45}
                for i, (uf, preco) in enumerate(ranking_sorted)
            ],
            "estatisticas": {
                "media": round(statistics.mean(valores), 2),
                "mediana": round(statistics.median(valores), 2),
                "minimo": round(min(valores), 2),
                "maximo": round(max(valores), 2),
                "uf_mais_barata": ranking_sorted[0][0],
                "uf_mais_cara": ranking_sorted[-1][0],
            },
            "total_ufs": len(ranking_sorted),
        }

    def percentil_uf(
        self,
        categoria: str,
        uf: str,
        periodo: str | None = None,
    ) -> dict[str, Any]:
        """Percentil da UF no ranking nacional para a categoria."""
        precos = _get_categoria(categoria)
        uf = uf.upper()

        if not precos or uf not in precos:
            return {
                "uf": uf,
                "categoria": categoria,
                "preco_medio": None,
                "rank": None,
                "percentil": None,
                "media_nacional": None,
                "diferenca_media_pct": None,
                "status": None,
            }

        ranking_sorted = sorted(precos.items(), key=lambda x: x[1])
        preco_uf = precos[uf]
        rank = next(i + 1 for i, (u, _) in enumerate(ranking_sorted) if u == uf)
        total = len(ranking_sorted)
        percentil = round((rank / total) * 100, 1)
        media = statistics.mean(precos.values())
        diferenca_pct = round(((preco_uf - media) / media) * 100, 2)

        return {
            "uf": uf,
            "categoria": categoria,
            "preco_medio": preco_uf,
            "rank": rank,
            "total_ufs": total,
            "percentil": percentil,
            "media_nacional": round(media, 2),
            "diferenca_media_pct": diferenca_pct,
            "status": (
                "BARATO" if percentil <= 33
                else "MEDIO" if percentil <= 66
                else "CARO"
            ),
        }

    def evolucao_regional(
        self,
        categoria: str,
        ufs: list[str] | None = None,
        meses: int = 6,
    ) -> dict[str, Any]:
        """Série temporal de preço médio por UF nos últimos N meses."""
        precos_base = _get_categoria(categoria)
        if not precos_base:
            return {"categoria": categoria, "meses": meses, "serie": {}}

        ufs_alvo = [u.upper() for u in ufs] if ufs else list(precos_base.keys())
        hoje = datetime.now()
        serie: dict[str, list[dict[str, Any]]] = {}

        for uf in ufs_alvo:
            if uf not in precos_base:
                continue
            preco_base = precos_base[uf]
            pontos = []
            preco_anterior = None
            for m in range(meses - 1, -1, -1):
                dt = hoje - timedelta(days=30 * m)
                variacao_acum = 1 + (0.003 * (meses - m))
                preco_atual = round(preco_base * variacao_acum, 2)
                variacao_pct = round(((preco_atual - preco_anterior) / preco_anterior) * 100, 2) if preco_anterior else 0.0
                pontos.append({
                    "periodo": dt.strftime("%Y-%m"),
                    "preco": preco_atual,
                    "variacao_pct": variacao_pct,
                    "n_amostras": 40 + m,
                })
                preco_anterior = preco_atual
            serie[uf] = pontos

        return {
            "categoria": categoria,
            "ufs": list(serie.keys()),
            "meses": meses,
            "serie": serie,
        }

    def resumo_benchmark(
        self,
        categorias: list[str] | None = None,
    ) -> dict[str, Any]:
        """Resumo de benchmark para múltiplas categorias."""
        cats = categorias if categorias else list(_PRECOS_UF.keys())
        resumos = []
        for cat in cats:
            precos = _PRECOS_UF.get(cat)
            if not precos:
                continue
            ranking = sorted(precos.items(), key=lambda x: x[1])
            resumos.append({
                "categoria": cat,
                "media_nacional": round(statistics.mean(precos.values()), 2),
                "mediana_nacional": round(statistics.median(precos.values()), 2),
                "uf_mais_barata": ranking[0][0],
                "preco_mais_barato": ranking[0][1],
                "uf_mais_cara": ranking[-1][0],
                "preco_mais_caro": ranking[-1][1],
                "total_ufs": len(precos),
            })

        return {
            "resumos": resumos,
            "total_categorias": len(resumos),
        }
