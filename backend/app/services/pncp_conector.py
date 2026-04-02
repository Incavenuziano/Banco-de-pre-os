"""Conector para a API do Portal Nacional de Contratações Públicas (PNCP).

Implementa chamadas HTTP à API REST do PNCP com retry automático
em caso de timeout ou erro de conexão.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class PNCPConector:
    """Cliente para a API pública do PNCP.

    Realiza buscas de contratações, itens e resultados de itens
    com retry automático (até 2 tentativas) em caso de timeout
    ou erro de conexão.
    """

    BASE_URL: str = "https://pncp.gov.br/api/pncp/v1"
    TIMEOUT: int = 30
    MAX_RETRIES: int = 2

    def buscar_contratacoes(
        self,
        uf: str,
        municipio: str | None = None,
        data_inicio: str = "",
        data_fim: str = "",
        pagina: int = 1,
        tam_pagina: int = 50,
    ) -> dict[str, Any]:
        """Busca contratações por UF e município no PNCP.

        Args:
            uf: Sigla da UF (ex: 'GO').
            municipio: Nome do município (opcional).
            data_inicio: Data inicial no formato YYYYMMDD.
            data_fim: Data final no formato YYYYMMDD.
            pagina: Número da página (default 1).
            tam_pagina: Tamanho da página (default 50).

        Returns:
            Dicionário com a resposta JSON ou {'data': [], 'totalRegistros': 0}
            em caso de erro.
        """
        params: dict[str, Any] = {
            "uf": uf,
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
            "pagina": pagina,
            "tamanhoPagina": tam_pagina,
        }
        if municipio:
            params["municipio"] = municipio

        url = f"{self.BASE_URL}/orgaos/compras"
        return self._get_com_retry(url, params, fallback={"data": [], "totalRegistros": 0})

    def buscar_itens_contratacao(
        self,
        cnpj_orgao: str,
        ano: int,
        numero_sequencial: int,
    ) -> list[dict[str, Any]]:
        """Busca itens de uma contratação específica.

        Args:
            cnpj_orgao: CNPJ do órgão contratante.
            ano: Ano da contratação.
            numero_sequencial: Número sequencial da contratação.

        Returns:
            Lista de itens ou [] em caso de erro.
        """
        url = f"{self.BASE_URL}/orgaos/{cnpj_orgao}/compras/{ano}/{numero_sequencial}/itens"
        return self._get_com_retry(url, {}, fallback=[])

    def buscar_resultado_item(
        self,
        cnpj_orgao: str,
        ano: int,
        numero_sequencial: int,
        numero_item: int,
    ) -> dict[str, Any] | None:
        """Busca resultado de um item específico de contratação.

        Args:
            cnpj_orgao: CNPJ do órgão contratante.
            ano: Ano da contratação.
            numero_sequencial: Número sequencial da contratação.
            numero_item: Número do item.

        Returns:
            Dicionário com resultado ou None em caso de erro.
        """
        url = (
            f"{self.BASE_URL}/orgaos/{cnpj_orgao}/compras/{ano}/"
            f"{numero_sequencial}/itens/{numero_item}/resultado"
        )
        return self._get_com_retry(url, {}, fallback=None)

    def _get_com_retry(
        self,
        url: str,
        params: dict[str, Any],
        fallback: Any,
    ) -> Any:
        """Executa GET com retry automático em caso de timeout/conexão.

        Tenta até MAX_RETRIES vezes antes de retornar o fallback.
        """
        tentativas = 0
        while tentativas <= self.MAX_RETRIES:
            try:
                resp = requests.get(url, params=params, timeout=self.TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                tentativas += 1
                logger.warning(
                    "Tentativa %d/%d falhou para %s: %s",
                    tentativas,
                    self.MAX_RETRIES + 1,
                    url,
                    exc,
                )
                if tentativas > self.MAX_RETRIES:
                    logger.error("Todas as tentativas falharam para %s", url)
                    return fallback
            except requests.exceptions.HTTPError as exc:
                logger.error("Erro HTTP %s para %s", exc.response.status_code if exc.response else "?", url)
                return fallback
            except Exception as exc:
                logger.error("Erro inesperado para %s: %s", url, exc)
                return fallback
        return fallback
