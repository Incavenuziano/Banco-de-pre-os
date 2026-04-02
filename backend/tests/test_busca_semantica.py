"""Testes para o serviço de busca semântica (EmbeddingsService)."""

from __future__ import annotations

import math

from app.services.embeddings_service import EmbeddingsService

svc = EmbeddingsService()


class TestTokenizar:
    """Testes de tokenização."""

    def test_tokeniza_texto_simples(self) -> None:
        tokens = svc._tokenizar("Papel Sulfite A4")
        assert "papel" in tokens
        assert "sulfite" in tokens

    def test_remove_stopwords(self) -> None:
        tokens = svc._tokenizar("preço de papel da resma")
        assert "de" not in tokens
        assert "da" not in tokens

    def test_remove_acentos(self) -> None:
        tokens = svc._tokenizar("café expresso orgânico")
        assert "cafe" in tokens
        assert "organico" in tokens

    def test_texto_vazio(self) -> None:
        tokens = svc._tokenizar("")
        assert tokens == []

    def test_apenas_stopwords(self) -> None:
        tokens = svc._tokenizar("de da do das dos")
        assert tokens == []


class TestVetorizar:
    """Testes de vetorização TF-IDF."""

    def test_vetor_nao_vazio(self) -> None:
        corpus = ["papel sulfite a4", "caneta azul", "toner hp"]
        vetor = svc.vetorizar("papel sulfite", corpus)
        assert len(vetor) > 0

    def test_vetor_normalizado(self) -> None:
        corpus = ["papel sulfite a4", "caneta esferográfica"]
        vetor = svc.vetorizar("papel sulfite a4", corpus)
        norma = math.sqrt(sum(v * v for v in vetor))
        if norma > 0:
            assert abs(norma - 1.0) < 0.01

    def test_corpus_vazio(self) -> None:
        vetor = svc.vetorizar("teste", [])
        assert vetor == []


class TestSimilaridadeCosseno:
    """Testes de similaridade de cosseno."""

    def test_vetores_identicos(self) -> None:
        v = [1.0, 0.0, 0.5]
        assert svc.similaridade_cosseno(v, v) > 0.99

    def test_vetores_ortogonais(self) -> None:
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        assert svc.similaridade_cosseno(v1, v2) == 0.0

    def test_vetores_vazios(self) -> None:
        assert svc.similaridade_cosseno([], []) == 0.0

    def test_vetores_tamanho_diferente(self) -> None:
        assert svc.similaridade_cosseno([1.0], [1.0, 2.0]) == 0.0

    def test_similaridade_entre_0_e_1(self) -> None:
        v1 = [0.5, 0.3, 0.8]
        v2 = [0.2, 0.7, 0.1]
        s = svc.similaridade_cosseno(v1, v2)
        assert 0 <= s <= 1


class TestBuscarSimilares:
    """Testes de busca por similaridade."""

    def test_busca_retorna_resultados(self) -> None:
        corpus = ["papel sulfite a4", "caneta azul esferográfica", "toner para impressora hp"]
        resultados = svc.buscar_similares("papel a4", corpus, top_n=3)
        assert len(resultados) > 0

    def test_resultado_mais_similar_primeiro(self) -> None:
        corpus = ["gasolina comum litro", "diesel s10", "papel sulfite a4 resma"]
        resultados = svc.buscar_similares("gasolina comum", corpus, top_n=3)
        assert resultados[0]["score"] >= resultados[-1]["score"]

    def test_top_n_limita_resultados(self) -> None:
        corpus = ["item " + str(i) for i in range(10)]
        resultados = svc.buscar_similares("item 1", corpus, top_n=3)
        assert len(resultados) <= 3

    def test_corpus_vazio(self) -> None:
        resultados = svc.buscar_similares("teste", [], top_n=5)
        assert resultados == []

    def test_resultado_tem_campos_esperados(self) -> None:
        corpus = ["papel sulfite", "caneta"]
        resultados = svc.buscar_similares("papel", corpus, top_n=2)
        for r in resultados:
            assert "texto" in r
            assert "score" in r
            assert "indice" in r

    def test_score_texto_exato(self) -> None:
        corpus = ["detergente liquido neutro", "sabao em po", "amaciante"]
        resultados = svc.buscar_similares("detergente liquido neutro", corpus, top_n=1)
        assert resultados[0]["score"] > 0.5

    def test_busca_com_acentos(self) -> None:
        corpus = ["café especial", "açúcar cristal"]
        resultados = svc.buscar_similares("cafe especial", corpus, top_n=2)
        assert resultados[0]["texto"] == "café especial"
