"""Serviço de integração com Compras.gov (mock) — busca de itens e preços."""

from __future__ import annotations

import hashlib


class ComprasGovService:
    """Integração mockada com o portal Compras.gov.br."""

    def buscar_itens(self, descricao: str, uf: str | None = None) -> list[dict]:
        """Busca itens no Compras.gov por descrição.

        Args:
            descricao: Texto de busca.
            uf: Filtro opcional por UF.

        Returns:
            Lista de itens mockados compatíveis com FontePreco.
        """
        itens = [
            {
                "fonte_tipo": "compras_gov",
                "fonte_referencia": f"CG-{i:05d}",
                "descricao": f"{descricao} - variação {i}",
                "preco_unitario": 10.0 + i * 2.5,
                "quantidade": 100,
                "unidade_normalizada": "UN",
                "uf": uf or "DF",
                "data_referencia": "2026-03-01",
                "score_confianca": 70 + i,
            }
            for i in range(1, 6)
        ]
        return itens

    def buscar_preco_referencia(self, codigo_catmat: str) -> dict | None:
        """Busca preço de referência por código CATMAT.

        Args:
            codigo_catmat: Código CATMAT do item.

        Returns:
            Dict com preço de referência ou None se não encontrado.
        """
        # Simular catmats conhecidos
        catmats_conhecidos = {
            "150233": {"descricao": "Papel Sulfite A4", "preco_referencia": 22.50, "unidade": "RM"},
            "234012": {"descricao": "Detergente Líquido 500ml", "preco_referencia": 2.80, "unidade": "FR"},
            "381024": {"descricao": "Toner HP CF258A", "preco_referencia": 89.90, "unidade": "UN"},
        }
        return catmats_conhecidos.get(codigo_catmat)


def consolidar_fontes(
    fontes_pncp: list[dict], fontes_compras_gov: list[dict]
) -> list[dict]:
    """Consolida fontes do PNCP e Compras.gov, removendo duplicatas.

    Marca cada item com fonte_tipo e remove duplicatas por hash da
    combinação (descrição, preço, data, UF).

    Args:
        fontes_pncp: Lista de fontes do PNCP.
        fontes_compras_gov: Lista de fontes do Compras.gov.

    Returns:
        Lista consolidada sem duplicatas.
    """
    for f in fontes_pncp:
        f.setdefault("fonte_tipo", "pncp")
    for f in fontes_compras_gov:
        f.setdefault("fonte_tipo", "compras_gov")

    todas = fontes_pncp + fontes_compras_gov
    vistos: set[str] = set()
    resultado: list[dict] = []

    for item in todas:
        chave = hashlib.md5(
            f"{item.get('descricao','')}"
            f"|{item.get('preco_unitario','')}"
            f"|{item.get('data_referencia','')}"
            f"|{item.get('uf','')}".encode()
        ).hexdigest()

        if chave not in vistos:
            vistos.add(chave)
            resultado.append(item)

    return resultado
