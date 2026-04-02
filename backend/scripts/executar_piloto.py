#!/usr/bin/env python3
"""Script de execução do piloto controlado — Semana 7.

Executa ingestão focada em Santo Antônio do Descoberto (GO) e Anápolis (GO),
seleciona os 20 itens mais recorrentes por município e gera relatório PDF.

Uso:
    python3 backend/scripts/executar_piloto.py
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Adiciona diretório backend ao path para imports
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from app.services.pncp_conector import PNCPConector
from app.services.pipeline_piloto import PipelinePiloto


# Municípios-alvo do piloto
MUNICIPIOS_PILOTO: list[dict[str, str]] = [
    {"uf": "GO", "municipio": "Santo Antônio do Descoberto"},
    {"uf": "GO", "municipio": "Anápolis"},
]

OUTPUT_DIR = _BACKEND_DIR / "output"


def main() -> None:
    """Executa o pipeline piloto para os municípios-alvo."""
    # Período: últimos 90 dias
    hoje = date.today()
    data_fim = hoje.strftime("%Y%m%d")
    data_inicio = (hoje - timedelta(days=90)).strftime("%Y%m%d")

    print("=" * 60)
    print("BANCO DE PREÇOS — PILOTO CONTROLADO (Semana 7)")
    print(f"Período: {data_inicio} a {data_fim}")
    print("=" * 60)

    # Criar diretório de saída
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conector = PNCPConector()
    pipeline = PipelinePiloto(conector=conector)

    for mun in MUNICIPIOS_PILOTO:
        uf = mun["uf"]
        municipio = mun["municipio"]

        print(f"\n{'—' * 40}")
        print(f"Processando: {municipio}/{uf}")
        print(f"{'—' * 40}")

        resultado = pipeline.executar_municipio(
            uf=uf,
            municipio=municipio,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total_contratacoes = resultado["total_contratacoes"]
        total_itens = resultado["total_itens"]
        erros = resultado["erros"]

        print(f"  Contratações coletadas: {total_contratacoes}")
        print(f"  Itens processados: {total_itens}")
        if erros:
            print(f"  Erros: {len(erros)}")

        # Selecionar top 20 itens
        top_itens = pipeline.selecionar_top_itens(resultado["itens_processados"], n=20)

        if top_itens:
            print(f"\n  Top 5 itens mais recorrentes:")
            for i, item in enumerate(top_itens[:5], 1):
                desc = item["descricao_normalizada"][:50]
                cat = item["categoria"]
                ocorr = item["ocorrencias"]
                mediana = item["preco_mediano"]
                preco_str = f"R$ {mediana:,.2f}" if mediana else "N/D"
                print(f"    {i}. [{cat}] {desc} — {ocorr}x — {preco_str}")

            # Gerar relatório PDF
            try:
                pdf_bytes = pipeline.gerar_relatorio_piloto(municipio, uf, top_itens)
                nome_arquivo = f"relatorio_piloto_{municipio.replace(' ', '_')}_{hoje.isoformat()}.pdf"
                caminho_pdf = OUTPUT_DIR / nome_arquivo
                caminho_pdf.write_bytes(pdf_bytes)
                print(f"\n  PDF gerado: {caminho_pdf}")
            except Exception as exc:
                print(f"\n  Erro ao gerar PDF: {exc}")
        else:
            print("\n  Nenhum item encontrado para este município.")

    print(f"\n{'=' * 60}")
    print("Piloto concluído.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
