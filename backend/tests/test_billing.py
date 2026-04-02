"""Testes para o serviço e API de billing."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.billing_service import BillingService

# Mock de sessão do banco para endpoints que usam Depends(get_db)
_mock_db = MagicMock()
_mock_db.query.return_value.filter.return_value.first.return_value = None


def _override_get_db():
    yield _mock_db


app.dependency_overrides[get_db] = _override_get_db

client = TestClient(app)
service = BillingService()


class TestBillingService:
    """Testes do BillingService."""

    def test_listar_planos_retorna_4(self) -> None:
        """listar_planos retorna exatamente 4 planos."""
        planos = service.listar_planos()
        assert len(planos) == 4

    def test_obter_plano_free(self) -> None:
        """obter_plano('free') retorna dados do plano free."""
        plano = service.obter_plano("free")
        assert plano is not None
        assert plano["id"] == "free"
        assert plano["consultas_mes"] == 10

    def test_obter_plano_inexistente_none(self) -> None:
        """obter_plano com ID inválido retorna None."""
        assert service.obter_plano("platinum") is None

    def test_verificar_limite_permitido(self) -> None:
        """Limite mockado (contadores zerados) é sempre permitido."""
        resultado = service.verificar_limite("t1", "free", "consulta")
        assert resultado["permitido"] is True
        assert resultado["usado"] == 0

    def test_calcular_custo_anual_basico(self) -> None:
        """Custo anual do plano básico = 197 * 10 = 1970."""
        custo = service.calcular_custo_anual("basico")
        assert custo == 1970.0

    def test_calcular_custo_anual_profissional(self) -> None:
        """Custo anual do plano profissional = 497 * 10 = 4970."""
        custo = service.calcular_custo_anual("profissional")
        assert custo == 4970.0


class TestBillingAPI:
    """Testes dos endpoints de billing."""

    def test_api_planos_retorna_lista(self) -> None:
        """GET /billing/planos retorna lista com 4 planos."""
        resp = client.get("/api/v1/billing/planos")
        assert resp.status_code == 200
        assert len(resp.json()) == 4

    def test_api_plano_especifico(self) -> None:
        """GET /billing/plano/basico retorna plano básico."""
        resp = client.get("/api/v1/billing/plano/basico")
        assert resp.status_code == 200
        assert resp.json()["id"] == "basico"

    def test_api_uso_tenant(self) -> None:
        """GET /billing/uso retorna uso do tenant."""
        resp = client.get("/api/v1/billing/uso?tenant_id=t1")
        assert resp.status_code == 200
        data = resp.json()
        assert "consultas" in data
        assert "relatorios" in data

    def test_api_upgrade_sucesso(self) -> None:
        """POST /billing/upgrade realiza upgrade com sucesso."""
        resp = client.post(
            "/api/v1/billing/upgrade",
            json={"tenant_id": "t1", "novo_plano": "profissional"},
        )
        assert resp.status_code == 200
        assert resp.json()["sucesso"] is True


class TestUsoMensalModel:
    """Testes do modelo UsoMensal."""

    def test_uso_mensal_model_campos(self) -> None:
        """Verifica que o modelo UsoMensal tem todos os campos obrigatórios."""
        from app.db.models.uso_mensal import UsoMensal

        colunas = {c.name for c in UsoMensal.__table__.columns}
        esperadas = {
            "id", "tenant_id", "plano_id", "mes_referencia",
            "consultas_utilizadas", "relatorios_utilizados",
            "created_at", "updated_at",
        }
        assert esperadas.issubset(colunas)
        assert UsoMensal.__tablename__ == "uso_mensal"


class TestBillingServicePersistencia:
    """Testes do BillingService com persistência (mock de db)."""

    def test_incrementar_uso_retorna_dict(self) -> None:
        """incrementar_uso retorna dict com dentro_limite, usado e limite."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resultado = service.incrementar_uso(mock_db, "t1", "free", "consulta")

        assert isinstance(resultado, dict)
        assert "dentro_limite" in resultado
        assert "usado" in resultado
        assert "limite" in resultado
        assert resultado["usado"] == 1
        assert resultado["dentro_limite"] is True

    def test_upgrade_persiste_plano(self) -> None:
        """upgrade_tenant persiste plano via upsert e retorna sucesso."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        resultado = service.upgrade_tenant(mock_db, "t1", "profissional")

        assert resultado["sucesso"] is True
        assert resultado["plano_novo"] == "profissional"
        assert resultado["plano_anterior"] == "free"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
