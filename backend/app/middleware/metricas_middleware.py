"""Middleware de métricas — registra tempo de cada request."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.observabilidade_service import observabilidade


class MetricasMiddleware(BaseHTTPMiddleware):
    """Middleware que registra duração de cada request nas métricas."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Intercepta requests e registra tempo de execução.

        Args:
            request: Objeto Request.
            call_next: Próximo handler na cadeia.

        Returns:
            Response do handler.
        """
        inicio = time.time()
        response = await call_next(request)
        duracao_ms = (time.time() - inicio) * 1000

        sucesso = 200 <= response.status_code < 400
        observabilidade.registrar_consulta(duracao_ms, sucesso)

        return response
