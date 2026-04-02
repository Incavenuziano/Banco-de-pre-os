"""Serviço de análise de preços: tendências, comparativo por UF e categorias.

Semana 14 — Integração com Plataforma de Análise & Dashboard.
Semana 21 — Reescrito para consultar banco de dados (fontes_preco + categorias).
"""

from __future__ import annotations

import csv
import io
import statistics
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

# UFs suportadas
UFS_VALIDADAS = [
    "AC", "AL", "AM", "BA", "CE",
    "DF", "GO", "MA", "MG", "MS",
    "MT", "PA", "PE", "PR", "RJ",
    "RS", "SC", "SE", "SP", "TO",
    "PI", "RO", "RR",
]

# Categorias — mantidas para compatibilidade com imports externos (ex: backup_service)
CATEGORIAS = [
    "Água Mineral",
    "Armário / Arquivo",
    "Câmera de Segurança (CFTV)",
    "Cartucho / Toner",
    "Cesta Básica",
    "Cimento / Areia / Brita",
    "Combustível (Gasolina / Etanol / Diesel)",
    "Computador Desktop",
    "Drone / UAV",
    "DVR / NVR",
    "Envelopes e Formulários",
    "EPI (Equipamento de Proteção Individual)",
    "Equipamento Odontológico",
    "Gás de Cozinha (GLP)",
    "Gêneros Alimentícios (Merenda Escolar)",
    "Impressora",
    "Instrumento Musical",
    "Kit de Primeiros Socorros",
    "Material de Expediente Geral",
    "Material de Limpeza Geral",
    "Material Elétrico",
    "Material Esportivo",
    "Material Hidráulico",
    "Material Hospitalar / Descartáveis Médicos",
    "Medicamentos Básicos (OTC)",
    "Mesa / Cadeira de Escritório",
    "Mobiliário Escolar",
    "Nobreak / UPS",
    "Notebook / Laptop",
    "Papel Higiênico",
    "Papel A4",
    "Peças e Acessórios para Veículos",
    "Pneu / Câmara de Ar",
    "Projetor Multimídia",
    "Sabonete / Álcool em Gel",
    "Saco de Lixo",
    "Serviço de Dedetização / Controle de Pragas",
    "Serviço de Impressão / Reprografia",
    "Serviço de Limpeza e Conservação",
    "Serviço de Manutenção Predial",
    "Serviço de Telefonia / Internet",
    "Serviço de TI / Suporte",
    "Serviço de Transporte Escolar",
    "Serviço de Vigilância / Portaria",
    "Software / Sistema de Informação",
    "Switch / Roteador",
    "Tablet",
    "Tela Interativa / Lousa Digital",
    "Tintas e Vernizes",
    "Uniforme Funcional",
]


def _variacao_mensal(base: float, mes: int, ano: int, seed: int) -> float:
    """Gera variação de preço determinística (mantida para compatibilidade de testes)."""
    fator = 1.0 + ((((seed * mes + ano) % 11) - 5) / 100.0)
    return round(base * fator, 4)


def _get_session() -> Session:
    """Cria sessão direta do banco."""
    return SessionLocal()


class AnaliseService:
    """Serviço de análise de preços consultando o banco de dados."""

    # ------------------------------------------------------------------ #
    #  listar_precos                                                        #
    # ------------------------------------------------------------------ #
    def listar_precos(
        self,
        uf: str | None = None,
        categoria: str | None = None,
        municipio: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
        pagina: int = 1,
        por_pagina: int = 20,
        ordenar_por: str = "data",   # "data" | "preco"
        ordem: str = "desc",         # "asc" | "desc"
    ) -> dict[str, Any]:
        """Lista preços com filtros avançados e paginação.

        Combina via UNION:
        - Fonte A: tabela fontes_preco (dados seed/pipeline processado)
        - Fonte B: itens PNCP diretos sem fontes_preco (dados coletados pelo coletor_municipal)

        Isso garante que todos os dados coletados apareçam na listagem
        independentemente do estágio de processamento.
        """
        # Sanitizar parâmetros de ordenação (sem interpolação direta)
        # Nota: aliases do UNION — data_referencia = ct.data_publicacao, preco_unitario
        campo_ord = "data_referencia" if ordenar_por == "data" else "preco_unitario"
        dir_ord = "ASC" if ordem == "asc" else "DESC"

        db = _get_session()
        try:
            params: dict[str, Any] = {}

            # ── Fonte A: fontes_preco processadas ──────────────────────────
            sql_a = """
                SELECT
                    fp.id::text              AS id,
                    COALESCE(fp.uf, o.uf)    AS uf,
                    c.nome                   AS categoria,
                    COALESCE(
                        NULLIF(TRIM(
                            REGEXP_REPLACE(i.descricao, '^\\[SEED\\]\\s*', '', 'i')
                        ), ''),
                        NULLIF(TRIM(ct.objeto), ''),
                        '—'
                    )                        AS descricao,
                    fp.preco_unitario        AS preco_unitario,
                    fp.unidade_normalizada   AS unidade,
                    ct.data_publicacao       AS data_referencia,
                    o.razao_social           AS orgao,
                    fp.score_confianca       AS score_confianca,
                    ct.numero_controle_pncp  AS numero_controle_pncp
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN contratacoes ct  ON i.contratacao_id = ct.id
                JOIN orgaos o         ON ct.orgao_id      = o.id
                LEFT JOIN item_categoria ic ON i.id        = ic.item_id
                LEFT JOIN categorias c      ON ic.categoria_id = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                  AND fp.preco_unitario IS NOT NULL
                  AND fp.preco_unitario > 0
                  AND ct.numero_controle_pncp ~ '^[0-9]{14}-'
            """

            # ── Fonte B: itens PNCP diretos (sem fontes_preco) ─────────────
            sql_b = """
                SELECT
                    i.id::text               AS id,
                    o.uf                     AS uf,
                    NULL::text               AS categoria,
                    COALESCE(
                        NULLIF(TRIM(
                            REGEXP_REPLACE(i.descricao, '^\\[SEED\\]\\s*', '', 'i')
                        ), ''),
                        NULLIF(TRIM(ct.objeto), ''),
                        '—'
                    )                        AS descricao,
                    i.valor_unitario         AS preco_unitario,
                    i.unidade                AS unidade,
                    ct.data_publicacao       AS data_referencia,
                    o.razao_social           AS orgao,
                    0.75::numeric            AS score_confianca,
                    ct.numero_controle_pncp  AS numero_controle_pncp
                FROM itens i
                JOIN contratacoes ct ON i.contratacao_id = ct.id
                JOIN orgaos o        ON ct.orgao_id      = o.id
                WHERE i.valor_unitario IS NOT NULL
                  AND i.valor_unitario > 0
                  AND ct.numero_controle_pncp ~ '^[0-9]{14}-'
                  AND NOT EXISTS (
                      SELECT 1 FROM fontes_preco fp WHERE fp.item_id = i.id
                  )
            """

            # Filtros — aplicados no UNION completo
            filtros_a: list[str] = []
            filtros_b: list[str] = []

            if uf:
                filtros_a.append("COALESCE(fp.uf, o.uf) = :uf")
                filtros_b.append("o.uf = :uf")
                params["uf"] = uf.upper()

            if categoria:
                filtros_a.append("c.nome ILIKE :categoria")
                # Fonte B não tem categoria — filtrar por descrição
                filtros_b.append("i.descricao ILIKE :categoria")
                params["categoria"] = f"%{categoria}%"

            if data_inicio:
                filtros_a.append("COALESCE(ct.data_publicacao, fp.data_referencia) >= :data_inicio")
                filtros_b.append("ct.data_publicacao >= :data_inicio")
                params["data_inicio"] = data_inicio

            if data_fim:
                filtros_a.append("COALESCE(ct.data_publicacao, fp.data_referencia) <= :data_fim")
                filtros_b.append("ct.data_publicacao <= :data_fim")
                params["data_fim"] = data_fim

            if preco_min is not None:
                filtros_a.append("fp.preco_unitario >= :preco_min")
                filtros_b.append("i.valor_unitario >= :preco_min")
                params["preco_min"] = preco_min

            if preco_max is not None:
                filtros_a.append("fp.preco_unitario <= :preco_max")
                filtros_b.append("i.valor_unitario <= :preco_max")
                params["preco_max"] = preco_max

            if municipio:
                filtros_a.append("o.municipio ILIKE :municipio")
                filtros_b.append("o.municipio ILIKE :municipio")
                params["municipio"] = f"%{municipio}%"

            if filtros_a:
                sql_a += " AND " + " AND ".join(filtros_a)
            if filtros_b:
                sql_b += " AND " + " AND ".join(filtros_b)

            union_sql = f"({sql_a}) UNION ALL ({sql_b})"

            # Total
            total = db.execute(text(f"SELECT COUNT(*) FROM ({union_sql}) sub"), params).scalar() or 0

            # Ordenação + paginação
            # id como desempate garante paginação estável mesmo com valores iguais
            offset = (pagina - 1) * por_pagina
            final_sql = (
                f"SELECT * FROM ({union_sql}) dados "
                f"ORDER BY {campo_ord} {dir_ord} NULLS LAST, id ASC "
                f"LIMIT :limit OFFSET :offset"
            )
            params["limit"] = por_pagina
            params["offset"] = offset

            rows = db.execute(text(final_sql), params).fetchall()

            itens: list[dict] = []
            for r in rows:
                score = float(r.score_confianca) if r.score_confianca else 0.75
                confianca = "ALTA" if score >= 0.8 else ("MEDIA" if score >= 0.5 else "BAIXA")
                numero_controle = getattr(r, "numero_controle_pncp", None) or ""
                # Formato: CNPJ-codigoUnidade-SEQUENCIAL/ANO → /app/editais/CNPJ/ANO/SEQUENCIAL
                pncp_url = ""
                if numero_controle:
                    try:
                        # Ex: "26868133000178-1-000018/2026"
                        partes = numero_controle.split("-")
                        cnpj_part = partes[0]
                        seq_ano = partes[-1]  # "000018/2026"
                        seq, ano = seq_ano.split("/")
                        seq_int = int(seq)  # remove zeros à esquerda
                        pncp_url = f"https://pncp.gov.br/app/editais/{cnpj_part}/{ano}/{seq_int}"
                    except Exception:
                        pncp_url = f"https://pncp.gov.br/app/editais/{numero_controle}"
                # Descrição: truncar em 300 chars para exibição limpa
                descricao_raw = r.descricao or ""
                # Pegar apenas a parte antes do primeiro "-" se for muito longa
                descricao_exib = descricao_raw[:300].strip()

                data_ref = r.data_referencia
                data_str = data_ref.isoformat() if data_ref else ""

                itens.append({
                    "id": r.id,
                    "uf": r.uf or "",
                    "categoria": r.categoria or "—",
                    "descricao": descricao_exib,
                    "preco_unitario": round(float(r.preco_unitario), 4),
                    "unidade": r.unidade or "UN",
                    "data_referencia": data_str,
                    "orgao": r.orgao or "",
                    "confianca": confianca,
                    "numero_controle_pncp": numero_controle,
                    "pncp_url": pncp_url,
                })

            return {
                "itens": itens,
                "total": total,
                "pagina": pagina,
                "por_pagina": por_pagina,
                "total_paginas": max(1, (total + por_pagina - 1) // por_pagina),
                "filtros_aplicados": {
                    "uf": uf,
                    "categoria": categoria,
                    "data_inicio": data_inicio,
                    "data_fim": data_fim,
                    "preco_min": preco_min,
                    "preco_max": preco_max,
                    "ordenar_por": ordenar_por,
                    "ordem": ordem,
                },
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  obter_tendencias                                                    #
    # ------------------------------------------------------------------ #
    def obter_tendencias(
        self,
        categoria: str,
        ufs: list[str] | None = None,
        meses: int = 6,
    ) -> dict[str, Any]:
        """Retorna tendências de preço mensal por categoria e UF."""
        db = _get_session()
        try:
            ufs_alvo = ufs if ufs else ["SP", "RJ", "MG", "BA", "RS"]
            ufs_placeholder = ", ".join(f":uf{i}" for i in range(len(ufs_alvo)))
            params: dict[str, Any] = {"categoria": f"%{categoria}%", "meses": meses}
            for i, u in enumerate(ufs_alvo):
                params[f"uf{i}"] = u.upper()

            sql = f"""
                SELECT
                    fp.uf,
                    TO_CHAR(fp.data_referencia, 'YYYY-MM') AS periodo,
                    AVG(fp.preco_unitario)                  AS preco_medio
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN item_categoria ic ON i.id             = ic.item_id
                JOIN categorias c     ON ic.categoria_id  = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                  AND c.nome ILIKE :categoria
                  AND fp.uf IN ({ufs_placeholder})
                  AND fp.data_referencia >= CURRENT_DATE - INTERVAL '1 month' * :meses
                GROUP BY fp.uf, periodo
                ORDER BY fp.uf, periodo
            """

            rows = db.execute(text(sql), params).fetchall()

            # Organizar por UF
            serie: dict[str, list[dict]] = {uf: [] for uf in ufs_alvo}
            for r in rows:
                uf_key = r.uf
                if uf_key in serie:
                    serie[uf_key].append({
                        "periodo": r.periodo,
                        "preco": round(float(r.preco_medio), 4),
                    })

            # Calcular variação por UF
            resumo_ufs: dict[str, dict] = {}
            for uf_key, pontos in serie.items():
                if pontos:
                    precos = [p["preco"] for p in pontos]
                    var_total = round(((precos[-1] - precos[0]) / precos[0]) * 100, 2) if len(precos) >= 2 else 0.0
                    tendencia = "ALTA" if var_total > 2 else ("QUEDA" if var_total < -2 else "ESTAVEL")
                    resumo_ufs[uf_key] = {
                        "preco_atual": precos[-1],
                        "preco_inicial": precos[0],
                        "variacao_total_pct": var_total,
                        "tendencia": tendencia,
                        "minimo": min(precos),
                        "maximo": max(precos),
                    }
                # UFs sem dados são omitidas do resumo_por_uf

            # Enriquecer pontos com variação_%
            for uf_key, pontos in serie.items():
                if pontos:
                    base = pontos[0]["preco"]
                    for p in pontos:
                        p["variacao_pct"] = round(((p["preco"] - base) / base) * 100, 2) if base > 0 else 0.0

            todos_precos = [p["preco"] for pts in serie.values() for p in pts]
            media_geral = round(statistics.mean(todos_precos), 4) if todos_precos else 0.0

            hoje = date.today()
            return {
                "categoria": categoria,
                "ufs_analisadas": ufs_alvo,
                "meses": meses,
                "serie_temporal": serie,
                "resumo_por_uf": resumo_ufs,
                "media_geral": media_geral,
                "periodo_inicio": (hoje - timedelta(days=(meses - 1) * 30)).strftime("%Y-%m"),
                "periodo_fim": hoje.strftime("%Y-%m"),
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  obter_comparativo_ufs                                               #
    # ------------------------------------------------------------------ #
    def obter_comparativo_ufs(
        self,
        categoria: str,
        ufs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compara preços de uma categoria entre múltiplas UFs."""
        db = _get_session()
        try:
            ufs_alvo = ufs if ufs else UFS_VALIDADAS
            ufs_placeholder = ", ".join(f":uf{i}" for i in range(len(ufs_alvo)))
            params: dict[str, Any] = {"categoria": f"%{categoria}%"}
            for i, u in enumerate(ufs_alvo):
                params[f"uf{i}"] = u.upper()

            sql = f"""
                SELECT
                    fp.uf,
                    AVG(fp.preco_unitario) AS preco_medio,
                    MIN(fp.preco_unitario) AS preco_min,
                    MAX(fp.preco_unitario) AS preco_max,
                    COUNT(*)               AS n_registros
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN item_categoria ic ON i.id             = ic.item_id
                JOIN categorias c     ON ic.categoria_id  = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                  AND c.nome ILIKE :categoria
                  AND fp.uf IN ({ufs_placeholder})
                GROUP BY fp.uf
                ORDER BY preco_medio ASC
            """

            rows = db.execute(text(sql), params).fetchall()

            comparativo: list[dict] = []
            for r in rows:
                comparativo.append({
                    "uf": r.uf,
                    "preco_base": round(float(r.preco_medio), 4),
                    "preco_atual": round(float(r.preco_medio), 4),
                    "preco_min": round(float(r.preco_min), 4),
                    "preco_max": round(float(r.preco_max), 4),
                    "n_registros": r.n_registros,
                    "variacao_pct": 0.0,
                })

            precos = [c["preco_atual"] for c in comparativo]
            media = round(statistics.mean(precos), 4) if precos else 0.0
            mediana = round(statistics.median(precos), 4) if precos else 0.0
            desvio = round(statistics.stdev(precos), 4) if len(precos) >= 2 else 0.0

            for i, item in enumerate(comparativo):
                item["rank"] = i + 1
                item["diferenca_media_pct"] = (
                    round(((item["preco_atual"] - media) / media) * 100, 2) if media > 0 else 0.0
                )

            return {
                "categoria": categoria,
                "ufs_analisadas": [c["uf"] for c in comparativo],
                "comparativo": comparativo,
                "estatisticas": {
                    "media": media,
                    "mediana": mediana,
                    "desvio_padrao": desvio,
                    "minimo": min(precos) if precos else 0.0,
                    "maximo": max(precos) if precos else 0.0,
                    "uf_mais_barata": comparativo[0]["uf"] if comparativo else None,
                    "uf_mais_cara": comparativo[-1]["uf"] if comparativo else None,
                },
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  obter_resumo_dashboard                                              #
    # ------------------------------------------------------------------ #
    def obter_resumo_dashboard(
        self,
        ufs: list[str] | None = None,
        categoria: str | None = None,
    ) -> dict[str, Any]:
        """Retorna resumo agregado para o dashboard principal."""
        db = _get_session()
        try:
            params: dict[str, Any] = {}
            uf_filter = ""
            cat_filter = ""

            if ufs:
                ufs_ph = ", ".join(f":uf{i}" for i in range(len(ufs)))
                uf_filter = f" AND fp.uf IN ({ufs_ph})"
                for i, u in enumerate(ufs):
                    params[f"uf{i}"] = u.upper()

            if categoria:
                cat_filter = " AND c.nome ILIKE :categoria"
                params["categoria"] = f"%{categoria}%"

            # KPIs gerais
            kpi_sql = f"""
                SELECT
                    COUNT(DISTINCT fp.id)   AS total_registros,
                    COUNT(DISTINCT c.id)    AS total_categorias,
                    COUNT(DISTINCT fp.uf)   AS total_ufs,
                    MAX(fp.data_referencia) AS ultima_atualizacao
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN item_categoria ic ON i.id             = ic.item_id
                JOIN categorias c     ON ic.categoria_id  = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                {uf_filter}
                {cat_filter}
            """
            kpi_row = db.execute(text(kpi_sql), params).fetchone()

            total_registros = kpi_row.total_registros or 0
            total_categorias = kpi_row.total_categorias or 0
            total_ufs_db = kpi_row.total_ufs or 0
            ultima_att = kpi_row.ultima_atualizacao

            # KPIs por UF
            kpi_uf_sql = f"""
                SELECT
                    fp.uf,
                    COUNT(fp.id)            AS total_itens,
                    AVG(fp.preco_unitario)  AS media_preco,
                    MAX(fp.data_referencia) AS ultima_atualizacao
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN item_categoria ic ON i.id             = ic.item_id
                JOIN categorias c     ON ic.categoria_id  = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                {uf_filter}
                {cat_filter}
                GROUP BY fp.uf
                ORDER BY fp.uf
            """
            uf_rows = db.execute(text(kpi_uf_sql), params).fetchall()
            kpis_por_uf = [
                {
                    "uf": r.uf,
                    "total_itens": r.total_itens,
                    "media_preco": round(float(r.media_preco), 2),
                    "ultima_atualizacao": r.ultima_atualizacao.isoformat() if r.ultima_atualizacao else date.today().isoformat(),
                }
                for r in uf_rows
            ]

            # Top 5 categorias
            top_sql = f"""
                SELECT
                    c.nome,
                    COUNT(fp.id) AS n_registros
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id       = i.id
                JOIN item_categoria ic ON i.id             = ic.item_id
                JOIN categorias c     ON ic.categoria_id  = c.id
                WHERE fp.ativo = true
                  AND fp.outlier_flag = false
                {uf_filter}
                {cat_filter}
                GROUP BY c.nome
                ORDER BY n_registros DESC
                LIMIT 5
            """
            top_rows = db.execute(text(top_sql), params).fetchall()
            top_categorias = [
                {"categoria": r.nome, "n_registros": r.n_registros}
                for r in top_rows
            ]

            ufs_cobertas = [r["uf"] for r in kpis_por_uf]

            return {
                "kpis": {
                    "total_registros": total_registros,
                    "total_categorias": total_categorias,
                    "total_ufs": total_ufs_db,
                    "ultima_atualizacao": ultima_att.isoformat() if ultima_att else date.today().isoformat(),
                    "cobertura_pct": round(total_ufs_db / 27 * 100, 1),
                },
                "kpis_por_uf": kpis_por_uf,
                "top_categorias": top_categorias,
                "ufs_cobertas": ufs_cobertas,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  exportar_csv                                                        #
    # ------------------------------------------------------------------ #
    def exportar_csv(
        self,
        uf: str | None = None,
        categoria: str | None = None,
        municipio: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> bytes:
        """Gera CSV com todos os preços filtrados (UTF-8 BOM para Excel)."""
        resultado = self.listar_precos(
            uf=uf,
            categoria=categoria,
            municipio=municipio,
            data_inicio=data_inicio,
            data_fim=data_fim,
            preco_min=preco_min,
            preco_max=preco_max,
            pagina=1,
            por_pagina=10000,
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            "ID", "UF", "Categoria", "Descrição",
            "Preço Unitário", "Unidade", "Data Referência",
            "Órgão", "Confiança",
        ])
        for item in resultado["itens"]:
            writer.writerow([
                item["id"],
                item["uf"],
                item["categoria"],
                item["descricao"],
                f"{item['preco_unitario']:.2f}",
                item["unidade"],
                item["data_referencia"],
                item["orgao"],
                item["confianca"],
            ])

        csv_str = buffer.getvalue()
        buffer.close()
        return b"\xef\xbb\xbf" + csv_str.encode("utf-8")

    # ------------------------------------------------------------------ #
    #  listar_categorias / listar_ufs                                      #
    # ------------------------------------------------------------------ #
    def listar_categorias(self) -> list[dict[str, Any]]:
        """Lista categorias disponíveis no banco com contagem de registros."""
        db = _get_session()
        try:
            sql = """
                SELECT
                    c.nome,
                    COUNT(DISTINCT fp.uf)  AS n_ufs,
                    COUNT(fp.id)           AS n_registros,
                    MAX(fp.data_referencia) AS ultima_atualizacao
                FROM categorias c
                LEFT JOIN item_categoria ic ON c.id = ic.categoria_id
                LEFT JOIN itens i           ON ic.item_id = i.id
                LEFT JOIN fontes_preco fp   ON fp.item_id = i.id AND fp.ativo = true
                GROUP BY c.nome
                ORDER BY c.nome
            """
            rows = db.execute(text(sql)).fetchall()
            return [
                {
                    "nome": r.nome,
                    "n_ufs": r.n_ufs or 0,
                    "n_registros": r.n_registros or 0,
                    "ultima_atualizacao": r.ultima_atualizacao.isoformat() if r.ultima_atualizacao else date.today().isoformat(),
                }
                for r in rows
            ]
        finally:
            db.close()

    def listar_municipios(self, uf: str | None = None) -> list[dict[str, Any]]:
        """Lista municípios disponíveis no banco."""
        db = _get_session()
        try:
            sql = """
                SELECT DISTINCT o.municipio, o.uf
                FROM orgaos o
                JOIN contratacoes ct ON ct.orgao_id = o.id
                WHERE o.municipio IS NOT NULL
                  AND ct.objeto NOT LIKE '[SEED]%%'
            """
            params: dict[str, Any] = {}
            if uf:
                sql += " AND o.uf = :uf"
                params["uf"] = uf.upper()
            sql += " ORDER BY o.municipio"
            rows = db.execute(text(sql), params).fetchall()
            return [{"municipio": r.municipio, "uf": r.uf} for r in rows]
        finally:
            db.close()

    def listar_ufs(self) -> list[dict[str, Any]]:
        """Lista UFs com dados no banco e contagem de registros."""
        db = _get_session()
        try:
            sql = """
                SELECT
                    fp.uf,
                    COUNT(DISTINCT ic.categoria_id) AS n_categorias,
                    COUNT(fp.id)                    AS n_registros,
                    'VALIDADA'                      AS status
                FROM fontes_preco fp
                JOIN itens i          ON fp.item_id = i.id
                JOIN item_categoria ic ON i.id = ic.item_id
                WHERE fp.ativo = true
                GROUP BY fp.uf
                ORDER BY fp.uf
            """
            rows = db.execute(text(sql)).fetchall()
            return [
                {
                    "uf": r.uf,
                    "n_categorias": r.n_categorias or 0,
                    "n_registros": r.n_registros or 0,
                    "status": r.status,
                }
                for r in rows
            ]
        finally:
            db.close()
