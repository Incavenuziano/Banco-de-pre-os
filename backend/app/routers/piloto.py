"""Router da API de piloto controlado — Semana 7.

Endpoints para execução do pipeline piloto e consulta dos
itens mais frequentes por município.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.pncp_conector import PNCPConector
from app.services.pipeline_piloto import PipelinePiloto

router = APIRouter(prefix="/api/v1/piloto", tags=["piloto"])


# ---------- Schemas ----------

class ExecutarPilotoRequest(BaseModel):
    """Corpo da requisição para execução do piloto."""

    uf: str
    municipio: str
    data_inicio: str
    data_fim: str


class ExecutarPilotoResponse(BaseModel):
    """Resposta da execução do piloto."""

    task_id: str
    status: str
    message: str
    resultado: dict[str, Any] | None = None


class TopItemResponse(BaseModel):
    """Item no ranking dos mais frequentes."""

    descricao_normalizada: str
    categoria: str
    ocorrencias: int
    preco_mediano: float | None = None


# ---------- Dados mock para top-itens ----------

_MOCK_TOP_ITENS: list[dict[str, Any]] = [
    {"descricao_normalizada": "PAPEL A4 75G/M2 RESMA 500 FOLHAS", "categoria": "Papel A4", "ocorrencias": 45, "preco_mediano": 22.50},
    {"descricao_normalizada": "DETERGENTE LIQUIDO 500 ML", "categoria": "Detergente", "ocorrencias": 38, "preco_mediano": 2.80},
    {"descricao_normalizada": "GASOLINA COMUM", "categoria": "Gasolina Comum", "ocorrencias": 32, "preco_mediano": 5.89},
    {"descricao_normalizada": "ALCOOL GEL 70% 500 ML", "categoria": "Álcool Gel", "ocorrencias": 28, "preco_mediano": 8.90},
    {"descricao_normalizada": "TONER HP CF226A", "categoria": "Toner para Impressora", "ocorrencias": 25, "preco_mediano": 89.90},
    {"descricao_normalizada": "ARROZ TIPO 1 5 KG", "categoria": "Arroz", "ocorrencias": 24, "preco_mediano": 24.50},
    {"descricao_normalizada": "FEIJAO CARIOCA TIPO 1 1 KG", "categoria": "Feijão", "ocorrencias": 22, "preco_mediano": 7.90},
    {"descricao_normalizada": "DIESEL S10", "categoria": "Diesel S10", "ocorrencias": 20, "preco_mediano": 6.29},
    {"descricao_normalizada": "DESINFETANTE LAVANDA 2 L", "categoria": "Desinfetante", "ocorrencias": 19, "preco_mediano": 5.50},
    {"descricao_normalizada": "OLEO DE SOJA 900 ML", "categoria": "Óleo de Soja", "ocorrencias": 18, "preco_mediano": 6.80},
    {"descricao_normalizada": "ACUCAR CRISTAL 5 KG", "categoria": "Açúcar", "ocorrencias": 17, "preco_mediano": 18.90},
    {"descricao_normalizada": "LEITE INTEGRAL 1 L", "categoria": "Leite", "ocorrencias": 16, "preco_mediano": 5.20},
    {"descricao_normalizada": "CANETA ESFEROGRAFICA AZUL", "categoria": "Papel A4", "ocorrencias": 15, "preco_mediano": 1.20},
    {"descricao_normalizada": "SACO DE LIXO 100 L PRETO", "categoria": "Detergente", "ocorrencias": 14, "preco_mediano": 0.45},
    {"descricao_normalizada": "LUVA DE PROCEDIMENTO M", "categoria": "Luva de Procedimento", "ocorrencias": 13, "preco_mediano": 28.90},
    {"descricao_normalizada": "MASCARA CIRURGICA DESCARTAVEL", "categoria": "Luva de Procedimento", "ocorrencias": 12, "preco_mediano": 12.50},
    {"descricao_normalizada": "CIMENTO PORTLAND 50 KG", "categoria": "Papel A4", "ocorrencias": 11, "preco_mediano": 32.00},
    {"descricao_normalizada": "CADEIRA ESCRITORIO GIRATORIA", "categoria": "Cadeira de Escritório", "ocorrencias": 10, "preco_mediano": 450.00},
    {"descricao_normalizada": "UNIFORME ESCOLAR CAMISETA", "categoria": "Uniforme Escolar", "ocorrencias": 9, "preco_mediano": 25.00},
    {"descricao_normalizada": "BOTA SEGURANCA PVC", "categoria": "Bota de Segurança", "ocorrencias": 8, "preco_mediano": 42.00},
]


# ---------- Endpoints ----------

@router.post("/executar", response_model=ExecutarPilotoResponse)
def executar_piloto(body: ExecutarPilotoRequest) -> ExecutarPilotoResponse:
    """Executa o pipeline piloto para um município.

    Por ora executa síncronamente e retorna resultados direto.
    """
    task_id = str(uuid.uuid4())

    conector = PNCPConector()
    pipeline = PipelinePiloto(conector=conector)

    resultado = pipeline.executar_municipio(
        uf=body.uf,
        municipio=body.municipio,
        data_inicio=body.data_inicio,
        data_fim=body.data_fim,
    )

    # Converte itens processados para serialização
    resultado_serializado = {
        "municipio": resultado["municipio"],
        "uf": resultado["uf"],
        "total_contratacoes": resultado["total_contratacoes"],
        "total_itens": resultado["total_itens"],
        "erros": resultado["erros"],
    }

    return ExecutarPilotoResponse(
        task_id=task_id,
        status="accepted",
        message=f"Pipeline executado para {body.municipio}/{body.uf}",
        resultado=resultado_serializado,
    )


@router.get("/top-itens", response_model=list[TopItemResponse])
def top_itens(
    uf: str = Query(..., description="Sigla da UF"),
    municipio: str = Query(..., description="Nome do município"),
    n: int = Query(20, ge=1, le=100, description="Número de itens a retornar"),
) -> list[TopItemResponse]:
    """Retorna os itens mais frequentes (dados de exemplo).

    Utiliza dados mock fixos para demonstração do formato da API.
    """
    itens = _MOCK_TOP_ITENS[:n]
    return [
        TopItemResponse(
            descricao_normalizada=item["descricao_normalizada"],
            categoria=item["categoria"],
            ocorrencias=item["ocorrencias"],
            preco_mediano=item["preco_mediano"],
        )
        for item in itens
    ]
