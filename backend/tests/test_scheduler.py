"""Testes para o serviço de scheduler de ingestão automática."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestCriarScheduler:
    """Testa a fábrica do scheduler."""

    def test_criar_scheduler_sem_apscheduler_lanca_import_error(self) -> None:
        """Se APScheduler não estiver instalado, deve lançar ImportError."""
        import sys
        # Simula ausência da biblioteca
        with patch.dict(sys.modules, {"apscheduler": None,
                                       "apscheduler.schedulers": None,
                                       "apscheduler.schedulers.background": None,
                                       "apscheduler.triggers": None,
                                       "apscheduler.triggers.cron": None}):
            from importlib import reload
            import app.services.scheduler as sched_mod
            with pytest.raises(ImportError, match="APScheduler"):
                sched_mod.criar_scheduler()

    def test_criar_scheduler_retorna_objeto_com_jobs(self) -> None:
        """Scheduler criado deve ter exatamente 2 jobs registrados."""
        pytest.importorskip("apscheduler", reason="APScheduler não instalado")
        from app.services.scheduler import criar_scheduler

        scheduler = criar_scheduler()
        try:
            jobs = scheduler.get_jobs()
            assert len(jobs) == 2
            ids = {j.id for j in jobs}
            assert "ingestao_go_diaria" in ids
            assert "cobertura_go_semanal" in ids
        finally:
            scheduler.shutdown(wait=False)

    def test_jobs_tem_nomes_descritivos(self) -> None:
        """Jobs devem ter nomes legíveis."""
        pytest.importorskip("apscheduler", reason="APScheduler não instalado")
        from app.services.scheduler import criar_scheduler

        scheduler = criar_scheduler()
        try:
            nomes = {j.name for j in scheduler.get_jobs()}
            assert any("Goiás" in n for n in nomes)
            assert any("cobertura" in n.lower() for n in nomes)
        finally:
            scheduler.shutdown(wait=False)


class TestStatusScheduler:
    """Testa a função de status do scheduler."""

    def test_status_retorna_rodando_e_jobs(self) -> None:
        """status_scheduler deve retornar dict com 'rodando' e 'jobs'."""
        pytest.importorskip("apscheduler", reason="APScheduler não instalado")
        from app.services.scheduler import criar_scheduler, status_scheduler

        scheduler = criar_scheduler()
        scheduler.start()
        try:
            status = status_scheduler(scheduler)
            assert "rodando" in status
            assert "jobs" in status
            assert status["rodando"] is True
            assert len(status["jobs"]) == 2
        finally:
            scheduler.shutdown(wait=False)

    def test_cada_job_tem_proximo_disparo(self) -> None:
        """Cada job deve ter next_run_time quando o scheduler está rodando."""
        pytest.importorskip("apscheduler", reason="APScheduler não instalado")
        from app.services.scheduler import criar_scheduler, status_scheduler

        scheduler = criar_scheduler()
        scheduler.start()
        try:
            status = status_scheduler(scheduler)
            for job in status["jobs"]:
                assert "proximo_disparo" in job
                assert job["proximo_disparo"] is not None
        finally:
            scheduler.shutdown(wait=False)


class TestJobIngestaoGo:
    """Testa o job de ingestão GO de forma isolada."""

    def test_job_ingestao_go_trata_excecao(self) -> None:
        """_job_ingestao_go não deve propagar exceções."""
        from app.services.scheduler import _job_ingestao_go

        with patch("app.services.scheduler.PipelineMultiUF", side_effect=Exception("falha simulada")):
            # Não deve lançar exceção
            try:
                _job_ingestao_go()
            except Exception:
                pytest.fail("_job_ingestao_go propagou exceção — não deveria")

    def test_job_ingestao_go_usa_apenas_go(self) -> None:
        """O job deve invocar o pipeline apenas com UF='GO'."""
        from app.services.scheduler import _job_ingestao_go

        mock_pipeline = MagicMock()
        mock_relatorio = MagicMock()
        mock_relatorio.total_contratacoes = 0
        mock_relatorio.total_itens = 0
        mock_relatorio.ufs_com_falha = []
        mock_pipeline.return_value.executar.return_value = mock_relatorio

        with patch("app.services.scheduler.PipelineMultiUF", mock_pipeline):
            _job_ingestao_go()

        # Verifica que foi chamado com ufs=["GO"]
        mock_pipeline.assert_called_once_with(ufs=["GO"])


class TestJobCoberturaGo:
    """Testa o job de cobertura GO de forma isolada."""

    def test_job_cobertura_go_trata_excecao(self) -> None:
        """_job_cobertura_go não deve propagar exceções."""
        from app.services.scheduler import _job_cobertura_go

        with patch("app.services.scheduler.SessionLocal", side_effect=Exception("db down")):
            try:
                _job_cobertura_go()
            except Exception:
                pytest.fail("_job_cobertura_go propagou exceção — não deveria")
