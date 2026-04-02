"""Router FastAPI para geração de relatórios PDF."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.relatorios import AmostraRelatorio, RelatorioInput, RelatorioPreviewResponse
from app.services.gerador_relatorio import GeradorRelatorio

import io

router = APIRouter(prefix="/api/v1/relatorios", tags=["relatórios"])

_gerador = GeradorRelatorio()


@router.post("/gerar")
def gerar_relatorio(dados: RelatorioInput) -> StreamingResponse:
    """Gera relatório PDF a partir dos dados informados.

    Retorna o PDF como streaming response para download.
    """
    pdf_bytes = _gerador.gerar(dados)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=relatorio_{dados.id_relatorio}.pdf"
        },
    )


@router.get("/preview/{id_relatorio}")
def preview_relatorio(id_relatorio: str) -> RelatorioPreviewResponse:
    """Retorna dados de exemplo que seriam usados para gerar o relatório.

    Simula a recuperação de dados de um relatório pelo ID.
    """
    dados_mock = RelatorioInput(
        orgao_nome="Prefeitura Municipal de Exemplo",
        orgao_cnpj="12.345.678/0001-90",
        item_descricao="Papel Sulfite A4 75g/m² - Resma com 500 folhas",
        categoria_nome="Papel A4",
        periodo_inicio="2025-01-01",
        periodo_fim="2025-12-31",
        uf_filtro=None,
        amostras=[
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
            AmostraRelatorio(
                numero_controle="PE-003/2025",
                orgao_origem="Prefeitura de Belo Horizonte",
                data_referencia="2025-05-20",
                preco_unitario=85.00,
                unidade="RESMA",
                uf="MG",
                qualidade="ESTIMADO",
                outlier=True,
            ),
        ],
        estatisticas={
            "n": 3,
            "media": 43.83,
            "mediana": 24.00,
            "desvio_padrao": 35.79,
            "q1": 23.25,
            "q3": 54.50,
        },
        preco_referencial=23.25,
        confianca="MEDIA",
        n_outliers_excluidos=1,
        id_relatorio=id_relatorio,
        emitido_em="2025-06-01T10:00:00",
    )
    return RelatorioPreviewResponse(id_relatorio=id_relatorio, dados=dados_mock)
