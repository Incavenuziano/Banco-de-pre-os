"""Testes aprimorados de observabilidade — Semana 17."""

from __future__ import annotations

from app.services.observabilidade_service import ObservabilidadeService


class TestHealthCheckDetalhado:
    """Testes de health_check_detalhado()."""

    def setup_method(self) -> None:
        self.svc = ObservabilidadeService()

    def test_retorna_dict(self) -> None:
        r = self.svc.health_check_detalhado()
        assert isinstance(r, dict)

    def test_status_ok(self) -> None:
        r = self.svc.health_check_detalhado()
        assert r["status"] == "ok"

    def test_componentes_presentes(self) -> None:
        r = self.svc.health_check_detalhado()
        assert "database" in r["componentes"]
        assert "pgvector" in r["componentes"]
        assert "ibge_api" in r["componentes"]
        assert "filesystem" in r["componentes"]

    def test_uptime_positivo(self) -> None:
        r = self.svc.health_check_detalhado()
        assert r["uptime_segundos"] >= 0

    def test_versao(self) -> None:
        r = self.svc.health_check_detalhado()
        assert r["versao"] == "0.9.0"


class TestMetricasDetalhadas:
    """Testes de obter_metricas_detalhadas()."""

    def setup_method(self) -> None:
        self.svc = ObservabilidadeService()

    def test_retorna_dict(self) -> None:
        r = self.svc.obter_metricas_detalhadas()
        assert isinstance(r, dict)

    def test_p50_presente(self) -> None:
        r = self.svc.obter_metricas_detalhadas()
        assert "p50_ms" in r

    def test_p95_presente(self) -> None:
        r = self.svc.obter_metricas_detalhadas()
        assert "p95_ms" in r

    def test_total_requests(self) -> None:
        r = self.svc.obter_metricas_detalhadas()
        assert "total_requests" in r

    def test_p50_apos_consultas(self) -> None:
        self.svc.registrar_consulta(10.0, True)
        self.svc.registrar_consulta(20.0, True)
        self.svc.registrar_consulta(30.0, True)
        r = self.svc.obter_metricas_detalhadas()
        assert r["p50_ms"] > 0

    def test_p95_apos_consultas(self) -> None:
        for i in range(20):
            self.svc.registrar_consulta(float(i * 5), True)
        r = self.svc.obter_metricas_detalhadas()
        assert r["p95_ms"] >= r["p50_ms"]

    def test_total_requests_correto(self) -> None:
        self.svc.registrar_consulta(5.0, True)
        self.svc.registrar_consulta(10.0, True)
        r = self.svc.obter_metricas_detalhadas()
        assert r["total_requests"] == 2


class TestRegistrarErro:
    """Testes de registrar_erro()."""

    def setup_method(self) -> None:
        self.svc = ObservabilidadeService()

    def test_incrementa_erros_total(self) -> None:
        self.svc.registrar_erro("validation", "campo inválido")
        m = self.svc.obter_metricas()
        assert m["erros_total"] == 1

    def test_erros_por_tipo(self) -> None:
        self.svc.registrar_erro("validation", "campo x")
        self.svc.registrar_erro("timeout", "db lento")
        self.svc.registrar_erro("validation", "campo y")
        m = self.svc.obter_metricas()
        assert m["erros_por_tipo"]["validation"] == 2
        assert m["erros_por_tipo"]["timeout"] == 1

    def test_multiplos_tipos(self) -> None:
        self.svc.registrar_erro("auth", "token inválido")
        self.svc.registrar_erro("validation", "campo obrigatório")
        m = self.svc.obter_metricas()
        assert len(m["erros_por_tipo"]) == 2


class TestRegistrarConsulta:
    """Testes de registrar_consulta() e registrar_relatorio()."""

    def setup_method(self) -> None:
        self.svc = ObservabilidadeService()

    def test_incrementa_consultas(self) -> None:
        self.svc.registrar_consulta(5.0, True)
        m = self.svc.obter_metricas()
        assert m["consultas_total"] == 1

    def test_tempo_medio(self) -> None:
        self.svc.registrar_consulta(10.0, True)
        self.svc.registrar_consulta(20.0, True)
        m = self.svc.obter_metricas()
        assert m["tempo_medio_ms"] == 15.0

    def test_registrar_relatorio(self) -> None:
        self.svc.registrar_relatorio(50.0, True)
        m = self.svc.obter_metricas()
        assert m["relatorios_total"] == 1

    def test_erro_incrementa(self) -> None:
        self.svc.registrar_consulta(5.0, False)
        m = self.svc.obter_metricas()
        assert m["erros_total"] == 1
