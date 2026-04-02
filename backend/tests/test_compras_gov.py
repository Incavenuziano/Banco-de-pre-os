"""Testes para o serviço de integração com Compras.gov."""

from __future__ import annotations

from app.services.compras_gov_service import (
    ComprasGovService,
    consolidar_fontes,
)

service = ComprasGovService()


class TestComprasGovService:
    """Testes do ComprasGovService."""

    def test_buscar_itens_retorna_lista(self) -> None:
        """buscar_itens retorna lista com 5 itens."""
        itens = service.buscar_itens("papel sulfite")
        assert isinstance(itens, list)
        assert len(itens) == 5

    def test_buscar_itens_tem_campos_obrigatorios(self) -> None:
        """Cada item tem os campos obrigatórios."""
        itens = service.buscar_itens("detergente")
        for item in itens:
            assert "fonte_tipo" in item
            assert "preco_unitario" in item
            assert "descricao" in item
            assert "uf" in item

    def test_buscar_preco_referencia_catmat_conhecido(self) -> None:
        """CATMAT conhecido retorna preço de referência."""
        resultado = service.buscar_preco_referencia("150233")
        assert resultado is not None
        assert resultado["preco_referencia"] == 22.50

    def test_buscar_preco_referencia_catmat_desconhecido(self) -> None:
        """CATMAT desconhecido retorna None."""
        resultado = service.buscar_preco_referencia("999999")
        assert resultado is None


class TestConsolidarFontes:
    """Testes para consolidar_fontes."""

    def test_consolidar_fontes_une_listas(self) -> None:
        """Fontes de PNCP e Compras.gov são unidas."""
        pncp = [{"descricao": "item A", "preco_unitario": 10.0, "data_referencia": "2026-01-01", "uf": "SP"}]
        cg = [{"descricao": "item B", "preco_unitario": 20.0, "data_referencia": "2026-01-01", "uf": "SP"}]
        resultado = consolidar_fontes(pncp, cg)
        assert len(resultado) == 2

    def test_consolidar_fontes_remove_duplicatas(self) -> None:
        """Itens com mesma chave (desc+preço+data+uf) são deduplicados."""
        item = {"descricao": "item X", "preco_unitario": 10.0, "data_referencia": "2026-01-01", "uf": "DF"}
        pncp = [dict(item)]
        cg = [dict(item)]
        resultado = consolidar_fontes(pncp, cg)
        assert len(resultado) == 1
