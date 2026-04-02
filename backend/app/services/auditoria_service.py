"""Serviço de auditoria — registro e consulta de eventos de auditoria."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone


class AuditoriaService:
    """Registra e consulta eventos de auditoria do sistema."""

    def __init__(self) -> None:
        """Inicializa lista de eventos vazia."""
        self.EVENTOS: list[dict] = []

    def registrar(
        self,
        entidade: str,
        acao: str,
        usuario_id: str | None,
        payload: dict | None = None,
    ) -> dict:
        """Registra um evento de auditoria.

        Args:
            entidade: Entidade afetada (ex: 'usuario', 'relatorio').
            acao: Ação realizada (ex: 'criar', 'atualizar', 'excluir').
            usuario_id: ID do usuário que realizou a ação.
            payload: Dados adicionais do evento.

        Returns:
            Dict com dados do evento registrado.
        """
        evento = {
            "id": str(uuid.uuid4()),
            "entidade": entidade,
            "acao": acao,
            "usuario_id": usuario_id,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.EVENTOS.append(evento)
        return evento

    def listar(
        self,
        entidade: str | None = None,
        usuario_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Lista eventos de auditoria com filtros opcionais.

        Args:
            entidade: Filtro por entidade.
            usuario_id: Filtro por usuário.
            limit: Número máximo de eventos retornados.

        Returns:
            Lista de eventos filtrados.
        """
        resultado = self.EVENTOS
        if entidade:
            resultado = [e for e in resultado if e["entidade"] == entidade]
        if usuario_id:
            resultado = [e for e in resultado if e["usuario_id"] == usuario_id]
        return resultado[:limit]

    def exportar_csv(self) -> str:
        """Exporta todos os eventos de auditoria como CSV.

        Returns:
            String CSV com cabeçalho e dados.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "entidade", "acao", "usuario_id", "payload", "timestamp"])
        for evento in self.EVENTOS:
            writer.writerow([
                evento["id"],
                evento["entidade"],
                evento["acao"],
                evento.get("usuario_id", ""),
                str(evento.get("payload", "")),
                evento["timestamp"],
            ])
        return output.getvalue()


# Instância global
auditoria = AuditoriaService()
