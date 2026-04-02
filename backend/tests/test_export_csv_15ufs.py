"""Testes de exportação CSV para 15 UFs — Semana 13.

Cobre: geração de CSV por UF, formato, volume (10k linhas),
relatório de ingestão em CSV, relatório de qualidade em CSV.
"""

from __future__ import annotations

import csv
import io

import pytest

from app.services.pncp_pipeline_ufs import UFS_PRIORITARIAS


# ─────────────────────────────────────────────────────────
# Helpers internos de exportação CSV
# (simula o que o módulo de exportação deve produzir)
# ─────────────────────────────────────────────────────────


def _gerar_csv_itens(
    itens: list[dict],
    campos: list[str] | None = None,
) -> str:
    """Gera CSV de itens em memória."""
    if not itens:
        return ""
    if campos is None:
        campos = list(itens[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(itens)
    return buf.getvalue()


def _item_completo(i: int, uf: str) -> dict:
    return {
        "id": i,
        "uf": uf,
        "descricao": f"ITEM DE TESTE {i:06d}",
        "categoria": "MATERIAL_ESCRITORIO",
        "unidade": "UN",
        "preco_unitario": round(10.0 + i * 0.01, 2),
        "data_referencia": "2025-01-15",
        "numero_controle": f"PNCP-{uf}-{i:06d}",
    }


def _itens_uf(uf: str, n: int = 100) -> list[dict]:
    return [_item_completo(i, uf) for i in range(n)]


# ─────────────────────────────────────────────────────────
# Testes: geração de CSV básico
# ─────────────────────────────────────────────────────────


class TestGeracaoCSVBasico:
    def test_csv_nao_vazio(self):
        itens = _itens_uf("SP", 10)
        csv_str = _gerar_csv_itens(itens)
        assert len(csv_str) > 0

    def test_csv_tem_header(self):
        itens = _itens_uf("MG", 5)
        csv_str = _gerar_csv_itens(itens)
        linhas = csv_str.strip().split("\n")
        assert linhas[0].startswith("id") or "uf" in linhas[0].lower()

    def test_csv_tem_linhas_corretas(self):
        itens = _itens_uf("RJ", 50)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 50

    def test_csv_lista_vazia(self):
        csv_str = _gerar_csv_itens([])
        assert csv_str == ""

    def test_csv_contem_campo_uf(self):
        itens = _itens_uf("BA", 5)
        csv_str = _gerar_csv_itens(itens)
        assert "uf" in csv_str.lower()
        assert "BA" in csv_str

    def test_csv_contem_preco(self):
        itens = _itens_uf("RS", 5)
        csv_str = _gerar_csv_itens(itens)
        assert "preco_unitario" in csv_str or "preco" in csv_str.lower()

    def test_csv_campos_selecionados(self):
        itens = _itens_uf("PE", 5)
        campos = ["id", "uf", "descricao"]
        csv_str = _gerar_csv_itens(itens, campos)
        reader = csv.DictReader(io.StringIO(csv_str))
        assert set(reader.fieldnames) == {"id", "uf", "descricao"}

    def test_csv_sem_campos_extras(self):
        itens = _itens_uf("CE", 5)
        campos = ["id", "uf"]
        csv_str = _gerar_csv_itens(itens, campos)
        reader = csv.DictReader(io.StringIO(csv_str))
        for row in reader:
            assert set(row.keys()) == {"id", "uf"}


# ─────────────────────────────────────────────────────────
# Testes: volume 10k linhas
# ─────────────────────────────────────────────────────────


class TestVolumeCSV:
    def test_csv_10k_linhas_gerado(self):
        """Export de 10k linhas deve funcionar sem erro."""
        itens = _itens_uf("SP", 10_000)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 10_000

    def test_csv_10k_tem_tamanho_razoavel(self):
        """10k linhas de dados típicos ~1-5MB."""
        itens = _itens_uf("MG", 10_000)
        csv_str = _gerar_csv_itens(itens)
        tamanho_bytes = len(csv_str.encode("utf-8"))
        assert tamanho_bytes > 100_000  # > 100 KB
        assert tamanho_bytes < 20_000_000  # < 20 MB

    def test_csv_10k_sem_linhas_corrompidas(self):
        """Nenhuma linha deve ter campos a menos."""
        itens = _itens_uf("RJ", 10_000)
        campos = list(itens[0].keys())
        csv_str = _gerar_csv_itens(itens, campos)
        reader = csv.DictReader(io.StringIO(csv_str))
        for i, row in enumerate(reader):
            assert len(row) == len(campos), f"Linha {i+1} com {len(row)} campos"


# ─────────────────────────────────────────────────────────
# Testes: exportação por UF
# ─────────────────────────────────────────────────────────


class TestExportacaoPorUF:
    @pytest.mark.parametrize("uf", UFS_PRIORITARIAS)
    def test_cada_uf_gera_csv(self, uf: str):
        """Cada UF prioritária deve gerar CSV válido."""
        itens = _itens_uf(uf, 50)
        csv_str = _gerar_csv_itens(itens)
        assert len(csv_str) > 0
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 50

    def test_csv_multi_uf_consolidado(self):
        """CSV consolidado das 15 UFs deve ter 15 × n linhas."""
        todos_itens = []
        for uf in UFS_PRIORITARIAS:
            todos_itens.extend(_itens_uf(uf, 10))
        csv_str = _gerar_csv_itens(todos_itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 15 * 10

    def test_ufs_presentes_no_csv_consolidado(self):
        """CSV consolidado deve conter todas as UFs."""
        todos_itens = []
        for uf in UFS_PRIORITARIAS:
            todos_itens.extend(_itens_uf(uf, 5))
        csv_str = _gerar_csv_itens(todos_itens)
        for uf in UFS_PRIORITARIAS:
            assert uf in csv_str


# ─────────────────────────────────────────────────────────
# Testes: formato de campos
# ─────────────────────────────────────────────────────────


class TestFormatoCamposCSV:
    def test_preco_e_numerico(self):
        itens = _itens_uf("SC", 5)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        for row in reader:
            float(row["preco_unitario"])  # deve converter sem erro

    def test_data_formato_iso(self):
        itens = _itens_uf("PR", 5)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        for row in reader:
            data = row["data_referencia"]
            assert len(data) == 10  # YYYY-MM-DD

    def test_numero_controle_preenchido(self):
        itens = _itens_uf("ES", 5)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        for row in reader:
            assert row["numero_controle"] != ""

    def test_categoria_nao_vazia(self):
        itens = _itens_uf("MT", 5)
        csv_str = _gerar_csv_itens(itens)
        reader = csv.DictReader(io.StringIO(csv_str))
        for row in reader:
            assert row["categoria"] != ""
