"""Router FastAPI para autenticação e gerenciamento de sessão."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.middleware.auth_middleware import get_usuario_atual
from app.services.auth_service import (
    gerar_token,
    hash_senha,
    verificar_senha,
    verificar_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Usuários de teste in-memory
_usuarios_teste: list[dict] = [
    {
        "id": "u1",
        "tenant_id": "t1",
        "nome": "Admin Teste",
        "email": "admin@teste.com",
        "senha_hash": hash_senha("senha123"),
        "papel": "admin",
        "ativo": True,
    },
    {
        "id": "u2",
        "tenant_id": "t1",
        "nome": "Operador",
        "email": "op@teste.com",
        "senha_hash": hash_senha("senha456"),
        "papel": "operador",
        "ativo": True,
    },
]


class LoginRequest(BaseModel):
    """Corpo da requisição de login."""

    email: str
    senha: str


class RefreshRequest(BaseModel):
    """Corpo da requisição de refresh de token."""

    token: str


@router.post("/login")
def login(body: LoginRequest) -> dict:
    """Autentica usuário por e-mail e senha.

    Retorna token JWT e dados básicos do usuário.
    """
    usuario = next(
        (u for u in _usuarios_teste if u["email"] == body.email), None
    )
    if usuario is None:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not verificar_senha(body.senha, usuario["senha_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = gerar_token(usuario["id"], usuario["tenant_id"], usuario["papel"])
    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "papel": usuario["papel"],
            "tenant_id": usuario["tenant_id"],
        },
    }


@router.post("/refresh")
def refresh(body: RefreshRequest) -> dict:
    """Renova um token JWT válido.

    Retorna novo token com expiração renovada.
    """
    payload = verificar_token(body.token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    novo_token = gerar_token(payload["sub"], payload["tenant"], payload.get("papel", "viewer"))
    return {"token": novo_token}


@router.get("/me")
def me(request: Request) -> dict:
    """Retorna dados do usuário autenticado pelo token JWT."""
    usuario_payload = get_usuario_atual(request)
    if usuario_payload is None:
        raise HTTPException(status_code=401, detail="Não autenticado")

    # Buscar dados completos do usuário
    usuario = next(
        (u for u in _usuarios_teste if u["id"] == usuario_payload["sub"]), None
    )
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "papel": usuario["papel"],
        "tenant_id": usuario["tenant_id"],
    }
