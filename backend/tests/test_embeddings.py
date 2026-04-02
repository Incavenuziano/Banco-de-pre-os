"""Testes para o serviço de busca semântica com TF-IDF."""

from __future__ import annotations

from app.services.embeddings_service import EmbeddingsService

service = EmbeddingsService()


class TestEmbeddingsService:
    """Testes do EmbeddingsService."""

    def test_tokenizar_remove_stopwords(self) -> None:
        """Stopwords em PT são removidas na tokenização."""
        tokens = service._tokenizar("Papel de impressora para escritório")
        assert "de" not in tokens
        assert "para" not in tokens
        assert "papel" in tokens

    def test_tokenizar_lowercase(self) -> None:
        """Tokens são convertidos para lowercase."""
        tokens = service._tokenizar("PAPEL SULFITE A4")
        assert all(t == t.lower() for t in tokens)

    def test_similaridade_textos_iguais(self) -> None:
        """Textos idênticos têm similaridade 1.0."""
        corpus = ["papel sulfite A4", "detergente líquido", "gasolina comum"]
        v = service.vetorizar("papel sulfite A4", corpus)
        score = service.similaridade_cosseno(v, v)
        assert score == 1.0

    def test_similaridade_textos_diferentes(self) -> None:
        """Textos diferentes têm similaridade < 1.0."""
        corpus = ["papel sulfite A4", "detergente líquido", "gasolina comum"]
        v1 = service.vetorizar("papel sulfite A4", corpus)
        v2 = service.vetorizar("gasolina comum", corpus)
        score = service.similaridade_cosseno(v1, v2)
        assert score < 1.0

    def test_buscar_similares_retorna_lista(self) -> None:
        """buscar_similares retorna lista de dicts."""
        corpus = ["papel A4", "papel ofício", "detergente", "gasolina"]
        resultado = service.buscar_similares("papel sulfite", corpus)
        assert isinstance(resultado, list)
        assert len(resultado) > 0

    def test_buscar_similares_ordenado_por_score(self) -> None:
        """Resultados são ordenados por score decrescente."""
        corpus = ["papel A4", "papel ofício", "detergente", "gasolina"]
        resultado = service.buscar_similares("papel sulfite", corpus)
        scores = [r["score"] for r in resultado]
        assert scores == sorted(scores, reverse=True)

    def test_buscar_similares_top_n_respeitado(self) -> None:
        """top_n limita o número de resultados."""
        corpus = ["papel A4", "papel ofício", "detergente", "gasolina", "diesel"]
        resultado = service.buscar_similares("papel", corpus, top_n=2)
        assert len(resultado) <= 2

    def test_vetorizar_retorna_lista_floats(self) -> None:
        """vetorizar retorna lista de floats."""
        corpus = ["papel A4", "detergente"]
        vetor = service.vetorizar("papel", corpus)
        assert isinstance(vetor, list)
        assert all(isinstance(v, float) for v in vetor)
