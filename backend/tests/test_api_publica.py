"""Testes da API pública — Semana 19."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPrecosPublicos:
    """Testes do endpoint GET /api/v1/public/precos."""

    def test_status_200_sem_key(self) -> None:
        resp = client.get("/api/v1/public/precos")
        assert resp.status_code == 200

    def test_retorna_fonte(self) -> None:
        data = client.get("/api/v1/public/precos").json()
        assert data["fonte"] == "Banco de Preços"

    def test_retorna_itens(self) -> None:
        data = client.get("/api/v1/public/precos").json()
        assert "itens" in data

    def test_filtro_uf(self) -> None:
        data = client.get("/api/v1/public/precos", params={"uf": "SP"}).json()
        for item in data["itens"]:
            assert item["uf"] == "SP"

    def test_paginacao(self) -> None:
        data = client.get("/api/v1/public/precos", params={"por_pagina": 5}).json()
        assert len(data["itens"]) <= 5

    def test_key_invalida_403(self) -> None:
        resp = client.get("/api/v1/public/precos", headers={"X-API-Key": "invalida"})
        assert resp.status_code == 403


class TestCategoriasPublicas:
    """Testes do endpoint GET /api/v1/public/categorias."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/public/categorias")
        assert resp.status_code == 200

    def test_retorna_lista(self) -> None:
        data = client.get("/api/v1/public/categorias").json()
        assert "categorias" in data
        assert "total" in data

    def test_total_positivo(self) -> None:
        data = client.get("/api/v1/public/categorias").json()
        assert data["total"] > 0


class TestIPCAPublico:
    """Testes do endpoint GET /api/v1/public/ipca/fator."""

    def test_status_200(self) -> None:
        resp = client.get("/api/v1/public/ipca/fator", params={
            "data_inicio": "2020-01-01", "data_fim": "2023-01-01"
        })
        assert resp.status_code == 200

    def test_retorna_fator(self) -> None:
        data = client.get("/api/v1/public/ipca/fator", params={
            "data_inicio": "2020-01-01", "data_fim": "2023-01-01"
        }).json()
        assert data["fator"] > 1.0
        assert data["indice"] == "IPCA"

    def test_sem_params_422(self) -> None:
        resp = client.get("/api/v1/public/ipca/fator")
        assert resp.status_code == 422


class TestGerenciarAPIKeys:
    """Testes de gerenciamento de API keys."""

    def test_gerar_key(self) -> None:
        resp = client.post("/api/v1/public/keys/gerar", params={"nome": "Teste"})
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data
        assert "laas_" in data["key"]  # Prefixo da key

    def test_listar_keys(self) -> None:
        resp = client.get("/api/v1/public/keys")
        assert resp.status_code == 200
        assert "keys" in resp.json()

    def test_gerar_e_usar_key(self) -> None:
        key = client.post("/api/v1/public/keys/gerar", params={"nome": "Test2"}).json()["key"]
        resp = client.get("/api/v1/public/precos", headers={"X-API-Key": key})
        assert resp.status_code == 200

    def test_revogar_key(self) -> None:
        data = client.post("/api/v1/public/keys/gerar", params={"nome": "Test3"}).json()
        key_id = data["id"]
        resp = client.delete("/api/v1/public/keys/revogar", params={"key": key_id})
        assert resp.json()["revogada"] is True

    def test_key_revogada_403(self) -> None:
        data = client.post("/api/v1/public/keys/gerar", params={"nome": "Test4"}).json()
        key_plain = data["key"]
        key_id = data["id"]
        client.delete("/api/v1/public/keys/revogar", params={"key": key_id})
        resp = client.get("/api/v1/public/precos", headers={"X-API-Key": key_plain})
        assert resp.status_code == 403

    def test_gerar_key_com_tenant(self) -> None:
        resp = client.post("/api/v1/public/keys/gerar", params={
            "nome": "Org Test", "tenant_id": "t123"
        })
        assert resp.json()["tenant_id"] == "t123"
