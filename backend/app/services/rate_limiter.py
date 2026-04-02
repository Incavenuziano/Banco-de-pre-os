"""Serviço de rate limiting — controle de taxa de requisições."""

from __future__ import annotations

import time


class RateLimiter:
    """Controla taxa de requisições por chave (IP, tenant, etc.)."""

    def __init__(self) -> None:
        """Inicializa contadores vazios."""
        self.CONTADORES: dict[str, dict] = {}

    def verificar(
        self, key: str, limite: int = 60, janela_segundos: int = 60
    ) -> dict:
        """Verifica se uma chave está dentro do limite de requisições.

        Args:
            key: Identificador da chave (ex: IP, tenant_id).
            limite: Número máximo de requisições na janela.
            janela_segundos: Tamanho da janela em segundos.

        Returns:
            Dict com permitido, restante e reset_em.
        """
        agora = time.time()
        contador = self.CONTADORES.get(key)

        if contador is None or agora >= contador["reset_at"]:
            self.CONTADORES[key] = {
                "count": 1,
                "reset_at": agora + janela_segundos,
            }
            return {
                "permitido": True,
                "restante": limite - 1,
                "reset_em": agora + janela_segundos,
            }

        contador["count"] += 1
        restante = max(limite - contador["count"], 0)
        permitido = contador["count"] <= limite

        return {
            "permitido": permitido,
            "restante": restante,
            "reset_em": contador["reset_at"],
        }

    def resetar(self, key: str) -> None:
        """Reseta o contador de uma chave.

        Args:
            key: Identificador da chave a ser resetada.
        """
        self.CONTADORES.pop(key, None)


# Instância global
rate_limiter = RateLimiter()
