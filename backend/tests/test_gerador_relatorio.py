"""Testes para o serviço de geração de relatório PDF."""

from __future__ import annotations

import uuid

import pytest

from app.schemas.relatorios import AmostraRelatorio, RelatorioInput
from app.services.gerador_relatorio import GeradorRelatorio


def _criar_input_basico(**kwargs) -> RelatorioInput:
    """Cria um RelatorioInput com dados padrão para testes."""
    defaults = {
        "orgao_nome": "Prefeitura de Teste",
        "orgao_cnpj": "12.345.678/0001-90",
        "item_descricao": "Papel A4 75g/m²",
        "categoria_nome": "Papel A4",
        "periodo_inicio": "2025-01-01",
        "periodo_fim": "2025-12-31",
        "uf_filtro": "SP",
        "amostras": [
            AmostraRelatorio(
                numero_controle="PE-001/2025",
                orgao_origem="Prefeitura de São Paulo",
                data_referencia="2025-03-15",
                preco_unitario=22.50,
                unidade="RESMA",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=False,
            ),
            AmostraRelatorio(
                numero_controle="PE-002/2025",
                orgao_origem="Câmara Municipal de Campinas",
                data_referencia="2025-04-10",
                preco_unitario=24.00,
                unidade="RESMA",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=False,
            ),
        ],
        "estatisticas": {
            "n": 2,
            "media": 23.25,
            "mediana": 23.25,
            "desvio_padrao": 1.06,
            "q1": 22.875,
            "q3": 23.625,
        },
        "preco_referencial": 23.25,
        "confianca": "ALTA",
        "n_outliers_excluidos": 0,
        "id_relatorio": str(uuid.uuid4()),
        "emitido_em": "2025-06-01T10:00:00",
    }
    defaults.update(kwargs)
    return RelatorioInput(**defaults)


@pytest.fixture
def gerador() -> GeradorRelatorio:
    """Fixture para o gerador de relatórios."""
    return GeradorRelatorio()


class TestGeradorRelatorio:
    """Testes para GeradorRelatorio."""

    def test_gera_pdf_bytes_nao_vazios(self, gerador: GeradorRelatorio) -> None:
        """Verifica que gerar() retorna bytes com conteúdo."""
        dados = _criar_input_basico()
        resultado = gerador.gerar(dados)
        assert isinstance(resultado, bytes)
        assert len(resultado) > 0

    def test_pdf_comeca_com_magic_bytes(self, gerador: GeradorRelatorio) -> None:
        """Verifica que o PDF começa com os magic bytes corretos."""
        dados = _criar_input_basico()
        resultado = gerador.gerar(dados)
        assert resultado[:5] == b"%PDF-"

    def test_sem_amostras(self, gerador: GeradorRelatorio) -> None:
        """Verifica que gerar() com amostras vazias não lança exceção."""
        dados = _criar_input_basico(amostras=[])
        resultado = gerador.gerar(dados)
        assert resultado[:5] == b"%PDF-"

    def test_com_outliers(self, gerador: GeradorRelatorio) -> None:
        """Verifica que amostras com outlier=True não lançam exceção."""
        amostras = [
            AmostraRelatorio(
                numero_controle="PE-001/2025",
                orgao_origem="Prefeitura de São Paulo",
                data_referencia="2025-03-15",
                preco_unitario=22.50,
                unidade="RESMA",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=False,
            ),
            AmostraRelatorio(
                numero_controle="PE-002/2025",
                orgao_origem="Prefeitura de Belo Horizonte",
                data_referencia="2025-05-20",
                preco_unitario=85.00,
                unidade="RESMA",
                uf="MG",
                qualidade="ESTIMADO",
                outlier=True,
            ),
        ]
        dados = _criar_input_basico(amostras=amostras, n_outliers_excluidos=1)
        resultado = gerador.gerar(dados)
        assert len(resultado) > 0

    def test_campos_none(self, gerador: GeradorRelatorio) -> None:
        """Verifica que campos opcionais como None não lançam exceção."""
        dados = _criar_input_basico(
            orgao_cnpj=None,
            categoria_nome=None,
            uf_filtro=None,
        )
        resultado = gerador.gerar(dados)
        assert resultado[:5] == b"%PDF-"

    def test_id_relatorio_no_pdf(self, gerador: GeradorRelatorio) -> None:
        """Verifica que o PDF é gerado com sucesso para um id_relatorio específico."""
        id_relatorio = "abc-123-test-uuid"
        dados = _criar_input_basico(id_relatorio=id_relatorio)
        resultado = gerador.gerar(dados)
        assert len(resultado) > 100
        assert resultado[:5] == b"%PDF-"

    def test_preco_referencial_none(self, gerador: GeradorRelatorio) -> None:
        """Verifica que preco_referencial=None não lança exceção."""
        dados = _criar_input_basico(preco_referencial=None)
        resultado = gerador.gerar(dados)
        assert resultado[:5] == b"%PDF-"

    def test_confianca_insuficiente(self, gerador: GeradorRelatorio) -> None:
        """Verifica que confianca='INSUFICIENTE' renderiza sem erro."""
        dados = _criar_input_basico(
            confianca="INSUFICIENTE",
            preco_referencial=None,
        )
        resultado = gerador.gerar(dados)
        assert resultado[:5] == b"%PDF-"
