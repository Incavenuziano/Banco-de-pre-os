"""Serviço de alertas de sobrepreço — análise, relatórios e economia."""

from __future__ import annotations


class AlertaService:
    """Analisa preços propostos e gera alertas de sobrepreço."""

    def analisar_preco(
        self,
        preco_proposto: float,
        estatisticas: dict,
        categoria: str | None = None,
    ) -> dict:
        """Analisa um preço proposto em relação às estatísticas de referência.

        CRITICO: preco > mediana * 1.5
        ATENCAO: preco > mediana * 1.2
        OK: preco <= mediana * 1.2

        Args:
            preco_proposto: Preço proposto para análise.
            estatisticas: Dict com campo 'mediana'.
            categoria: Categoria do item (opcional).

        Returns:
            Dict com alerta, nivel, percentual_desvio, mensagem e recomendacao.
        """
        mediana = estatisticas.get("mediana", 0)
        if mediana <= 0:
            return {
                "alerta": False,
                "nivel": "OK",
                "percentual_desvio": 0.0,
                "mensagem": "Sem mediana de referência para comparação",
                "recomendacao": "Coletar mais amostras",
            }

        percentual_desvio = round((preco_proposto - mediana) / mediana * 100, 2)

        if preco_proposto > mediana * 1.5:
            return {
                "alerta": True,
                "nivel": "CRITICO",
                "percentual_desvio": percentual_desvio,
                "mensagem": f"Preço {percentual_desvio}% acima da mediana — sobrepreço crítico",
                "recomendacao": "Renegociar ou justificar formalmente o preço",
            }
        elif preco_proposto > mediana * 1.2:
            return {
                "alerta": True,
                "nivel": "ATENCAO",
                "percentual_desvio": percentual_desvio,
                "mensagem": f"Preço {percentual_desvio}% acima da mediana — atenção",
                "recomendacao": "Verificar justificativa e considerar renegociação",
            }
        else:
            return {
                "alerta": False,
                "nivel": "OK",
                "percentual_desvio": percentual_desvio,
                "mensagem": "Preço dentro da faixa aceitável",
                "recomendacao": "Nenhuma ação necessária",
            }

    def gerar_relatorio_alertas(self, itens: list[dict]) -> dict:
        """Gera relatório consolidado de alertas para uma lista de itens.

        Args:
            itens: Lista de dicts com descricao, preco_proposto e estatisticas.

        Returns:
            Dict com total, contadores por nível e lista de itens analisados.
        """
        resultados: list[dict] = []
        criticos = 0
        atencao = 0
        ok = 0

        for item in itens:
            alerta = self.analisar_preco(
                item["preco_proposto"],
                item["estatisticas"],
                item.get("categoria"),
            )
            resultados.append({"descricao": item["descricao"], "alerta": alerta})

            if alerta["nivel"] == "CRITICO":
                criticos += 1
            elif alerta["nivel"] == "ATENCAO":
                atencao += 1
            else:
                ok += 1

        return {
            "total": len(itens),
            "criticos": criticos,
            "atencao": atencao,
            "ok": ok,
            "itens": resultados,
        }

    def calcular_economia_potencial(
        self, preco_proposto: float, preco_referencial: float, quantidade: int
    ) -> dict:
        """Calcula economia potencial ao adotar o preço referencial.

        Args:
            preco_proposto: Preço unitário proposto.
            preco_referencial: Preço unitário de referência.
            quantidade: Quantidade a ser adquirida.

        Returns:
            Dict com economia_unitaria, economia_total, percentual_reducao e viavel.
        """
        economia_unitaria = round(preco_proposto - preco_referencial, 2)
        economia_total = round(economia_unitaria * quantidade, 2)
        percentual_reducao = (
            round(economia_unitaria / preco_proposto * 100, 2)
            if preco_proposto > 0
            else 0.0
        )
        viavel = economia_total > 0

        return {
            "economia_unitaria": economia_unitaria,
            "economia_total": economia_total,
            "percentual_reducao": percentual_reducao,
            "viavel": viavel,
        }
