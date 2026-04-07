"""Pipeline de ingestão automática com APScheduler.

Registra dois jobs recorrentes no FastAPI via lifespan:

  • ingestao_go_diaria   — todo dia às 02:00 (America/Sao_Paulo)
                           Coleta dados do PNCP para GO dos últimos 2 dias.

  • cobertura_semanal    — todo domingo às 03:00 (America/Sao_Paulo)
                           Atualiza a tabela cobertura_municipios para GO.

Uso no main.py:
    from contextlib import asynccontextmanager
    from app.services.scheduler import criar_scheduler

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler = criar_scheduler()
        scheduler.start()
        yield
        scheduler.shutdown(wait=False)

    app = FastAPI(lifespan=lifespan)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Jobs
# ──────────────────────────────────────────────────────────────────────────────

def _job_ingestao_go() -> None:
    """Ingere dados do PNCP para Goiás (janela: últimos 2 dias).

    Executado diariamente às 02:00. Usa PipelineMultiUF com UFs=['GO'].
    Erros são logados mas não propagados para não travar o scheduler.
    """
    try:
        from app.services.pncp_pipeline_ufs import PipelineMultiUF

        hoje = datetime.now(tz=timezone.utc)
        data_fim = hoje.strftime("%Y%m%d")
        data_inicio = (hoje - timedelta(days=2)).strftime("%Y%m%d")

        logger.info(
            "[scheduler] Iniciando ingestão GO: %s → %s", data_inicio, data_fim
        )
        pipeline = PipelineMultiUF(ufs=["GO"])
        relatorio = pipeline.executar(data_inicio=data_inicio, data_fim=data_fim)

        logger.info(
            "[scheduler] Ingestão GO concluída: contratos=%d, itens=%d, falhas=%s",
            relatorio.total_contratacoes,
            relatorio.total_itens,
            relatorio.ufs_com_falha,
        )
    except Exception:
        logger.exception("[scheduler] Erro no job de ingestão GO")


def _job_cobertura_go() -> None:
    """Atualiza tabela cobertura_municipios para todos os municípios de GO.

    Executado semanalmente (domingo às 03:00). Consulta fontes_preco por
    município e persiste o resultado em cobertura_municipios.
    Erros são logados mas não propagados.
    """
    try:
        from sqlalchemy import text

        from app.db.session import SessionLocal
        from app.services.cobertura_service import CoberturaService

        svc = CoberturaService()
        municipios_go = svc.obter_todos_municipios_go()

        with SessionLocal() as db:
            # Conta amostras por município em GO
            rows = db.execute(
                text(
                    """
                    SELECT fp.municipio,
                           COUNT(*) AS n_amostras,
                           COUNT(DISTINCT c.id) AS n_categorias
                    FROM fontes_preco fp
                    JOIN itens i ON i.id = fp.item_id
                    LEFT JOIN categorias c ON c.id = i.categoria_id
                    WHERE fp.uf = 'GO'
                      AND fp.ativo = TRUE
                    GROUP BY fp.municipio
                    """
                )
            ).fetchall()

            contagens: dict[str, dict[str, int]] = {
                r.municipio: {
                    "n_amostras": r.n_amostras,
                    "n_categorias": r.n_categorias,
                }
                for r in rows
                if r.municipio
            }

            # Persiste/atualiza cobertura por município
            for municipio in municipios_go:
                dados = contagens.get(municipio, {"n_amostras": 0, "n_categorias": 0})
                status = svc.calcular_cobertura_municipio(
                    municipio=municipio,
                    uf="GO",
                    n_amostras=dados["n_amostras"],
                    n_categorias=dados["n_categorias"],
                )
                db.execute(
                    text(
                        """
                        INSERT INTO cobertura_municipios
                            (municipio, uf, n_amostras, n_categorias, nivel, atualizado_em)
                        VALUES
                            (:municipio, :uf, :n_amostras, :n_categorias, :nivel, NOW())
                        ON CONFLICT (municipio, uf)
                        DO UPDATE SET
                            n_amostras   = EXCLUDED.n_amostras,
                            n_categorias = EXCLUDED.n_categorias,
                            nivel        = EXCLUDED.nivel,
                            atualizado_em = NOW()
                        """
                    ),
                    {
                        "municipio": municipio,
                        "uf": "GO",
                        "n_amostras": status["n_amostras"],
                        "n_categorias": status["n_categorias"],
                        "nivel": status["nivel"],
                    },
                )
            db.commit()

        logger.info(
            "[scheduler] Cobertura GO atualizada: %d municípios processados",
            len(municipios_go),
        )
    except Exception:
        logger.exception("[scheduler] Erro no job de cobertura GO")


# ──────────────────────────────────────────────────────────────────────────────
# Fábrica do scheduler
# ──────────────────────────────────────────────────────────────────────────────

def criar_scheduler() -> Any:
    """Cria e configura o APScheduler com os jobs do banco de preços.

    Returns:
        BackgroundScheduler configurado (ainda não iniciado).

    Raises:
        ImportError: se apscheduler não estiver instalado.
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError as exc:
        raise ImportError(
            "APScheduler não instalado. Execute: pip install apscheduler>=3.10,<4"
        ) from exc

    scheduler = BackgroundScheduler(
        timezone="America/Sao_Paulo",
        job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 3600},
    )

    # Job 1: ingestão GO diária às 02:00
    scheduler.add_job(
        _job_ingestao_go,
        trigger=CronTrigger(hour=2, minute=0, timezone="America/Sao_Paulo"),
        id="ingestao_go_diaria",
        name="Ingestão PNCP Goiás (diária)",
        replace_existing=True,
    )

    # Job 2: atualização de cobertura GO toda domingo às 03:00
    scheduler.add_job(
        _job_cobertura_go,
        trigger=CronTrigger(
            day_of_week="sun", hour=3, minute=0, timezone="America/Sao_Paulo"
        ),
        id="cobertura_go_semanal",
        name="Atualização cobertura GO (semanal)",
        replace_existing=True,
    )

    logger.info(
        "[scheduler] Configurado: %d jobs registrados",
        len(scheduler.get_jobs()),
    )
    return scheduler


def status_scheduler(scheduler: Any) -> dict[str, Any]:
    """Retorna status dos jobs registrados no scheduler.

    Args:
        scheduler: Instância do BackgroundScheduler.

    Returns:
        Dict com lista de jobs e estado geral do scheduler.
    """
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append(
            {
                "id": job.id,
                "nome": job.name,
                "proximo_disparo": next_run.isoformat() if next_run else None,
            }
        )
    return {
        "rodando": scheduler.running,
        "jobs": jobs,
    }
