"""Router FastAPI para alertas de sobrepreço."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.alerta_service import AlertaService
from app.services.alerta_sobrepreco import AlertaSobreprecoService

router = APIRouter(prefix="/api/v1/alertas", tags=["alertas"])
_service = AlertaService()
_sobrepreco = AlertaSobreprecoService()


class AnalisarRequest(BaseModel):
    """Corpo da requisição de análise de preço."""

    preco_proposto: float
    estatisticas: dict
    categoria: str | None = None


class RelatorioRequest(BaseModel):
    """Corpo da requisição de relatório de alertas."""

    itens: list[dict]


class EconomiaRequest(BaseModel):
    """Corpo da requisição de cálculo de economia."""

    preco_proposto: float
    preco_referencial: float
    quantidade: int


@router.post("/analisar")
def analisar(body: AnalisarRequest) -> dict:
    """Analisa um preço proposto em relação à mediana de referência."""
    return _service.analisar_preco(body.preco_proposto, body.estatisticas, body.categoria)


@router.post("/relatorio")
def relatorio(body: RelatorioRequest) -> dict:
    """Gera relatório consolidado de alertas de sobrepreço."""
    return _service.gerar_relatorio_alertas(body.itens)


@router.post("/economia")
def economia(body: EconomiaRequest) -> dict:
    """Calcula economia potencial ao adotar preço referencial."""
    return _service.calcular_economia_potencial(
        body.preco_proposto, body.preco_referencial, body.quantidade
    )


# --- Endpoints de sobrepreço avançado (S16) ---


class AvaliarPrecoRequest(BaseModel):
    """Body para avaliação de sobrepreço."""

    item_descricao: str
    valor: float
    uf: str | None = None
    categoria: str | None = None


@router.post("/avaliar")
def avaliar_preco(body: AvaliarPrecoRequest) -> dict:
    """Avalia um preço contra referências de mercado."""
    return _sobrepreco.avaliar_preco(
        body.item_descricao, body.valor, body.uf, body.categoria
    )


@router.get("/historico")
def historico_alertas(
    tenant_id: str = "default",
    limite: int = 50,
) -> dict:
    """Lista alertas por tenant."""
    alertas = _sobrepreco.obter_historico(tenant_id, limite)
    return {"tenant_id": tenant_id, "total": len(alertas), "alertas": alertas}


@router.get("/estatisticas")
def estatisticas_alertas() -> dict:
    """Resumo de alertas por categoria e UF."""
    return _sobrepreco.obter_estatisticas()
