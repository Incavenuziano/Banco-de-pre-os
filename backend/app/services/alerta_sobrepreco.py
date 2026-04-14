"""Serviço aprimorado de alertas de sobrepreço — Semana 16.

Avalia preços contra estatísticas de referência por categoria/UF,
com percentis, desvio da mediana, e histórico de alertas.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime
from typing import Any


# Dados de referência por categoria (mediana, desvio padrão, n_amostras)
_REFERENCIA: dict[str, dict[str, dict[str, float]]] = {
    "Papel A4": {
        "SP": {"mediana": 24.50, "dp": 3.20, "n": 45},
        "RJ": {"mediana": 25.20, "dp": 3.50, "n": 38},
        "MG": {"mediana": 23.80, "dp": 2.90, "n": 42},
        "BA": {"mediana": 26.10, "dp": 3.80, "n": 30},
        "RS": {"mediana": 24.00, "dp": 3.10, "n": 35},
        "DF": {"mediana": 25.50, "dp": 3.40, "n": 28},
    },
    "Detergente": {
        "SP": {"mediana": 3.20, "dp": 0.60, "n": 50},
        "RJ": {"mediana": 3.50, "dp": 0.70, "n": 40},
        "MG": {"mediana": 3.10, "dp": 0.55, "n": 45},
        "BA": {"mediana": 3.60, "dp": 0.75, "n": 32},
        "RS": {"mediana": 3.00, "dp": 0.50, "n": 38},
    },
    "Gasolina Comum": {
        "SP": {"mediana": 5.89, "dp": 0.40, "n": 120},
        "RJ": {"mediana": 6.10, "dp": 0.45, "n": 100},
        "MG": {"mediana": 5.75, "dp": 0.38, "n": 95},
    },
}

# Histórico de alertas em memória (em produção seria tabela DB)
_HISTORICO_ALERTAS: list[dict] = []


class AlertaSobreprecoService:
    """Analisa preços propostos e gera alertas com classificação por severidade."""

    def avaliar_preco(
        self,
        item_descricao: str,
        valor: float,
        uf: str | None = None,
        categoria: str | None = None,
    ) -> dict:
        """Avalia um preço contra referências de mercado.

        Args:
            item_descricao: Descrição do item.
            valor: Preço proposto.
            uf: UF de referência (opcional).
            categoria: Categoria do item (opcional).

        Returns:
            Dict com status, percentil, desvio_mediana_pct, alertas.
        """
        ref = self._obter_referencia(categoria, uf)

        if ref is None:
            return {
                "item": item_descricao,
                "valor": valor,
                "status": "SEM_REFERENCIA",
                "percentil": None,
                "desvio_mediana_pct": None,
                "alertas": ["Sem dados de referência para esta categoria/UF"],
                "mediana_referencia": None,
                "n_amostras": 0,
            }

        mediana = ref["mediana"]
        dp = ref["dp"]
        n = ref["n"]

        desvio_pct = round((valor - mediana) / mediana * 100, 2) if mediana > 0 else 0.0

        # Calcular percentil aproximado (distribuição normal)
        if dp > 0:
            z_score = (valor - mediana) / dp
            percentil = self._z_para_percentil(z_score)
        else:
            percentil = 50 if valor == mediana else (99 if valor > mediana else 1)

        # Classificação
        alertas: list[str] = []
        if desvio_pct > 50:
            status = "CRITICO"
            alertas.append(f"Preço {desvio_pct}% acima da mediana — sobrepreço crítico")
            alertas.append("Renegociar ou justificar formalmente")
        elif desvio_pct > 25:
            status = "ATENCAO"
            alertas.append(f"Preço {desvio_pct}% acima da mediana — atenção recomendada")
            alertas.append("Verificar justificativa de preço")
        else:
            status = "NORMAL"

        resultado = {
            "item": item_descricao,
            "valor": valor,
            "status": status,
            "percentil": percentil,
            "desvio_mediana_pct": desvio_pct,
            "alertas": alertas,
            "mediana_referencia": mediana,
            "n_amostras": n,
        }

        # Salvar no histórico
        _HISTORICO_ALERTAS.append({
            **resultado,
            "uf": uf,
            "categoria": categoria,
            "avaliado_em": datetime.utcnow().isoformat(),
            "tenant_id": "default",
        })

        return resultado

    def obter_historico(
        self, tenant_id: str = "default", limite: int = 50
    ) -> list[dict]:
        """Retorna histórico de alertas por tenant.

        Args:
            tenant_id: ID do tenant.
            limite: Número máximo de registros.

        Returns:
            Lista de alertas do tenant.
        """
        alertas = [
            a for a in _HISTORICO_ALERTAS if a.get("tenant_id") == tenant_id
        ]
        return alertas[-limite:]

    def obter_estatisticas(self) -> dict:
        """Retorna resumo estatístico dos alertas.

        Returns:
            Dict com contadores por status e por categoria/UF.
        """
        total = len(_HISTORICO_ALERTAS)
        criticos = sum(1 for a in _HISTORICO_ALERTAS if a.get("status") == "CRITICO")
        atencao = sum(1 for a in _HISTORICO_ALERTAS if a.get("status") == "ATENCAO")
        normais = sum(1 for a in _HISTORICO_ALERTAS if a.get("status") == "NORMAL")

        # Por categoria
        por_categoria: dict[str, dict[str, int]] = {}
        for a in _HISTORICO_ALERTAS:
            cat = a.get("categoria", "Sem categoria")
            if cat not in por_categoria:
                por_categoria[cat] = {"CRITICO": 0, "ATENCAO": 0, "NORMAL": 0, "SEM_REFERENCIA": 0}
            status = a.get("status", "SEM_REFERENCIA")
            por_categoria[cat][status] = por_categoria[cat].get(status, 0) + 1

        # Por UF
        por_uf: dict[str, dict[str, int]] = {}
        for a in _HISTORICO_ALERTAS:
            uf_val = a.get("uf", "N/A")
            if uf_val not in por_uf:
                por_uf[uf_val] = {"CRITICO": 0, "ATENCAO": 0, "NORMAL": 0, "SEM_REFERENCIA": 0}
            status = a.get("status", "SEM_REFERENCIA")
            por_uf[uf_val][status] = por_uf[uf_val].get(status, 0) + 1

        return {
            "total_alertas": total,
            "criticos": criticos,
            "atencao": atencao,
            "normais": normais,
            "por_categoria": por_categoria,
            "por_uf": por_uf,
        }

    def limpar_historico(self) -> None:
        """Limpa histórico de alertas (para testes)."""
        _HISTORICO_ALERTAS.clear()

    def _obter_referencia(
        self, categoria: str | None, uf: str | None
    ) -> dict[str, float] | None:
        """Busca dados de referência para categoria/UF."""
        if categoria and categoria in _REFERENCIA:
            dados_cat = _REFERENCIA[categoria]
            if uf and uf in dados_cat:
                return dados_cat[uf]
            # Média entre UFs
            if dados_cat:
                medianas = [v["mediana"] for v in dados_cat.values()]
                dps = [v["dp"] for v in dados_cat.values()]
                ns = [v["n"] for v in dados_cat.values()]
                return {
                    "mediana": statistics.mean(medianas),
                    "dp": statistics.mean(dps),
                    "n": sum(ns),
                }
        return None

    @staticmethod
    def _z_para_percentil(z: float) -> int:
        """Converte z-score em percentil usando aproximação de Abramowitz & Stegun (26.2.17).

        Erro máximo: |ε(z)| < 7.5e-8 — suficiente para fins de alerta de preço.
        """
        if z < -3:
            return 1
        if z > 3:
            return 99
        # PDF da normal padrão: φ(z) = (1/√(2π)) * exp(-z²/2)
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        phi = math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
        # Polinômio de Horner (coeficientes de A&S tabela 26.2.17)
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        # CDF: Φ(z) ≈ 1 - φ(z)*poly para z ≥ 0; Φ(z) = 1 - Φ(-z) para z < 0
        if z >= 0:
            return min(99, max(1, int((1.0 - phi * poly) * 100)))
        return min(99, max(1, int(phi * poly * 100)))
