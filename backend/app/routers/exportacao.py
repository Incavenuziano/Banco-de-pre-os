"""Router FastAPI para exportação de dados em CSV/XLSX e JSON."""

from __future__ import annotations

import io

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.schemas.relatorios import RelatorioInput
from app.services.gerador_relatorio import GeradorRelatorio

router = APIRouter(prefix="/api/v1/exportacao", tags=["exportação"])

_gerador = GeradorRelatorio()


@router.post("/xlsx")
def exportar_xlsx(dados: RelatorioInput) -> StreamingResponse:
    """Exporta amostras em formato CSV (UTF-8-BOM) compatível com Excel.

    Args:
        dados: Dados de entrada do relatório.

    Returns:
        StreamingResponse com arquivo CSV para download.
    """
    csv_bytes = _gerador.gerar_xlsx(dados)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=amostras_{dados.id_relatorio}.csv"
        },
    )


@router.post("/json")
def exportar_json(dados: RelatorioInput) -> JSONResponse:
    """Exporta dados estruturados do relatório em formato JSON.

    Args:
        dados: Dados de entrada do relatório.

    Returns:
        JSON com todos os dados do relatório sem gerar PDF.
    """
    return JSONResponse(content=dados.model_dump())
