"""Testes para cobertura por município goiano."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.cobertura_service import (
    MUNICIPIOS_GOIAS,
    CoberturaService,
)

client = TestClient(app)
service = CoberturaService()


# ──────────────────────────────────────────────────────────────────────────────
# Lista de municípios
# ──────────────────────────────────────────────────────────────────────────────

class TestMunicipiosGoias:
    """Testa a lista de municípios goianos."""

    def test_lista_nao_vazia(self) -> None:
        assert len(MUNICIPIOS_GOIAS) >= 50

    def test_goiania_esta_na_lista(self) -> None:
        assert "Goiânia" in MUNICIPIOS_GOIAS

    def test_sem_duplicatas(self) -> None:
        assert len(MUNICIPIOS_GOIAS) == len(set(MUNICIPIOS_GOIAS))

    def test_obter_todos_municipios_go_retorna_lista(self) -> None:
        municipios = service.obter_todos_municipios_go()
        assert isinstance(municipios, list)
        assert len(municipios) >= 50


# ──────────────────────────────────────────────────────────────────────────────
# calcular_cobertura_municipio
# ──────────────────────────────────────────────────────────────────────────────

class TestCalcularCoberturaMunicipio:
    """Testa a classificação de cobertura por município."""

    def test_nivel_alta(self) -> None:
        r = service.calcular_cobertura_municipio("Goiânia", "GO", 100, 10)
        assert r["nivel"] == "ALTA"

    def test_nivel_media(self) -> None:
        r = service.calcular_cobertura_municipio("Anápolis", "GO", 30, 4)
        assert r["nivel"] == "MEDIA"

    def test_nivel_baixa(self) -> None:
        r = service.calcular_cobertura_municipio("Ceres", "GO", 8, 2)
        assert r["nivel"] == "BAIXA"

    def test_nivel_insuficiente_sem_dados(self) -> None:
        r = service.calcular_cobertura_municipio("Cumari", "GO", 0, 0)
        assert r["nivel"] == "INSUFICIENTE"

    def test_nivel_insuficiente_poucas_amostras(self) -> None:
        r = service.calcular_cobertura_municipio("Cumari", "GO", 2, 1)
        assert r["nivel"] == "INSUFICIENTE"

    def test_resultado_tem_todos_os_campos(self) -> None:
        r = service.calcular_cobertura_municipio("Goiânia", "GO", 50, 5)
        assert "municipio" in r
        assert "uf" in r
        assert "n_amostras" in r
        assert "n_categorias" in r
        assert "nivel" in r
        assert "ultima_atualizacao" in r

    def test_uf_normalizada_para_maiusculo(self) -> None:
        r = service.calcular_cobertura_municipio("Goiânia", "go", 10, 5)
        assert r["uf"] == "GO"

    def test_ultima_atualizacao_none_quando_nao_informada(self) -> None:
        r = service.calcular_cobertura_municipio("Goiânia", "GO", 10, 5)
        assert r["ultima_atualizacao"] is None

    def test_ultima_atualizacao_iso_quando_informada(self) -> None:
        from datetime import datetime
        dt = datetime(2026, 4, 7, 12, 0, 0)
        r = service.calcular_cobertura_municipio("Goiânia", "GO", 10, 5, dt)
        assert r["ultima_atualizacao"] is not None
        assert "2026-04-07" in r["ultima_atualizacao"]


# ──────────────────────────────────────────────────────────────────────────────
# obter_mapa_cobertura_go
# ──────────────────────────────────────────────────────────────────────────────

class TestMapaCoberturaGo:
    """Testa o mapa de cobertura completo de GO."""

    def test_retorna_todos_municipios(self) -> None:
        mapa = service.obter_mapa_cobertura_go()
        assert len(mapa) == len(MUNICIPIOS_GOIAS)

    def test_sem_contagens_tudo_insuficiente(self) -> None:
        mapa = service.obter_mapa_cobertura_go()
        assert all(m["nivel"] == "INSUFICIENTE" for m in mapa)

    def test_com_contagens_parciais(self) -> None:
        contagens = {
            "Goiânia": {"n_amostras": 100, "n_categorias": 10},
            "Anápolis": {"n_amostras": 25, "n_categorias": 4},
        }
        mapa = service.obter_mapa_cobertura_go(contagens)
        goiania = next(m for m in mapa if m["municipio"] == "Goiânia")
        anapolis = next(m for m in mapa if m["municipio"] == "Anápolis")
        assert goiania["nivel"] == "ALTA"
        assert anapolis["nivel"] == "MEDIA"

    def test_municipios_inexistentes_em_contagens_ficam_insuficientes(self) -> None:
        contagens = {"Goiânia": {"n_amostras": 100, "n_categorias": 10}}
        mapa = service.obter_mapa_cobertura_go(contagens)
        outros = [m for m in mapa if m["municipio"] != "Goiânia"]
        assert all(m["nivel"] == "INSUFICIENTE" for m in outros)

    def test_ordenado_alta_primeiro(self) -> None:
        contagens = {
            "Goiânia": {"n_amostras": 100, "n_categorias": 10},
            "Anápolis": {"n_amostras": 3, "n_categorias": 1},
        }
        mapa = service.obter_mapa_cobertura_go(contagens)
        # Goiânia (ALTA) deve vir antes de Anápolis (INSUFICIENTE)
        idx_goiania = next(i for i, m in enumerate(mapa) if m["municipio"] == "Goiânia")
        idx_anapolis = next(i for i, m in enumerate(mapa) if m["municipio"] == "Anápolis")
        assert idx_goiania < idx_anapolis


# ──────────────────────────────────────────────────────────────────────────────
# resumo_cobertura_go
# ──────────────────────────────────────────────────────────────────────────────

class TestResumoCoberturaGo:
    """Testa o resumo estatístico de cobertura de GO."""

    def test_sem_dados_tudo_insuficiente(self) -> None:
        resumo = service.resumo_cobertura_go()
        assert resumo["por_nivel"]["INSUFICIENTE"] == len(MUNICIPIOS_GOIAS)
        assert resumo["municipios_cobertos"] == 0
        assert resumo["percentual_coberto"] == 0.0

    def test_total_municipios_correto(self) -> None:
        resumo = service.resumo_cobertura_go()
        assert resumo["total_municipios"] == len(MUNICIPIOS_GOIAS)

    def test_com_alguns_cobertos(self) -> None:
        contagens = {
            "Goiânia":  {"n_amostras": 100, "n_categorias": 10},
            "Anápolis": {"n_amostras": 30,  "n_categorias": 5},
        }
        resumo = service.resumo_cobertura_go(contagens)
        assert resumo["municipios_cobertos"] == 2
        assert resumo["percentual_coberto"] > 0.0

    def test_percentual_max_100(self) -> None:
        # Cobre todos com ALTA
        contagens = {
            m: {"n_amostras": 100, "n_categorias": 10}
            for m in MUNICIPIOS_GOIAS
        }
        resumo = service.resumo_cobertura_go(contagens)
        assert resumo["percentual_coberto"] == pytest.approx(100.0)


# ──────────────────────────────────────────────────────────────────────────────
# API endpoints novos
# ──────────────────────────────────────────────────────────────────────────────

class TestCoberturaGoAPI:
    """Testa os novos endpoints de cobertura GO."""

    def test_get_municipios_go_retorna_200(self) -> None:
        resp = client.get("/api/v1/cobertura/go/municipios")
        assert resp.status_code == 200

    def test_get_municipios_go_tem_goiania(self) -> None:
        resp = client.get("/api/v1/cobertura/go/municipios")
        assert "Goiânia" in resp.json()

    def test_get_municipios_go_tamanho(self) -> None:
        resp = client.get("/api/v1/cobertura/go/municipios")
        assert len(resp.json()) >= 50

    def test_get_mapa_go_retorna_200(self) -> None:
        resp = client.get("/api/v1/cobertura/go/mapa")
        assert resp.status_code == 200

    def test_get_mapa_go_retorna_lista(self) -> None:
        resp = client.get("/api/v1/cobertura/go/mapa")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 50

    def test_get_mapa_go_cada_item_tem_nivel(self) -> None:
        resp = client.get("/api/v1/cobertura/go/mapa")
        for item in resp.json():
            assert "nivel" in item
            assert item["nivel"] in ("ALTA", "MEDIA", "BAIXA", "INSUFICIENTE")

    def test_get_resumo_go_retorna_200(self) -> None:
        resp = client.get("/api/v1/cobertura/go/resumo")
        assert resp.status_code == 200

    def test_get_resumo_go_tem_campos_esperados(self) -> None:
        resp = client.get("/api/v1/cobertura/go/resumo")
        data = resp.json()
        assert "total_municipios" in data
        assert "municipios_cobertos" in data
        assert "percentual_coberto" in data
        assert "por_nivel" in data
