"""Testes da heurística de tipo_objeto via inferir_tipo_objeto (coletor municipal)."""

from app.services.classificador_tipo_objeto import inferir_tipo_objeto


def test_infer_tipo_objeto_detecta_servico() -> None:
    assert inferir_tipo_objeto("Servico de limpeza predial") == "servico"


def test_infer_tipo_objeto_detecta_obra() -> None:
    assert inferir_tipo_objeto("Obra de pavimentacao asfaltica") == "obra"


def test_infer_tipo_objeto_default_material() -> None:
    assert inferir_tipo_objeto("Papel A4 sulfite 75g") == "material"
