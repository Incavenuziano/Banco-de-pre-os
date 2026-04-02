"""Testes para o serviço de alertas de sobrepreço (AlertaSobreprecoService)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.alerta_sobrepreco import AlertaSobreprecoService

client = TestClient(app)


class TestAvaliarPreco:
    """Testes do método avaliar_preco."""

    def setup_method(self) -> None:
        self.svc = AlertaSobreprecoService()
        self.svc.limpar_historico()

    def test_preco_normal(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        assert resultado["status"] == "NORMAL"
        assert resultado["percentil"] is not None

    def test_preco_atencao(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 32.00, "SP", "Papel A4")
        assert resultado["status"] == "ATENCAO"
        assert resultado["desvio_mediana_pct"] > 25

    def test_preco_critico(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 40.00, "SP", "Papel A4")
        assert resultado["status"] == "CRITICO"
        assert resultado["desvio_mediana_pct"] > 50

    def test_sem_referencia(self) -> None:
        resultado = self.svc.avaliar_preco("Item Desconhecido", 100.0, "XX", "Inexistente")
        assert resultado["status"] == "SEM_REFERENCIA"
        assert resultado["percentil"] is None

    def test_resultado_tem_campos_esperados(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        assert "status" in resultado
        assert "percentil" in resultado
        assert "desvio_mediana_pct" in resultado
        assert "alertas" in resultado
        assert "mediana_referencia" in resultado

    def test_mediana_referencia_correta(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.50, "SP", "Papel A4")
        assert resultado["mediana_referencia"] == 24.50

    def test_sem_uf_usa_media(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.00, None, "Papel A4")
        assert resultado["status"] in ("NORMAL", "ATENCAO", "CRITICO")
        assert resultado["mediana_referencia"] is not None

    def test_preco_abaixo_mediana(self) -> None:
        resultado = self.svc.avaliar_preco("Gasolina", 4.50, "SP", "Gasolina Comum")
        assert resultado["status"] == "NORMAL"
        assert resultado["desvio_mediana_pct"] < 0

    def test_desvio_pct_calculado(self) -> None:
        resultado = self.svc.avaliar_preco("Detergente", 3.20, "SP", "Detergente")
        assert resultado["desvio_mediana_pct"] == 0.0

    def test_alertas_critico_tem_mensagens(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 50.00, "SP", "Papel A4")
        assert resultado["status"] == "CRITICO"
        assert len(resultado["alertas"]) >= 1

    def test_alertas_normal_sem_mensagens(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        assert resultado["status"] == "NORMAL"
        assert len(resultado["alertas"]) == 0

    def test_percentil_entre_1_e_99(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 25.00, "SP", "Papel A4")
        assert 1 <= resultado["percentil"] <= 99

    def test_n_amostras_retornado(self) -> None:
        resultado = self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        assert resultado["n_amostras"] > 0


class TestHistorico:
    """Testes do histórico de alertas."""

    def setup_method(self) -> None:
        self.svc = AlertaSobreprecoService()
        self.svc.limpar_historico()

    def test_historico_vazio_inicialmente(self) -> None:
        historico = self.svc.obter_historico()
        assert len(historico) == 0

    def test_historico_apos_avaliacao(self) -> None:
        self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        historico = self.svc.obter_historico()
        assert len(historico) == 1

    def test_historico_multiplas_avaliacoes(self) -> None:
        self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        self.svc.avaliar_preco("Detergente", 3.50, "RJ", "Detergente")
        historico = self.svc.obter_historico()
        assert len(historico) == 2

    def test_historico_respeita_limite(self) -> None:
        for i in range(10):
            self.svc.avaliar_preco(f"Item {i}", 10.0, "SP", "Papel A4")
        historico = self.svc.obter_historico(limite=5)
        assert len(historico) == 5

    def test_limpar_historico(self) -> None:
        self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        self.svc.limpar_historico()
        assert len(self.svc.obter_historico()) == 0


class TestEstatisticas:
    """Testes de estatísticas dos alertas."""

    def setup_method(self) -> None:
        self.svc = AlertaSobreprecoService()
        self.svc.limpar_historico()

    def test_estatisticas_vazias(self) -> None:
        stats = self.svc.obter_estatisticas()
        assert stats["total_alertas"] == 0

    def test_estatisticas_contagem_por_status(self) -> None:
        self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")  # NORMAL
        self.svc.avaliar_preco("Papel A4", 40.00, "SP", "Papel A4")  # CRITICO
        stats = self.svc.obter_estatisticas()
        assert stats["total_alertas"] == 2
        assert stats["criticos"] >= 1
        assert stats["normais"] >= 1

    def test_estatisticas_por_categoria(self) -> None:
        self.svc.avaliar_preco("Papel A4", 40.00, "SP", "Papel A4")
        stats = self.svc.obter_estatisticas()
        assert "por_categoria" in stats
        assert "Papel A4" in stats["por_categoria"]

    def test_estatisticas_por_uf(self) -> None:
        self.svc.avaliar_preco("Papel A4", 24.00, "SP", "Papel A4")
        stats = self.svc.obter_estatisticas()
        assert "por_uf" in stats
        assert "SP" in stats["por_uf"]


class TestAlertasAPIAvaliar:
    """Testes dos endpoints REST de alertas de sobrepreço."""

    def test_post_avaliar_ok(self) -> None:
        resp = client.post("/api/v1/alertas/avaliar", json={
            "item_descricao": "Papel A4",
            "valor": 24.00,
            "uf": "SP",
            "categoria": "Papel A4",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "percentil" in data

    def test_post_avaliar_critico(self) -> None:
        resp = client.post("/api/v1/alertas/avaliar", json={
            "item_descricao": "Papel A4",
            "valor": 50.00,
            "uf": "SP",
            "categoria": "Papel A4",
        })
        assert resp.json()["status"] == "CRITICO"

    def test_post_avaliar_sem_referencia(self) -> None:
        resp = client.post("/api/v1/alertas/avaliar", json={
            "item_descricao": "Produto X",
            "valor": 100.0,
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "SEM_REFERENCIA"

    def test_get_historico(self) -> None:
        resp = client.get("/api/v1/alertas/historico")
        assert resp.status_code == 200
        data = resp.json()
        assert "alertas" in data
        assert "total" in data

    def test_get_estatisticas(self) -> None:
        resp = client.get("/api/v1/alertas/estatisticas")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alertas" in data
        assert "criticos" in data
