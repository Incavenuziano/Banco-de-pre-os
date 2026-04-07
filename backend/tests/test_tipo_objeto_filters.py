"""Testes de filtro por tipo_objeto na camada de analise."""

from __future__ import annotations

from types import SimpleNamespace

import app.services.analise_service as analise_module
from app.services.analise_service import AnaliseService, _normalize_tipo_objeto


class _FakeResult:
    def __init__(self, scalar_value=None, rows=None):
        self._scalar_value = scalar_value
        self._rows = rows or []

    def scalar(self):
        return self._scalar_value

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _FakeSession:
    def __init__(self):
        self.calls = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.calls.append((sql, params or {}))
        if 'SELECT COUNT(*)' in sql:
            return _FakeResult(scalar_value=0)
        if 'SELECT * FROM (' in sql:
            return _FakeResult(rows=[])
        if 'COUNT(*)               AS total_registros' in sql:
            row = SimpleNamespace(total_registros=0, total_ufs=0, ultima_atualizacao=None)
            return _FakeResult(rows=[row])
        if 'COUNT(DISTINCT c.id) AS total_categorias' in sql:
            return _FakeResult(scalar_value=0)
        return _FakeResult(rows=[])

    def close(self):
        return None


def test_normalize_tipo_objeto_aceita_valores_validos() -> None:
    assert _normalize_tipo_objeto('Servico') == 'servico'
    assert _normalize_tipo_objeto('obra') == 'obra'


def test_normalize_tipo_objeto_rejeita_valor_invalido() -> None:
    assert _normalize_tipo_objeto('foo') is None


def test_listar_precos_injeta_filtro_tipo_objeto(monkeypatch) -> None:
    fake = _FakeSession()
    monkeypatch.setattr(analise_module, '_get_session', lambda: fake)

    resultado = AnaliseService().listar_precos(tipo_objeto='servico')

    assert resultado['filtros_aplicados']['tipo_objeto'] == 'servico'
    assert any("COALESCE(i.tipo_objeto, 'material') = :tipo_objeto" in sql for sql, _ in fake.calls)
    assert any(params.get('tipo_objeto') == 'servico' for _, params in fake.calls)


def test_dashboard_injeta_filtro_tipo_objeto(monkeypatch) -> None:
    fake = _FakeSession()
    monkeypatch.setattr(analise_module, '_get_session', lambda: fake)

    AnaliseService().obter_resumo_dashboard(tipo_objeto='obra')

    assert any(params.get('tipo_objeto') == 'obra' for _, params in fake.calls)
