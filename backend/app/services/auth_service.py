"""Serviço de autenticação — hash de senha, JWT simples (sem libs externas)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

SECRET_KEY = "bdp_secret_2026_dev"
_SALT = "bdp_salt_2026"
_TOKEN_EXPIRACAO_SEGUNDOS = 8 * 3600  # 8 horas
_REFRESH_EXPIRACAO_SEGUNDOS = 30 * 24 * 3600  # 30 dias

# Blacklist de tokens revogados (em produção, usar Redis)
_TOKEN_BLACKLIST: set[str] = set()


def hash_senha(senha: str) -> str:
    """Gera hash SHA-256 da senha com salt fixo.

    Args:
        senha: Senha em texto claro.

    Returns:
        Hash hexadecimal da senha.
    """
    return hashlib.sha256(f"{_SALT}{senha}".encode()).hexdigest()


def verificar_senha(senha: str, hash_esperado: str) -> bool:
    """Verifica se a senha corresponde ao hash armazenado.

    Args:
        senha: Senha em texto claro.
        hash_esperado: Hash previamente gerado.

    Returns:
        True se a senha é válida.
    """
    return hash_senha(senha) == hash_esperado


def _b64_encode(data: bytes) -> str:
    """Codifica bytes em base64 URL-safe sem padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    """Decodifica string base64 URL-safe (adicionando padding)."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def gerar_token(usuario_id: str, tenant_id: str, papel: str = "viewer") -> str:
    """Gera JWT simples usando HMAC-SHA256.

    Args:
        usuario_id: ID do usuário.
        tenant_id: ID do tenant.
        papel: Papel do usuário (admin, operador, viewer).

    Returns:
        Token JWT como string (header.payload.signature).
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": usuario_id,
        "tenant": tenant_id,
        "papel": papel,
        "exp": int(time.time()) + _TOKEN_EXPIRACAO_SEGUNDOS,
    }

    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    assinatura = hmac.new(
        SECRET_KEY.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(assinatura)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def gerar_refresh_token(usuario_id: str, tenant_id: str) -> str:
    """Gera refresh token com expiração longa.

    Args:
        usuario_id: ID do usuário.
        tenant_id: ID do tenant.

    Returns:
        Refresh token JWT.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": usuario_id,
        "tenant": tenant_id,
        "tipo": "refresh",
        "exp": int(time.time()) + _REFRESH_EXPIRACAO_SEGUNDOS,
    }
    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    assinatura = hmac.new(
        SECRET_KEY.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(assinatura)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def revogar_token(token: str) -> bool:
    """Adiciona token à blacklist.

    Args:
        token: Token JWT a ser revogado.

    Returns:
        True se revogado com sucesso.
    """
    _TOKEN_BLACKLIST.add(token)
    return True


def token_revogado(token: str) -> bool:
    """Verifica se um token foi revogado.

    Args:
        token: Token JWT.

    Returns:
        True se token está na blacklist.
    """
    return token in _TOKEN_BLACKLIST


def limpar_blacklist() -> None:
    """Limpa blacklist (para testes)."""
    _TOKEN_BLACKLIST.clear()


def verificar_token(token: str) -> dict | None:
    """Verifica e decodifica um token JWT.

    Args:
        token: Token JWT completo.

    Returns:
        Payload decodificado como dict, ou None se inválido/expirado.
    """
    try:
        # Verificar blacklist
        if token_revogado(token):
            return None

        partes = token.split(".")
        if len(partes) != 3:
            return None

        header_b64, payload_b64, sig_b64 = partes

        # Verificar assinatura
        assinatura_esperada = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest()
        sig_recebida = _b64_decode(sig_b64)

        if not hmac.compare_digest(assinatura_esperada, sig_recebida):
            return None

        # Decodificar payload
        payload = json.loads(_b64_decode(payload_b64))

        # Verificar expiração
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None
