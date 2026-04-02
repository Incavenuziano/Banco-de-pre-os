"""Serviço de compatibilidade e conversão de unidades de medida.

Permite verificar se unidades são comparáveis e converter valores
entre unidades da mesma grandeza física.
"""

from __future__ import annotations


class CompatibilidadeUnidades:
    """Converte e compara preços entre unidades de medida compatíveis."""

    # Fatores de conversão: valor × fator = valor na unidade base da grandeza
    FATORES_CONVERSAO: dict[str, dict[str, float]] = {
        "volume": {
            "L": 1.0,
            "ML": 0.001,
            "KL": 1000.0,
        },
        "massa": {
            "KG": 1.0,
            "G": 0.001,
            "MG": 0.000001,
            "TON": 1000.0,
        },
        "comprimento": {
            "M": 1.0,
            "CM": 0.01,
            "MM": 0.001,
            "KM": 1000.0,
        },
    }

    # Mapa reverso: unidade → (grandeza, fator)
    _UNIDADE_MAP: dict[str, tuple[str, float]] = {}

    # Unidade base por grandeza
    _UNIDADE_BASE: dict[str, str] = {
        "volume": "L",
        "massa": "KG",
        "comprimento": "M",
    }

    def __init__(self) -> None:
        """Inicializa o mapa reverso de unidades."""
        if not CompatibilidadeUnidades._UNIDADE_MAP:
            for grandeza, unidades in self.FATORES_CONVERSAO.items():
                for unidade, fator in unidades.items():
                    CompatibilidadeUnidades._UNIDADE_MAP[unidade] = (grandeza, fator)

    def _lookup(self, unidade: str) -> tuple[str, float] | None:
        """Busca grandeza e fator de conversão de uma unidade.

        Args:
            unidade: Sigla da unidade (ex: 'ML', 'KG').

        Returns:
            Tupla (grandeza, fator) ou None se unidade desconhecida.
        """
        return self._UNIDADE_MAP.get(unidade.upper())

    def converter(
        self, valor: float, unidade_origem: str, unidade_destino: str
    ) -> float | None:
        """Converte um valor entre duas unidades da mesma grandeza.

        Args:
            valor: Valor numérico a converter.
            unidade_origem: Unidade de origem (ex: 'ML').
            unidade_destino: Unidade de destino (ex: 'L').

        Returns:
            Valor convertido ou None se conversão impossível.
        """
        orig = self._lookup(unidade_origem)
        dest = self._lookup(unidade_destino)

        if orig is None or dest is None:
            return None

        grandeza_orig, fator_orig = orig
        grandeza_dest, fator_dest = dest

        if grandeza_orig != grandeza_dest:
            return None

        # Converte para base e depois para destino
        valor_base = valor * fator_orig
        return valor_base / fator_dest

    def sao_comparaveis(self, unidade_a: str, unidade_b: str) -> bool:
        """Verifica se duas unidades são da mesma grandeza física.

        Args:
            unidade_a: Primeira unidade.
            unidade_b: Segunda unidade.

        Returns:
            True se as unidades são comparáveis (mesma grandeza).
        """
        a = self._lookup(unidade_a)
        b = self._lookup(unidade_b)

        if a is None or b is None:
            return False

        return a[0] == b[0]

    def normalizar_para_base(
        self, valor: float, unidade: str
    ) -> tuple[float, str] | None:
        """Converte valor para a unidade base da grandeza correspondente.

        Args:
            valor: Valor numérico.
            unidade: Unidade do valor (ex: 'ML').

        Returns:
            Tupla (valor_na_base, unidade_base) ou None se unidade desconhecida.
            Ex: (500, 'ML') → (0.5, 'L').
        """
        info = self._lookup(unidade)
        if info is None:
            return None

        grandeza, fator = info
        unidade_base = self._UNIDADE_BASE[grandeza]
        return (valor * fator, unidade_base)

    def comparar_precos(
        self,
        preco_a: float,
        unidade_a: str,
        preco_b: float,
        unidade_b: str,
    ) -> dict | None:
        """Compara dois preços convertendo para a unidade base comum.

        Args:
            preco_a: Preço do item A.
            unidade_a: Unidade do item A.
            preco_b: Preço do item B.
            unidade_b: Unidade do item B.

        Returns:
            Dict com preco_base_a, preco_base_b, unidade_base, comparavel, razao.
            None se alguma unidade for desconhecida.
        """
        norm_a = self.normalizar_para_base(preco_a, unidade_a)
        norm_b = self.normalizar_para_base(preco_b, unidade_b)

        if norm_a is None or norm_b is None:
            return None

        preco_base_a, base_a = norm_a
        preco_base_b, base_b = norm_b

        comparavel = base_a == base_b
        razao: float | None = None
        if comparavel and preco_base_b != 0:
            razao = round(preco_base_a / preco_base_b, 4)

        return {
            "preco_base_a": round(preco_base_a, 6),
            "preco_base_b": round(preco_base_b, 6),
            "unidade_base": base_a if comparavel else None,
            "comparavel": comparavel,
            "razao": razao,
        }
