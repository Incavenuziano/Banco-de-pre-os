"""Middleware de autenticação — extrai usuário do token JWT."""

from __future__ import annotations

from fastapi import Request

from app.services.auth_service import verificar_token


def get_usuario_atual(request: Request) -> dict | None:
    """Extrai e valida o token JWT do header Authorization.

    Args:
        request: Objeto Request do FastAPI.

    Returns:
        Payload decodificado do token, ou None se ausente/inválido.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    return verificar_token(token)
