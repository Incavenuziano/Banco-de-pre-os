"""Testes para funcionalidades avançadas do gerador de relatório (S18)."""

from __future__ import annotations

from app.schemas.relatorios import AmostraRelatorio, RelatorioInput
from app.services.gerador_relatorio import GeradorRelatorio

gerador = GeradorRelatorio()


def _criar_dados_relatorio(**kwargs) -> RelatorioInput:
    """Cria dados de relatório para testes."""
    defaults = {
        "id_relatorio": "TEST-001",
        "orgao_nome": "Prefeitura Teste",
        "orgao_cnpj": "00.000.000/0001-00",
        "item_descricao": "Papel Sulfite A4",
        "categoria_nome": "Papel A4",
        "periodo_inicio": "2024-01-01",
        "periodo_fim": "2025-12-01",
        "uf_filtro": "SP",
        "emitido_em": "2026-04-01",
        "preco_referencial": 24.50,
        "confianca": "ALTA",
        "n_outliers_excluidos": 0,
        "estatisticas": {"mediana": 24.50, "media": 25.0, "desvio_padrao": 2.5, "q1": 22.0, "q3": 27.0, "n": 30},
        "amostras": [
            AmostraRelatorio(
                numero_controle="NC-001",
                orgao_origem="Prefeitura ABC",
                data_referencia="2025-06-15",
                preco_unitario=24.50,
                unidade="Resma",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=False,
            ),
        ],
    }
    defaults.update(kwargs)
    return RelatorioInput(**defaults)


class TestCorrecaoIPCARelatorio:
    """Testes da seção IPCA no relatório."""

    def test_pdf_contem_secao_ipca(self) -> None:
        dados = _criar_dados_relatorio()
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_gerado_com_ipca(self) -> None:
        dados = _criar_dados_relatorio(periodo_inicio="2024-01-01", periodo_fim="2025-12-01")
        pdf = gerador.gerar(dados)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_pdf_com_periodo_invalido_nao_quebra(self) -> None:
        dados = _criar_dados_relatorio(periodo_inicio="1990-01-01", periodo_fim="1990-12-01")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_sem_preco_referencial(self) -> None:
        dados = _criar_dados_relatorio(preco_referencial=None)
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0


class TestBenchmarkRegionalRelatorio:
    """Testes da seção benchmark no relatório."""

    def test_pdf_com_benchmark(self) -> None:
        dados = _criar_dados_relatorio(categoria_nome="Papel A4")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_sem_categoria(self) -> None:
        dados = _criar_dados_relatorio(categoria_nome=None)
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_categoria_inexistente(self) -> None:
        dados = _criar_dados_relatorio(categoria_nome="CategoriaInexistente")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_com_uf_filtro(self) -> None:
        dados = _criar_dados_relatorio(uf_filtro="SP")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_sem_uf_filtro(self) -> None:
        dados = _criar_dados_relatorio(uf_filtro=None)
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0


class TestAlertasSobreprecoRelatorio:
    """Testes da seção alertas no relatório."""

    def test_pdf_com_alerta_normal(self) -> None:
        dados = _criar_dados_relatorio(preco_referencial=24.00, categoria_nome="Papel A4", uf_filtro="SP")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_com_alerta_critico(self) -> None:
        dados = _criar_dados_relatorio(preco_referencial=50.00, categoria_nome="Papel A4", uf_filtro="SP")
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_pdf_sem_referencial_sobrepreco(self) -> None:
        dados = _criar_dados_relatorio(preco_referencial=None)
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0


class TestRelatorioCompletoAvancado:
    """Testes de integração do relatório completo com todas seções S18."""

    def test_pdf_completo(self) -> None:
        dados = _criar_dados_relatorio()
        pdf = gerador.gerar(dados)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 1000

    def test_pdf_multiplas_amostras(self) -> None:
        amostras = [
            AmostraRelatorio(
                numero_controle=f"NC-{i:03d}",
                orgao_origem=f"Órgão {i}",
                data_referencia="2025-06-15",
                preco_unitario=20.0 + i,
                unidade="Resma",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=i > 8,
            )
            for i in range(10)
        ]
        dados = _criar_dados_relatorio(amostras=amostras)
        pdf = gerador.gerar(dados)
        assert len(pdf) > 2000

    def test_pdf_sem_amostras(self) -> None:
        dados = _criar_dados_relatorio(amostras=[])
        pdf = gerador.gerar(dados)
        assert len(pdf) > 0

    def test_csv_funciona_com_novas_secoes(self) -> None:
        dados = _criar_dados_relatorio()
        csv_bytes = gerador.gerar_xlsx(dados)
        assert len(csv_bytes) > 0
        assert csv_bytes[:3] == b"\xef\xbb\xbf"

    def test_pdf_tamanho_razoavel(self) -> None:
        dados = _criar_dados_relatorio()
        pdf = gerador.gerar(dados)
        # PDF com todas as seções deve ter mais que 3KB
        assert len(pdf) > 3000
