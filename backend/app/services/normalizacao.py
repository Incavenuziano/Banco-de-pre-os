"""Serviço de normalização de dados para o Banco de Preços."""

import hashlib
import re
import unicodedata
from datetime import date
from typing import Any

# Expressão usada para marcar limites de palavra ao compilar padrões de sinônimos
_WB = r"\b"


# Mapa de sinônimos de unidade para forma canônica
_UNIDADE_MAP: dict[str, str] = {
    # ── Unidade genérica ─────────────────────────────────────────────────────
    "UN": "UN",
    "UND": "UN",
    "UNID": "UN",
    "UNIDADE": "UN",
    "UNIDADES": "UN",
    # ── Massa ────────────────────────────────────────────────────────────────
    "KG": "KG",
    "KILO": "KG",
    "QUILO": "KG",
    "QUILOGRAMA": "KG",
    "QUILOGRAMAS": "KG",
    "G": "G",
    "GR": "G",           # variante comum (ex: "500GR")
    "GRAMA": "G",
    "GRAMAS": "G",
    "TON": "TON",
    "TONELADA": "TON",
    "TONELADAS": "TON",
    # ── Farmacêutico / Saúde ─────────────────────────────────────────────────
    "MG": "MG",          # miligrama — importante para medicamentos
    "MILIGRAMA": "MG",
    "MILIGRAMAS": "MG",
    "MCG": "MCG",        # micrograma
    "UG": "MCG",
    "UI": "UI",          # unidade internacional (vacinas, hormônios)
    "IU": "UI",
    "CP": "CP",
    "COMP": "CP",
    "COMPRIMIDO": "CP",
    "COMPRIMIDOS": "CP",
    "CAP": "CAP",        # cápsula
    "CAPSULA": "CAP",
    "CAPSULAS": "CAP",
    "CÁPSULA": "CAP",
    "CÁPSULAS": "CAP",
    "AMP": "AMP",
    "AMPOLA": "AMP",
    "AMPOLAS": "AMP",
    "DS": "DS",          # dose
    "DOSE": "DS",
    "DOSES": "DS",
    # ── Volume ───────────────────────────────────────────────────────────────
    "L": "L",
    "LT": "L",
    "LITRO": "L",
    "LITROS": "L",
    "ML": "ML",
    "MILILITRO": "ML",
    "MILILITROS": "ML",
    "GL": "GL",
    "GALAO": "GL",
    "GALÃO": "GL",
    # ── Comprimento / Área / Volume ──────────────────────────────────────────
    "CM": "CM",
    "CENTIMETRO": "CM",
    "CENTIMETROS": "CM",
    "M": "M",
    "METRO": "M",
    "METROS": "M",
    "M2": "M2",
    "M²": "M2",
    "METRO QUADRADO": "M2",
    "METROS QUADRADOS": "M2",
    "M3": "M3",
    "M³": "M3",
    "METRO CUBICO": "M3",
    "METROS CUBICOS": "M3",
    # ── Embalagem / Papelaria ─────────────────────────────────────────────────
    "CX": "CX",
    "CAIXA": "CX",
    "CAIXAS": "CX",
    "PC": "PC",
    "PECA": "PC",
    "PECAS": "PC",
    "PEÇA": "PC",
    "PEÇAS": "PC",
    "POTE": "PC",        # pote = container unitário
    "POTES": "PC",
    "PCT": "PCT",
    "PACOTE": "PCT",
    "PACOTES": "PCT",
    "SACHE": "PCT",      # sachê = pacote individual
    "SACHÊ": "PCT",
    "FD": "FD",
    "FARDO": "FD",
    "FARDOS": "FD",
    "FR": "FR",
    "FRASCO": "FR",
    "FRASCOS": "FR",
    "GARRAFA": "FR",     # garrafa = frasco de vidro/plástico
    "GARRAFAS": "FR",
    "VIDRO": "FR",       # "vidro de 500ml" = frasco
    "TB": "TB",
    "TUBO": "TB",
    "TUBOS": "TB",
    "BISNAGA": "TB",     # bisnaga = tubo colapsível
    "BISNAGAS": "TB",
    "RL": "RL",
    "ROLO": "RL",
    "ROLOS": "RL",
    "SC": "SC",
    "SACO": "SC",
    "SACOS": "SC",
    "RM": "RM",          # resma (papel)
    "RESMA": "RM",
    "RESMAS": "RM",
    "FH": "FH",          # folha
    "FL": "FH",
    "FOLHA": "FH",
    "FOLHAS": "FH",
    "KT": "KT",          # kit
    "KIT": "KT",
    "KITS": "KT",
    # ── Outros ───────────────────────────────────────────────────────────────
    "PAR": "PAR",
    "PARES": "PAR",
    "SERVICO": "SV",
    "SERVIÇO": "SV",
    "SV": "SV",
    "MES": "MES",
    "MÊS": "MES",
    "MENSAL": "MES",
    "DIARIA": "DIA",
    "DIÁRIA": "DIA",
    "DIA": "DIA",
    "HORA": "HR",
    "HR": "HR",
    "H": "HR",
}

# ─────────────────────────────────────────────────────────────────────────────
# Sinônimos regionais — Semana 13
# Mapeiam termos regionais para a descrição padronizada nacional
# ─────────────────────────────────────────────────────────────────────────────
SINONIMOS_REGIONAIS: dict[str, str] = {
    # ── Água / Recursos hídricos ─────────────────────────────────────────────
    "ACUDE": "RESERVATORIO",
    "CACIMBA": "POCO",
    "AGUADA": "RESERVATORIO",
    "CISTERNAS": "CISTERNA",
    "TANQUE DE PEDRA": "RESERVATORIO",
    "BARRAGEM": "RESERVATORIO",
    # ── Combustíveis / Região Norte e Nordeste ───────────────────────────────
    "OLEO DIESEL S10": "DIESEL S10",
    "GASOLINA TIPO C": "GASOLINA COMUM",
    "ETANOL HIDRATADO": "ETANOL",
    "ALCOOL ETILICO": "ETANOL",
    # ── Alimentos / Variantes regionais ─────────────────────────────────────
    "CARNE DE SOL": "CARNE BOVINA",
    "CHARQUE": "CARNE BOVINA",
    "CARNE SECA": "CARNE BOVINA",
    "JACUBA": "FARINHA DE MANDIOCA",
    "GOMA DE TAPIOCA": "TAPIOCA",
    "POLVILHO AZEDO": "POLVILHO",
    "POLVILHO DOCE": "POLVILHO",
    "BEIJU": "TAPIOCA",
    "PAÇOCA DE PILAO": "AMENDOIM",
    "RAPADURA": "ACUCAR",
    "MELADO": "ACUCAR",
    "FARINHA DE MILHO": "FUBA",
    "ANGU": "FUBA",
    "CUSCUZ": "FUBA",
    # ── Limpeza / Variantes regionais ───────────────────────────────────────
    "AGUA RAS": "SOLVENTE",
    "QUEROSENE": "COMBUSTIVEL",
    "VASSOURA DE PALHA": "VASSOURA",
    "VASSOURA DE PIAÇAVA": "VASSOURA",
    "RODO DUPLO": "RODO",
    "ESCOVAO": "VASSOURA",
    # ── EPI / Segurança / Trabalho rural ────────────────────────────────────
    "BOTA DE BORRACHA": "BOTA DE SEGURANCA",
    "CHAPEU DE PALHA": "CHAPEU DE PROTECAO",
    "MACACÃO": "MACACAO",
    "MACACAO DE TRABALHO": "MACACAO",
    "AVENTAL DE RASPA": "AVENTAL",
    "PROTETOR AURICULAR": "PROTETOR AURICULAR",
    # ── Construção / Materiais regionais ────────────────────────────────────
    "ADOBE": "TIJOLO",
    "TELHA COLONIAL": "TELHA",
    "TELHA DE BARRO": "TELHA",
    "PEDRA MARROADA": "BRITA",
    "PEDRA BRITADA": "BRITA",
    "CACO DE TIJOLO": "MATERIAL DE CONSTRUCAO",
    "CAL HIDRATADA": "CAL",
    "REBOCO PAULISTA": "REBOCO",
    # ── Serviços ─────────────────────────────────────────────────────────────
    "ROÇAGEM": "LIMPEZA DE TERRENO",
    "ROCAGEM": "LIMPEZA DE TERRENO",
    "CAPINA": "LIMPEZA DE TERRENO",
    "LIMPEZA DE BOCAS DE LOBO": "SERVICO DE LIMPEZA",
    "DESJEJUM": "CAFE DA MANHA",
    "RANCHO": "ALIMENTACAO",
    "REFEICAO": "ALIMENTACAO",
    "MARMITA": "ALIMENTACAO",
    # ── Informática / Variantes ──────────────────────────────────────────────
    "CARTUCHO DE TINTA ORIGINAL": "CARTUCHO DE TINTA",
    "TONER COMPATIVEL": "TONER",
    "TONER REMANUFATURADO": "TONER",
    "IMPRESSORA MATRICIAL": "IMPRESSORA",
    "IMPRESSORA LASER": "IMPRESSORA",
    # ── Papelaria ────────────────────────────────────────────────────────────
    "PAPEL A4 75GR": "PAPEL A4",
    "PAPEL A4 75G": "PAPEL A4",
    "PAPEL A4 90GR": "PAPEL A4",
    "PAPEL SULFITE A4": "PAPEL A4",
    "PAPEL COPIA": "PAPEL A4",
    # ── Saúde / Farmácia ─────────────────────────────────────────────────────
    "SORO FISIOLOGICO": "SOLUCAO FISIOLOGICA",
    "SF 0,9%": "SOLUCAO FISIOLOGICA",
    "DIPIRONA SODICA": "DIPIRONA",
    "PARACETAMOL 500MG": "PARACETAMOL",
    "AMOXICILINA 500MG": "AMOXICILINA",
    "ALGODAO HIDROFILO": "ALGODAO",
    "ATADURA CREPE": "ATADURA",
    "ESPARADRAPO": "FITA ADESIVA HOSPITALAR",
}

# Mapa de sinônimos por UF (regionalismos mais específicos)
SINONIMOS_POR_UF: dict[str, dict[str, str]] = {
    "BA": {
        "ABARA": "CUZCUZ DE FEIJAO",
        "VATAPÁ": "VATAPA",
        "ACARAJE": "BOLINHO DE FEIJAO",
    },
    "PE": {
        "SURURU": "MEXILHAO",
        "MOCOTO": "JOELHO BOVINO",
    },
    "CE": {
        "CUMBU": "RAPADURA",
        "PAÇOCA": "AMENDOIM TORRADO",
    },
    "PA": {
        "AÇAI": "ACAI",
        "TUCUMÃ": "TUCUMA",
        "PUPUNHA": "FRUTO PUPUNHA",
    },
    "AM": {
        "CASTANHA DO PARA": "CASTANHA DO BRASIL",
        "TUCUMÃ": "TUCUMA",
        "PIRARUCU": "PEIXE PIRARUCU",
    },
    "RS": {
        "CHIMIA": "GELEIA",
        "CUCAS": "BOLO COLONIAL",
        "NATA": "CREME DE LEITE",
    },
    "SC": {
        "CUCA": "BOLO COLONIAL",
        "SALAME COLONIAL": "SALAME",
    },
    "MG": {
        "QUITANDA": "PRODUTOS DE PADARIA",
        "PA DE QUEIJO": "PAO DE QUEIJO",
    },
    "GO": {
        "EMPADAO GOIANO": "EMPADAO",
        "ARAGUAIA": "PEIXE ARAGUAIA",
    },
    "MT": {
        "PACU": "PEIXE PACU",
        "PINTADO": "PEIXE PINTADO",
    },
}


# Padrões compilados com word boundary para evitar substituições dentro de outras palavras.
# Ex: "CAL" como sinônimo não pode substituir "CAL" dentro de "CALCÁRIO".
# Compilados uma vez em nível de módulo para eficiência.
_SINONIMOS_REGIONAIS_COMPILED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(_WB + re.escape(sinonimo) + _WB, re.UNICODE), padrao)
    for sinonimo, padrao in SINONIMOS_REGIONAIS.items()
]

_SINONIMOS_POR_UF_COMPILED: dict[str, list[tuple[re.Pattern[str], str]]] = {
    uf: [
        (re.compile(_WB + re.escape(sinonimo.upper()) + _WB, re.UNICODE), padrao.upper())
        for sinonimo, padrao in sinonimos.items()
    ]
    for uf, sinonimos in SINONIMOS_POR_UF.items()
}


def normalizar_sinonimo_regional(
    texto: str, uf: str | None = None
) -> str:
    """Normaliza sinônimos regionais para termos padronizados.

    Usa word boundary (\b) para evitar substituições parciais dentro de palavras.
    Ex: "CAL HIDRATADA" é normalizado mas "CALCÁRIO" não é afetado.

    Primeiro aplica sinônimos gerais, depois os específicos por UF se disponível.
    """
    if not texto:
        return texto

    resultado = texto.upper().strip()

    # Sinônimos gerais — com word boundary (pré-compilados)
    for pattern, padrao in _SINONIMOS_REGIONAIS_COMPILED:
        resultado = pattern.sub(padrao, resultado)

    # Sinônimos por UF — com word boundary (pré-compilados)
    if uf and uf.upper() in _SINONIMOS_POR_UF_COMPILED:
        for pattern, padrao in _SINONIMOS_POR_UF_COMPILED[uf.upper()]:
            resultado = pattern.sub(padrao, resultado)

    return resultado


# Padrões de ruído comuns em descrições de licitação
_RUIDO_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bCONFORME\s+EDITAL\b", re.IGNORECASE),
    re.compile(r"\bDE\s+ACORDO\s+COM\s+O\s+EDITAL\b", re.IGNORECASE),
    re.compile(r"\bDEMAIS\s+ESPECIFICA[ÇC][OÕ]ES\b", re.IGNORECASE),
    re.compile(r"\bCONFORME\s+TERMO\s+DE\s+REFER[EÊ]NCIA\b", re.IGNORECASE),
    re.compile(r"\bVIDE\s+EDITAL\b", re.IGNORECASE),
    re.compile(r"\bCONFORME\s+DESCRI[ÇC][AÃ]O\s+COMPLETA\b", re.IGNORECASE),
    re.compile(r"\bCONFORME\s+ESPECIFICA[ÇC][OÕ]ES\b", re.IGNORECASE),
    re.compile(r"\bVER\s+ANEXO\b", re.IGNORECASE),
    re.compile(r"\bOBS\.?:?\s*$", re.IGNORECASE),
]

# Padrões de ruído adicionais (Semana 4)
_RUIDO_PATTERNS_EXTRA: list[re.Pattern[str]] = [
    re.compile(r"\bCONFORME\s+ESPECIFICA[ÇC][OÕ]ES\s+T[EÉ]CNICAS\b", re.IGNORECASE | re.UNICODE),
    re.compile(r"\bDE\s+ACORDO\s+COM\s+EDITAL\b", re.IGNORECASE | re.UNICODE),
    re.compile(r"\bCONFORME\s+MEMORIAL\s+DESCRITIVO\b", re.IGNORECASE | re.UNICODE),
    re.compile(r"\bOU\s+SIMILAR\b", re.IGNORECASE | re.UNICODE),
    re.compile(r"\bOU\s+EQUIVALENTE\b", re.IGNORECASE | re.UNICODE),
]

# Padrões para normalização de números/medidas
_NUMERO_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 1.000 ml → 1000 ML, 500gr → 500 G, etc.
    (re.compile(r"(\d)\.(\d{3})\s*(ML|G|KG|L|M|CM)\b", re.IGNORECASE), r"\1\2 \3"),
    # 500gr → 500 G
    (re.compile(r"(\d+)\s*GR\b", re.IGNORECASE), r"\1 G"),
    # 500ml → 500 ML
    (re.compile(r"(\d+)\s*ML\b", re.IGNORECASE), r"\1 ML"),
    # 500g → 500 G (mas não 500gr, já tratado acima)
    (re.compile(r"(\d+)\s*G\b", re.IGNORECASE), r"\1 G"),
    # 1l, 2l → 1 L, 2 L
    (re.compile(r"(\d+)\s*L\b", re.IGNORECASE), r"\1 L"),
    # 500kg → 500 KG
    (re.compile(r"(\d+)\s*KG\b", re.IGNORECASE), r"\1 KG"),
    # 10cm → 10 CM
    (re.compile(r"(\d+)\s*CM\b", re.IGNORECASE), r"\1 CM"),
    # 5m → 5 M (cuidado: não casar "5mm")
    (re.compile(r"(\d+)\s*M\b(?!M|L|2|3|²|³)", re.IGNORECASE), r"\1 M"),
]

# Padrões para extração de atributos
_MARCA_RE = re.compile(r"\bMARCA\s*:?\s*([A-Z0-9][A-Z0-9 ]{1,30})\b", re.IGNORECASE | re.UNICODE)
_MODELO_RE = re.compile(r"\bMODELO\s*:?\s*([A-Z0-9][A-Z0-9\- ]{1,30})\b", re.IGNORECASE | re.UNICODE)
_CAPACIDADE_RE = re.compile(r"(\d+[\.,]?\d*)\s*(ML|L|G|KG|M|CM|M2|M3|TON)\b", re.IGNORECASE | re.UNICODE)
_VOLUME_RE = re.compile(r"(\d+[\.,]?\d*)\s*(ML|L|LITRO|LITROS)\b", re.IGNORECASE | re.UNICODE)
_DIMENSAO_RE = re.compile(r"(\d+[\.,]?\d*)\s*[Xx×]\s*(\d+[\.,]?\d*)\s*(?:[Xx×]\s*(\d+[\.,]?\d*))?\s*(CM|M|MM)?", re.IGNORECASE | re.UNICODE)
_MATERIAL_RE = re.compile(r"\b(ACO|AÇO|INOX|PLASTICO|PLÁSTICO|MADEIRA|MDF|VIDRO|ALUMINIO|ALUMÍNIO|PVC|NYLON|POLIETILENO|BORRACHA|LATEX|LÁTEX|NITRILA|COURO|TECIDO|ALGODAO|ALGODÃO)\b", re.IGNORECASE | re.UNICODE)
_UNIDADE_EMBALAGEM_RE = re.compile(r"\b(CAIXA|CX|PACOTE|PCT|FARDO|FD|ROLO|RL|FRASCO|FR|GALAO|GALÃO|GL|SACO|SC)\s+COM\s+(\d+)", re.IGNORECASE | re.UNICODE)
_QUANTIDADE_EMBALAGEM_RE = re.compile(r"\b(\d+)\s*(UN|UND|UNIDADE|UNIDADES|FOLHAS?|FL)\s*/\s*(CAIXA|CX|PACOTE|PCT|FARDO|FD|ROLO|RL)", re.IGNORECASE | re.UNICODE)


def normalizar_data(texto: str) -> date | None:
    """Converte texto de data para date ISO 8601.

    Suporta formatos: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD.MM.YYYY.
    Retorna None se não conseguir interpretar.
    """
    texto = texto.strip()
    if not texto:
        return None

    # YYYY-MM-DD
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", texto)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    # DD/MM/YYYY ou DD-MM-YYYY ou DD.MM.YYYY
    match = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$", texto)
    if match:
        return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))

    return None


def normalizar_cnpj(texto: str) -> str | None:
    """Normaliza CNPJ para formato XX.XXX.XXX/XXXX-XX.

    Aceita com ou sem pontuação. Retorna None se o número de dígitos não for 14.
    """
    apenas_digitos = re.sub(r"\D", "", texto.strip())
    if len(apenas_digitos) != 14:
        return None
    return f"{apenas_digitos[:2]}.{apenas_digitos[2:5]}.{apenas_digitos[5:8]}/{apenas_digitos[8:12]}-{apenas_digitos[12:14]}"


def normalizar_unidade(texto: str) -> str | None:
    """Normaliza texto de unidade para forma canônica (UN, KG, L, M, etc.).

    Retorna None se não encontrar correspondência.
    """
    if not texto:
        return None
    chave = unicodedata.normalize("NFKC", texto.strip().upper())
    # Remove pontos finais
    chave = chave.rstrip(".")
    return _UNIDADE_MAP.get(chave)


def limpar_descricao(texto: str) -> str:
    """Limpa descrição de item para normalização.

    Aplica: uppercase, normalização Unicode NFKC, remoção de ruído,
    remoção de pontuação inútil, compactação de espaços.
    """
    if not texto:
        return ""
    # Normaliza Unicode
    resultado = unicodedata.normalize("NFKC", texto)
    # Uppercase
    resultado = resultado.upper()
    # Remove padrões de ruído (lista original + expandida)
    for pattern in _RUIDO_PATTERNS:
        resultado = pattern.sub("", resultado)
    for pattern in _RUIDO_PATTERNS_EXTRA:
        resultado = pattern.sub("", resultado)
    # Remove pontuação inútil (mantém hífens e barras que podem ser relevantes)
    resultado = re.sub(r"[;:!?\"\'`´*#@&%$]+", " ", resultado)
    # Remove parênteses vazios
    resultado = re.sub(r"\(\s*\)", "", resultado)
    # Compacta espaços múltiplos
    resultado = re.sub(r"\s+", " ", resultado)
    return resultado.strip()


def calcular_chave_deduplicacao(
    fonte_tipo: str,
    fonte_ref: str | None,
    item_id: int | None,
    data_ref: date | None,
    preco: float | None,
    qtd: float | None,
) -> str:
    """Calcula hash SHA256 para deduplicação de fontes de preço.

    Concatena os campos e retorna o hexdigest.
    """
    partes = [
        str(fonte_tipo or ""),
        str(fonte_ref or ""),
        str(item_id or ""),
        str(data_ref or ""),
        str(preco or ""),
        str(qtd or ""),
    ]
    payload = "|".join(partes)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Funções expandidas — Semana 4
# ---------------------------------------------------------------------------


def remove_ruido(texto: str) -> str:
    """Remove frases genéricas de edital que não agregam valor à descrição.

    Aplica tanto os padrões originais quanto os novos padrões expandidos.
    """
    if not texto:
        return ""
    resultado = texto
    for pattern in _RUIDO_PATTERNS:
        resultado = pattern.sub("", resultado)
    for pattern in _RUIDO_PATTERNS_EXTRA:
        resultado = pattern.sub("", resultado)
    resultado = re.sub(r"\s+", " ", resultado)
    return resultado.strip()


def normalizar_numeros(texto: str) -> str:
    """Padroniza medidas numéricas no texto.

    Exemplos: 1.000 ml → 1000 ML, 500gr → 500 G, 2l → 2 L.
    Resultado sempre em uppercase para a unidade.
    """
    if not texto:
        return ""
    resultado = texto.upper()
    for pattern, repl in _NUMERO_PATTERNS:
        resultado = pattern.sub(repl, resultado)
    # Garante unidades em uppercase
    resultado = re.sub(r"\s+", " ", resultado)
    return resultado.strip()


def extrair_atributos(texto: str) -> dict[str, Any]:
    """Extrai atributos estruturados de uma descrição de item.

    Retorna dict com chaves opcionais: marca, modelo, capacidade,
    volume, dimensao, material, unidade_embalagem, quantidade_embalagem.
    """
    atributos: dict[str, Any] = {}
    if not texto:
        return atributos

    texto_upper = texto.upper()

    match = _MARCA_RE.search(texto_upper)
    if match:
        atributos["marca"] = match.group(1).strip()

    match = _MODELO_RE.search(texto_upper)
    if match:
        atributos["modelo"] = match.group(1).strip()

    match = _VOLUME_RE.search(texto_upper)
    if match:
        atributos["volume"] = f"{match.group(1)} {match.group(2).upper()}"

    if "volume" not in atributos:
        match = _CAPACIDADE_RE.search(texto_upper)
        if match:
            atributos["capacidade"] = f"{match.group(1)} {match.group(2).upper()}"

    match = _DIMENSAO_RE.search(texto_upper)
    if match:
        partes = [match.group(1), match.group(2)]
        if match.group(3):
            partes.append(match.group(3))
        unidade = match.group(4) or ""
        atributos["dimensao"] = "x".join(partes) + (f" {unidade.upper()}" if unidade else "")

    match = _MATERIAL_RE.search(texto_upper)
    if match:
        atributos["material"] = match.group(1).upper()

    match = _UNIDADE_EMBALAGEM_RE.search(texto_upper)
    if match:
        atributos["unidade_embalagem"] = match.group(1).upper()
        atributos["quantidade_embalagem"] = int(match.group(2))

    if "unidade_embalagem" not in atributos:
        match = _QUANTIDADE_EMBALAGEM_RE.search(texto_upper)
        if match:
            atributos["quantidade_embalagem"] = int(match.group(1))
            atributos["unidade_embalagem"] = match.group(3).upper()

    return atributos


def normalizar_descricao_completa(texto: str) -> dict[str, Any]:
    """Pipeline completo de normalização de descrição.

    Integra limpeza, normalização de números, extração de atributos
    e tokenização.

    Retorna dict com: descricao_limpa, atributos, tokens.
    """
    if not texto:
        return {"descricao_limpa": "", "atributos": {}, "tokens": []}

    # Passo 1: limpeza textual completa
    limpo = limpar_descricao(texto)

    # Passo 2: normalizar números/medidas
    limpo = normalizar_numeros(limpo)

    # Passo 3: extrair atributos do texto original (mais rico)
    atributos = extrair_atributos(texto)

    # Passo 4: tokenizar
    tokens = [t for t in limpo.split() if len(t) > 1]

    return {
        "descricao_limpa": limpo,
        "atributos": atributos,
        "tokens": tokens,
    }
