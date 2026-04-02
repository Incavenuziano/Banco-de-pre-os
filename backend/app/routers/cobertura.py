"""Router FastAPI para cobertura de UFs e municípios."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.cobertura_service import CoberturaService

router = APIRouter(prefix="/api/v1/cobertura", tags=["cobertura"])
_service = CoberturaService()


@router.get("/ufs")
def listar_ufs() -> list[str]:
    """Lista UFs com cobertura de municípios prioritários."""
    return _service.obter_ufs_cobertas()


@router.get("/municipios")
def municipios(uf: str = Query(..., description="Sigla da UF")) -> list[str]:
    """Retorna municípios prioritários de uma UF."""
    return _service.obter_municipios_por_uf(uf)


@router.get("/indice")
def indice(
    uf: str = Query(..., description="Sigla da UF"),
    n_amostras: int = Query(..., ge=0, description="Número de amostras"),
    n_categorias: int = Query(..., ge=0, description="Número de categorias"),
) -> dict:
    """Calcula índice de cobertura de uma UF."""
    return _service.calcular_indice_cobertura(uf, n_amostras, n_categorias)
