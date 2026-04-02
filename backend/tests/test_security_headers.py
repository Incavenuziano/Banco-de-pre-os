"""Testes para o middleware de headers de segurança HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSecurityHeaders:
    """Verifica que todos os headers de segurança estão presentes."""

    def test_x_content_type_options(self) -> None:
        resp = client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self) -> None:
        resp = client.get("/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection(self) -> None:
        resp = client.get("/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_strict_transport_security(self) -> None:
        resp = client.get("/health")
        hsts = resp.headers.get("Strict-Transport-Security", "")
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts

    def test_referrer_policy(self) -> None:
        resp = client.get("/health")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self) -> None:
        resp = client.get("/health")
        pp = resp.headers.get("Permissions-Policy", "")
        assert "camera=()" in pp
        assert "microphone=()" in pp

    def test_content_security_policy(self) -> None:
        resp = client.get("/health")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp

    def test_cache_control(self) -> None:
        resp = client.get("/health")
        cc = resp.headers.get("Cache-Control", "")
        assert "no-store" in cc

    def test_headers_em_endpoint_api(self) -> None:
        resp = client.get("/api/v1/busca/categorias")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_headers_em_endpoint_post(self) -> None:
        resp = client.post("/api/v1/alertas/analisar", json={
            "preco_proposto": 100.0,
            "estatisticas": {"mediana": 100.0},
        })
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_headers_em_404(self) -> None:
        resp = client.get("/rota-inexistente")
        assert resp.status_code == 404
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_hsts_max_age_valido(self) -> None:
        resp = client.get("/health")
        hsts = resp.headers.get("Strict-Transport-Security", "")
        # Extrair max-age
        for parte in hsts.split(";"):
            parte = parte.strip()
            if parte.startswith("max-age="):
                valor = int(parte.split("=")[1])
                assert valor >= 31536000  # pelo menos 1 ano

    def test_todos_headers_presentes(self) -> None:
        resp = client.get("/health")
        headers_esperados = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Permissions-Policy",
            "Content-Security-Policy",
            "Cache-Control",
        ]
        for h in headers_esperados:
            assert h in resp.headers, f"Header {h} ausente"

    def test_csp_restringe_scripts(self) -> None:
        resp = client.get("/health")
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "script-src" in csp

    def test_headers_multiplas_requisicoes(self) -> None:
        for _ in range(3):
            resp = client.get("/health")
            assert resp.headers.get("X-Frame-Options") == "DENY"
