"""Router FastAPI para documentação técnica — changelog, metodologia e compliance."""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/docs", tags=["docs"])

_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs")


@router.get("/changelog")
def changelog() -> list[dict]:
    """Retorna lista de versões com descrição das mudanças."""
    return [
        {
            "versao": "0.9.0",
            "data": "2026-03-31",
            "descricao": "Semana 19 — documentação e playbooks",
            "mudancas": [
                "Endpoints de documentação técnica (changelog, metodologia, compliance)",
                "Metodologia de cálculo de preço referencial documentada",
                "Playbook operacional com rotinas e troubleshooting",
                "Análise de gaps jurídicos e técnicos",
            ],
        },
        {
            "versao": "0.8.0",
            "data": "2026-03-24",
            "descricao": "Semana 18 — hardening e segurança",
            "mudancas": [
                "Serviço de auditoria com exportação CSV",
                "Rate limiter por chave (IP/tenant)",
                "Endpoints administrativos de auditoria",
            ],
        },
        {
            "versao": "0.7.0",
            "data": "2026-03-17",
            "descricao": "Semana 17 — observabilidade e health checks",
            "mudancas": [
                "Métricas de consultas, relatórios e erros",
                "Health check com status de banco e storage",
                "Endpoint /metrics para monitoramento",
            ],
        },
        {
            "versao": "0.6.0",
            "data": "2026-03-10",
            "descricao": "Semanas 13-16 — expansão de UFs, Compras.gov, alertas e busca semântica",
            "mudancas": [
                "Cobertura de 10 UFs com municípios prioritários",
                "Integração mockada com Compras.gov",
                "Alertas de sobrepreço (CRITICO/ATENCAO/OK)",
                "Busca semântica com TF-IDF",
            ],
        },
        {
            "versao": "0.5.0",
            "data": "2026-02-24",
            "descricao": "Semanas 9-12 — auth, dashboard, billing e onboarding",
            "mudancas": [
                "Autenticação JWT com hash SHA-256",
                "Dashboard com resumo e histórico",
                "Billing com 4 planos (free a enterprise)",
                "Onboarding com checklist e feedback",
            ],
        },
    ]


@router.get("/metodologia")
def metodologia() -> str:
    """Retorna texto da metodologia de cálculo de preço referencial."""
    caminho = os.path.join(_DOCS_DIR, "METODOLOGIA.md")
    try:
        with open(caminho, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Documento de metodologia não encontrado."


@router.get("/compliance")
def compliance() -> dict:
    """Retorna informações de conformidade legal."""
    return {
        "normas_aplicaveis": [
            {
                "norma": "IN 65/2021",
                "descricao": "Instrução Normativa nº 65/2021 — Pesquisa de preços para aquisições públicas",
                "status": "Parcialmente implementado",
                "observacoes": "Cálculo de mediana e exclusão de outliers conforme Art. 5º",
            },
            {
                "norma": "Lei 14.133/2021",
                "descricao": "Nova Lei de Licitações e Contratos Administrativos",
                "status": "Em conformidade",
                "observacoes": "Art. 23 — pesquisa de preços com parâmetros definidos, usando fontes oficiais (PNCP, Compras.gov)",
            },
        ],
        "fontes_preco_aceitas": [
            "PNCP — Portal Nacional de Contratações Públicas",
            "Compras.gov.br — Portal de Compras do Governo Federal",
            "Atas de registro de preços vigentes",
            "Pesquisa de mercado publicada em mídia especializada",
        ],
        "metodologia_resumo": (
            "Preço referencial calculado pela mediana das amostras válidas, "
            "após exclusão de outliers pelo método IQR. Score de confiança "
            "baseado em número de amostras e coeficiente de variação."
        ),
    }
