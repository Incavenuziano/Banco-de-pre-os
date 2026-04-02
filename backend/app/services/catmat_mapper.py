"""Mapeamento de códigos CATMAT/CATSER para categorias do Banco de Preços.

Contém um dicionário de lookup com os códigos mais frequentes em compras
municipais, cobrindo as 50 categorias prioritárias.
"""

from typing import Any


# Dicionário: código CATMAT/CATSER → (nome_categoria, confiança 0-1)
# Códigos reais do CATMAT usados frequentemente em pregões municipais.
_CATMAT_LOOKUP: dict[int, tuple[str, float]] = {
    # TIC
    27995: ("Computador Desktop", 0.95),
    44103: ("Computador Desktop", 0.90),
    27880: ("Notebook", 0.95),
    26077: ("Monitor", 0.95),
    26093: ("Impressora", 0.95),
    44811: ("Câmera de Segurança", 0.90),
    26123: ("Switch de Rede", 0.90),
    27464: ("Software e Licenças", 0.85),
    26263: ("Nobreak/UPS", 0.90),
    44906: ("Projetor Multimídia", 0.90),

    # Material de Escritório
    16884: ("Papel A4", 0.95),
    16602: ("Papel A4", 0.90),
    16578: ("Caneta Esferográfica", 0.95),
    16667: ("Toner para Impressora", 0.95),
    16616: ("Cartucho de Tinta", 0.95),
    16659: ("Envelope", 0.90),

    # Limpeza e Higiene
    21181: ("Detergente", 0.95),
    21210: ("Álcool Gel", 0.95),
    21199: ("Papel Higiênico", 0.95),
    21236: ("Desinfetante", 0.95),
    21244: ("Saco de Lixo", 0.90),

    # Alimentação
    19054: ("Arroz", 0.95),
    19062: ("Feijão", 0.95),
    19100: ("Leite", 0.95),
    19127: ("Óleo de Soja", 0.95),
    19038: ("Açúcar", 0.95),

    # Mobiliário
    24902: ("Cadeira de Escritório", 0.90),
    24910: ("Mesa de Escritório", 0.90),
    24937: ("Armário de Aço", 0.90),
    24945: ("Estante Metálica", 0.90),
    24953: ("Carteira Escolar", 0.85),

    # Combustíveis
    15121: ("Gasolina Comum", 0.95),
    15130: ("Diesel S10", 0.95),
    15148: ("Etanol", 0.95),

    # Saúde
    22590: ("Luva de Procedimento", 0.95),
    22616: ("Seringa Descartável", 0.95),
    22632: ("Medicamento Genérico", 0.80),
    22640: ("Máscara Cirúrgica", 0.95),
    22574: ("Material Odontológico", 0.85),

    # Construção
    28055: ("Cimento Portland", 0.95),
    28063: ("Tinta Acrílica", 0.90),
    28080: ("Tubo PVC", 0.90),
    28098: ("Fio Elétrico", 0.90),
    28101: ("Lâmpada LED", 0.90),

    # Serviços (CATSER)
    3883: ("Serviço de Limpeza", 0.90),
    3891: ("Serviço de Vigilância", 0.90),
    3468: ("Serviço de TI", 0.85),
    3476: ("Serviço de Manutenção Predial", 0.85),
    3484: ("Serviço de Transporte", 0.85),

    # Uniformes / EPIs
    22152: ("Uniforme Escolar", 0.85),
    22160: ("Bota de Segurança", 0.90),
    22178: ("Capacete de Segurança", 0.90),
}


def mapear_catmat(
    codigo: int | str | None,
    categorias: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Mapeia um código CATMAT/CATSER para uma categoria do Banco de Preços.

    Args:
        codigo: código numérico CATMAT ou CATSER.
        categorias: lista opcional de dicts com 'id' e 'nome' para
                    resolver o categoria_id.

    Retorna dict com categoria_id, categoria_nome e confianca, ou None
    se o código não estiver no dicionário.
    """
    if codigo is None:
        return None

    try:
        codigo_int = int(codigo)
    except (ValueError, TypeError):
        return None

    resultado = _CATMAT_LOOKUP.get(codigo_int)
    if resultado is None:
        return None

    nome, confianca = resultado
    categoria_id = None

    if categorias:
        for cat in categorias:
            if cat["nome"] == nome:
                categoria_id = cat["id"]
                break

    return {
        "categoria_id": categoria_id,
        "categoria_nome": nome,
        "confianca": confianca,
    }


def listar_codigos() -> dict[int, str]:
    """Retorna dicionário de todos os códigos CATMAT/CATSER mapeados.

    Útil para verificar cobertura e debug.
    """
    return {codigo: nome for codigo, (nome, _) in _CATMAT_LOOKUP.items()}
