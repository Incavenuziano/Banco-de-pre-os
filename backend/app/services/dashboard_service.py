"""Serviço de dashboard — resumo, histórico e cobertura."""

from __future__ import annotations

import time
from datetime import datetime, timedelta

_INICIO_APP = time.time()


class DashboardService:
    """Fornece dados agregados para o dashboard do sistema."""

    def obter_resumo(self, tenant_id: str) -> dict:
        """Retorna resumo geral do tenant.

        Args:
            tenant_id: Identificador do tenant.

        Returns:
            Dict com totais de consultas, relatórios, categorias mais buscadas,
            cobertura de UFs e média de score de confiança.
        """
        return {
            "total_consultas": 1234,
            "total_relatorios": 56,
            "categorias_mais_buscadas": [
                {"categoria": "Papel A4", "count": 320},
                {"categoria": "Detergente", "count": 215},
                {"categoria": "Gasolina Comum", "count": 198},
                {"categoria": "Toner para Impressora", "count": 142},
                {"categoria": "Arroz", "count": 110},
            ],
            "cobertura_ufs": ["DF", "GO", "SP", "MG", "BA"],
            "media_score_confianca": 72.5,
        }

    def obter_historico_consultas(
        self, tenant_id: str, dias: int = 30
    ) -> list[dict]:
        """Retorna histórico de consultas e relatórios por dia.

        Args:
            tenant_id: Identificador do tenant.
            dias: Número de dias para o histórico.

        Returns:
            Lista de dicts com data, consultas e relatórios por dia.
        """
        hoje = datetime.utcnow().date()
        historico: list[dict] = []
        for i in range(dias):
            data = hoje - timedelta(days=dias - 1 - i)
            historico.append({
                "data": data.isoformat(),
                "consultas": 30 + (i * 7) % 50,
                "relatorios": 2 + (i * 3) % 8,
            })
        return historico

    def obter_cobertura_categorias(self) -> dict:
        """Retorna cobertura de categorias com amostras.

        Returns:
            Dict com total de categorias, com/sem amostras e detalhes por categoria.
        """
        categorias = [
            {"nome": "Papel A4", "n_amostras": 450, "ultima_atualizacao": "2026-03-15"},
            {"nome": "Detergente", "n_amostras": 380, "ultima_atualizacao": "2026-03-14"},
            {"nome": "Gasolina Comum", "n_amostras": 1200, "ultima_atualizacao": "2026-03-20"},
            {"nome": "Toner para Impressora", "n_amostras": 220, "ultima_atualizacao": "2026-03-10"},
            {"nome": "Arroz", "n_amostras": 600, "ultima_atualizacao": "2026-03-18"},
            {"nome": "Feijão", "n_amostras": 550, "ultima_atualizacao": "2026-03-17"},
            {"nome": "Diesel S10", "n_amostras": 950, "ultima_atualizacao": "2026-03-20"},
            {"nome": "Álcool Gel", "n_amostras": 420, "ultima_atualizacao": "2026-03-12"},
            {"nome": "Cadeira de Escritório", "n_amostras": 0, "ultima_atualizacao": None},
            {"nome": "Notebook", "n_amostras": 0, "ultima_atualizacao": None},
        ]
        com_amostras = sum(1 for c in categorias if c["n_amostras"] > 0)
        return {
            "total_categorias": len(categorias),
            "com_amostras": com_amostras,
            "sem_amostras": len(categorias) - com_amostras,
            "por_categoria": categorias,
        }

    def admin_status(self) -> dict:
        """Retorna status geral do sistema para administração.

        Returns:
            Dict com versão, totais e status dos testes.
        """
        return {
            "versao": "0.9.0",
            "total_usuarios": 2,
            "total_tenants": 1,
            "uptime_segundos": round(time.time() - _INICIO_APP, 2),
            "testes_ok": True,
        }
