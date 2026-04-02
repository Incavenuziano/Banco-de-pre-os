"""Testes para o pipeline de ingestão piloto.

O PNCPConector é mockado em todos os testes — nenhuma chamada HTTP real.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.pipeline_piloto import ItemProcessado, PipelinePiloto


def _mock_conector_vazio() -> MagicMock:
    """Cria um conector mock que retorna dados vazios."""
    conector = MagicMock()
    conector.buscar_contratacoes.return_value = {"data": [], "totalRegistros": 0}
    conector.buscar_itens_contratacao.return_value = []
    conector.buscar_resultado_item.return_value = None
    return conector


def _mock_conector_com_dados() -> MagicMock:
    """Cria um conector mock que retorna contratações e itens."""
    conector = MagicMock()
    conector.buscar_contratacoes.return_value = {
        "data": [
            {
                "cnpjOrgao": "12345678000190",
                "anoCompra": 2025,
                "sequencialCompra": 1,
                "dataPublicacaoPncp": "2025-03-15",
                "numeroControlePNCP": "CTRL-001",
                "situacaoCompraId": 1,
            },
        ],
        "totalRegistros": 1,
    }
    conector.buscar_itens_contratacao.return_value = [
        {
            "descricao": "PAPEL A4 75G/M2 CONFORME EDITAL",
            "unidadeMedida": "RESMA",
            "valorUnitarioEstimado": 22.50,
            "quantidade": 100,
        },
        {
            "descricao": "DETERGENTE LIQUIDO 500ML",
            "unidadeMedida": "UNIDADE",
            "valorUnitarioEstimado": 2.80,
            "quantidade": 200,
        },
    ]
    return conector


class TestExecutarMunicipio:
    """Testes para executar_municipio."""

    def test_executar_municipio_sem_contratacoes(self) -> None:
        """Pipeline retorna totais zerados quando conector retorna vazio."""
        conector = _mock_conector_vazio()
        pipeline = PipelinePiloto(conector=conector)

        resultado = pipeline.executar_municipio("GO", "Anápolis", "20250101", "20250331")

        assert resultado["total_contratacoes"] == 0
        assert resultado["total_itens"] == 0
        assert resultado["itens_processados"] == []
        assert resultado["municipio"] == "Anápolis"
        assert resultado["uf"] == "GO"

    def test_executar_municipio_com_itens(self) -> None:
        """Pipeline processa itens corretamente quando há contratações."""
        conector = _mock_conector_com_dados()
        pipeline = PipelinePiloto(conector=conector)

        resultado = pipeline.executar_municipio("GO", "Santo Antônio do Descoberto", "20250101", "20250331")

        assert resultado["total_contratacoes"] == 1
        assert resultado["total_itens"] == 2
        assert len(resultado["itens_processados"]) == 2

        item = resultado["itens_processados"][0]
        assert isinstance(item, ItemProcessado)
        assert item.uf == "GO"
        assert item.municipio == "Santo Antônio do Descoberto"


class TestSelecionarTopItens:
    """Testes para selecionar_top_itens."""

    def test_selecionar_top_itens_ordena_por_ocorrencias(self) -> None:
        """Itens devem ser ordenados por ocorrências (desc)."""
        pipeline = PipelinePiloto(conector=_mock_conector_vazio())

        itens = [
            ItemProcessado(numero_controle="1", descricao_original="A", descricao_normalizada="ITEM A", categoria_nome="Cat1", preco_unitario=10.0),
            ItemProcessado(numero_controle="2", descricao_original="A", descricao_normalizada="ITEM A", categoria_nome="Cat1", preco_unitario=12.0),
            ItemProcessado(numero_controle="3", descricao_original="B", descricao_normalizada="ITEM B", categoria_nome="Cat2", preco_unitario=5.0),
        ]

        top = pipeline.selecionar_top_itens(itens, n=10)

        assert len(top) == 2
        assert top[0]["ocorrencias"] == 2
        assert top[0]["descricao_normalizada"] == "ITEM A"
        assert top[1]["ocorrencias"] == 1

    def test_selecionar_top_itens_respeita_n(self) -> None:
        """Retorna no máximo n itens."""
        pipeline = PipelinePiloto(conector=_mock_conector_vazio())

        itens = [
            ItemProcessado(numero_controle=str(i), descricao_original=f"Item {i}", descricao_normalizada=f"ITEM {i}", categoria_nome=f"Cat{i}", preco_unitario=float(i))
            for i in range(10)
        ]

        top = pipeline.selecionar_top_itens(itens, n=3)

        assert len(top) == 3

    def test_selecionar_top_itens_lista_vazia(self) -> None:
        """Retorna lista vazia quando não há itens."""
        pipeline = PipelinePiloto(conector=_mock_conector_vazio())

        top = pipeline.selecionar_top_itens([], n=20)

        assert top == []


class TestItemProcessado:
    """Testes para processamento individual de itens."""

    def test_item_processado_normalizado(self) -> None:
        """Descrição 'PAPEL A4 75G/M2 CONFORME EDITAL' deve ser normalizada sem ruído."""
        conector = _mock_conector_com_dados()
        pipeline = PipelinePiloto(conector=conector)

        resultado = pipeline.executar_municipio("GO", "Anápolis", "20250101", "20250331")
        item = resultado["itens_processados"][0]

        # 'CONFORME EDITAL' deve ser removido pela normalização
        assert "CONFORME EDITAL" not in item.descricao_normalizada
        assert "PAPEL" in item.descricao_normalizada

    def test_score_confianca_calculado(self) -> None:
        """Item com preço válido deve ter score > 0."""
        conector = _mock_conector_com_dados()
        pipeline = PipelinePiloto(conector=conector)

        resultado = pipeline.executar_municipio("GO", "Anápolis", "20250101", "20250331")

        for item in resultado["itens_processados"]:
            assert item.score_confianca > 0

    def test_categoria_classificada(self) -> None:
        """'PAPEL A4' deve ser classificado na categoria Papel A4."""
        conector = _mock_conector_com_dados()
        pipeline = PipelinePiloto(conector=conector)

        resultado = pipeline.executar_municipio("GO", "Anápolis", "20250101", "20250331")
        item_papel = resultado["itens_processados"][0]

        assert item_papel.categoria_nome == "Papel A4"
        assert item_papel.categoria_score is not None
        assert item_papel.categoria_score > 0


class TestGerarRelatorioPiloto:
    """Testes para geração de relatório PDF piloto."""

    def test_gerar_relatorio_piloto_retorna_bytes(self) -> None:
        """Gerador retorna bytes não-vazios."""
        pipeline = PipelinePiloto(conector=_mock_conector_vazio())

        top_itens = [
            {
                "descricao_normalizada": "PAPEL A4",
                "categoria": "Papel A4",
                "ocorrencias": 10,
                "precos": [22.50, 23.00, 24.00],
                "preco_mediano": 23.00,
            },
        ]

        pdf = pipeline.gerar_relatorio_piloto("Anápolis", "GO", top_itens)

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_gerar_relatorio_piloto_pdf_valido(self) -> None:
        """PDF gerado começa com %PDF."""
        pipeline = PipelinePiloto(conector=_mock_conector_vazio())

        top_itens = [
            {
                "descricao_normalizada": "DETERGENTE 500ML",
                "categoria": "Detergente",
                "ocorrencias": 5,
                "precos": [2.80, 3.00],
                "preco_mediano": 2.90,
            },
        ]

        pdf = pipeline.gerar_relatorio_piloto("Santo Antônio do Descoberto", "GO", top_itens)

        assert pdf[:5] == b"%PDF-"
