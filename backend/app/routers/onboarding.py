"""Router FastAPI para onboarding — criação de conta, checklist e feedback."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])
_service = OnboardingService()


class CriarContaRequest(BaseModel):
    """Corpo da requisição de criação de conta."""

    nome: str
    email: str
    plano: str = "free"


class FeedbackRequest(BaseModel):
    """Corpo da requisição de feedback."""

    tenant_id: str
    tipo: str
    texto: str
    nota: int


@router.post("/criar-conta")
def criar_conta(body: CriarContaRequest) -> dict:
    """Cria nova conta (tenant + usuário admin)."""
    return _service.criar_tenant(body.nome, body.email, body.plano)


@router.get("/checklist")
def checklist(tenant_id: str = Query(..., description="ID do tenant")) -> dict:
    """Retorna checklist de onboarding do tenant."""
    return _service.checklist_onboarding(tenant_id)


@router.post("/feedback")
def feedback(body: FeedbackRequest) -> dict:
    """Registra feedback de um tenant."""
    try:
        return _service.registrar_feedback(
            body.tenant_id, body.tipo, body.texto, body.nota
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedbacks")
def feedbacks(tipo: str | None = Query(None, description="Filtro por tipo")) -> list[dict]:
    """Lista feedbacks registrados (admin)."""
    return _service.listar_feedbacks(tipo)


# ---------------------------------------------------------------------------
# Semana 12 — Beta fechado
# ---------------------------------------------------------------------------


class ConviteRequest(BaseModel):
    """Corpo da requisição de convite."""

    tenant_id: str
    email: str
    plano: str = "free"


class AceitarConviteRequest(BaseModel):
    """Corpo da requisição de aceite de convite."""

    token: str


class MarcarEtapaRequest(BaseModel):
    """Corpo da requisição de marcação de etapa."""

    tenant_id: str
    etapa: str


@router.post("/convidar")
def convidar(body: ConviteRequest) -> dict:
    """Gera e registra um convite para novo usuário."""
    return _service.criar_convite(None, body.tenant_id, body.email, body.plano)


@router.post("/aceitar-convite")
def aceitar_convite(body: AceitarConviteRequest) -> dict:
    """Aceita um convite pelo token."""
    return _service.aceitar_convite(None, body.token)


@router.post("/checklist/marcar")
def marcar_etapa(body: MarcarEtapaRequest) -> dict:
    """Marca uma etapa do checklist como concluída."""
    return _service.marcar_etapa(None, body.tenant_id, body.etapa)


# ---------------------------------------------------------------------------
# Semana 19 — Setup wizard
# ---------------------------------------------------------------------------


class SetupRequest(BaseModel):
    """Corpo da requisição de setup completo."""

    nome_organizacao: str
    email_admin: str
    plano: str = "free"
    ufs_interesse: list[str] | None = None
    categorias_interesse: list[str] | None = None


@router.post("/setup")
def setup_wizard(body: SetupRequest) -> dict:
    """Wizard de configuração inicial — cria tenant + admin + configs padrão."""
    # Criar tenant
    conta = _service.criar_tenant(body.nome_organizacao, body.email_admin, body.plano)

    # Configurações
    configuracoes = {
        "ufs_interesse": body.ufs_interesse or ["SP", "RJ", "MG"],
        "categorias_interesse": body.categorias_interesse or [],
        "notificacoes_ativas": True,
        "relatorio_automatico": False,
    }

    return {
        "status": "ok",
        "mensagem": "Setup concluído com sucesso",
        "tenant": conta,
        "configuracoes": configuracoes,
        "proximos_passos": [
            "Importar dados via pipeline PNCP",
            "Configurar categorias de interesse",
            "Gerar primeira pesquisa de preços",
        ],
    }
