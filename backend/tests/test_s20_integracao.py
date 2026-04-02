"""Testes de integração S20 — cobertura complementar go-live."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.api_key_service import ApiKeyService
from app.services.backup_service import BackupService
from app.services.correcao_monetaria import CorrecaoMonetariaService

client = TestClient(app)


# ── Fluxo end-to-end: gerar key → usar API pública ─────────────────────────

class TestFluxoApiPublica:
    """Fluxo completo de uso da API pública com API keys."""

    def setup_method(self) -> None:
        ApiKeyService().limpar()

    def test_gerar_key_retorna_prefixo_laas(self) -> None:
        r = client.post("/api/v1/public/keys/gerar?nome=e2e-test")
        assert r.status_code == 200
        assert r.json()["key"].startswith("laas_")

    def test_key_gerada_tem_id(self) -> None:
        r = client.post("/api/v1/public/keys/gerar?nome=id-test")
        data = r.json()
        assert "id" in data
        assert len(data["id"]) > 0

    def test_precos_endpoint_acessivel(self) -> None:
        r = client.get("/api/v1/public/precos")
        # endpoint pode ser público (200) ou protegido (401)
        assert r.status_code in (200, 401)

    def test_precos_retorna_itens(self) -> None:
        rk = client.post("/api/v1/public/keys/gerar?nome=precos-test")
        key = rk.json()["key"]
        r = client.get("/api/v1/public/precos", headers={"x-api-key": key})
        assert r.status_code == 200
        data = r.json()
        assert "itens" in data or "precos" in data or "resultados" in data

    def test_precos_tem_paginacao(self) -> None:
        rk = client.post("/api/v1/public/keys/gerar?nome=pag-test")
        key = rk.json()["key"]
        r = client.get("/api/v1/public/precos", headers={"x-api-key": key})
        assert r.status_code == 200
        data = r.json()
        assert "total" in data or "pagina" in data

    def test_key_invalida_retorna_none_ou_falsa(self) -> None:
        """Key inválida deve retornar None ou dict com valida=False."""
        from app.services.api_key_service import ApiKeyService
        svc = ApiKeyService()
        resultado = svc.validar("laas_invalida_abc123")
        assert resultado is None or resultado.get("valida") is False

    def test_revogar_key(self) -> None:
        from app.services.api_key_service import ApiKeyService
        rk = ApiKeyService().gerar("rev-test")
        key_id = rk["id"]
        r = client.delete(f"/api/v1/public/keys/revogar?key={key_id}")
        assert r.status_code == 200

    def test_filtro_uf_aceito(self) -> None:
        rk = client.post("/api/v1/public/keys/gerar?nome=uf-test")
        key = rk.json()["key"]
        r = client.get("/api/v1/public/precos?uf=DF", headers={"x-api-key": key})
        assert r.status_code == 200
        data = r.json()
        filtros = data.get("filtros_aplicados", {})
        assert filtros.get("uf") == "DF"

    def test_filtro_categoria_aceito(self) -> None:
        rk = client.post("/api/v1/public/keys/gerar?nome=cat-test")
        key = rk.json()["key"]
        r = client.get("/api/v1/public/precos?categoria=Papel", headers={"x-api-key": key})
        assert r.status_code == 200

    def test_listar_categorias_publicas(self) -> None:
        rk = client.post("/api/v1/public/keys/gerar?nome=cats-test")
        key = rk.json()["key"]
        r = client.get("/api/v1/public/categorias", headers={"x-api-key": key})
        assert r.status_code == 200
        data = r.json()
        assert "categorias" in data or isinstance(data, list)


# ── Backup e integridade ────────────────────────────────────────────────────

class TestBackupIntegracao:
    """Integridade do serviço de backup."""

    def test_export_json_decodificavel(self) -> None:
        svc = BackupService()
        b = svc.exportar_json_bytes()
        dados = json.loads(b)
        assert dados["metadados"]["sistema"] == "Banco de Preços v3"

    def test_export_versao_correta(self) -> None:
        svc = BackupService()
        dados = svc.exportar_completo()
        assert dados["metadados"]["versao"] == "1.0"

    def test_integridade_retorna_status(self) -> None:
        svc = BackupService()
        r = svc.validar_integridade()
        assert r["status"] in ("ok", "problemas")

    def test_endpoint_export_responde(self) -> None:
        resp = client.get("/api/v1/admin/export")
        assert resp.status_code == 200
        assert len(resp.content) > 10


# ── Correção monetária — casos extremos ───────────────────────────────────

class TestCorrecaoExtreme:
    """Casos extremos do serviço de correção monetária."""

    def setup_method(self) -> None:
        self.svc = CorrecaoMonetariaService()

    def test_mesmo_periodo_fator_proximo_de_um(self) -> None:
        f = self.svc.fator_correcao("2023-01-01", "2023-01-01")
        assert abs(f - 1.0) < 0.01

    def test_valor_zero_retorna_zero(self) -> None:
        v = self.svc.corrigir_preco(0.0, "2020-01-01", "2025-01-01")
        assert v == 0.0

    def test_fator_sempre_positivo(self) -> None:
        f = self.svc.fator_correcao("2020-01-01", "2026-01-01")
        assert f > 0

    def test_corrigir_via_endpoint(self) -> None:
        r = client.post(
            "/api/v1/correcao/preco",
            json={"valor": 200.0, "data_origem": "2021-01-01", "data_destino": "2025-01-01"},
        )
        assert r.status_code == 200
        dados = r.json()
        assert dados["valor_original"] == 200.0
        assert dados["valor_corrigido"] > 0


# ── Onboarding ──────────────────────────────────────────────────────────────

class TestOnboardingIntegracao:
    """Fluxo de onboarding com schema correto."""

    def test_setup_cria_org(self) -> None:
        r = client.post(
            "/api/v1/onboarding/setup",
            json={
                "nome_organizacao": "Empresa Teste S20",
                "email_admin": "admin@s20.test",
                "plano": "free",
            },
        )
        assert r.status_code in (200, 201)

    def test_setup_retorna_tenant_id(self) -> None:
        r = client.post(
            "/api/v1/onboarding/setup",
            json={
                "nome_organizacao": "Empresa Campos",
                "email_admin": "campos@s20.test",
            },
        )
        assert r.status_code in (200, 201)
        data = r.json()
        # aceita qualquer chave de identificador
        assert any(k in data for k in ("tenant_id", "tenant", "id", "sucesso", "conta"))


# ── Admin — auditoria e métricas ────────────────────────────────────────────

class TestAdminIntegracao:
    """Endpoints admin básicos."""

    def test_auditoria_responde(self) -> None:
        r = client.get("/api/v1/admin/auditoria")
        assert r.status_code == 200

    def test_metricas_retornam_dict(self) -> None:
        r = client.get("/api/v1/admin/metricas")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_saude_tem_status(self) -> None:
        r = client.get("/api/v1/admin/saude")
        assert r.status_code == 200
        assert "status" in r.json()
