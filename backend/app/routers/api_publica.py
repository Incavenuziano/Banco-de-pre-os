"""Router FastAPI para API pública — Semana 19.

Endpoints públicos com autenticação por API key.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.services.analise_service import AnaliseService
from app.services.api_key_service import ApiKeyService
from app.services.correcao_monetaria import CorrecaoMonetariaService

router = APIRouter(prefix="/api/v1/public", tags=["public"])

_analise = AnaliseService()
_api_keys = ApiKeyService()
_correcao = CorrecaoMonetariaService()


def _validar_api_key(x_api_key: str | None) -> dict:
    """Valida API key do header. Permite acesso sem key para demo."""
    if x_api_key is None:
        # Acesso demo limitado
        return {"valida": True, "nome": "demo", "restante": 100}
    resultado = _api_keys.validar(x_api_key)
    if resultado is None:
        raise HTTPException(status_code=403, detail="API key inválida ou revogada")
    return resultado


@router.get("/precos", summary="Consulta pública de preços")
def precos_publicos(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    uf: str | None = Query(None),
    categoria: str | None = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=50),
) -> dict:
    """Consulta preços com filtros. Rate limited por API key."""
    _validar_api_key(x_api_key)
    dados = _analise.listar_precos(
        uf=uf, categoria=categoria, pagina=pagina, por_pagina=por_pagina
    )
    return {
        "fonte": "Banco de Preços",
        "versao": "1.0",
        **dados,
    }


@router.get("/categorias", summary="Lista de categorias públicas")
def categorias_publicas(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Lista categorias disponíveis no banco de preços."""
    _validar_api_key(x_api_key)
    return {
        "categorias": _analise.listar_categorias(),
        "total": len(_analise.listar_categorias()),
    }


@router.get("/ipca/fator", summary="Fator de correção IPCA público")
def ipca_fator_publico(
    data_inicio: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="Data final (YYYY-MM-DD)"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """Fator de correção IPCA entre duas datas (acesso público)."""
    _validar_api_key(x_api_key)
    fator = _correcao.fator_correcao(data_inicio, data_fim)
    variacao = _correcao.variacao_periodo(data_inicio, data_fim)
    return {
        "fator": round(fator, 6),
        "variacao_percentual": variacao,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "indice": "IPCA",
    }


# --- Endpoints de gerenciamento de API keys ---


@router.post("/keys/gerar", summary="Gerar nova API key")
def gerar_api_key(nome: str = Query(...), tenant_id: str | None = None) -> dict:
    """Gera nova API key (em produção, requer auth admin)."""
    return _api_keys.gerar(nome, tenant_id=tenant_id or "default")


@router.get("/keys", summary="Listar API keys")
def listar_api_keys(tenant_id: str | None = None) -> dict:
    """Lista API keys ativas."""
    keys = _api_keys.listar(tenant_id)
    return {"total": len(keys), "keys": keys}


@router.delete("/keys/revogar", summary="Revogar API key")
def revogar_api_key(key_id: str = Query(..., alias="key")) -> dict:
    """Revoga uma API key pelo ID."""
    sucesso = _api_keys.revogar(key_id)
    return {"revogada": sucesso}
