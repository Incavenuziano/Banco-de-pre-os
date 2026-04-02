"""Testes para exportação CSV/XLSX e JSON."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.relatorios import AmostraRelatorio, RelatorioInput
from app.services.gerador_relatorio import GeradorRelatorio


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste FastAPI."""
    return TestClient(app)


@pytest.fixture
def dados_relatorio() -> RelatorioInput:
    """Dados de exemplo para relatório."""
    return RelatorioInput(
        orgao_nome="Prefeitura de Teste",
        orgao_cnpj="12.345.678/0001-90",
        item_descricao="Papel A4",
        categoria_nome="Papel A4",
        periodo_inicio="2025-01-01",
        periodo_fim="2025-12-31",
        amostras=[
            AmostraRelatorio(
                numero_controle="PE-001",
                orgao_origem="Órgão A",
                data_referencia="2025-03-15",
                preco_unitario=22.50,
                unidade="RESMA",
                uf="SP",
                qualidade="HOMOLOGADO",
                outlier=False,
            ),
            AmostraRelatorio(
                numero_controle="PE-002",
                orgao_origem="Órgão B",
                data_referencia="2025-04-10",
                preco_unitario=24.00,
                unidade="RESMA",
                uf="MG",
                qualidade="ESTIMADO",
                outlier=True,
            ),
        ],
        estatisticas={"n": 2, "mediana": 23.25},
        preco_referencial=23.25,
        confianca="MEDIA",
        n_outliers_excluidos=0,
        id_relatorio="TEST-001",
        emitido_em="2025-06-01T10:00:00",
    )


@pytest.fixture
def payload(dados_relatorio: RelatorioInput) -> dict:
    """Payload JSON para API."""
    return dados_relatorio.model_dump()


class TestGerarXlsx:
    """Testes do método gerar_xlsx."""

    def test_gerar_xlsx_retorna_bytes(self, dados_relatorio: RelatorioInput) -> None:
        """gerar_xlsx retorna bytes."""
        gerador = GeradorRelatorio()
        resultado = gerador.gerar_xlsx(dados_relatorio)
        assert isinstance(resultado, bytes)

    def test_gerar_xlsx_tem_cabecalho(self, dados_relatorio: RelatorioInput) -> None:
        """CSV gerado contém linha de cabeçalho."""
        gerador = GeradorRelatorio()
        resultado = gerador.gerar_xlsx(dados_relatorio)
        texto = resultado.decode("utf-8-sig")
        assert "Nº Controle" in texto
        assert "Preço Unitário" in texto

    def test_gerar_xlsx_tem_dados(self, dados_relatorio: RelatorioInput) -> None:
        """CSV gerado contém dados das amostras."""
        gerador = GeradorRelatorio()
        resultado = gerador.gerar_xlsx(dados_relatorio)
        texto = resultado.decode("utf-8-sig")
        assert "PE-001" in texto
        assert "22.50" in texto

    def test_gerar_xlsx_bom(self, dados_relatorio: RelatorioInput) -> None:
        """CSV começa com UTF-8 BOM."""
        gerador = GeradorRelatorio()
        resultado = gerador.gerar_xlsx(dados_relatorio)
        assert resultado[:3] == b"\xef\xbb\xbf"


class TestApiExportacao:
    """Testes dos endpoints de exportação."""

    def test_api_post_xlsx_retorna_csv(self, client: TestClient, payload: dict) -> None:
        """POST /xlsx retorna CSV com status 200."""
        resp = client.post("/api/v1/exportacao/xlsx", json=payload)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_api_post_json_retorna_dict(self, client: TestClient, payload: dict) -> None:
        """POST /json retorna JSON com dados do relatório."""
        resp = client.post("/api/v1/exportacao/json", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgao_nome"] == "Prefeitura de Teste"
        assert data["id_relatorio"] == "TEST-001"

    def test_api_post_xlsx_content_disposition(self, client: TestClient, payload: dict) -> None:
        """POST /xlsx retorna header Content-Disposition correto."""
        resp = client.post("/api/v1/exportacao/xlsx", json=payload)
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "amostras_TEST-001.csv" in cd
