"""Testes para o classificador semântico e híbrido."""

from __future__ import annotations

import pytest

from app.services.classificador_semantico import (
    ClassificadorHibrido,
    ClassificadorSemantico,
    TFIDFBackend,
    VOCABULARIO_CATEGORIAS,
    _normalizar_texto,
    _similaridade_cosseno,
    _tokenizar,
)


# ──────────────────────────────────────────────────────────────────────────────
# Utilitários internos
# ──────────────────────────────────────────────────────────────────────────────

class TestUtilitarios:
    """Testa funções auxiliares do módulo."""

    def test_normalizar_texto_remove_acentos(self) -> None:
        assert _normalizar_texto("Álcool Géis") == "alcool geis"

    def test_normalizar_texto_lowercase(self) -> None:
        assert _normalizar_texto("PAPEL A4") == "papel a4"

    def test_tokenizar_remove_stopwords(self) -> None:
        tokens = _tokenizar("Papel de impressão para escritório")
        assert "de" not in tokens
        assert "para" not in tokens
        assert "papel" in tokens

    def test_tokenizar_remove_tokens_curtos(self) -> None:
        tokens = _tokenizar("a de o")
        assert tokens == []

    def test_similaridade_cosseno_vetores_iguais(self) -> None:
        v = [1.0, 0.5, 0.0]
        assert _similaridade_cosseno(v, v) == pytest.approx(1.0, abs=1e-5)

    def test_similaridade_cosseno_vetores_ortogonais(self) -> None:
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        assert _similaridade_cosseno(v1, v2) == pytest.approx(0.0, abs=1e-5)

    def test_similaridade_cosseno_vetores_vazios(self) -> None:
        assert _similaridade_cosseno([], []) == 0.0

    def test_similaridade_cosseno_tamanhos_diferentes(self) -> None:
        assert _similaridade_cosseno([1.0], [1.0, 2.0]) == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# TFIDFBackend
# ──────────────────────────────────────────────────────────────────────────────

class TestTFIDFBackend:
    """Testa o backend TF-IDF diretamente."""

    @pytest.fixture
    def backend(self) -> TFIDFBackend:
        corpus = list(VOCABULARIO_CATEGORIAS.values())
        return TFIDFBackend(corpus)

    def test_embed_retorna_lista_floats(self, backend: TFIDFBackend) -> None:
        vetor = backend.embed("papel sulfite A4")
        assert isinstance(vetor, list)
        assert all(isinstance(v, float) for v in vetor)

    def test_embed_dimensao_consistente(self, backend: TFIDFBackend) -> None:
        v1 = backend.embed("papel A4")
        v2 = backend.embed("gasolina comum")
        assert len(v1) == len(v2) == backend.dimensao

    def test_embed_vetor_normalizado(self, backend: TFIDFBackend) -> None:
        import math
        vetor = backend.embed("toner impressora")
        norma = math.sqrt(sum(v * v for v in vetor))
        # Vetor não-zero deve estar normalizado
        if norma > 0:
            assert norma == pytest.approx(1.0, abs=1e-5)

    def test_embed_texto_vazio_retorna_zeros(self, backend: TFIDFBackend) -> None:
        vetor = backend.embed("")
        assert all(v == 0.0 for v in vetor)

    def test_nome_backend(self, backend: TFIDFBackend) -> None:
        assert backend.nome == "semantico_tfidf"


# ──────────────────────────────────────────────────────────────────────────────
# ClassificadorSemantico (usando TFIDFBackend implicitamente)
# ──────────────────────────────────────────────────────────────────────────────

class TestClassificadorSemantico:
    """Testa o classificador semântico com fallback TF-IDF."""

    @pytest.fixture
    def clf(self) -> ClassificadorSemantico:
        # model_path="" força uso do TFIDFBackend
        return ClassificadorSemantico(model_path="")

    def test_descricao_vazia_retorna_none(self, clf: ClassificadorSemantico) -> None:
        assert clf.classificar("") is None

    def test_descricao_apenas_espacos_retorna_none(self, clf: ClassificadorSemantico) -> None:
        assert clf.classificar("   ") is None

    def test_classifica_combustivel(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("fornecimento de gasolina aditivada para frota municipal")
        assert resultado is not None
        assert "combustível" in resultado["categoria_nome"].lower() or \
               "gasolina" in resultado["categoria_nome"].lower()

    def test_classifica_material_limpeza(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("detergente neutro concentrado higienizacao")
        assert resultado is not None
        assert "limpeza" in resultado["categoria_nome"].lower() or \
               "sabonete" in resultado["categoria_nome"].lower() or \
               "higien" in resultado["categoria_nome"].lower()

    def test_classifica_papel(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("resma de papel sulfite branco 500 folhas")
        assert resultado is not None
        assert "papel" in resultado["categoria_nome"].lower()

    def test_classifica_merenda(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("fornecimento de arroz feijão e óleo para merenda")
        assert resultado is not None
        assert "gêneros" in resultado["categoria_nome"].lower() or \
               "aliment" in resultado["categoria_nome"].lower()

    def test_resultado_tem_campos_obrigatorios(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("papel A4 branco")
        assert resultado is not None
        assert "categoria_nome" in resultado
        assert "score" in resultado
        assert "metodo" in resultado

    def test_score_entre_0_e_1(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("toner impressora laser")
        if resultado is not None:
            assert 0.0 <= resultado["score"] <= 1.0

    def test_metodo_semantico(self, clf: ClassificadorSemantico) -> None:
        resultado = clf.classificar("papel sulfite A4")
        if resultado is not None:
            assert resultado["metodo"].startswith("semantico")

    def test_classificar_lote(self, clf: ClassificadorSemantico) -> None:
        descricoes = ["papel A4", "gasolina", "detergente"]
        resultados = clf.classificar_lote(descricoes)
        assert len(resultados) == 3

    def test_com_categorias_retorna_categoria_id(self) -> None:
        cats = [{"id": 99, "nome": "Papel A4"}]
        clf = ClassificadorSemantico(categorias=cats, model_path="")
        resultado = clf.classificar("resma papel sulfite impressão")
        # Se classificou como Papel A4, deve ter categoria_id=99
        if resultado and resultado["categoria_nome"] == "Papel A4":
            assert resultado["categoria_id"] == 99

    def test_backend_nome_acessivel(self, clf: ClassificadorSemantico) -> None:
        assert clf.backend_nome in ("semantico_tfidf", "semantico_llama")


# ──────────────────────────────────────────────────────────────────────────────
# ClassificadorHibrido
# ──────────────────────────────────────────────────────────────────────────────

class TestClassificadorHibrido:
    """Testa o classificador híbrido (regex + semântico)."""

    @pytest.fixture
    def clf(self) -> ClassificadorHibrido:
        return ClassificadorHibrido(model_path="")

    def test_regex_prevalece_para_match_exato(self, clf: ClassificadorHibrido) -> None:
        resultado = clf.classificar("Toner HP CF226A compatível")
        assert resultado is not None
        # Regex deve capturar e retornar score 1.0
        assert resultado["score"] == 1.0
        assert resultado["metodo"] == "regex"

    def test_semantico_cobre_o_que_regex_nao_cobre(self, clf: ClassificadorHibrido) -> None:
        # "resma de folhas para reprodução" — regex não tem essa variante
        resultado = clf.classificar("resma de folhas para reprodução reprográfica")
        # Semântico deve classificar como papel ou material expediente
        assert resultado is not None

    def test_descricao_vazia_retorna_none(self, clf: ClassificadorHibrido) -> None:
        assert clf.classificar("") is None

    def test_resultado_tem_score(self, clf: ClassificadorHibrido) -> None:
        resultado = clf.classificar("Detergente líquido neutro 500ml")
        assert resultado is not None
        assert "score" in resultado

    def test_classificar_lote_tamanho_correto(self, clf: ClassificadorHibrido) -> None:
        descricoes = ["papel A4", "gasolina comum", "xyz irrelevante 123"]
        resultados = clf.classificar_lote(descricoes)
        assert len(resultados) == 3

    def test_caneta_nao_classificada_por_regex(self, clf: ClassificadorHibrido) -> None:
        """Regex não tem regra para caneta — semântico deve tentar classificar."""
        resultado = clf.classificar("caneta esferográfica azul 1.0mm ponta fina")
        # Pode ou não classificar, mas não deve lançar exceção
        # Se classificar, deve ser material de expediente
        if resultado is not None:
            assert isinstance(resultado["categoria_nome"], str)
