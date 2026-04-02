"""Testes de ingestão para as 15 UFs prioritárias — Semana 13.

Cobre: JobIngestaoUF, PipelineMultiUF, RelatorioIngestionUFs,
validar_endpoints, retry/backoff, lag SLA.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.pncp_pipeline_ufs import (
    MAX_TENTATIVAS_UF,
    SLA_LAG_HORAS,
    JobIngestaoUF,
    PipelineMultiUF,
    RelatorioIngestionUFs,
    ResultadoUF,
    UFS_PRIORITARIAS,
)


# ─────────────────────────────────────────────────────────
# Fixtures / helpers
# ─────────────────────────────────────────────────────────


def _mock_conector_ok(n_contratacoes: int = 5, n_itens: int = 3) -> MagicMock:
    """Conector mock que retorna dados válidos."""
    conector = MagicMock()
    conector.buscar_contratacoes.return_value = {
        "data": [
            {
                "cnpjOrgao": f"0000000000{i:04d}",
                "anoCompra": 2025,
                "sequencialCompra": i + 1,  # evita sequencialCompra=0 (falsy)
            }
            for i in range(n_contratacoes)
        ],
        "totalRegistros": n_contratacoes,
    }
    conector.buscar_itens_contratacao.return_value = [{"descricao": f"Item {j}"} for j in range(n_itens)]
    return conector


def _mock_conector_vazio() -> MagicMock:
    """Conector mock que retorna lista vazia."""
    conector = MagicMock()
    conector.buscar_contratacoes.return_value = {"data": [], "totalRegistros": 0}
    conector.buscar_itens_contratacao.return_value = []
    return conector


def _mock_conector_falha() -> MagicMock:
    """Conector mock que sempre lança exceção."""
    conector = MagicMock()
    conector.buscar_contratacoes.side_effect = ConnectionError("Timeout PNCP")
    return conector


# ─────────────────────────────────────────────────────────
# Testes: UFS_PRIORITARIAS
# ─────────────────────────────────────────────────────────


class TestUFSPrioritarias:
    def test_total_15_ufs(self):
        assert len(UFS_PRIORITARIAS) == 15

    def test_ufs_obrigatorias_presentes(self):
        obrigatorias = ["SP", "MG", "RJ", "DF"]
        for uf in obrigatorias:
            assert uf in UFS_PRIORITARIAS, f"UF {uf} ausente"

    def test_todas_ufs_sao_siglas_2_chars(self):
        for uf in UFS_PRIORITARIAS:
            assert len(uf) == 2, f"UF inválida: {uf}"

    def test_sem_duplicatas(self):
        assert len(UFS_PRIORITARIAS) == len(set(UFS_PRIORITARIAS))


# ─────────────────────────────────────────────────────────
# Testes: ResultadoUF
# ─────────────────────────────────────────────────────────


class TestResultadoUF:
    def test_dentro_sla_sem_lag(self):
        r = ResultadoUF(uf="SP", sucesso=True, lag_estimado_horas=None)
        assert r.dentro_sla is True

    def test_dentro_sla_com_lag_ok(self):
        r = ResultadoUF(uf="MG", sucesso=True, lag_estimado_horas=3.0)
        assert r.dentro_sla is True

    def test_fora_sla_com_lag_alto(self):
        r = ResultadoUF(uf="RJ", sucesso=True, lag_estimado_horas=SLA_LAG_HORAS + 1)
        assert r.dentro_sla is False

    def test_lag_exatamente_sla(self):
        r = ResultadoUF(uf="BA", sucesso=True, lag_estimado_horas=float(SLA_LAG_HORAS))
        assert r.dentro_sla is True


# ─────────────────────────────────────────────────────────
# Testes: JobIngestaoUF
# ─────────────────────────────────────────────────────────


class TestJobIngestaoUF:
    def test_ingestao_bem_sucedida(self):
        conector = _mock_conector_ok(5, 3)
        job = JobIngestaoUF("SP", conector=conector)
        r = job.executar("20250101", "20250131")
        assert r.sucesso is True
        assert r.total_contratacoes == 5
        assert r.total_itens == 15  # 5 contratos × 3 itens

    def test_ingestao_vazia_sucesso(self):
        conector = _mock_conector_vazio()
        job = JobIngestaoUF("MG", conector=conector)
        r = job.executar("20250101", "20250131")
        assert r.sucesso is True
        assert r.total_contratacoes == 0

    def test_ingestao_falha_todas_tentativas(self):
        conector = _mock_conector_falha()
        job = JobIngestaoUF("RJ", conector=conector)
        with patch("time.sleep"):  # evita delay em testes
            r = job.executar("20250101", "20250131")
        assert r.sucesso is False
        assert r.tentativas == MAX_TENTATIVAS_UF

    def test_tentativas_registradas(self):
        conector = _mock_conector_ok()
        job = JobIngestaoUF("BA", conector=conector)
        r = job.executar("20250101", "20250131")
        assert r.tentativas >= 1

    def test_duracao_positiva(self):
        conector = _mock_conector_ok()
        job = JobIngestaoUF("RS", conector=conector)
        r = job.executar("20250101", "20250131")
        assert r.duracao_segundos >= 0

    def test_timestamps_registrados(self):
        conector = _mock_conector_ok()
        job = JobIngestaoUF("PE", conector=conector)
        r = job.executar("20250101", "20250131")
        assert r.timestamp_inicio != ""
        assert r.timestamp_fim != ""

    def test_lag_estimado_calculado(self):
        conector = _mock_conector_ok()
        job = JobIngestaoUF("CE", conector=conector)
        r = job.executar("20200101", "20200131")
        assert r.lag_estimado_horas is not None
        assert r.lag_estimado_horas > 0

    def test_erros_coletados_em_falha(self):
        conector = _mock_conector_falha()
        job = JobIngestaoUF("SC", conector=conector)
        with patch("time.sleep"):
            r = job.executar("20250101", "20250131")
        assert len(r.erros) > 0


# ─────────────────────────────────────────────────────────
# Testes: PipelineMultiUF
# ─────────────────────────────────────────────────────────


class TestPipelineMultiUF:
    def test_pipeline_executa_todas_ufs(self):
        conector = _mock_conector_ok(2, 1)
        pipeline = PipelineMultiUF(ufs=UFS_PRIORITARIAS, conector=conector)
        relatorio = pipeline.executar("20250101", "20250131")
        assert len(relatorio.resultados) == 15

    def test_pipeline_ufs_customizadas(self):
        conector = _mock_conector_ok(2, 1)
        pipeline = PipelineMultiUF(ufs=["SP", "MG"], conector=conector)
        relatorio = pipeline.executar("20250101", "20250131")
        assert len(relatorio.resultados) == 2

    def test_falha_em_uma_nao_impede_outras(self):
        """UF com falha não bloqueia demais UFs."""
        call_count = 0

        def conector_seletivo(uf, **kwargs):
            nonlocal call_count
            call_count += 1
            if uf == "SP":
                raise ConnectionError("Falha forçada SP")
            return {"data": [{"cnpjOrgao": "00000000000000", "anoCompra": 2025, "sequencialCompra": 1}], "totalRegistros": 1}

        conector = MagicMock()
        conector.buscar_contratacoes.side_effect = lambda uf, **kw: conector_seletivo(uf, **kw)
        conector.buscar_itens_contratacao.return_value = []

        with patch("time.sleep"):
            pipeline = PipelineMultiUF(ufs=["SP", "MG", "RJ"], conector=conector)
            relatorio = pipeline.executar("20250101", "20250131")

        ufs_sucesso = relatorio.ufs_com_sucesso
        ufs_falha = relatorio.ufs_com_falha
        assert "MG" in ufs_sucesso
        assert "RJ" in ufs_sucesso
        assert "SP" in ufs_falha

    def test_relatorio_total_itens(self):
        conector = _mock_conector_ok(3, 4)  # 3 contratos × 4 itens = 12 por UF
        pipeline = PipelineMultiUF(ufs=["SP", "MG"], conector=conector)
        relatorio = pipeline.executar("20250101", "20250131")
        assert relatorio.total_itens == 24  # 2 UFs × 12

    def test_relatorio_como_texto(self):
        conector = _mock_conector_ok(2, 2)
        pipeline = PipelineMultiUF(ufs=["SP", "MG"], conector=conector)
        relatorio = pipeline.executar("20250101", "20250131")
        texto = relatorio.como_texto()
        assert "RELATÓRIO DE INGESTÃO" in texto
        assert "SP" in texto
        assert "MG" in texto

    def test_validar_endpoints_ok(self):
        conector = _mock_conector_ok()
        pipeline = PipelineMultiUF(ufs=["SP", "MG"], conector=conector)
        disponibilidade = pipeline.validar_endpoints("20250101")
        assert disponibilidade["SP"] is True
        assert disponibilidade["MG"] is True

    def test_validar_endpoints_falha(self):
        conector = _mock_conector_falha()
        pipeline = PipelineMultiUF(ufs=["SP"], conector=conector)
        disponibilidade = pipeline.validar_endpoints("20250101")
        assert disponibilidade["SP"] is False


# ─────────────────────────────────────────────────────────
# Testes: RelatorioIngestionUFs
# ─────────────────────────────────────────────────────────


class TestRelatorioIngestionUFs:
    def _relatorio_com_resultados(self, n_ufs: int = 5, sucesso: bool = True) -> RelatorioIngestionUFs:
        r = RelatorioIngestionUFs(
            timestamp="2025-01-31T12:00:00",
            data_inicio="20250101",
            data_fim="20250131",
        )
        for i in range(n_ufs):
            r.resultados.append(
                ResultadoUF(
                    uf=UFS_PRIORITARIAS[i],
                    sucesso=sucesso,
                    total_contratacoes=10,
                    total_itens=30,
                    duracao_segundos=1.5,
                )
            )
        return r

    def test_ufs_com_sucesso(self):
        r = self._relatorio_com_resultados(3, sucesso=True)
        assert len(r.ufs_com_sucesso) == 3

    def test_ufs_com_falha(self):
        r = self._relatorio_com_resultados(3, sucesso=False)
        assert len(r.ufs_com_falha) == 3

    def test_total_itens_somado(self):
        r = self._relatorio_com_resultados(5)
        assert r.total_itens == 5 * 30

    def test_total_contratacoes_somado(self):
        r = self._relatorio_com_resultados(5)
        assert r.total_contratacoes == 5 * 10

    def test_como_texto_contem_headers(self):
        r = self._relatorio_com_resultados(3)
        texto = r.como_texto()
        assert "RELATÓRIO DE INGESTÃO" in texto
        assert "DETALHE POR UF" in texto
