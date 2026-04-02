"""Testes extras de busca e alertas sobrepreço — S16 complemento."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.alerta_sobrepreco import AlertaSobreprecoService

client = TestClient(app)


def _limpar() -> None:
    AlertaSobreprecoService().limpar_historico()


class TestBuscaEndpointsExtras:
    """Casos adicionais nos endpoints de busca."""

    def test_semantica_retorna_query_original(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "papel sulfite"})
        assert resp.json()["query"] == "papel sulfite"

    def test_full_text_retorna_total(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "gasolina"})
        assert "total" in resp.json()

    def test_full_text_resultado_tem_descricao(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "gasolina"})
        for item in resp.json()["resultados"]:
            assert "descricao" in item

    def test_combinada_query_retorna_metodo(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "detergente"})
        assert resp.json()["metodo"] == "combinada"

    def test_combinada_pesos_semantica_textual(self) -> None:
        resp = client.get("/api/v1/busca/combinada", params={"q": "papel", "peso_semantica": 0.4})
        pesos = resp.json()["pesos"]
        assert abs(pesos["semantica"] - 0.4) < 0.01
        assert abs(pesos["textual"] - 0.6) < 0.01

    def test_busca_itens_retorna_n_amostras(self) -> None:
        resp = client.get("/api/v1/busca/itens", params={"q": "papel"})
        for item in resp.json()["itens"]:
            assert "n_amostras" in item

    def test_busca_itens_retorna_uf(self) -> None:
        resp = client.get("/api/v1/busca/itens", params={"q": "papel"})
        for item in resp.json()["itens"]:
            assert "uf" in item

    def test_semantica_score_entre_0_e_1(self) -> None:
        resp = client.get("/api/v1/busca/semantica", params={"q": "caneta azul"})
        for item in resp.json()["resultados"]:
            score = item["score_similaridade"]
            assert 0.0 <= score <= 1.0

    def test_categorias_tem_id(self) -> None:
        resp = client.get("/api/v1/busca/categorias")
        for cat in resp.json():
            assert "id" in cat

    def test_categorias_tem_descricao(self) -> None:
        resp = client.get("/api/v1/busca/categorias")
        for cat in resp.json():
            assert "descricao" in cat

    def test_busca_itens_filtra_uf_rj(self) -> None:
        resp = client.get("/api/v1/busca/itens", params={"q": "papel", "uf": "RJ"})
        data = resp.json()
        for item in data["itens"]:
            assert item["uf"] == "RJ"

    def test_full_text_uf_filtro_mg(self) -> None:
        resp = client.get("/api/v1/busca/full-text", params={"q": "cimento", "uf": "MG"})
        data = resp.json()
        for item in data["resultados"]:
            assert item["uf"] == "MG"


class TestAlertaSobreprecoExtras:
    """Casos extras do serviço de sobrepreço."""

    def setup_method(self) -> None:
        _limpar()

    def test_detergente_sp_normal(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Detergente Neutro 500ml", 3.20, uf="SP", categoria="Detergente")
        assert r["status"] == "NORMAL"

    def test_detergente_sp_critico(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Detergente Caro", 10.0, uf="SP", categoria="Detergente")
        assert r["status"] == "CRITICO"

    def test_gasolina_sp_normal(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Gasolina Comum", 5.89, uf="SP", categoria="Gasolina Comum")
        assert r["status"] == "NORMAL"

    def test_retorna_item_na_resposta(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Caneta Azul", 1.20, categoria="CategoriaX")
        assert r["item"] == "Caneta Azul"

    def test_retorna_valor_na_resposta(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Papel A4", 30.0, uf="SP", categoria="Papel A4")
        assert r["valor"] == 30.0

    def test_categoria_sem_uf_usa_media(self) -> None:
        svc = AlertaSobreprecoService()
        r = svc.avaliar_preco("Papel A4", 24.50, categoria="Papel A4")
        assert r["status"] in ("NORMAL", "ATENCAO", "CRITICO")
        assert r["mediana_referencia"] is not None

    def test_historico_tenant_default(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="SP", categoria="Papel A4")
        hist = svc.obter_historico(tenant_id="default")
        assert len(hist) >= 1

    def test_estatisticas_normais_contagem(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="SP", categoria="Papel A4")
        stats = svc.obter_estatisticas()
        assert stats["normais"] >= 1

    def test_avaliacao_post_armazena_tenant(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="SP", categoria="Papel A4")
        hist = svc.obter_historico()
        assert hist[0]["tenant_id"] == "default"

    def test_avaliacao_armazena_uf(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="DF", categoria="Papel A4")
        hist = svc.obter_historico()
        last = hist[-1]
        assert last["uf"] == "DF"

    def test_avaliacao_armazena_categoria(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="SP", categoria="Papel A4")
        hist = svc.obter_historico()
        assert hist[-1]["categoria"] == "Papel A4"

    def test_avaliacao_armazena_timestamp(self) -> None:
        svc = AlertaSobreprecoService()
        svc.avaliar_preco("Papel A4", 24.50, uf="SP", categoria="Papel A4")
        hist = svc.obter_historico()
        assert "avaliado_em" in hist[-1]
