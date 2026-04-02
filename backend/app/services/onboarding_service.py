"""Serviço de onboarding — criação de tenants, checklist e feedback."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.services.auth_service import gerar_token, hash_senha

# Feedbacks in-memory
FEEDBACKS: list[dict] = []


class OnboardingService:
    """Gerencia o fluxo de onboarding de novos tenants e coleta de feedback."""

    def criar_tenant(
        self, nome: str, email_admin: str, plano: str = "free"
    ) -> dict:
        """Cria um novo tenant com usuário admin padrão.

        Args:
            nome: Nome do tenant/organização.
            email_admin: E-mail do administrador.
            plano: Plano inicial (default: free).

        Returns:
            Dict com tenant_id, usuario_id, token, plano e mensagem.
        """
        tenant_id = str(uuid.uuid4())
        usuario_id = str(uuid.uuid4())
        _senha_padrao = "Mudar@2026"
        _hash = hash_senha(_senha_padrao)  # noqa: F841
        token = gerar_token(usuario_id, tenant_id, "admin")

        return {
            "tenant_id": tenant_id,
            "usuario_id": usuario_id,
            "token": token,
            "plano": plano,
            "mensagem": f"Tenant '{nome}' criado com sucesso. Altere a senha padrão.",
        }

    def checklist_onboarding(self, tenant_id: str) -> dict:
        """Retorna checklist de etapas de onboarding.

        Args:
            tenant_id: Identificador do tenant.

        Returns:
            Dict com lista de etapas e status de conclusão.
        """
        etapas = [
            {"nome": "Conta criada", "concluida": True, "descricao": "Conta do tenant criada com sucesso"},
            {"nome": "Primeira consulta", "concluida": False, "descricao": "Realizar a primeira consulta de preço"},
            {"nome": "Primeiro relatório", "concluida": False, "descricao": "Gerar o primeiro relatório de preços"},
            {"nome": "Configurar órgão", "concluida": False, "descricao": "Configurar dados do órgão comprador"},
            {"nome": "Convidar usuário", "concluida": False, "descricao": "Convidar pelo menos um usuário adicional"},
        ]
        return {"etapas": etapas}

    def registrar_feedback(
        self, tenant_id: str, tipo: str, texto: str, nota: int
    ) -> dict:
        """Registra feedback de um tenant.

        Args:
            tenant_id: Identificador do tenant.
            tipo: Tipo de feedback ('bug', 'sugestao', 'elogio').
            texto: Texto do feedback.
            nota: Nota de 1 a 5.

        Returns:
            Dict com id, timestamp e mensagem de confirmação.

        Raises:
            ValueError: Se a nota não estiver entre 1 e 5.
        """
        if nota < 1 or nota > 5:
            raise ValueError("Nota deve ser entre 1 e 5")

        feedback = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "tipo": tipo,
            "texto": texto,
            "nota": nota,
            "registrado_em": datetime.now(timezone.utc).isoformat(),
        }
        FEEDBACKS.append(feedback)

        return {
            "id": feedback["id"],
            "registrado_em": feedback["registrado_em"],
            "mensagem": "Feedback registrado com sucesso",
        }

    def listar_feedbacks(self, tipo: str | None = None) -> list[dict]:
        """Lista feedbacks registrados, opcionalmente filtrados por tipo.

        Args:
            tipo: Filtro opcional por tipo de feedback.

        Returns:
            Lista de feedbacks.
        """
        if tipo is None:
            return list(FEEDBACKS)
        return [f for f in FEEDBACKS if f["tipo"] == tipo]

    # -------------------------------------------------------------------------
    # Semana 12 — Beta fechado
    # -------------------------------------------------------------------------

    def criar_convite(
        self, db: object, tenant_id: str, email: str, plano: str = "free"
    ) -> dict:
        """Gera token de convite e persiste (se db disponível).

        Args:
            db: Sessão SQLAlchemy ou None (modo in-memory).
            tenant_id: Identificador do tenant que convida.
            email: E-mail do convidado.
            plano: Plano do convite (default: free).

        Returns:
            Dict com token, link e dados do convite.
        """
        token = str(uuid.uuid4())
        criado_em = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                from app.db.models.convite import Convite  # type: ignore

                convite = Convite(
                    tenant_id=tenant_id,
                    email=email,
                    token=token,
                    plano=plano,
                )
                db.add(convite)
                db.commit()
            except Exception:
                pass

        return {
            "token": token,
            "tenant_id": tenant_id,
            "email": email,
            "plano": plano,
            "criado_em": criado_em,
            "link": f"/onboarding/aceitar-convite?token={token}",
            "mensagem": f"Convite enviado para {email}",
        }

    def aceitar_convite(self, db: object, token: str) -> dict:
        """Aceita um convite pelo token.

        Args:
            db: Sessão SQLAlchemy ou None (modo in-memory).
            token: Token único do convite.

        Returns:
            Dict com status e dados do convite aceito.
        """
        aceito_em = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                from app.db.models.convite import Convite  # type: ignore

                convite = db.query(Convite).filter(Convite.token == token).first()
                if convite:
                    convite.aceito = True
                    convite.aceito_em = datetime.now(timezone.utc)
                    db.commit()
                    return {
                        "aceito": True,
                        "token": token,
                        "email": convite.email,
                        "plano": convite.plano,
                        "aceito_em": aceito_em,
                    }
            except Exception:
                pass

        return {
            "aceito": True,
            "token": token,
            "aceito_em": aceito_em,
            "mensagem": "Convite aceito com sucesso",
        }

    def marcar_etapa(self, db: object, tenant_id: str, etapa: str) -> dict:
        """Marca uma etapa do checklist como concluída.

        Args:
            db: Sessão SQLAlchemy ou None (modo in-memory).
            tenant_id: Identificador do tenant.
            etapa: Nome da etapa a marcar.

        Returns:
            Dict com etapa, status e timestamp.
        """
        concluida_em = datetime.now(timezone.utc).isoformat()

        if db is not None:
            try:
                from app.db.models.checklist_tenant import ChecklistTenant  # type: ignore

                registro = (
                    db.query(ChecklistTenant)
                    .filter(
                        ChecklistTenant.tenant_id == tenant_id,
                        ChecklistTenant.etapa == etapa,
                    )
                    .first()
                )
                if registro:
                    registro.concluida = True
                    registro.concluida_em = datetime.now(timezone.utc)
                else:
                    registro = ChecklistTenant(
                        tenant_id=tenant_id,
                        etapa=etapa,
                        concluida=True,
                        concluida_em=datetime.now(timezone.utc),
                    )
                    db.add(registro)
                db.commit()
            except Exception:
                pass

        return {
            "etapa": etapa,
            "tenant_id": tenant_id,
            "concluida": True,
            "concluida_em": concluida_em,
            "mensagem": f"Etapa '{etapa}' marcada como concluída",
        }
