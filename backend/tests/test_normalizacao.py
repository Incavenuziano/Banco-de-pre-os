"""Testes unitários do serviço de normalização."""

from datetime import date

import pytest

from app.services.normalizacao import (
    calcular_chave_deduplicacao,
    limpar_descricao,
    normalizar_cnpj,
    normalizar_data,
    normalizar_unidade,
)


# --- normalizar_data ---

class TestNormalizarData:
    """Testes para normalizar_data."""

    def test_formato_dd_mm_yyyy_barra(self) -> None:
        assert normalizar_data("25/12/2024") == date(2024, 12, 25)

    def test_formato_yyyy_mm_dd(self) -> None:
        assert normalizar_data("2024-01-15") == date(2024, 1, 15)

    def test_formato_dd_mm_yyyy_hifen(self) -> None:
        assert normalizar_data("05-03-2025") == date(2025, 3, 5)

    def test_formato_dd_mm_yyyy_ponto(self) -> None:
        assert normalizar_data("01.06.2023") == date(2023, 6, 1)

    def test_string_vazia(self) -> None:
        assert normalizar_data("") is None

    def test_formato_invalido(self) -> None:
        assert normalizar_data("abc") is None

    def test_espacos_ao_redor(self) -> None:
        assert normalizar_data("  2024-03-10  ") == date(2024, 3, 10)


# --- normalizar_cnpj ---

class TestNormalizarCnpj:
    """Testes para normalizar_cnpj."""

    def test_cnpj_so_digitos(self) -> None:
        assert normalizar_cnpj("12345678000199") == "12.345.678/0001-99"

    def test_cnpj_com_pontuacao(self) -> None:
        assert normalizar_cnpj("12.345.678/0001-99") == "12.345.678/0001-99"

    def test_cnpj_com_espacos(self) -> None:
        assert normalizar_cnpj("  12345678000199  ") == "12.345.678/0001-99"

    def test_cnpj_digitos_insuficientes(self) -> None:
        assert normalizar_cnpj("1234567800019") is None

    def test_cnpj_digitos_demais(self) -> None:
        assert normalizar_cnpj("123456780001999") is None

    def test_cnpj_vazio(self) -> None:
        assert normalizar_cnpj("") is None

    def test_cnpj_com_letras_extras(self) -> None:
        # Letras extras alem dos dígitos do CNPJ invalidam
        assert normalizar_cnpj("12345678000199999") is None


# --- normalizar_unidade ---

class TestNormalizarUnidade:
    """Testes para normalizar_unidade."""

    def test_un(self) -> None:
        assert normalizar_unidade("UN") == "UN"

    def test_und(self) -> None:
        assert normalizar_unidade("UND") == "UN"

    def test_unidade(self) -> None:
        assert normalizar_unidade("UNIDADE") == "UN"

    def test_unidade_minuscula(self) -> None:
        assert normalizar_unidade("unidade") == "UN"

    def test_cx(self) -> None:
        assert normalizar_unidade("CX") == "CX"

    def test_caixa(self) -> None:
        assert normalizar_unidade("Caixa") == "CX"

    def test_litro(self) -> None:
        assert normalizar_unidade("LITRO") == "L"

    def test_l(self) -> None:
        assert normalizar_unidade("L") == "L"

    def test_kg(self) -> None:
        assert normalizar_unidade("KG") == "KG"

    def test_kilo(self) -> None:
        assert normalizar_unidade("KILO") == "KG"

    def test_quilograma(self) -> None:
        assert normalizar_unidade("quilograma") == "KG"

    def test_metro_quadrado(self) -> None:
        assert normalizar_unidade("M²") == "M2"

    def test_peca(self) -> None:
        assert normalizar_unidade("PEÇA") == "PC"

    def test_pacote(self) -> None:
        assert normalizar_unidade("PACOTE") == "PCT"

    def test_vazio(self) -> None:
        assert normalizar_unidade("") is None

    def test_none(self) -> None:
        assert normalizar_unidade(None) is None

    def test_desconhecido(self) -> None:
        assert normalizar_unidade("XPTO") is None

    def test_com_ponto_final(self) -> None:
        assert normalizar_unidade("UN.") == "UN"


# --- limpar_descricao ---

class TestLimparDescricao:
    """Testes para limpar_descricao."""

    def test_uppercase(self) -> None:
        assert limpar_descricao("papel a4") == "PAPEL A4"

    def test_remove_conforme_edital(self) -> None:
        resultado = limpar_descricao("Papel A4 conforme edital")
        assert "CONFORME EDITAL" not in resultado
        assert "PAPEL A4" in resultado

    def test_remove_demais_especificacoes(self) -> None:
        resultado = limpar_descricao("Caneta azul demais especificações")
        assert "DEMAIS" not in resultado

    def test_remove_pontuacao_iutil(self) -> None:
        resultado = limpar_descricao('Papel A4 75g; "branco"')
        assert ";" not in resultado
        assert '"' not in resultado

    def test_compacta_espacos(self) -> None:
        resultado = limpar_descricao("Papel   A4    75g")
        assert "  " not in resultado

    def test_vazio(self) -> None:
        assert limpar_descricao("") == ""

    def test_remove_vide_edital(self) -> None:
        resultado = limpar_descricao("Caneta esferográfica vide edital")
        assert "VIDE EDITAL" not in resultado

    def test_unicode_nfkc(self) -> None:
        # ﬁ (ligatura) deve ser normalizada para fi
        resultado = limpar_descricao("oﬁcina")
        assert "OFICINA" in resultado

    def test_mantem_hifens(self) -> None:
        resultado = limpar_descricao("papel auto-adesivo")
        assert "-" in resultado

    def test_remove_parenteses_vazios(self) -> None:
        resultado = limpar_descricao("Papel A4 ( )")
        assert "( )" not in resultado
        assert "()" not in resultado


# --- calcular_chave_deduplicacao ---

class TestCalcularChaveDeduplicacao:
    """Testes para calcular_chave_deduplicacao."""

    def test_mesmos_dados_mesma_chave(self) -> None:
        chave1 = calcular_chave_deduplicacao("PNCP", "REF1", 1, date(2024, 1, 1), 10.0, 5.0)
        chave2 = calcular_chave_deduplicacao("PNCP", "REF1", 1, date(2024, 1, 1), 10.0, 5.0)
        assert chave1 == chave2

    def test_dados_diferentes_chave_diferente(self) -> None:
        chave1 = calcular_chave_deduplicacao("PNCP", "REF1", 1, date(2024, 1, 1), 10.0, 5.0)
        chave2 = calcular_chave_deduplicacao("PNCP", "REF2", 1, date(2024, 1, 1), 10.0, 5.0)
        assert chave1 != chave2

    def test_retorna_hexdigest_sha256(self) -> None:
        chave = calcular_chave_deduplicacao("PNCP", "REF1", 1, date(2024, 1, 1), 10.0, 5.0)
        assert len(chave) == 64
        assert all(c in "0123456789abcdef" for c in chave)

    def test_com_nones(self) -> None:
        chave = calcular_chave_deduplicacao("PNCP", None, None, None, None, None)
        assert len(chave) == 64
