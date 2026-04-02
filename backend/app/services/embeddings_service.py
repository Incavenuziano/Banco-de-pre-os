"""Serviço de busca semântica com TF-IDF simples (stdlib apenas)."""

from __future__ import annotations

import math
import re
import unicodedata

STOPWORDS_PT: set[str] = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "a", "o", "os", "as", "e", "é", "um", "uma", "uns", "umas",
    "para", "por", "com", "que", "se", "ao", "à",
}


class EmbeddingsService:
    """Busca semântica baseada em TF-IDF com similaridade de cosseno."""

    def _tokenizar(self, texto: str) -> list[str]:
        """Tokeniza texto: lowercase, split, remove stopwords e acentos.

        Args:
            texto: Texto a ser tokenizado.

        Returns:
            Lista de tokens filtrados.
        """
        texto_lower = texto.lower()
        # Remover acentos
        texto_norm = unicodedata.normalize("NFD", texto_lower)
        texto_sem_acento = "".join(
            c for c in texto_norm if unicodedata.category(c) != "Mn"
        )
        # Split por espaço/pontuação
        tokens = re.split(r"[\s\W]+", texto_sem_acento)
        # Remover stopwords (comparar sem acento)
        stopwords_norm = set()
        for sw in STOPWORDS_PT:
            sw_norm = unicodedata.normalize("NFD", sw.lower())
            sw_clean = "".join(c for c in sw_norm if unicodedata.category(c) != "Mn")
            stopwords_norm.add(sw_clean)

        return [t for t in tokens if t and t not in stopwords_norm]

    def _calcular_tfidf(self, corpus: list[str]) -> dict[str, float]:
        """Calcula IDF para cada termo do corpus.

        Args:
            corpus: Lista de textos.

        Returns:
            Dict termo → IDF.
        """
        n_docs = len(corpus)
        if n_docs == 0:
            return {}

        doc_freq: dict[str, int] = {}
        for texto in corpus:
            tokens = set(self._tokenizar(texto))
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        idf: dict[str, float] = {}
        for termo, df in doc_freq.items():
            idf[termo] = math.log(n_docs / (1 + df)) + 1

        return idf

    def vetorizar(self, texto: str, corpus: list[str]) -> list[float]:
        """Gera vetor TF-IDF normalizado para um texto.

        Args:
            texto: Texto a ser vetorizado.
            corpus: Corpus de referência para cálculo de IDF.

        Returns:
            Lista de floats (vetor TF-IDF normalizado).
        """
        idf = self._calcular_tfidf(corpus)
        if not idf:
            return []

        vocabulario = sorted(idf.keys())
        tokens = self._tokenizar(texto)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        vetor = [tf.get(termo, 0) * idf.get(termo, 0) for termo in vocabulario]

        # Normalizar (L2)
        norma = math.sqrt(sum(v * v for v in vetor))
        if norma > 0:
            vetor = [v / norma for v in vetor]

        return vetor

    def similaridade_cosseno(self, v1: list[float], v2: list[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores.

        Args:
            v1: Primeiro vetor.
            v2: Segundo vetor.

        Returns:
            Similaridade entre 0.0 e 1.0.
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot = sum(a * b for a, b in zip(v1, v2))
        norma1 = math.sqrt(sum(a * a for a in v1))
        norma2 = math.sqrt(sum(b * b for b in v2))

        if norma1 == 0 or norma2 == 0:
            return 0.0

        return round(min(dot / (norma1 * norma2), 1.0), 6)

    def buscar_similares(
        self, query: str, corpus: list[str], top_n: int = 5
    ) -> list[dict]:
        """Busca textos mais similares à query no corpus.

        Args:
            query: Texto de busca.
            corpus: Lista de textos para comparação.
            top_n: Número máximo de resultados.

        Returns:
            Lista de dicts com texto, score e indice, ordenada por score desc.
        """
        if not corpus:
            return []

        vetor_query = self.vetorizar(query, corpus)
        resultados: list[dict] = []

        for i, texto in enumerate(corpus):
            vetor_doc = self.vetorizar(texto, corpus)
            score = self.similaridade_cosseno(vetor_query, vetor_doc)
            resultados.append({"texto": texto, "score": score, "indice": i})

        resultados.sort(key=lambda x: x["score"], reverse=True)
        return resultados[:top_n]
