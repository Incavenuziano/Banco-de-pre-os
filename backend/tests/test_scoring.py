"""Testes unitários do cálculo de score de confiança."""

import pytest

from app.services.scoring import calcular_score_fonte


class TestScoreMinimo:
    """Testes para score mínimo (0)."""

    def test_dict_vazio(self) -> None:
        assert calcular_score_fonte({}) == 0

    def test_campos_none(self) -> None:
        fonte = {
            "url_origem": None,
            "data_referencia": None,
            "quantidade": None,
            "qualidade_tipo": None,
            "storage_path": None,
            "hash_sha256": None,
            "unidade_normalizada": None,
            "categoria_id": None,
            "score_classificacao": None,
        }
        assert calcular_score_fonte(fonte) == 0

    def test_campos_vazios(self) -> None:
        fonte = {
            "url_origem": "",
            "qualidade_tipo": "",
            "storage_path": "",
            "hash_sha256": "",
            "unidade_normalizada": "",
        }
        assert calcular_score_fonte(fonte) == 0


class TestScoreMaximo:
    """Testes para score máximo (100)."""

    def test_todos_campos_presentes_homologado(self) -> None:
        fonte = {
            "url_origem": "https://pncp.gov.br/item/123",
            "data_referencia": "2024-01-15",
            "quantidade": 100,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/evidencias/123.pdf",
            "hash_sha256": "abc123" * 10,
            "unidade_normalizada": "UN",
            "categoria_id": 1,
            "score_classificacao": 0.95,
        }
        assert calcular_score_fonte(fonte) == 100

    def test_score_nao_ultrapassa_100(self) -> None:
        """Mesmo com tudo preenchido, não ultrapassa 100."""
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": "2024-06-01",
            "quantidade": 500,
            "qualidade_tipo": "HOMOLOGADO",
            "storage_path": "/path/doc.pdf",
            "hash_sha256": "deadbeef" * 8,
            "unidade_normalizada": "KG",
            "categoria_id": 5,
            "score_classificacao": 1.0,
        }
        assert calcular_score_fonte(fonte) <= 100


class TestScoreIntermediario:
    """Testes para scores intermediários."""

    def test_apenas_url(self) -> None:
        fonte = {"url_origem": "https://example.com"}
        assert calcular_score_fonte(fonte) == 10

    def test_completude_total(self) -> None:
        """url_origem + data_referencia + quantidade = 20."""
        fonte = {
            "url_origem": "https://example.com",
            "data_referencia": "2024-01-01",
            "quantidade": 10,
        }
        assert calcular_score_fonte(fonte) == 20

    def test_confiabilidade_tabela_oficial(self) -> None:
        fonte = {"qualidade_tipo": "TABELA_OFICIAL"}
        assert calcular_score_fonte(fonte) == 25

    def test_confiabilidade_estimado(self) -> None:
        fonte = {"qualidade_tipo": "ESTIMADO"}
        assert calcular_score_fonte(fonte) == 15

    def test_confiabilidade_mercado(self) -> None:
        fonte = {"qualidade_tipo": "MERCADO"}
        assert calcular_score_fonte(fonte) == 10

    def test_evidencia_storage_path(self) -> None:
        fonte = {"storage_path": "/evidencias/doc.pdf"}
        assert calcular_score_fonte(fonte) == 10

    def test_evidencia_completa(self) -> None:
        fonte = {
            "storage_path": "/evidencias/doc.pdf",
            "hash_sha256": "abc123def456",
        }
        assert calcular_score_fonte(fonte) == 20

    def test_unidade_normalizada_valida(self) -> None:
        fonte = {"unidade_normalizada": "KG"}
        assert calcular_score_fonte(fonte) == 15

    def test_unidade_outro_nao_pontua(self) -> None:
        fonte = {"unidade_normalizada": "OUTRO"}
        assert calcular_score_fonte(fonte) == 0

    def test_categoria_sem_score_alto(self) -> None:
        """Categoria presente mas score <= 0.8 → só 10 pontos."""
        fonte = {"categoria_id": 1, "score_classificacao": 0.5}
        assert calcular_score_fonte(fonte) == 10

    def test_categoria_com_score_alto(self) -> None:
        """Categoria + score > 0.8 → 15 pontos."""
        fonte = {"categoria_id": 1, "score_classificacao": 0.95}
        assert calcular_score_fonte(fonte) == 15

    def test_qualidade_case_insensitive(self) -> None:
        fonte = {"qualidade_tipo": "homologado"}
        assert calcular_score_fonte(fonte) == 30
