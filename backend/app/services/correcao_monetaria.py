"""Serviço de correção monetária pelo IPCA.

Permite corrigir preços entre datas usando o índice IPCA,
calcular fatores de correção e variação acumulada.
"""

from __future__ import annotations

from app.services.ibge_service import IBGEService


class CorrecaoMonetariaService:
    """Correção monetária de preços pelo IPCA."""

    def __init__(self, ibge_service: IBGEService | None = None) -> None:
        self._ibge = ibge_service or IBGEService()

    def _parse_data(self, data: str) -> tuple[int, int]:
        """Extrai (ano, mes) de uma string YYYY-MM-DD ou YYYY-MM.

        Args:
            data: Data no formato YYYY-MM-DD ou YYYY-MM.

        Returns:
            Tupla (ano, mes).

        Raises:
            ValueError: Se formato inválido.
        """
        partes = data.split("-")
        if len(partes) < 2:
            raise ValueError(f"Formato de data inválido: {data}. Use YYYY-MM-DD ou YYYY-MM.")
        ano = int(partes[0])
        mes = int(partes[1])
        if not (1 <= mes <= 12):
            raise ValueError(f"Mês inválido: {mes}. Deve ser entre 1 e 12.")
        return ano, mes

    def fator_correcao(self, data_origem: str, data_destino: str) -> float:
        """Calcula fator de correção IPCA entre duas datas.

        Args:
            data_origem: Data de origem (YYYY-MM-DD ou YYYY-MM).
            data_destino: Data de destino (YYYY-MM-DD ou YYYY-MM).

        Returns:
            Fator multiplicativo (ex: 1.35 = 35% de inflação).

        Raises:
            ValueError: Se datas inválidas ou período sem dados.
        """
        ano_orig, mes_orig = self._parse_data(data_origem)
        ano_dest, mes_dest = self._parse_data(data_destino)

        if (ano_orig, mes_orig) == (ano_dest, mes_dest):
            return 1.0

        if (ano_orig, mes_orig) > (ano_dest, mes_dest):
            raise ValueError(
                f"Data de origem ({data_origem}) posterior à data de destino ({data_destino})"
            )

        # O fator é calculado do mês seguinte à origem até o mês destino
        # (o preço na data_origem já reflete o índice daquele mês)
        mes_inicio = mes_orig + 1
        ano_inicio = ano_orig
        if mes_inicio > 12:
            mes_inicio = 1
            ano_inicio += 1

        if (ano_inicio, mes_inicio) > (ano_dest, mes_dest):
            return 1.0

        return self._ibge.get_indice_acumulado_entre(
            ano_inicio, mes_inicio, ano_dest, mes_dest
        )

    def corrigir_preco(
        self, valor: float, data_origem: str, data_destino: str
    ) -> float:
        """Corrige um preço pela inflação IPCA entre duas datas.

        Args:
            valor: Valor original.
            data_origem: Data do valor original (YYYY-MM-DD).
            data_destino: Data para a qual corrigir (YYYY-MM-DD).

        Returns:
            Valor corrigido pela inflação.

        Raises:
            ValueError: Se valor negativo, datas inválidas.
        """
        if valor < 0:
            raise ValueError(f"Valor não pode ser negativo: {valor}")

        fator = self.fator_correcao(data_origem, data_destino)
        return round(valor * fator, 2)

    def variacao_periodo(self, data_inicio: str, data_fim: str) -> float:
        """Calcula variação percentual acumulada no período.

        Args:
            data_inicio: Data inicial (YYYY-MM-DD).
            data_fim: Data final (YYYY-MM-DD).

        Returns:
            Variação percentual (ex: 35.2 = 35.2%).
        """
        fator = self.fator_correcao(data_inicio, data_fim)
        return round((fator - 1) * 100, 2)

    def corrigir_preco_detalhado(
        self, valor: float, data_origem: str, data_destino: str
    ) -> dict:
        """Correção detalhada com todas as informações.

        Args:
            valor: Valor original.
            data_origem: Data de origem.
            data_destino: Data de destino.

        Returns:
            Dict com valor_original, valor_corrigido, fator, variacao_percentual,
            data_origem, data_destino, indice.
        """
        fator = self.fator_correcao(data_origem, data_destino)
        valor_corrigido = round(valor * fator, 2)
        variacao = round((fator - 1) * 100, 2)

        return {
            "valor_original": valor,
            "valor_corrigido": valor_corrigido,
            "fator": round(fator, 6),
            "variacao_percentual": variacao,
            "data_origem": data_origem,
            "data_destino": data_destino,
            "indice": "IPCA",
        }
