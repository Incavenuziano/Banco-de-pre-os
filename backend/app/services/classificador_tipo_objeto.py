"""Classificador de tipo_objeto para itens de licitação.

Classifica descrições de itens em três categorias:
  - material: bem móvel fungível ou infungível
  - servico:  prestação de serviço continuado ou pontual
  - obra:     construção, reforma ou infraestrutura

Arquitetura em camadas (ordem de precedência):
  1. Override manual — revisor humano define o tipo definitivo
  2. Regras do banco   — regex configuráveis por prioridade (TTL 5 min)
  3. Regras builtin    — fallback quando DB indisponível ou n < threshold

O texto é normalizado (sem acentos, maiúsculas) antes de cada regex,
tornando os padrões independentes de acentuação.
"""

from __future__ import annotations

import logging
import re
import time
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Regras builtin (fallback — sem necessidade de banco de dados)
#
# Estrutura: {"padrao": str, "tipo": str, "prioridade": int, "descricao": str}
# "padrao" é regex Python aplicado sobre texto normalizado (sem acentos + upper).
# Prioridades: obra=90, servico=80, material=10 (default, sem regra explícita).
# ─────────────────────────────────────────────────────────────────────────────
REGRAS_BUILTIN: list[dict[str, Any]] = [
    # ── OBRAS (prioridade 90) ─────────────────────────────────────────────
    {"padrao": r"\bOBRA\b",                         "tipo": "obra",    "prioridade": 90, "descricao": "Palavra OBRA isolada"},
    {"padrao": r"\bENGENHARIA\b",                   "tipo": "obra",    "prioridade": 90, "descricao": "Engenharia"},
    {"padrao": r"\bREFORMA\b",                      "tipo": "obra",    "prioridade": 90, "descricao": "Reforma de edificação"},
    {"padrao": r"\bPAVIMENTA",                      "tipo": "obra",    "prioridade": 90, "descricao": "Pavimentação / asfalto"},
    {"padrao": r"\bCALCAMENTO\b",                   "tipo": "obra",    "prioridade": 90, "descricao": "Calçamento de vias"},
    {"padrao": r"\bCONSTRU",                        "tipo": "obra",    "prioridade": 90, "descricao": "Construção"},
    {"padrao": r"\bEDIFICA",                        "tipo": "obra",    "prioridade": 90, "descricao": "Edificação"},
    {"padrao": r"\bDRENAGEM\b",                     "tipo": "obra",    "prioridade": 90, "descricao": "Drenagem pluvial ou sanitária"},
    {"padrao": r"\bTERRAPLANAGEM\b",                "tipo": "obra",    "prioridade": 90, "descricao": "Terraplanagem"},
    {"padrao": r"\bFUNDACAO\b",                     "tipo": "obra",    "prioridade": 90, "descricao": "Fundação de edificação"},
    {"padrao": r"\bSANEAMENTO\b",                   "tipo": "obra",    "prioridade": 90, "descricao": "Obras de saneamento"},
    {"padrao": r"\bGALERIA\s+DE\s+AGUA",            "tipo": "obra",    "prioridade": 90, "descricao": "Galeria de águas pluviais"},

    # ── SERVIÇOS (prioridade 80) ──────────────────────────────────────────
    {"padrao": r"\bSERVICOS?\b",                    "tipo": "servico", "prioridade": 80, "descricao": "Palavra SERVICO/SERVICOS"},
    {"padrao": r"\bMANUTENCAO\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Manutenção preventiva ou corretiva"},
    {"padrao": r"\bLOCACAO\b",                      "tipo": "servico", "prioridade": 80, "descricao": "Locação"},
    {"padrao": r"\bCONSULTORIA\b",                  "tipo": "servico", "prioridade": 80, "descricao": "Consultoria"},
    {"padrao": r"\bSUPORTE\s+TECNICO\b",            "tipo": "servico", "prioridade": 80, "descricao": "Suporte técnico"},
    {"padrao": r"\bLIMPEZA\b",                      "tipo": "servico", "prioridade": 80, "descricao": "Limpeza"},
    {"padrao": r"\bTRANSPORTE\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Transporte"},
    {"padrao": r"\bVIGILANCIA\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Vigilância"},
    {"padrao": r"\bSEGURANCA\s+PATRIMONIAL\b",      "tipo": "servico", "prioridade": 80, "descricao": "Segurança patrimonial"},
    {"padrao": r"\bPORTARIA\b",                     "tipo": "servico", "prioridade": 80, "descricao": "Portaria"},
    {"padrao": r"\bDEDETIZACAO\b",                  "tipo": "servico", "prioridade": 80, "descricao": "Dedetização"},
    {"padrao": r"\bCONTROLE\s+DE\s+PRAGA",          "tipo": "servico", "prioridade": 80, "descricao": "Controle de pragas"},
    {"padrao": r"\bREPROGRAFIA\b",                  "tipo": "servico", "prioridade": 80, "descricao": "Reprografia"},
    {"padrao": r"\bTELEFONIA\b",                    "tipo": "servico", "prioridade": 80, "descricao": "Telefonia"},
    {"padrao": r"\bINTERNET\b",                     "tipo": "servico", "prioridade": 80, "descricao": "Internet"},
    {"padrao": r"\bASSESSORIA\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Assessoria"},
    {"padrao": r"\bTREINAMENTO\b",                  "tipo": "servico", "prioridade": 80, "descricao": "Treinamento"},
    {"padrao": r"\bCAPACITACAO\b",                  "tipo": "servico", "prioridade": 80, "descricao": "Capacitação"},
    {"padrao": r"\bJARDINAGEM\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Jardinagem"},
    {"padrao": r"\bCOLETA\s+DE\s+LIXO\b",           "tipo": "servico", "prioridade": 80, "descricao": "Coleta de resíduos"},
    {"padrao": r"\bCOPEIRAGEM\b",                   "tipo": "servico", "prioridade": 80, "descricao": "Copeiragem"},
    {"padrao": r"\bRECEPCAO\b",                     "tipo": "servico", "prioridade": 80, "descricao": "Recepção"},
]

# Pré-compilar regras builtin (evita recompilação a cada chamada)
_COMPILED_BUILTIN: list[tuple[re.Pattern[str], str, int]] = [
    (re.compile(r["padrao"], re.UNICODE), r["tipo"], r["prioridade"])
    for r in sorted(REGRAS_BUILTIN, key=lambda x: -x["prioridade"])
]

_CACHE_TTL_S: float = 300.0  # 5 minutos


def _normalizar(texto: str) -> str:
    """Remove acentos e converte para maiúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.upper()


class ClassificadorTipoObjeto:
    """Classifica descrições de itens em material/servico/obra.

    Modo standalone (sem DB):
        c = ClassificadorTipoObjeto()
        resultado = c.classificar("Pavimentação da Rua Principal")
        # {"tipo": "obra", "metodo": "builtin", "score": 1.0}

    Modo com DB (SQLAlchemy):
        c = ClassificadorTipoObjeto(db=session)
        resultado = c.classificar("Serviço de limpeza", item_id="uuid-...")
    """

    def __init__(self, db: Any = None) -> None:
        """
        Args:
            db: SQLAlchemy Session opcional. Se None, usa apenas regras builtin.
        """
        self._db = db
        self._db_regras: list[tuple[re.Pattern[str], str, int]] = []
        self._cache_ts: float = 0.0

    # ─────────────────────────────────────────────────────────────────────
    # API principal
    # ─────────────────────────────────────────────────────────────────────

    def classificar(
        self,
        descricao: str,
        item_id: str | None = None,
        registrar_auditoria: bool = False,
    ) -> dict[str, Any]:
        """Classifica uma descrição de item.

        Precedência:
          1. Override manual (se item_id fornecido e DB disponível)
          2. Regras do DB (com TTL cache)
          3. Regras builtin

        Args:
            descricao: Texto do item a classificar.
            item_id:   UUID do item em itens (para lookup de override).
            registrar_auditoria: Se True, persiste resultado em tipo_objeto_auditoria.

        Returns:
            dict com tipo, metodo, score.
        """
        texto_normalizado = _normalizar(descricao or "")

        # 1. Override manual
        if item_id and self._db is not None:
            override = self._buscar_override(item_id)
            if override:
                resultado = {"tipo": override, "metodo": "override", "score": 1.0}
                if registrar_auditoria:
                    self._registrar_auditoria(
                        item_id=item_id,
                        descricao=descricao,
                        tipo_inferido=override,
                        metodo="override",
                        score=1.0,
                    )
                return resultado

        # 2. Regras do DB
        if self._db is not None:
            regras_db = self._carregar_regras_db()
            match_db = self._aplicar_regras(texto_normalizado, regras_db)
            if match_db:
                if registrar_auditoria:
                    self._registrar_auditoria(
                        item_id=item_id,
                        descricao=descricao,
                        tipo_inferido=match_db["tipo"],
                        metodo="db_regras",
                        score=match_db["score"],
                    )
                return match_db

        # 3. Regras builtin (fallback)
        match_builtin = self._aplicar_regras_compiladas(
            texto_normalizado, _COMPILED_BUILTIN
        )
        if match_builtin:
            if registrar_auditoria and self._db is not None:
                self._registrar_auditoria(
                    item_id=item_id,
                    descricao=descricao,
                    tipo_inferido=match_builtin["tipo"],
                    metodo="builtin",
                    score=match_builtin["score"],
                )
            return match_builtin

        # Default: material
        return {"tipo": "material", "metodo": "builtin_default", "score": 0.5}

    def registrar_override(
        self,
        item_id: str,
        tipo: str,
        usuario: str = "admin",
        motivo: str | None = None,
    ) -> bool:
        """Registra override manual para um item.

        Args:
            item_id: UUID do item.
            tipo:    material | servico | obra.
            usuario: Identificador do revisor.
            motivo:  Justificativa textual.

        Returns:
            True se persistido com sucesso, False em caso de erro.
        """
        if self._db is None:
            logger.warning("registrar_override chamado sem DB configurado")
            return False

        if tipo not in ("material", "servico", "obra"):
            raise ValueError(f"tipo inválido: {tipo!r}")

        try:
            from sqlalchemy import text as sa_text

            self._db.execute(
                sa_text(
                    """
                    INSERT INTO tipo_objeto_overrides (item_id, tipo_override, usuario, motivo)
                    VALUES (:item_id, :tipo, :usuario, :motivo)
                    ON CONFLICT (item_id) DO UPDATE
                        SET tipo_override = EXCLUDED.tipo_override,
                            usuario       = EXCLUDED.usuario,
                            motivo        = EXCLUDED.motivo,
                            criado_em     = NOW()
                    """
                ),
                {"item_id": item_id, "tipo": tipo, "usuario": usuario, "motivo": motivo},
            )
            self._db.commit()
            return True
        except Exception as exc:
            logger.error("Falha ao registrar override para item %s: %s", item_id, exc)
            self._db.rollback()
            return False

    def invalidar_cache(self) -> None:
        """Força recarga das regras na próxima chamada."""
        self._cache_ts = 0.0
        self._db_regras = []

    # ─────────────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────────────

    def _carregar_regras_db(self) -> list[tuple[re.Pattern[str], str, int]]:
        """Carrega regras do banco com TTL cache de 5 minutos."""
        agora = time.monotonic()
        if self._db_regras and (agora - self._cache_ts) < _CACHE_TTL_S:
            return self._db_regras

        try:
            from sqlalchemy import text as sa_text

            rows = self._db.execute(
                sa_text(
                    """
                    SELECT padrao, tipo, prioridade
                    FROM tipo_objeto_regras
                    WHERE ativo = TRUE
                    ORDER BY prioridade DESC
                    """
                )
            ).fetchall()

            compiladas: list[tuple[re.Pattern[str], str, int]] = []
            for row in rows:
                try:
                    compiladas.append(
                        (re.compile(row[0], re.UNICODE), row[1], int(row[2]))
                    )
                except re.error as exc:
                    logger.warning("Regra inválida ignorada (padrao=%r): %s", row[0], exc)

            self._db_regras = compiladas
            self._cache_ts = agora
            return compiladas

        except Exception as exc:
            logger.warning("Falha ao carregar regras do DB, usando builtin: %s", exc)
            return []

    def _buscar_override(self, item_id: str) -> str | None:
        """Busca override manual para o item. Retorna tipo ou None."""
        try:
            from sqlalchemy import text as sa_text

            row = self._db.execute(
                sa_text(
                    "SELECT tipo_override FROM tipo_objeto_overrides WHERE item_id = :id"
                ),
                {"id": item_id},
            ).fetchone()
            return row[0] if row else None
        except Exception as exc:
            logger.debug("Falha ao buscar override item %s: %s", item_id, exc)
            return None

    def _registrar_auditoria(
        self,
        item_id: str | None,
        descricao: str,
        tipo_inferido: str,
        metodo: str,
        score: float,
    ) -> None:
        """Persiste registro de auditoria (erros ignorados — melhor esforço)."""
        try:
            from sqlalchemy import text as sa_text

            self._db.execute(
                sa_text(
                    """
                    INSERT INTO tipo_objeto_auditoria
                        (item_id, descricao_trecho, tipo_inferido, metodo, score)
                    VALUES (:item_id, :descricao, :tipo, :metodo, :score)
                    """
                ),
                {
                    "item_id": item_id,
                    "descricao": (descricao or "")[:200],
                    "tipo": tipo_inferido,
                    "metodo": metodo,
                    "score": score,
                },
            )
            # Não comitar aqui — deixar para a transação do caller
        except Exception as exc:
            logger.debug("Falha ao registrar auditoria: %s", exc)

    @staticmethod
    def _aplicar_regras(
        texto_normalizado: str,
        regras: list[tuple[re.Pattern[str], str, int]],
    ) -> dict[str, Any] | None:
        """Aplica lista de (pattern, tipo, prioridade) e retorna o primeiro match."""
        for pattern, tipo, prioridade in regras:
            if pattern.search(texto_normalizado):
                score = 1.0 if prioridade >= 80 else 0.8
                return {"tipo": tipo, "metodo": "db_regras", "score": score}
        return None

    @staticmethod
    def _aplicar_regras_compiladas(
        texto_normalizado: str,
        regras: list[tuple[re.Pattern[str], str, int]],
    ) -> dict[str, Any] | None:
        """Aplica regras builtin pré-compiladas."""
        for pattern, tipo, prioridade in regras:
            if pattern.search(texto_normalizado):
                score = 1.0 if prioridade >= 80 else 0.8
                return {"tipo": tipo, "metodo": "builtin", "score": score}
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Instância global para uso em coletor_municipal.py (modo standalone, sem DB)
# ─────────────────────────────────────────────────────────────────────────────
_classificador_standalone = ClassificadorTipoObjeto(db=None)


def inferir_tipo_objeto(descricao: str | None) -> str:
    """Função de conveniência para uso em contextos sem DB (ex: coletor).

    Substitui a função _infer_tipo_objeto() do coletor_municipal.py.
    Retorna 'material' | 'servico' | 'obra'.
    """
    if not descricao:
        return "material"
    resultado = _classificador_standalone.classificar(descricao)
    return resultado["tipo"]
