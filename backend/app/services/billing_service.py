"""Serviço de billing — planos, limites e cobrança."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

PLANOS: dict[str, dict] = {
    "free": {
        "consultas_mes": 10,
        "relatorios_mes": 2,
        "ufs": ["DF"],
        "suporte": False,
    },
    "basico": {
        "consultas_mes": 100,
        "relatorios_mes": 20,
        "ufs": ["DF", "GO", "SP", "MG", "BA"],
        "suporte": False,
        "preco_mensal": 197.0,
    },
    "profissional": {
        "consultas_mes": 500,
        "relatorios_mes": 100,
        "ufs": "todas",
        "suporte": True,
        "preco_mensal": 497.0,
    },
    "enterprise": {
        "consultas_mes": 9999,
        "relatorios_mes": 9999,
        "ufs": "todas",
        "suporte": True,
        "preco_mensal": 1497.0,
    },
}

# Contadores simulados por tenant
_CONTADORES: dict[str, dict[str, int]] = {}


def _primeiro_dia_mes_atual() -> date:
    """Retorna o primeiro dia do mês atual."""
    hoje = date.today()
    return hoje.replace(day=1)


class BillingService:
    """Gerencia planos, limites de uso e upgrades."""

    def obter_plano(self, plano_id: str) -> dict | None:
        """Retorna detalhes de um plano pelo ID.

        Args:
            plano_id: Identificador do plano (free, basico, profissional, enterprise).

        Returns:
            Dict com detalhes do plano ou None se inexistente.
        """
        plano = PLANOS.get(plano_id)
        if plano is None:
            return None
        return {"id": plano_id, **plano}

    def verificar_limite(
        self,
        tenant_id: str,
        plano_id: str,
        tipo: str,
        db: Session | None = None,
    ) -> dict:
        """Verifica se o tenant atingiu o limite de uso do plano.

        Args:
            tenant_id: Identificador do tenant.
            plano_id: Identificador do plano.
            tipo: Tipo de recurso ('consulta' ou 'relatorio').
            db: Sessão do banco de dados (opcional, fallback in-memory).

        Returns:
            Dict com permitido, usado, limite e percentual.
        """
        plano = PLANOS.get(plano_id, PLANOS["free"])
        chave_limite = "consultas_mes" if tipo == "consulta" else "relatorios_mes"
        limite = plano[chave_limite]

        if db is not None:
            from app.db.models.uso_mensal import UsoMensal

            mes = _primeiro_dia_mes_atual()
            registro = (
                db.query(UsoMensal)
                .filter(UsoMensal.tenant_id == tenant_id, UsoMensal.mes_referencia == mes)
                .first()
            )
            if registro:
                usado = (
                    registro.consultas_utilizadas if tipo == "consulta"
                    else registro.relatorios_utilizados
                )
            else:
                usado = 0
        else:
            contadores = _CONTADORES.get(tenant_id, {"consultas": 0, "relatorios": 0})
            usado = contadores.get("consultas" if tipo == "consulta" else "relatorios", 0)

        percentual = round(usado / limite * 100, 2) if limite > 0 else 0.0
        return {
            "permitido": usado < limite,
            "usado": usado,
            "limite": limite,
            "percentual": percentual,
        }

    def incrementar_uso(
        self,
        db: Session,
        tenant_id: str,
        plano_id: str,
        tipo: str,
    ) -> dict:
        """Incrementa o uso mensal do tenant (upsert).

        Args:
            db: Sessão do banco de dados.
            tenant_id: Identificador do tenant.
            plano_id: Identificador do plano.
            tipo: Tipo de recurso ('consulta' ou 'relatorio').

        Returns:
            Dict com dentro_limite, usado e limite.
        """
        from app.db.models.uso_mensal import UsoMensal

        mes = _primeiro_dia_mes_atual()
        registro = (
            db.query(UsoMensal)
            .filter(UsoMensal.tenant_id == tenant_id, UsoMensal.mes_referencia == mes)
            .first()
        )

        if registro is None:
            registro = UsoMensal(
                tenant_id=tenant_id,
                plano_id=plano_id,
                mes_referencia=mes,
                consultas_utilizadas=0,
                relatorios_utilizados=0,
            )
            db.add(registro)

        if tipo == "consulta":
            registro.consultas_utilizadas += 1
            usado = registro.consultas_utilizadas
        else:
            registro.relatorios_utilizados += 1
            usado = registro.relatorios_utilizados

        registro.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(registro)

        plano = PLANOS.get(plano_id, PLANOS["free"])
        chave_limite = "consultas_mes" if tipo == "consulta" else "relatorios_mes"
        limite = plano[chave_limite]

        return {
            "dentro_limite": usado <= limite,
            "usado": usado,
            "limite": limite,
        }

    def upgrade_tenant(
        self,
        db: Session,
        tenant_id: str,
        novo_plano: str,
    ) -> dict:
        """Persiste upgrade de plano, zerando contadores do mês.

        Args:
            db: Sessão do banco de dados.
            tenant_id: Identificador do tenant.
            novo_plano: Identificador do novo plano.

        Returns:
            Dict com sucesso, plano_anterior e plano_novo.
        """
        from app.db.models.uso_mensal import UsoMensal

        mes = _primeiro_dia_mes_atual()
        registro = (
            db.query(UsoMensal)
            .filter(UsoMensal.tenant_id == tenant_id, UsoMensal.mes_referencia == mes)
            .first()
        )

        plano_anterior = "free"
        if registro is None:
            registro = UsoMensal(
                tenant_id=tenant_id,
                plano_id=novo_plano,
                mes_referencia=mes,
                consultas_utilizadas=0,
                relatorios_utilizados=0,
            )
            db.add(registro)
        else:
            plano_anterior = registro.plano_id
            registro.plano_id = novo_plano
            registro.consultas_utilizadas = 0
            registro.relatorios_utilizados = 0
            registro.updated_at = datetime.utcnow()

        db.commit()

        return {
            "sucesso": True,
            "plano_anterior": plano_anterior,
            "plano_novo": novo_plano,
            "mensagem": f"Upgrade para {novo_plano} realizado com sucesso",
        }

    def listar_planos(self) -> list[dict]:
        """Lista todos os planos disponíveis.

        Returns:
            Lista de dicts com detalhes de cada plano.
        """
        return [{"id": pid, **dados} for pid, dados in PLANOS.items()]

    def calcular_custo_anual(self, plano_id: str) -> float:
        """Calcula o custo anual com desconto de 2 meses (paga 10).

        Args:
            plano_id: Identificador do plano.

        Returns:
            Custo anual em reais (0.0 para plano free).
        """
        plano = PLANOS.get(plano_id)
        if plano is None:
            return 0.0
        preco_mensal = plano.get("preco_mensal", 0.0)
        return round(preco_mensal * 10, 2)
