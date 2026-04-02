"""Aplicação FastAPI — Banco de Preços."""

from fastapi import FastAPI

from app.routers.precos import router as precos_router
from app.routers.relatorios import router as relatorios_router
from app.routers.busca import router as busca_router
from app.routers.piloto import router as piloto_router
from app.routers.exportacao import router as exportacao_router
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.billing import router as billing_router
from app.routers.onboarding import router as onboarding_router
from app.routers.cobertura import router as cobertura_router
from app.routers.alertas import router as alertas_router
from app.routers.admin import router as admin_router
from app.routers.docs_api import router as docs_router
from app.routers.analise import router as analise_router
from app.routers.api_publica import router as api_publica_router
from app.routers.correcao import router as correcao_router
from app.services.observabilidade_service import observabilidade

from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(
    title="Banco de Preços",
    description="API do Banco de Preços para pesquisa de preços em licitações municipais.",
    version="0.1.0",
)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(precos_router)
app.include_router(relatorios_router)
app.include_router(busca_router)
app.include_router(piloto_router)
app.include_router(exportacao_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(billing_router)
app.include_router(onboarding_router)
app.include_router(cobertura_router)
app.include_router(alertas_router)
app.include_router(admin_router)
app.include_router(docs_router)
app.include_router(analise_router)
app.include_router(correcao_router)
app.include_router(api_publica_router)


@app.get("/health")
def health_check() -> dict:
    """Verifica se a aplicação está no ar."""
    return observabilidade.health_check()


@app.get("/metrics")
def metrics() -> dict:
    """Retorna métricas de uso do sistema."""
    return observabilidade.obter_metricas()
