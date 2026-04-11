"""Portão de qualidade para ingestão de itens do PNCP.

Cada item passa por três camadas de validação antes de ser persistido:

  REJEITADO  — dados inválidos que nunca devem entrar no banco
               (preço negativo, CNPJ com dígito verificador errado,
                descrição vazia, data futura, quantidade absurda)

  QUARENTENA — dados suspeitos que precisam de revisão humana
               (unidade ausente, preço redondo, preço improvável para
                a categoria, descrição copiada do objeto da contratação)

  ACEITO     — dados válidos, possivelmente com alertas de baixa confiança
               (preço estimado, categoria não identificada)

Uso:
    from app.services.validacao_ingestao import validar_item, StatusValidacao

    resultado = validar_item(
        descricao="Papel Sulfite A4 75g",
        preco_unitario=25.90,
        quantidade=10,
        unidade="RM",
        data_referencia="2025-03-01",
    )
    if resultado.status == StatusValidacao.REJEITADO:
        ...
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


# ─────────────────────────────────────────────────────────
# Enums e dataclasses
# ─────────────────────────────────────────────────────────

class StatusValidacao(str, Enum):
    ACEITO = "aceito"
    QUARENTENA = "quarentena"
    REJEITADO = "rejeitado"


@dataclass
class ResultadoValidacao:
    """Resultado da validação de um item de ingestão."""

    status: StatusValidacao
    motivos_rejeicao: list[str] = field(default_factory=list)
    motivos_quarentena: list[str] = field(default_factory=list)
    alertas: list[str] = field(default_factory=list)

    @property
    def rejeitado(self) -> bool:
        return self.status == StatusValidacao.REJEITADO

    @property
    def em_quarentena(self) -> bool:
        return self.status == StatusValidacao.QUARENTENA

    @property
    def aceito(self) -> bool:
        return self.status == StatusValidacao.ACEITO

    def motivo_principal(self) -> str:
        """Retorna o primeiro motivo de rejeição ou quarentena."""
        if self.motivos_rejeicao:
            return self.motivos_rejeicao[0]
        if self.motivos_quarentena:
            return self.motivos_quarentena[0]
        return ""

    def todos_os_motivos(self) -> list[str]:
        """Lista plana de todos os motivos (rejeição + quarentena + alertas)."""
        return self.motivos_rejeicao + self.motivos_quarentena + self.alertas


# ─────────────────────────────────────────────────────────
# Constantes de validação
# ─────────────────────────────────────────────────────────

# Preço máximo absoluto aceito para qualquer item unitário (R$)
PRECO_MAXIMO_ABSOLUTO: float = 1_000_000.0

# Preço mínimo: abaixo disso provavelmente é erro de campo (ex: quantidade no lugar do preço)
PRECO_MINIMO_ABSOLUTO: float = 0.001

# Data mínima aceitável — PNCP tem dados retroativos a 2021, mas aceitamos até 2018
# para cobrir contratos plurianuais com referências mais antigas
DATA_MINIMA: date = date(2018, 1, 1)

# Quantidade máxima aceita por item em qualquer unidade
QUANTIDADE_MAXIMA: float = 10_000_000.0

# Faixas de preço plausíveis por categoria (R$ por unidade padrão)
# Baseadas em medianas históricas do PNCP — revisar anualmente
FAIXAS_PLAUSÍVEIS: dict[str, tuple[float, float]] = {
    # Combustíveis (R$/litro)
    "Gasolina Comum":        (3.50,   10.00),
    "Diesel S10":            (3.50,   10.00),
    "Etanol":                (2.50,    8.00),
    # Material de escritório
    "Papel A4":              (15.00,  90.00),   # R$/resma 500 folhas
    # Alimentos básicos (R$/kg ou R$/litro)
    "Arroz":                 (2.00,   35.00),
    "Feijão":                (3.00,   50.00),
    "Açúcar":                (2.00,   30.00),
    "Óleo de Soja":          (3.00,   35.00),
    "Leite":                 (3.00,   30.00),
    # Limpeza (R$/unidade)
    "Detergente":            (1.00,   50.00),
    "Álcool Gel":            (2.00,   80.00),
    "Desinfetante":          (2.00,   60.00),
    # TI (R$/unidade)
    "Toner para Impressora": (20.00, 1_800.00),
    "Cartucho de Tinta":     (10.00,   500.00),
    # Serviços (R$/mês — preço total mensal)
    "Serviço de Limpeza":    (500.00, 100_000.00),
}


# ─────────────────────────────────────────────────────────
# Funções auxiliares
# ─────────────────────────────────────────────────────────

def validar_cnpj(cnpj: str | None) -> bool:
    """Valida CNPJ com verificação dos dígitos verificadores.

    Implementa o algoritmo oficial da Receita Federal (módulo 11).
    Aceita CNPJ formatado (XX.XXX.XXX/XXXX-DD) ou apenas dígitos.
    """
    if not cnpj:
        return False

    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        return False

    # CNPJs com todos os dígitos iguais são inválidos (ex: 00000000000000)
    if len(set(digits)) == 1:
        return False

    # Primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(d) * p for d, p in zip(digits[:12], pesos1))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if int(digits[12]) != d1:
        return False

    # Segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(d) * p for d, p in zip(digits[:13], pesos2))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    return int(digits[13]) == d2


def eh_preco_redondo_suspeito(preco: float) -> bool:
    """Retorna True se o preço parece uma estimativa grosseira.

    Critério: múltiplo de 100 sem frações de centavo e valor >= R$100.
    Exemplos suspeitos:  100.00, 500.00, 1000.00, 2500.00
    Exemplos normais:     99.90,  123.45,   50.00,   10.50
    """
    if preco <= 0:
        return False
    # Converte para centavos inteiros e verifica se é múltiplo de 10000 (= R$100 sem centavos)
    centavos = round(preco * 100)
    return centavos % 10000 == 0 and preco >= 100.0


def preco_plausivel_para_categoria(
    preco: float,
    categoria_nome: str | None,
) -> bool | None:
    """Verifica se o preço está dentro da faixa plausível para a categoria.

    Returns:
        True  — dentro da faixa
        False — fora da faixa (improvável)
        None  — categoria desconhecida, não é possível avaliar
    """
    if not categoria_nome:
        return None

    faixa = FAIXAS_PLAUSÍVEIS.get(categoria_nome)
    if faixa is None:
        return None

    minimo, maximo = faixa
    return minimo <= preco <= maximo


def _descricao_copiada_do_objeto(
    descricao: str | None,
    objeto_contratacao: str | None,
) -> bool:
    """Detecta se a descrição do item é igual (ou idêntica) ao objeto da contratação.

    Isso indica que o pregoeiro preencheu o campo errado na plataforma.
    Só verifica quando ambas as strings têm pelo menos 20 caracteres
    (evita falsos positivos com descrições genéricas curtas).
    """
    if not descricao or not objeto_contratacao:
        return False

    d = descricao.strip().lower()
    o = objeto_contratacao.strip().lower()

    if len(d) < 20 or len(o) < 20:
        return False

    # Idênticos
    if d == o:
        return True

    # Descrição está contida integralmente no objeto (substring)
    if d in o:
        return True

    return False


def _parsear_data(valor: str | date | None) -> tuple[date | None, str | None]:
    """Tenta parsear data. Retorna (date, None) ou (None, motivo_erro)."""
    if valor is None:
        return None, None
    if isinstance(valor, date):
        return valor, None
    try:
        return datetime.strptime(str(valor)[:10], "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"data_invalida:{valor!r}"


# ─────────────────────────────────────────────────────────
# Portão principal
# ─────────────────────────────────────────────────────────

def validar_item(
    descricao: str | None,
    preco_unitario: float | None,
    quantidade: float | None,
    unidade: str | None,
    data_referencia: str | date | None,
    cnpj: str | None = None,
    objeto_contratacao: str | None = None,
    categoria_nome: str | None = None,
    tipo_preco: str = "estimado",
) -> ResultadoValidacao:
    """Valida um item de ingestão e retorna status com motivos detalhados.

    Ordem de avaliação:
      1. Rejeições (inválido) → retorna imediatamente se houver
      2. Quarentenas (suspeito) → retorna imediatamente se houver
      3. Aceito com alertas opcionais

    Args:
        descricao:           Descrição do item (campo obrigatório)
        preco_unitario:      Preço por unidade em R$ (campo obrigatório)
        quantidade:          Quantidade licitada (opcional, mas validada se presente)
        unidade:             Unidade de medida (ausência gera quarentena)
        data_referencia:     Data da publicação/homologação (YYYY-MM-DD ou date)
        cnpj:                CNPJ do órgão licitante (validado se fornecido)
        objeto_contratacao:  Objeto geral da contratação (detecta cópia indevida)
        categoria_nome:      Nome da categoria classificada (para plausibilidade)
        tipo_preco:          "estimado" ou "homologado"

    Returns:
        ResultadoValidacao com status REJEITADO, QUARENTENA ou ACEITO.
    """
    motivos_rejeicao: list[str] = []
    motivos_quarentena: list[str] = []
    alertas: list[str] = []

    # ─── Camada 1: REJEIÇÕES ──────────────────────────────────────────

    # Descrição
    desc_limpa = (descricao or "").strip()
    if not desc_limpa:
        motivos_rejeicao.append("descricao_vazia")
    elif len(desc_limpa) < 3:
        motivos_rejeicao.append("descricao_muito_curta")

    # Preço
    if preco_unitario is None:
        motivos_rejeicao.append("preco_ausente")
    elif preco_unitario <= 0:
        motivos_rejeicao.append(f"preco_invalido:{preco_unitario:.4f}")
    elif preco_unitario < PRECO_MINIMO_ABSOLUTO:
        motivos_rejeicao.append(f"preco_abaixo_do_minimo:{preco_unitario:.6f}")
    elif preco_unitario > PRECO_MAXIMO_ABSOLUTO:
        motivos_rejeicao.append(f"preco_absurdo:{preco_unitario:.2f}")

    # Quantidade
    if quantidade is not None:
        if quantidade <= 0:
            motivos_rejeicao.append(f"quantidade_invalida:{quantidade}")
        elif quantidade > QUANTIDADE_MAXIMA:
            motivos_rejeicao.append(f"quantidade_absurda:{quantidade:.0f}")

    # Data
    data_parsed, erro_data = _parsear_data(data_referencia)
    if erro_data:
        motivos_rejeicao.append(erro_data)
    elif data_parsed is not None:
        hoje = date.today()
        if data_parsed > hoje:
            motivos_rejeicao.append(f"data_futura:{data_parsed}")
        elif data_parsed < DATA_MINIMA:
            motivos_rejeicao.append(f"data_muito_antiga:{data_parsed}")

    # CNPJ (somente se fornecido — ausência não é motivo de rejeição)
    if cnpj and not validar_cnpj(cnpj):
        motivos_rejeicao.append(f"cnpj_invalido:{cnpj[:18]}")

    if motivos_rejeicao:
        return ResultadoValidacao(
            status=StatusValidacao.REJEITADO,
            motivos_rejeicao=motivos_rejeicao,
        )

    # ─── Camada 2: QUARENTENAS ────────────────────────────────────────

    # Unidade ausente
    if not (unidade or "").strip():
        motivos_quarentena.append("unidade_ausente")

    # Preço redondo suspeito
    if preco_unitario and eh_preco_redondo_suspeito(preco_unitario):
        motivos_quarentena.append(f"preco_redondo_suspeito:{preco_unitario:.2f}")

    # Descrição copiada do objeto da contratação
    if _descricao_copiada_do_objeto(desc_limpa, objeto_contratacao):
        motivos_quarentena.append("descricao_igual_ao_objeto_contratacao")

    # Preço improvável para a categoria
    if preco_unitario and categoria_nome:
        plausivel = preco_plausivel_para_categoria(preco_unitario, categoria_nome)
        if plausivel is False:
            faixa = FAIXAS_PLAUSÍVEIS[categoria_nome]
            motivos_quarentena.append(
                f"preco_improvavel:{categoria_nome}:"
                f"R${preco_unitario:.2f}_fora_de_"
                f"R${faixa[0]:.2f}-R${faixa[1]:.2f}"
            )

    if motivos_quarentena:
        return ResultadoValidacao(
            status=StatusValidacao.QUARENTENA,
            motivos_quarentena=motivos_quarentena,
        )

    # ─── Camada 3: ACEITO (com alertas informativos) ──────────────────

    if tipo_preco == "estimado":
        alertas.append("preco_estimado_nao_homologado")

    if not categoria_nome:
        alertas.append("categoria_nao_identificada")

    return ResultadoValidacao(
        status=StatusValidacao.ACEITO,
        alertas=alertas,
    )
