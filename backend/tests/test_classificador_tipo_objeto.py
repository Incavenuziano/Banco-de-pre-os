"""Testes do ClassificadorTipoObjeto e da função inferir_tipo_objeto.

Cobertura:
  - Normalização de texto (acentos, maiúsculas)
  - Classificação de obras (prioridade 90)
  - Classificação de serviços (prioridade 80)
  - Fallback para material
  - Modo standalone (sem DB)
  - Override manual (mock de DB)
  - Precedência override > DB > builtin
  - Função de conveniência inferir_tipo_objeto
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from app.services.classificador_tipo_objeto import (
    ClassificadorTipoObjeto,
    REGRAS_BUILTIN,
    _normalizar,
    inferir_tipo_objeto,
)


# ─────────────────────────────────────────────────────────────────────────────
# Testes de normalização
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalizar:
    def test_remove_acento_cedilha(self) -> None:
        assert _normalizar("serviço") == "SERVICO"

    def test_remove_acento_til(self) -> None:
        assert _normalizar("manutenção") == "MANUTENCAO"

    def test_converte_maiuscula(self) -> None:
        assert _normalizar("papel a4") == "PAPEL A4"

    def test_texto_ja_normalizado(self) -> None:
        assert _normalizar("OBRA") == "OBRA"

    def test_texto_vazio(self) -> None:
        assert _normalizar("") == ""

    def test_acentos_variados(self) -> None:
        result = _normalizar("construção edificação drenagem")
        assert "CONSTRUCAO" in result
        assert "EDIFICACAO" in result
        assert "DRENAGEM" in result


# ─────────────────────────────────────────────────────────────────────────────
# Testes de regras builtin — estrutura
# ─────────────────────────────────────────────────────────────────────────────

class TestRegrasBuitinEstrutura:
    def test_todas_tem_campos_obrigatorios(self) -> None:
        for regra in REGRAS_BUILTIN:
            assert "padrao" in regra, f"Regra sem 'padrao': {regra}"
            assert "tipo" in regra, f"Regra sem 'tipo': {regra}"
            assert "prioridade" in regra, f"Regra sem 'prioridade': {regra}"

    def test_tipo_valido(self) -> None:
        tipos_validos = {"material", "servico", "obra"}
        for regra in REGRAS_BUILTIN:
            assert regra["tipo"] in tipos_validos, f"Tipo inválido: {regra['tipo']}"

    def test_prioridade_no_range(self) -> None:
        for regra in REGRAS_BUILTIN:
            assert 1 <= regra["prioridade"] <= 99, f"Prioridade fora do range: {regra}"

    def test_padroes_sao_regex_validos(self) -> None:
        for regra in REGRAS_BUILTIN:
            try:
                re.compile(regra["padrao"])
            except re.error as exc:
                pytest.fail(f"Regex inválida em regra {regra['padrao']!r}: {exc}")

    def test_obras_tem_prioridade_90(self) -> None:
        obras = [r for r in REGRAS_BUILTIN if r["tipo"] == "obra"]
        assert len(obras) > 0
        for r in obras:
            assert r["prioridade"] == 90, f"Obra com prioridade ≠ 90: {r}"

    def test_servicos_tem_prioridade_80(self) -> None:
        servicos = [r for r in REGRAS_BUILTIN if r["tipo"] == "servico"]
        assert len(servicos) > 0
        for r in servicos:
            assert r["prioridade"] == 80, f"Serviço com prioridade ≠ 80: {r}"


# ─────────────────────────────────────────────────────────────────────────────
# Testes do classificador standalone (sem DB)
# ─────────────────────────────────────────────────────────────────────────────

class TestClassificadorStandalone:
    def setup_method(self) -> None:
        self.c = ClassificadorTipoObjeto(db=None)

    # ── Obras ─────────────────────────────────────────────────────────────

    def test_classifica_obra_palavra_obra(self) -> None:
        r = self.c.classificar("Obra de ampliação da escola municipal")
        assert r["tipo"] == "obra"
        assert r["metodo"] == "builtin"

    def test_classifica_obra_pavimentacao(self) -> None:
        r = self.c.classificar("Pavimentação asfáltica da Rua das Flores")
        assert r["tipo"] == "obra"

    def test_classifica_obra_pavimentacao_sem_acento(self) -> None:
        r = self.c.classificar("Pavimentacao asfaltica da Rua das Flores")
        assert r["tipo"] == "obra"

    def test_classifica_obra_construcao(self) -> None:
        r = self.c.classificar("Construção de quadra poliesportiva")
        assert r["tipo"] == "obra"

    def test_classifica_obra_reforma(self) -> None:
        r = self.c.classificar("Reforma do prédio da secretaria de saúde")
        assert r["tipo"] == "obra"

    def test_classifica_obra_engenharia(self) -> None:
        r = self.c.classificar("Projeto de engenharia para drenagem pluvial")
        assert r["tipo"] == "obra"

    def test_classifica_obra_drenagem(self) -> None:
        r = self.c.classificar("Drenagem pluvial na av. central")
        assert r["tipo"] == "obra"

    def test_classifica_obra_saneamento(self) -> None:
        r = self.c.classificar("Saneamento básico no bairro norte")
        assert r["tipo"] == "obra"

    def test_classifica_obra_score_alto(self) -> None:
        r = self.c.classificar("Terraplanagem e obras de infraestrutura")
        assert r["score"] >= 1.0

    # ── Serviços ──────────────────────────────────────────────────────────

    def test_classifica_servico_palavra_servico(self) -> None:
        r = self.c.classificar("Serviço de limpeza predial")
        assert r["tipo"] == "servico"

    def test_classifica_servico_com_acento(self) -> None:
        r = self.c.classificar("Serviço de vigilância patrimonial")
        assert r["tipo"] == "servico"

    def test_classifica_servico_manutencao(self) -> None:
        r = self.c.classificar("Manutenção preventiva de ar-condicionado")
        assert r["tipo"] == "servico"

    def test_classifica_servico_locacao(self) -> None:
        r = self.c.classificar("Locação de veículo com motorista")
        assert r["tipo"] == "servico"

    def test_classifica_servico_consultoria(self) -> None:
        r = self.c.classificar("Consultoria em gestão municipal")
        assert r["tipo"] == "servico"

    def test_classifica_servico_limpeza(self) -> None:
        r = self.c.classificar("Limpeza e conservação das vias públicas")
        assert r["tipo"] == "servico"

    def test_classifica_servico_transporte(self) -> None:
        r = self.c.classificar("Transporte escolar para alunos da zona rural")
        assert r["tipo"] == "servico"

    def test_classifica_servico_vigilancia(self) -> None:
        r = self.c.classificar("Vigilancia armada 24h")
        assert r["tipo"] == "servico"

    def test_classifica_servico_dedetizacao(self) -> None:
        r = self.c.classificar("Dedetizacao e controle de pragas urbanas")
        assert r["tipo"] == "servico"

    def test_classifica_servico_telefonia(self) -> None:
        r = self.c.classificar("Telefonia fixa e móvel")
        assert r["tipo"] == "servico"

    def test_classifica_servico_internet(self) -> None:
        r = self.c.classificar("Internet banda larga para as unidades de saúde")
        assert r["tipo"] == "servico"

    def test_classifica_servico_treinamento(self) -> None:
        r = self.c.classificar("Treinamento de servidores em excel avançado")
        assert r["tipo"] == "servico"

    def test_classifica_servico_score_alto(self) -> None:
        r = self.c.classificar("Manutenção de equipamentos de informática")
        assert r["score"] >= 1.0

    # ── Material (default) ────────────────────────────────────────────────

    def test_classifica_material_papel_a4(self) -> None:
        r = self.c.classificar("Papel A4 sulfite 75g/m² resma com 500 folhas")
        assert r["tipo"] == "material"

    def test_classifica_material_gasolina(self) -> None:
        r = self.c.classificar("Gasolina comum - abastecimento da frota")
        assert r["tipo"] == "material"

    def test_classifica_material_cadeira(self) -> None:
        r = self.c.classificar("Cadeira de escritório giratória com regulagem")
        assert r["tipo"] == "material"

    def test_classifica_material_toner(self) -> None:
        r = self.c.classificar("Toner HP 85A original para impressora LaserJet")
        assert r["tipo"] == "material"

    def test_classifica_material_arroz(self) -> None:
        r = self.c.classificar("Arroz tipo 1 agulhinha polido saco 5kg")
        assert r["tipo"] == "material"

    def test_classifica_material_descricao_vazia(self) -> None:
        r = self.c.classificar("")
        assert r["tipo"] == "material"

    def test_classifica_material_metodo_builtin_default(self) -> None:
        r = self.c.classificar("")
        assert "builtin" in r["metodo"]

    # ── Precedência obra > serviço ─────────────────────────────────────────

    def test_obra_tem_precedencia_sobre_servico(self) -> None:
        # "limpeza" seria serviço mas "obra" aparece também
        r = self.c.classificar("Obra de limpeza e recuperação de canal")
        assert r["tipo"] == "obra"

    # ── None e edge cases ─────────────────────────────────────────────────

    def test_descricao_none_retorna_material(self) -> None:
        r = self.c.classificar(None)  # type: ignore[arg-type]
        assert r["tipo"] == "material"

    def test_descricao_so_espacos(self) -> None:
        r = self.c.classificar("   ")
        assert r["tipo"] == "material"

    def test_descricao_longa_com_keyword(self) -> None:
        descricao = "A" * 500 + " CONSTRUÇÃO " + "B" * 500
        r = self.c.classificar(descricao)
        assert r["tipo"] == "obra"


# ─────────────────────────────────────────────────────────────────────────────
# Testes com mock de DB (override)
# ─────────────────────────────────────────────────────────────────────────────

class TestClassificadorComOverride:
    def _make_db_com_override(self, tipo_override: str) -> MagicMock:
        """Cria mock de Session que retorna override para qualquer item_id."""
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda i: tipo_override if i == 0 else None)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row

        mock_db = MagicMock()
        mock_db.execute.return_value = mock_result
        return mock_db

    def _make_db_sem_override(self) -> MagicMock:
        """Mock de Session sem override (fetchone retorna None)."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_result.fetchall.return_value = []

        mock_db = MagicMock()
        mock_db.execute.return_value = mock_result
        return mock_db

    def test_override_material_para_item_classificado_como_obra(self) -> None:
        db = self._make_db_com_override("material")
        c = ClassificadorTipoObjeto(db=db)
        r = c.classificar("Reforma do prédio", item_id="uuid-123")
        assert r["tipo"] == "material"
        assert r["metodo"] == "override"

    def test_override_servico(self) -> None:
        db = self._make_db_com_override("servico")
        c = ClassificadorTipoObjeto(db=db)
        r = c.classificar("Papel A4", item_id="uuid-456")
        assert r["tipo"] == "servico"
        assert r["metodo"] == "override"

    def test_override_obra(self) -> None:
        db = self._make_db_com_override("obra")
        c = ClassificadorTipoObjeto(db=db)
        r = c.classificar("Detergente líquido", item_id="uuid-789")
        assert r["tipo"] == "obra"
        assert r["metodo"] == "override"

    def test_sem_override_usa_builtin(self) -> None:
        db = self._make_db_sem_override()
        c = ClassificadorTipoObjeto(db=db)
        r = c.classificar("Serviços de limpeza", item_id="uuid-000")
        # DB não tem override, DB não tem regras (fetchall=[]) → usa builtin
        assert r["tipo"] == "servico"
        assert r["metodo"] == "builtin"

    def test_sem_item_id_nao_busca_override(self) -> None:
        db = self._make_db_com_override("obra")
        c = ClassificadorTipoObjeto(db=db)
        # Sem item_id, não consulta override → usa DB rules → usa builtin
        r = c.classificar("Papel A4 resma 500 folhas", item_id=None)
        # Override não foi consultado → deve ser material
        assert r["tipo"] == "material"


# ─────────────────────────────────────────────────────────────────────────────
# Testes com mock de DB — regras do banco
# ─────────────────────────────────────────────────────────────────────────────

class TestClassificadorRegrasDB:
    def _make_db_com_regras(self, regras: list[tuple[str, str, int]]) -> MagicMock:
        """regras: [(padrao, tipo, prioridade), ...]"""
        mock_rows = [MagicMock(__getitem__=MagicMock(side_effect=lambda i, r=r: r[i]))
                     for r in regras]

        mock_result_override = MagicMock()
        mock_result_override.fetchone.return_value = None  # sem override

        mock_result_regras = MagicMock()
        mock_result_regras.fetchall.return_value = mock_rows

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_result_override  # primeira chamada: buscar override
            return mock_result_regras         # segunda chamada: carregar regras

        mock_db = MagicMock()
        mock_db.execute.side_effect = side_effect
        return mock_db

    def test_regra_db_sobrescreve_builtin(self) -> None:
        # Regra DB: "PAPEL" → obra (prioridade 95, forçado)
        db = self._make_db_com_regras([(r"\bPAPEL\b", "obra", 95)])
        c = ClassificadorTipoObjeto(db=db)
        r = c.classificar("Papel A4 sulfite", item_id="uuid-111")
        assert r["tipo"] == "obra"
        assert r["metodo"] == "db_regras"

    def test_regra_db_invalida_ignorada(self) -> None:
        # Regex inválida não deve travar o classificador
        db = self._make_db_com_regras([(r"[invalid", "obra", 95)])
        c = ClassificadorTipoObjeto(db=db)
        # Regex inválida é ignorada → cai no builtin
        r = c.classificar("Papel A4", item_id="uuid-222")
        # Sem regras DB válidas → builtin default
        assert r["tipo"] == "material"


# ─────────────────────────────────────────────────────────────────────────────
# Testes de invalidar_cache
# ─────────────────────────────────────────────────────────────────────────────

class TestInvalidarCache:
    def test_invalidar_cache_reseta_timestamp(self) -> None:
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_result.fetchone.return_value = None

        db = MagicMock()
        db.execute.return_value = mock_result

        c = ClassificadorTipoObjeto(db=db)
        c._cache_ts = 9999999.0
        c._db_regras = [(re.compile(r"\bTESTE\b"), "obra", 90)]

        c.invalidar_cache()

        assert c._cache_ts == 0.0
        assert c._db_regras == []


# ─────────────────────────────────────────────────────────────────────────────
# Testes da função de conveniência inferir_tipo_objeto
# ─────────────────────────────────────────────────────────────────────────────

class TestInferirTipoObjeto:
    """Testa a função standalone inferir_tipo_objeto (usada pelo coletor)."""

    def test_obra_com_palavra_obra(self) -> None:
        assert inferir_tipo_objeto("Obra de calçamento") == "obra"

    def test_obra_pavimentacao_acentuada(self) -> None:
        assert inferir_tipo_objeto("Pavimentação asfáltica") == "obra"

    def test_obra_construcao(self) -> None:
        assert inferir_tipo_objeto("Construção de UBS") == "obra"

    def test_obra_reforma(self) -> None:
        assert inferir_tipo_objeto("Reforma e ampliação da escola") == "obra"

    def test_obra_drenagem(self) -> None:
        assert inferir_tipo_objeto("Drenagem de águas pluviais") == "obra"

    def test_servico_limpeza(self) -> None:
        assert inferir_tipo_objeto("Serviço de limpeza e conservação predial") == "servico"

    def test_servico_manutencao(self) -> None:
        assert inferir_tipo_objeto("Manutenção corretiva de geradores") == "servico"

    def test_servico_vigilancia(self) -> None:
        assert inferir_tipo_objeto("Vigilância armada 24 horas") == "servico"

    def test_servico_transporte(self) -> None:
        assert inferir_tipo_objeto("Transporte de alunos — zona rural") == "servico"

    def test_servico_internet(self) -> None:
        assert inferir_tipo_objeto("Fornecimento de internet banda larga") == "servico"

    def test_servico_capacitacao(self) -> None:
        assert inferir_tipo_objeto("Capacitação de agentes de saúde") == "servico"

    def test_material_papel(self) -> None:
        assert inferir_tipo_objeto("Papel A4 75g resma 500 folhas") == "material"

    def test_material_combustivel(self) -> None:
        assert inferir_tipo_objeto("Diesel S10 — abastecimento") == "material"

    def test_material_equipamento(self) -> None:
        assert inferir_tipo_objeto("Computador desktop Intel Core i5") == "material"

    def test_material_alimento(self) -> None:
        assert inferir_tipo_objeto("Feijão carioca tipo 1 saco 50kg") == "material"

    def test_none_retorna_material(self) -> None:
        assert inferir_tipo_objeto(None) == "material"

    def test_string_vazia_retorna_material(self) -> None:
        assert inferir_tipo_objeto("") == "material"

    def test_descricao_apenas_numeros(self) -> None:
        assert inferir_tipo_objeto("12345") == "material"
