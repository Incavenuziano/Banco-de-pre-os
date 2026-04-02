"""Classificador de itens por categoria usando regras regex.

Cobre as top 10 categorias de compras municipais com regras
baseadas em padrões textuais frequentes em descrições de licitação.
"""

import re
import unicodedata
from typing import Any


def _strip_accents(texto: str) -> str:
    """Remove acentos de um texto, mantendo letras base."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class ClassificadorRegex:
    """Classifica descrições de itens em categorias usando regex.

    Cada regra é uma tupla (padrão, categoria_nome, match_exato).
    Score: 1.0 se match exato (termo principal), 0.8 se match parcial.
    """

    # (regex compilado, nome_categoria, é_match_exato)
    _REGRAS: list[tuple[re.Pattern[str], str, bool]] = [
        # --- Papel A4 / Cópia ---
        (re.compile(r"\bPAPEL\s+(SULFITE\s+)?A4\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+(SULFITE\s+)?OFICIO\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+(PARA\s+)?COPIA\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+SULFITE\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+REPROGRAFIA\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+XEROX\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\s+IMPRESSAO\b", re.IGNORECASE | re.UNICODE), "Papel A4", True),
        (re.compile(r"\bPAPEL\b.*\b(75\s*G|75\s*GR|90\s*G|90\s*GR)\b", re.IGNORECASE | re.UNICODE), "Papel A4", False),

        # --- Limpeza / Higiene ---
        (re.compile(r"\bDETERGENTE\b", re.IGNORECASE | re.UNICODE), "Detergente", True),
        (re.compile(r"\bMULTIUSO\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bLIMPADOR\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bLIMPA\s+VIDRO\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bDESENTUPIDOR\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bDESENGORDURANTE\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bSABAO\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bSABONETE\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bALCOOL\s*GEL\b", re.IGNORECASE | re.UNICODE), "Álcool Gel", True),
        (re.compile(r"\bDESINFETANTE\b", re.IGNORECASE | re.UNICODE), "Desinfetante", True),
        (re.compile(r"\bHIPOCLORITO\b", re.IGNORECASE | re.UNICODE), "Desinfetante", False),
        (re.compile(r"\bAGUA\s+SANITARIA\b", re.IGNORECASE | re.UNICODE), "Desinfetante", False),
        (re.compile(r"\bVASSOURA\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bRODO\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bBALDE\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bPANO\s*(DE\s+)?CHAO\b", re.IGNORECASE | re.UNICODE), "Detergente", False),
        (re.compile(r"\bESPONJA\b", re.IGNORECASE | re.UNICODE), "Detergente", False),

        # --- Combustíveis ---
        (re.compile(r"\bGASOLINA\s+ADITIVADA\b", re.IGNORECASE | re.UNICODE), "Gasolina Comum", True),
        (re.compile(r"\bGASOLINA\s+COMUM\b", re.IGNORECASE | re.UNICODE), "Gasolina Comum", True),
        (re.compile(r"\bGASOLINA\b", re.IGNORECASE | re.UNICODE), "Gasolina Comum", True),
        (re.compile(r"\bETANOL\b", re.IGNORECASE | re.UNICODE), "Etanol", True),
        (re.compile(r"\bOLEO\s+DIESEL\b", re.IGNORECASE | re.UNICODE), "Diesel S10", True),
        (re.compile(r"\bDIESEL\s*S[\s-]*10\b", re.IGNORECASE | re.UNICODE), "Diesel S10", True),
        (re.compile(r"\bDIESEL\s*S[\s-]*500\b", re.IGNORECASE | re.UNICODE), "Diesel S10", False),
        (re.compile(r"\bARLA\b", re.IGNORECASE | re.UNICODE), "Diesel S10", False),
        (re.compile(r"\bGNV\b", re.IGNORECASE | re.UNICODE), "Etanol", False),

        # --- Toner / Cartucho ---
        (re.compile(r"\bTONER\s+COMPATIVEL\b", re.IGNORECASE | re.UNICODE), "Toner para Impressora", True),
        (re.compile(r"\bTONER\s+ORIGINAL\b", re.IGNORECASE | re.UNICODE), "Toner para Impressora", True),
        (re.compile(r"\bTONER\b", re.IGNORECASE | re.UNICODE), "Toner para Impressora", True),
        (re.compile(r"\bCARTUCHO\s*(DE\s+)?TINTA\b", re.IGNORECASE | re.UNICODE), "Cartucho de Tinta", True),
        (re.compile(r"\bCARTUCHO\s+HP\b", re.IGNORECASE | re.UNICODE), "Cartucho de Tinta", False),
        (re.compile(r"\bCARTUCHO\s+EPSON\b", re.IGNORECASE | re.UNICODE), "Cartucho de Tinta", False),
        (re.compile(r"\bCARTUCHO\s+CANON\b", re.IGNORECASE | re.UNICODE), "Cartucho de Tinta", False),
        (re.compile(r"\bRIBBON\b", re.IGNORECASE | re.UNICODE), "Toner para Impressora", False),
        (re.compile(r"\bREFIL\s*(DE\s+)?TINTA\b", re.IGNORECASE | re.UNICODE), "Cartucho de Tinta", False),

        # --- Alimentos ---
        (re.compile(r"\bARROZ\s*(TIPO)?\b", re.IGNORECASE | re.UNICODE), "Arroz", True),
        (re.compile(r"\bFEIJAO\b", re.IGNORECASE | re.UNICODE), "Feijão", True),
        (re.compile(r"\bACUCAR\b", re.IGNORECASE | re.UNICODE), "Açúcar", True),
        (re.compile(r"\bSAL\s+REFINADO\b", re.IGNORECASE | re.UNICODE), "Açúcar", False),
        (re.compile(r"\bOLEO\s*(DE\s+)?SOJA\b", re.IGNORECASE | re.UNICODE), "Óleo de Soja", True),
        (re.compile(r"\bLEITE\s*(INTEGRAL)?\b", re.IGNORECASE | re.UNICODE), "Leite", True),
        (re.compile(r"\bFUBA\b", re.IGNORECASE | re.UNICODE), "Arroz", False),
        (re.compile(r"\bMACAR[RR]AO\b", re.IGNORECASE | re.UNICODE), "Arroz", False),
        (re.compile(r"\bFARINHA\s*(DE\s+)?TRIGO\b", re.IGNORECASE | re.UNICODE), "Arroz", False),

        # --- Serviços de limpeza ---
        (re.compile(r"\bSERVICO\s*(DE\s+)?LIMPEZA\b", re.IGNORECASE | re.UNICODE), "Serviço de Limpeza", True),
        (re.compile(r"\bLIMPEZA\s+PREDIAL\b", re.IGNORECASE | re.UNICODE), "Serviço de Limpeza", True),
        (re.compile(r"\bCONSERVACAO\s*(E\s+)?LIMPEZA\b", re.IGNORECASE | re.UNICODE), "Serviço de Limpeza", False),
        (re.compile(r"\bASSEIO\s*(E\s+)?CONSERVACAO\b", re.IGNORECASE | re.UNICODE), "Serviço de Limpeza", False),

        # --- Pneus ---
        (re.compile(r"\bPNEU\s*\d{3}\s*/\s*\d{2}\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", False),  # usa categoria existente mais próxima — pneu não existe como categoria
        (re.compile(r"\bPNEU\s*(ARO|R)\s*\d+\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", False),
        (re.compile(r"\bCAMARA\s*(DE\s+)?AR\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", False),

        # --- EPI / Uniforme ---
        (re.compile(r"\bCAPACETE\b", re.IGNORECASE | re.UNICODE), "Capacete de Segurança", True),
        (re.compile(r"\bBOTA\s*(DE\s+)?SEGURANCA\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", True),
        (re.compile(r"\bLUVA\s*(DE\s+)?NITRILA\b", re.IGNORECASE | re.UNICODE), "Luva de Procedimento", True),
        (re.compile(r"\bCOLETE\s*(DE\s+)?SINALIZAD?OR\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", False),
        (re.compile(r"\bOCULOS\s*(DE\s+)?PROTECAO\b", re.IGNORECASE | re.UNICODE), "Bota de Segurança", False),
        (re.compile(r"\bUNIFORME\b", re.IGNORECASE | re.UNICODE), "Uniforme Escolar", True),
        (re.compile(r"\bCAMISA\s+SOCIAL\b", re.IGNORECASE | re.UNICODE), "Uniforme Escolar", False),

        # --- Mobiliário ---
        (re.compile(r"\bCADEIRA\s*(DE\s+|PARA\s+)?ESCRITORIO\b", re.IGNORECASE | re.UNICODE), "Cadeira de Escritório", True),
        (re.compile(r"\bMESA\s*(DE\s+|PARA\s+)?ESCRITORIO\b", re.IGNORECASE | re.UNICODE), "Mesa de Escritório", True),
        (re.compile(r"\bARMARIO\s*(DE\s+|EM\s+)?ACO\b", re.IGNORECASE | re.UNICODE), "Armário de Aço", True),
        (re.compile(r"\bESTANTE\s*(DE\s+|EM\s+)?ACO\b", re.IGNORECASE | re.UNICODE), "Estante Metálica", True),
        (re.compile(r"\bARQUIVO\s*(DE\s+|EM\s+)?ACO\b", re.IGNORECASE | re.UNICODE), "Armário de Aço", False),

        # --- Informática ---
        (re.compile(r"\bCOMPUTADOR\b.*\bI[3579]\b", re.IGNORECASE | re.UNICODE), "Computador Desktop", True),
        (re.compile(r"\bNOTEBOOK\b.*\bI[3579]\b", re.IGNORECASE | re.UNICODE), "Notebook", True),
        (re.compile(r"\bMONITOR\b.*\b\d{2}\s*\"?\b", re.IGNORECASE | re.UNICODE), "Monitor", True),
        (re.compile(r"\bTECLADO\b.*\bMOUSE\b", re.IGNORECASE | re.UNICODE), "Computador Desktop", False),
        (re.compile(r"\bNOBREAK\b", re.IGNORECASE | re.UNICODE), "Nobreak/UPS", True),
        (re.compile(r"\bSWITCH\b.*\b\d+\s*PORTA\b", re.IGNORECASE | re.UNICODE), "Switch de Rede", True),
    ]

    def __init__(self, categorias: list[dict[str, Any]] | None = None) -> None:
        """Inicializa o classificador.

        Args:
            categorias: lista de dicts com 'id' e 'nome'. Se fornecido,
                        permite retornar categoria_id no resultado.
        """
        self._cat_map: dict[str, int] = {}
        if categorias:
            for cat in categorias:
                self._cat_map[cat["nome"]] = cat["id"]

    def classificar(self, descricao: str) -> dict[str, Any] | None:
        """Classifica uma descrição de item usando regras regex.

        Retorna dict com categoria_id, categoria_nome, score e metodo,
        ou None se nenhuma regra casar.
        """
        if not descricao:
            return None

        texto = _strip_accents(descricao.upper())

        for pattern, categoria_nome, exato in self._REGRAS:
            if pattern.search(texto):
                return {
                    "categoria_id": self._cat_map.get(categoria_nome),
                    "categoria_nome": categoria_nome,
                    "score": 1.0 if exato else 0.8,
                    "metodo": "regex",
                }

        return None

    def sugerir_correcao(
        self, descricao: str, resultado_atual: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Sugere correção para uma classificação existente.

        Analisa o resultado da classificação e indica se há necessidade
        de revisão manual com base no score de confiança.

        Args:
            descricao: Descrição do item classificado.
            resultado_atual: Resultado da classificação (output de classificar()),
                             ou None se nenhuma categoria foi identificada.

        Returns:
            Dict com sugestao, motivo e confianca_esperada.
        """
        if resultado_atual is None:
            return {
                "sugestao": "revisão manual",
                "motivo": "sem categoria identificada",
                "confianca_esperada": 0.0,
            }

        score = resultado_atual.get("score", 0.0)

        if score < 0.8:
            return {
                "sugestao": "verificar categoria manualmente",
                "motivo": "score baixo",
                "confianca_esperada": score,
            }

        return {
            "sugestao": None,
            "motivo": None,
            "confianca_esperada": score,
        }
