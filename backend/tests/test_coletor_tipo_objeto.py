"""Testes da heuristica de tipo_objeto no coletor municipal."""

from app.services.coletor_municipal import _infer_tipo_objeto


def test_infer_tipo_objeto_detecta_servico() -> None:
    assert _infer_tipo_objeto('Servico de limpeza predial') == 'servico'


def test_infer_tipo_objeto_detecta_obra() -> None:
    assert _infer_tipo_objeto('Obra de pavimentacao asfaltica') == 'obra'


def test_infer_tipo_objeto_default_material() -> None:
    assert _infer_tipo_objeto('Papel A4 sulfite 75g') == 'material'
