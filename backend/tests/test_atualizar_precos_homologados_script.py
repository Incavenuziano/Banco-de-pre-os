"""Testes do script de atualizacao de precos homologados."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "atualizar_precos_homologados.py"
SPEC = importlib.util.spec_from_file_location("atualizar_precos_homologados", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_float_positive_aceita_float_positivo() -> None:
    assert MODULE._float_positive(12.5) == 12.5


def test_float_positive_aceita_string_com_virgula() -> None:
    assert MODULE._float_positive("10,75") == 10.75


def test_float_positive_rejeita_zero_ou_negativo() -> None:
    assert MODULE._float_positive(0) is None
    assert MODULE._float_positive(-5) is None


def test_float_positive_rejeita_string_invalida() -> None:
    assert MODULE._float_positive("abc") is None


def test_parse_numero_controle_retorna_seq_e_ano() -> None:
    assert MODULE._parse_numero_controle("12345678000199-1-000123/2026") == (123, 2026)
