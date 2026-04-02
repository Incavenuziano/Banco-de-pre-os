"""Pipeline de ingestão PNCP multi-UF — Semana 13.

Expande a coleta do PNCP de 5 UFs para 15 UFs prioritárias,
com jobs independentes por UF, retry/backoff e monitoramento de lag.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.services.pncp_conector import PNCPConector

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Configuração das 15 UFs prioritárias (Semana 13)
# ─────────────────────────────────────────────────────────
UFS_PRIORITARIAS: list[str] = [
    "DF",  # Caso de uso Transferegov
    "SP",  # Maior volume
    "MG",  # Volume alto
    "RJ",  # Volume alto
    "BA",  # Volume médio
    "RS",  # Volume médio
    "PE",  # Volume médio
    "CE",  # Volume médio
    "SC",  # Volume médio
    "PR",  # Volume médio
    "ES",  # Volume baixo-médio
    "MT",  # Volume baixo
    "GO",  # Volume baixo
    "PI",  # Volume baixo
    "AL",  # Volume baixo
]

# SLA de lag de ingestão em horas
SLA_LAG_HORAS: int = 6

# Máximo de tentativas por UF antes de marcar como falha
MAX_TENTATIVAS_UF: int = 3

# Pausa entre tentativas (segundos) — exponencial: 2^n
BACKOFF_BASE: float = 2.0


@dataclass
class ResultadoUF:
    """Resultado de ingestão para uma UF."""

    uf: str
    sucesso: bool
    total_contratacoes: int = 0
    total_itens: int = 0
    erros: list[str] = field(default_factory=list)
    tentativas: int = 0
    duracao_segundos: float = 0.0
    timestamp_inicio: str = ""
    timestamp_fim: str = ""
    lag_estimado_horas: float | None = None

    @property
    def dentro_sla(self) -> bool:
        """Verifica se o lag está dentro do SLA de 6 horas."""
        if self.lag_estimado_horas is None:
            return True
        return self.lag_estimado_horas <= SLA_LAG_HORAS


@dataclass
class RelatorioIngestionUFs:
    """Relatório consolidado de ingestão por UF."""

    timestamp: str
    data_inicio: str
    data_fim: str
    resultados: list[ResultadoUF] = field(default_factory=list)

    @property
    def ufs_com_sucesso(self) -> list[str]:
        return [r.uf for r in self.resultados if r.sucesso]

    @property
    def ufs_com_falha(self) -> list[str]:
        return [r.uf for r in self.resultados if not r.sucesso]

    @property
    def total_itens(self) -> int:
        return sum(r.total_itens for r in self.resultados)

    @property
    def total_contratacoes(self) -> int:
        return sum(r.total_contratacoes for r in self.resultados)

    def como_texto(self) -> str:
        """Gera relatório textual estruturado."""
        linhas: list[str] = [
            "=" * 60,
            f"RELATÓRIO DE INGESTÃO — {self.timestamp}",
            f"Período: {self.data_inicio} → {self.data_fim}",
            "=" * 60,
            f"UFs com sucesso: {len(self.ufs_com_sucesso)}/{len(self.resultados)}",
            f"Total contratações: {self.total_contratacoes}",
            f"Total itens: {self.total_itens}",
            "",
            "DETALHE POR UF:",
            "-" * 40,
        ]
        for r in self.resultados:
            status = "✓" if r.sucesso else "✗"
            lag_info = f"lag={r.lag_estimado_horas:.1f}h" if r.lag_estimado_horas else "lag=N/A"
            linhas.append(
                f"  {status} {r.uf:<4} | contratos={r.total_contratacoes:>5} "
                f"| itens={r.total_itens:>6} | {lag_info} "
                f"| {r.duracao_segundos:.1f}s"
            )
            if r.erros:
                for erro in r.erros[:2]:
                    linhas.append(f"       ERRO: {erro}")
        linhas += ["=" * 60]
        return "\n".join(linhas)


class JobIngestaoUF:
    """Job de ingestão para uma UF específica com retry/backoff."""

    def __init__(self, uf: str, conector: PNCPConector | None = None) -> None:
        self.uf = uf
        self.conector = conector or PNCPConector()

    def executar(
        self,
        data_inicio: str,
        data_fim: str,
        tam_pagina: int = 50,
    ) -> ResultadoUF:
        """Executa ingestão completa para a UF com retry/backoff.

        Args:
            data_inicio: Data inicial no formato YYYYMMDD.
            data_fim: Data final no formato YYYYMMDD.
            tam_pagina: Tamanho de página para paginação.

        Returns:
            ResultadoUF com estatísticas e status.
        """
        ts_inicio = datetime.now()
        resultado = ResultadoUF(
            uf=self.uf,
            sucesso=False,
            timestamp_inicio=ts_inicio.isoformat(),
        )

        for tentativa in range(1, MAX_TENTATIVAS_UF + 1):
            resultado.tentativas = tentativa
            try:
                contratacoes, itens, erros = self._coletar_paginado(
                    data_inicio, data_fim, tam_pagina
                )
                resultado.total_contratacoes = contratacoes
                resultado.total_itens = itens
                resultado.erros = erros
                resultado.sucesso = True
                break

            except Exception as exc:
                erro_msg = f"Tentativa {tentativa}: {exc}"
                logger.warning("UF %s — %s", self.uf, erro_msg)
                resultado.erros.append(erro_msg)

                if tentativa < MAX_TENTATIVAS_UF:
                    espera = BACKOFF_BASE ** tentativa
                    logger.info("UF %s — aguardando %.1fs antes de tentar novamente", self.uf, espera)
                    time.sleep(espera)
                else:
                    logger.error("UF %s — todas as %d tentativas falharam", self.uf, MAX_TENTATIVAS_UF)

        ts_fim = datetime.now()
        resultado.timestamp_fim = ts_fim.isoformat()
        resultado.duracao_segundos = (ts_fim - ts_inicio).total_seconds()

        # Estima lag: diferença entre data_fim e agora
        try:
            dt_fim = datetime.strptime(data_fim, "%Y%m%d")
            resultado.lag_estimado_horas = (ts_fim - dt_fim).total_seconds() / 3600
        except ValueError:
            resultado.lag_estimado_horas = None

        return resultado

    def _coletar_paginado(
        self,
        data_inicio: str,
        data_fim: str,
        tam_pagina: int,
    ) -> tuple[int, int, list[str]]:
        """Coleta contratações paginadas e conta itens.

        Returns:
            Tupla (total_contratacoes, total_itens, erros).
        """
        total_contratacoes = 0
        total_itens = 0
        erros: list[str] = []
        pagina = 1

        while True:
            resp = self.conector.buscar_contratacoes(
                uf=self.uf,
                data_inicio=data_inicio,
                data_fim=data_fim,
                pagina=pagina,
                tam_pagina=tam_pagina,
            )

            contratacoes = resp.get("data", [])
            if not contratacoes:
                break

            total_contratacoes += len(contratacoes)

            for contratacao in contratacoes:
                cnpj = contratacao.get("cnpjOrgao", "")
                ano = contratacao.get("anoCompra", 0)
                seq = contratacao.get("sequencialCompra", 0)
                if not (cnpj and ano and seq):
                    continue
                try:
                    itens = self.conector.buscar_itens_contratacao(cnpj, ano, seq)
                    total_itens += len(itens)
                except Exception as exc:
                    erros.append(f"Itens {cnpj}/{ano}/{seq}: {exc}")

            total_registros = resp.get("totalRegistros", 0)
            if pagina * tam_pagina >= total_registros:
                break
            pagina += 1

        return total_contratacoes, total_itens, erros


class PipelineMultiUF:
    """Orquestra ingestão paralela (serial) de múltiplas UFs.

    Executa cada UF em sequência com isolamento de falhas:
    falha em uma UF não impede as demais.
    """

    def __init__(
        self,
        ufs: list[str] | None = None,
        conector: PNCPConector | None = None,
    ) -> None:
        self.ufs = ufs or UFS_PRIORITARIAS
        self.conector = conector or PNCPConector()

    def executar(
        self,
        data_inicio: str,
        data_fim: str,
        tam_pagina: int = 50,
    ) -> RelatorioIngestionUFs:
        """Executa ingestão para todas as UFs e retorna relatório consolidado.

        Args:
            data_inicio: Data inicial no formato YYYYMMDD.
            data_fim: Data final no formato YYYYMMDD.
            tam_pagina: Tamanho de página (default 50).

        Returns:
            RelatorioIngestionUFs com resultados por UF.
        """
        relatorio = RelatorioIngestionUFs(
            timestamp=datetime.now().isoformat(),
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        for uf in self.ufs:
            logger.info("Iniciando ingestão para UF %s", uf)
            job = JobIngestaoUF(uf=uf, conector=self.conector)
            resultado = job.executar(data_inicio, data_fim, tam_pagina)
            relatorio.resultados.append(resultado)

            status = "SUCESSO" if resultado.sucesso else "FALHA"
            logger.info(
                "UF %s — %s | contratos=%d | itens=%d | %.1fs",
                uf,
                status,
                resultado.total_contratacoes,
                resultado.total_itens,
                resultado.duracao_segundos,
            )

        return relatorio

    def validar_endpoints(self, data_teste: str = "20250101") -> dict[str, bool]:
        """Valida disponibilidade da API PNCP para cada UF.

        Faz uma requisição mínima (1 registro) por UF e verifica se responde.

        Args:
            data_teste: Data para consulta de teste (YYYYMMDD).

        Returns:
            Dict {uf: disponivel} para cada UF.
        """
        disponibilidade: dict[str, bool] = {}

        for uf in self.ufs:
            try:
                resp = self.conector.buscar_contratacoes(
                    uf=uf,
                    data_inicio=data_teste,
                    data_fim=data_teste,
                    pagina=1,
                    tam_pagina=1,
                )
                # Consideramos disponível se a resposta tem a estrutura esperada
                disponibilidade[uf] = "data" in resp
                logger.info("Endpoint UF %s: %s", uf, "OK" if disponibilidade[uf] else "ESTRUTURA INVÁLIDA")
            except Exception as exc:
                disponibilidade[uf] = False
                logger.warning("Endpoint UF %s: FALHA — %s", uf, exc)

        return disponibilidade
