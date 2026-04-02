"""Serviço de backup e exportação de dados — Semana 20."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.services.analise_service import AnaliseService, CATEGORIAS, UFS_VALIDADAS


class BackupService:
    """Exporta dados críticos do sistema em formato JSON."""

    def __init__(self) -> None:
        self._analise = AnaliseService()

    def exportar_completo(self) -> dict:
        """Exporta todos os dados críticos em formato JSON.

        Returns:
            Dict com metadados e dados exportados.
        """
        agora = datetime.utcnow().isoformat()

        # Exportar preços
        precos = self._analise.listar_precos(pagina=1, por_pagina=100)

        # Exportar categorias
        categorias = self._analise.listar_categorias()

        # Exportar UFs
        ufs = self._analise.listar_ufs()

        return {
            "metadados": {
                "exportado_em": agora,
                "versao": "1.0",
                "formato": "JSON",
                "sistema": "Banco de Preços v3",
            },
            "dados": {
                "precos": precos,
                "categorias": categorias,
                "ufs": ufs,
            },
            "estatisticas": {
                "total_precos": precos.get("total", 0),
                "total_categorias": len(categorias),
                "total_ufs": len(ufs),
            },
        }

    def exportar_json_bytes(self) -> bytes:
        """Exporta dados como bytes JSON (para download).

        Returns:
            JSON serializado como bytes UTF-8.
        """
        dados = self.exportar_completo()
        return json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")

    def validar_integridade(self) -> dict:
        """Verifica integridade dos dados do sistema.

        Returns:
            Dict com status e detalhes de verificação.
        """
        precos = self._analise.listar_precos(pagina=1, por_pagina=1)
        categorias = self._analise.listar_categorias()
        ufs = self._analise.listar_ufs()

        problemas: list[str] = []

        if precos.get("total", 0) == 0:
            problemas.append("Nenhum preço no sistema")

        if len(categorias) == 0:
            problemas.append("Nenhuma categoria cadastrada")

        if len(ufs) == 0:
            problemas.append("Nenhuma UF cadastrada")

        return {
            "status": "ok" if not problemas else "problemas",
            "total_precos": precos.get("total", 0),
            "total_categorias": len(categorias),
            "total_ufs": len(ufs),
            "problemas": problemas,
            "verificado_em": datetime.utcnow().isoformat(),
        }
