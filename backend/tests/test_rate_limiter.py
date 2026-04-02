"""Testes para o serviço de rate limiting."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.rate_limiter import RateLimiter

client = TestClient(app)


class TestRateLimiterService:
    """Testes do RateLimiter."""

    def test_rate_limiter_permite_dentro_limite(self) -> None:
        """Primeira requisição dentro do limite é permitida."""
        rl = RateLimiter()
        resultado = rl.verificar("test_key", limite=5)
        assert resultado["permitido"] is True

    def test_rate_limiter_bloqueia_apos_limite(self) -> None:
        """Requisição além do limite é bloqueada."""
        rl = RateLimiter()
        for _ in range(5):
            rl.verificar("test_key", limite=5)
        resultado = rl.verificar("test_key", limite=5)
        assert resultado["permitido"] is False

    def test_rate_limiter_restante_decrementa(self) -> None:
        """Campo restante decrementa a cada requisição."""
        rl = RateLimiter()
        r1 = rl.verificar("test_key", limite=10)
        r2 = rl.verificar("test_key", limite=10)
        assert r1["restante"] > r2["restante"]

    def test_rate_limiter_reset(self) -> None:
        """resetar limpa o contador da chave."""
        rl = RateLimiter()
        rl.verificar("test_key", limite=5)
        rl.resetar("test_key")
        resultado = rl.verificar("test_key", limite=5)
        assert resultado["restante"] == 4


class TestRateLimiterAPI:
    """Testes do endpoint de rate limiter."""

    def test_api_rate_limit_status(self) -> None:
        """GET /admin/rate-limit/status retorna 200."""
        resp = client.get("/api/v1/admin/rate-limit/status?key=test")
        assert resp.status_code == 200
        assert "permitido" in resp.json()
