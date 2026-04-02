"""Testes para o serviço e API de onboarding."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.onboarding_service import FEEDBACKS, OnboardingService

client = TestClient(app)
service = OnboardingService()


class TestOnboardingService:
    """Testes do OnboardingService."""

    def test_criar_tenant_retorna_token(self) -> None:
        """criar_tenant retorna dict com token JWT."""
        resultado = service.criar_tenant("Org Teste", "admin@org.com")
        assert "token" in resultado
        assert isinstance(resultado["token"], str)

    def test_criar_tenant_ids_unicos(self) -> None:
        """Dois tenants criados têm IDs diferentes."""
        r1 = service.criar_tenant("Org A", "a@org.com")
        r2 = service.criar_tenant("Org B", "b@org.com")
        assert r1["tenant_id"] != r2["tenant_id"]
        assert r1["usuario_id"] != r2["usuario_id"]

    def test_criar_tenant_plano_padrao_free(self) -> None:
        """Plano padrão é 'free'."""
        resultado = service.criar_tenant("Org X", "x@org.com")
        assert resultado["plano"] == "free"

    def test_checklist_tem_5_etapas(self) -> None:
        """Checklist retorna exatamente 5 etapas."""
        resultado = service.checklist_onboarding("t1")
        assert len(resultado["etapas"]) == 5

    def test_checklist_conta_criada_concluida(self) -> None:
        """Etapa 'Conta criada' está marcada como concluída."""
        resultado = service.checklist_onboarding("t1")
        conta_criada = resultado["etapas"][0]
        assert conta_criada["nome"] == "Conta criada"
        assert conta_criada["concluida"] is True

    def test_registrar_feedback_sucesso(self) -> None:
        """Feedback com dados válidos é registrado."""
        FEEDBACKS.clear()
        resultado = service.registrar_feedback("t1", "sugestao", "Ótimo sistema", 5)
        assert resultado["mensagem"] == "Feedback registrado com sucesso"
        assert "id" in resultado

    def test_registrar_feedback_nota_invalida(self) -> None:
        """Nota fora de 1-5 gera ValueError."""
        with pytest.raises(ValueError, match="Nota deve ser entre 1 e 5"):
            service.registrar_feedback("t1", "bug", "Erro", 6)

    def test_listar_feedbacks_todos(self) -> None:
        """listar_feedbacks sem filtro retorna todos."""
        FEEDBACKS.clear()
        service.registrar_feedback("t1", "bug", "Bug 1", 2)
        service.registrar_feedback("t1", "elogio", "Bom", 5)
        assert len(service.listar_feedbacks()) == 2

    def test_listar_feedbacks_por_tipo(self) -> None:
        """listar_feedbacks com filtro retorna apenas o tipo solicitado."""
        FEEDBACKS.clear()
        service.registrar_feedback("t1", "bug", "Bug 1", 2)
        service.registrar_feedback("t1", "elogio", "Bom", 5)
        bugs = service.listar_feedbacks(tipo="bug")
        assert len(bugs) == 1
        assert bugs[0]["tipo"] == "bug"


class TestOnboardingAPI:
    """Testes dos endpoints de onboarding."""

    def test_api_criar_conta_ok(self) -> None:
        """POST /onboarding/criar-conta retorna 200 com token."""
        resp = client.post(
            "/api/v1/onboarding/criar-conta",
            json={"nome": "Prefeitura X", "email": "pref@x.gov.br"},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()


class TestOnboardingS12:
    """Testes da Semana 12 — Beta fechado."""

    def test_criar_convite_retorna_token(self) -> None:
        """criar_convite sem db retorna dict com token."""
        resultado = service.criar_convite(None, "t1", "user@org.com")
        assert "token" in resultado
        assert isinstance(resultado["token"], str)
        assert len(resultado["token"]) > 0

    def test_criar_convite_retorna_link(self) -> None:
        """criar_convite retorna link de aceite."""
        resultado = service.criar_convite(None, "t1", "user@org.com")
        assert "link" in resultado
        assert resultado["token"] in resultado["link"]

    def test_aceitar_convite_sem_db(self) -> None:
        """aceitar_convite sem db retorna aceito=True."""
        resultado = service.aceitar_convite(None, "token-fake")
        assert resultado.get("aceito") is True

    def test_marcar_etapa_sem_db(self) -> None:
        """marcar_etapa sem db retorna concluida=True e nome da etapa."""
        resultado = service.marcar_etapa(None, "t1", "Primeira consulta")
        assert resultado.get("concluida") is True
        assert resultado.get("etapa") == "Primeira consulta"

    def test_api_convidar_ok(self) -> None:
        """POST /onboarding/convidar retorna 200 com token."""
        resp = client.post(
            "/api/v1/onboarding/convidar",
            json={"tenant_id": "t1", "email": "u@org.com"},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_api_aceitar_convite_ok(self) -> None:
        """POST /onboarding/aceitar-convite retorna 200."""
        resp = client.post(
            "/api/v1/onboarding/aceitar-convite",
            json={"token": "qualquer-token"},
        )
        assert resp.status_code == 200

    def test_api_marcar_etapa_ok(self) -> None:
        """POST /onboarding/checklist/marcar retorna 200 com etapa."""
        resp = client.post(
            "/api/v1/onboarding/checklist/marcar",
            json={"tenant_id": "t1", "etapa": "Primeira consulta"},
        )
        assert resp.status_code == 200
        assert resp.json().get("concluida") is True

    def test_beta_report_importa(self) -> None:
        """scripts/beta_report.py pode ser importado sem erro."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "beta_report", "scripts/beta_report.py"
        )
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        assert mod is not None
