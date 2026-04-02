"""Serviço de gerenciamento de API keys para acesso público."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any


_STORE: dict[str, dict[str, Any]] = {}   # key_hash → metadata
_BY_ID: dict[str, str] = {}              # key_id  → key_hash


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApiKeyService:
    """Geração, validação e revogação de API keys."""

    def gerar(
        self,
        nome: str,
        tenant_id: str = "default",
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Gera uma nova API key e retorna a chave em texto claro (única vez)."""
        key_plain = f"laas_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key_plain.encode()).hexdigest()
        key_id = str(uuid.uuid4())
        meta: dict[str, Any] = {
            "id": key_id,
            "nome": nome,
            "tenant_id": tenant_id,
            "scopes": scopes or ["read"],
            "criado_em": _agora(),
            "ultimo_uso": None,
            "uso_total": 0,
            "ativa": True,
        }
        _STORE[key_hash] = meta
        _BY_ID[key_id] = key_hash
        return {"key": key_plain, **meta}

    def validar(self, key_plain: str) -> dict[str, Any] | None:
        """Valida a key e retorna metadados se ativa, None se inválida/revogada."""
        key_hash = hashlib.sha256(key_plain.encode()).hexdigest()
        meta = _STORE.get(key_hash)
        if not meta or not meta["ativa"]:
            return None
        meta["ultimo_uso"] = _agora()
        meta["uso_total"] += 1
        return meta

    def revogar(self, key_id: str) -> bool:
        """Revoga uma API key pelo ID. Retorna True se encontrou."""
        key_hash = _BY_ID.get(key_id)
        if not key_hash or key_hash not in _STORE:
            return False
        _STORE[key_hash]["ativa"] = False
        return True

    def listar(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        """Lista todas as keys (sem revelar o hash). Filtra por tenant se informado."""
        keys = list(_STORE.values())
        if tenant_id:
            keys = [k for k in keys if k["tenant_id"] == tenant_id]
        return keys

    def obter(self, key_id: str) -> dict[str, Any] | None:
        """Retorna metadados de uma key pelo ID."""
        key_hash = _BY_ID.get(key_id)
        if not key_hash:
            return None
        return _STORE.get(key_hash)

    def limpar(self) -> None:
        """Remove todas as keys (uso em testes)."""
        _STORE.clear()
        _BY_ID.clear()
