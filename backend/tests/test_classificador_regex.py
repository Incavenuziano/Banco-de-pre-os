"""Testes unitários do classificador regex de categorias."""

import pytest

from app.services.classificador_regex import ClassificadorRegex


@pytest.fixture
def classificador() -> ClassificadorRegex:
    """Classificador sem mapa de categorias (categoria_id será None)."""
    return ClassificadorRegex()


@pytest.fixture
def classificador_com_ids() -> ClassificadorRegex:
    """Classificador com IDs para testar resolução de categoria_id."""
    cats = [
        {"id": 1, "nome": "Papel A4"},
        {"id": 2, "nome": "Detergente"},
        {"id": 3, "nome": "Gasolina Comum"},
    ]
    return ClassificadorRegex(categorias=cats)


# --- Papel A4 ---

class TestPapelA4:
    """Testes para classificação de Papel A4."""

    def test_papel_a4_simples(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Papel A4 75g branco")
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"
        assert r["score"] == 1.0

    def test_papel_sulfite_a4(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Papel sulfite A4 resma 500 folhas")
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"

    def test_papel_oficio(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Papel oficio 75g/m2")
        assert r is not None
        assert r["categoria_nome"] == "Papel A4"

    def test_nao_e_papel(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Caneta esferográfica azul")
        # Não deve classificar como Papel A4
        assert r is None or r["categoria_nome"] != "Papel A4"


# --- Limpeza / Higiene ---

class TestLimpeza:
    """Testes para classificação de itens de limpeza."""

    def test_detergente(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Detergente líquido neutro 500ml")
        assert r is not None
        assert r["categoria_nome"] == "Detergente"
        assert r["score"] == 1.0

    def test_alcool_gel(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Alcool gel 70% 500ml")
        assert r is not None
        assert r["categoria_nome"] == "Álcool Gel"
        assert r["score"] == 1.0

    def test_desinfetante(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Desinfetante floral 2 litros")
        assert r is not None
        assert r["categoria_nome"] == "Desinfetante"

    def test_nao_e_limpeza(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Notebook Dell i5 8GB RAM")
        assert r is None or "Detergente" not in r["categoria_nome"]


# --- Combustíveis ---

class TestCombustiveis:
    """Testes para classificação de combustíveis."""

    def test_gasolina(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Gasolina comum tipo C")
        assert r is not None
        assert r["categoria_nome"] == "Gasolina Comum"
        assert r["score"] == 1.0

    def test_etanol(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Etanol hidratado combustível")
        assert r is not None
        assert r["categoria_nome"] == "Etanol"

    def test_diesel_s10(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Diesel S10 aditivado")
        assert r is not None
        assert r["categoria_nome"] == "Diesel S10"
        assert r["score"] == 1.0

    def test_nao_e_combustivel(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Mesa de escritório em MDF")
        assert r is None or r["categoria_nome"] not in ("Gasolina Comum", "Etanol", "Diesel S10")


# --- Toner / Cartucho ---

class TestTonerCartucho:
    """Testes para classificação de toner e cartucho."""

    def test_toner(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Toner HP CF226A compatível")
        assert r is not None
        assert r["categoria_nome"] == "Toner para Impressora"
        assert r["score"] == 1.0

    def test_cartucho_tinta(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Cartucho de tinta HP 664 preto")
        assert r is not None
        assert r["categoria_nome"] == "Cartucho de Tinta"

    def test_nao_e_toner(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Arroz tipo 1 pacote 5kg")
        assert r is None or r["categoria_nome"] not in ("Toner para Impressora", "Cartucho de Tinta")


# --- Alimentos ---

class TestAlimentos:
    """Testes para classificação de alimentos."""

    def test_arroz(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Arroz tipo 1 longo fino 5kg")
        assert r is not None
        assert r["categoria_nome"] == "Arroz"

    def test_feijao(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Feijão carioca tipo 1 1kg")
        assert r is not None
        assert r["categoria_nome"] == "Feijão"

    def test_oleo_soja(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Oleo de soja refinado 900ml")
        assert r is not None
        assert r["categoria_nome"] == "Óleo de Soja"

    def test_nao_e_alimento(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Capacete de segurança branco")
        assert r is None or r["categoria_nome"] not in ("Arroz", "Feijão", "Açúcar")


# --- Serviços de Limpeza ---

class TestServicosLimpeza:
    """Testes para classificação de serviços de limpeza."""

    def test_servico_limpeza(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Serviço de limpeza e conservação predial")
        assert r is not None
        assert r["categoria_nome"] == "Serviço de Limpeza"

    def test_limpeza_predial(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Contratação de limpeza predial mensal")
        assert r is not None
        assert r["categoria_nome"] == "Serviço de Limpeza"

    def test_nao_e_servico_limpeza(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Gasolina comum automotiva")
        assert r is None or r["categoria_nome"] != "Serviço de Limpeza"


# --- EPI / Uniforme ---

class TestEpiUniforme:
    """Testes para classificação de EPIs e uniformes."""

    def test_capacete(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Capacete de segurança com jugular")
        assert r is not None
        assert r["categoria_nome"] == "Capacete de Segurança"
        assert r["score"] == 1.0

    def test_bota_seguranca(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Bota de segurança com biqueira de aço")
        assert r is not None
        assert r["categoria_nome"] == "Bota de Segurança"

    def test_nao_e_epi(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Papel A4 branco 75g")
        assert r is None or r["categoria_nome"] not in ("Capacete de Segurança", "Bota de Segurança")


# --- Mobiliário ---

class TestMobiliario:
    """Testes para classificação de mobiliário."""

    def test_cadeira_escritorio(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Cadeira de escritório giratória")
        assert r is not None
        assert r["categoria_nome"] == "Cadeira de Escritório"

    def test_armario_aco(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Armário de aço 2 portas")
        assert r is not None
        assert r["categoria_nome"] == "Armário de Aço"

    def test_nao_e_mobiliario(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Detergente líquido 500ml")
        assert r is None or r["categoria_nome"] not in ("Cadeira de Escritório", "Mesa de Escritório")


# --- Informática ---

class TestInformatica:
    """Testes para classificação de informática."""

    def test_computador_i5(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Computador desktop i5 8GB 256GB SSD")
        assert r is not None
        assert r["categoria_nome"] == "Computador Desktop"
        assert r["score"] == 1.0

    def test_nobreak(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Nobreak 1500VA bivolt")
        assert r is not None
        assert r["categoria_nome"] == "Nobreak/UPS"

    def test_nao_e_informatica(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Feijão carioca tipo 1")
        assert r is None or r["categoria_nome"] not in ("Computador Desktop", "Notebook")


# --- Gerais ---

class TestGerais:
    """Testes gerais do classificador."""

    def test_descricao_vazia(self, classificador: ClassificadorRegex) -> None:
        assert classificador.classificar("") is None

    def test_descricao_none_retorna_none(self, classificador: ClassificadorRegex) -> None:
        assert classificador.classificar(None) is None

    def test_sem_match(self, classificador: ClassificadorRegex) -> None:
        assert classificador.classificar("xyz abc 123 irrelevante") is None

    def test_metodo_sempre_regex(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Toner HP LaserJet")
        assert r is not None
        assert r["metodo"] == "regex"

    def test_com_categoria_id(self, classificador_com_ids: ClassificadorRegex) -> None:
        r = classificador_com_ids.classificar("Gasolina comum")
        assert r is not None
        assert r["categoria_id"] == 3

    def test_categoria_id_none_sem_mapa(self, classificador: ClassificadorRegex) -> None:
        r = classificador.classificar("Gasolina comum")
        assert r is not None
        assert r["categoria_id"] is None
