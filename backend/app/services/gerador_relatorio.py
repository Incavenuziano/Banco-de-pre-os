"""Serviço de geração de relatório PDF e CSV/XLSX de pesquisa de preços."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

if TYPE_CHECKING:
    from app.schemas.relatorios import RelatorioInput


# Cores padrão do relatório
AZUL_ESCURO = colors.HexColor("#1a3c5e")
CINZA_CLARO = colors.HexColor("#f2f2f2")
VERMELHO_CLARO = colors.HexColor("#ffe0e0")
CINZA_TEXTO = colors.HexColor("#666666")


class GeradorRelatorio:
    """Gera relatórios PDF de pesquisa de preços conforme IN SEGES/ME nº 65/2021."""

    def __init__(self) -> None:
        """Inicializa estilos do relatório."""
        self._styles = getSampleStyleSheet()
        self._titulo_style = ParagraphStyle(
            "Titulo",
            parent=self._styles["Title"],
            fontSize=16,
            alignment=1,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
        self._subtitulo_style = ParagraphStyle(
            "Subtitulo",
            parent=self._styles["Normal"],
            fontSize=9,
            alignment=1,
            textColor=CINZA_TEXTO,
            spaceAfter=12,
        )
        self._bloco_titulo_style = ParagraphStyle(
            "BlocoTitulo",
            parent=self._styles["Heading2"],
            fontSize=12,
            fontName="Helvetica-Bold",
            spaceAfter=6,
            spaceBefore=12,
            textColor=AZUL_ESCURO,
        )
        self._campo_style = ParagraphStyle(
            "Campo",
            parent=self._styles["Normal"],
            fontSize=10,
            spaceAfter=2,
        )
        self._destaque_style = ParagraphStyle(
            "Destaque",
            parent=self._styles["Normal"],
            fontSize=14,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        self._rodape_style = ParagraphStyle(
            "Rodape",
            parent=self._styles["Normal"],
            fontSize=8,
            textColor=CINZA_TEXTO,
            spaceAfter=4,
        )

    def gerar(self, dados: RelatorioInput) -> bytes:
        """Gera o relatório PDF e retorna como bytes.

        Args:
            dados: Dados de entrada do relatório.

        Returns:
            Conteúdo do PDF em bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        elementos: list = []
        self._adicionar_cabecalho(elementos)
        self._adicionar_dados_solicitacao(elementos, dados)
        self._adicionar_estatisticas(elementos, dados)
        self._adicionar_preco_referencial(elementos, dados)
        self._adicionar_qualidade_dados(elementos, dados)
        self._adicionar_conformidade_in65(elementos, dados)
        self._adicionar_correcao_ipca(elementos, dados)
        self._adicionar_benchmark_regional(elementos, dados)
        self._adicionar_alertas_sobrepreco(elementos, dados)
        if dados.amostras:
            self._adicionar_tabela_amostras(elementos, dados)
        self._adicionar_rodape(elementos)

        doc.build(elementos, onFirstPage=self._rodape_pagina, onLaterPages=self._rodape_pagina)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _adicionar_cabecalho(self, elementos: list) -> None:
        """Adiciona cabeçalho com título e subtítulo ao relatório."""
        elementos.append(Paragraph("PESQUISA DE PREÇOS", self._titulo_style))
        elementos.append(
            Paragraph(
                "Elaborado conforme art. 23 da Lei nº 14.133/2021 e IN SEGES/ME nº 65/2021",
                self._subtitulo_style,
            )
        )
        # Linha separadora
        linha = Table([[""]],  colWidths=[16.5 * cm], rowHeights=[1])
        linha.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1, AZUL_ESCURO),
        ]))
        elementos.append(linha)
        elementos.append(Spacer(1, 12))

    def _adicionar_dados_solicitacao(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona bloco de dados da solicitação."""
        elementos.append(Paragraph("DADOS DA SOLICITAÇÃO", self._bloco_titulo_style))

        campos = [
            ("Órgão", dados.orgao_nome),
            ("CNPJ", dados.orgao_cnpj or "Não informado"),
            ("Item", dados.item_descricao),
            ("Categoria", dados.categoria_nome or "Não classificado"),
            ("Período", f"{dados.periodo_inicio} a {dados.periodo_fim}"),
            ("UF Filtro", dados.uf_filtro or "Todas"),
            ("ID Relatório", dados.id_relatorio),
            ("Data Emissão", dados.emitido_em),
        ]
        for label, valor in campos:
            elementos.append(
                Paragraph(f"<b>{label}:</b> {valor}", self._campo_style)
            )
        elementos.append(Spacer(1, 8))

    def _adicionar_estatisticas(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona bloco de estatísticas descritivas."""
        elementos.append(Paragraph("ESTATÍSTICAS", self._bloco_titulo_style))

        est = dados.estatisticas
        campos = [
            ("Mediana", self._formatar_valor(est.get("mediana"))),
            ("Média", self._formatar_valor(est.get("media"))),
            ("Desvio Padrão", self._formatar_valor(est.get("desvio_padrao"))),
            ("Q1", self._formatar_valor(est.get("q1"))),
            ("Q3", self._formatar_valor(est.get("q3"))),
            ("Nº Amostras", str(est.get("n", len(dados.amostras)))),
            ("Outliers Excluídos", str(dados.n_outliers_excluidos)),
            ("Confiança", dados.confianca),
        ]
        for label, valor in campos:
            elementos.append(
                Paragraph(f"<b>{label}:</b> {valor}", self._campo_style)
            )
        elementos.append(Spacer(1, 8))

    def _adicionar_preco_referencial(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona bloco do preço referencial recomendado."""
        elementos.append(
            Paragraph("PREÇO REFERENCIAL RECOMENDADO", self._bloco_titulo_style)
        )

        if dados.preco_referencial is not None:
            valor_str = f"R$ {dados.preco_referencial:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            valor_str = "Não disponível (dados insuficientes)"

        elementos.append(Paragraph(valor_str, self._destaque_style))
        elementos.append(
            Paragraph(f"<b>Nível de Confiança:</b> {dados.confianca}", self._campo_style)
        )
        elementos.append(Spacer(1, 8))

    def _adicionar_tabela_amostras(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona tabela com as amostras de preço."""
        elementos.append(Paragraph("AMOSTRAS DE PREÇO", self._bloco_titulo_style))

        cabecalho = ["Nº Controle", "Órgão", "Data", "Preço Unit.", "Unidade", "UF", "Qualidade", "Outlier"]
        linhas = [cabecalho]

        for a in dados.amostras:
            preco_fmt = f"R$ {a.preco_unitario:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            linhas.append([
                a.numero_controle or "-",
                self._truncar(a.orgao_origem or "-", 25),
                a.data_referencia or "-",
                preco_fmt,
                a.unidade or "-",
                a.uf or "-",
                a.qualidade or "-",
                "Sim" if a.outlier else "Não",
            ])

        col_widths = [1.5 * cm, 3.5 * cm, 2 * cm, 2.2 * cm, 1.5 * cm, 1 * cm, 2.3 * cm, 1.2 * cm]
        tabela = Table(linhas, colWidths=col_widths, repeatRows=1)

        estilo = [
            # Cabeçalho
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        # Linhas alternadas cinza/branco
        for i in range(1, len(linhas)):
            if i % 2 == 0:
                estilo.append(("BACKGROUND", (0, i), (-1, i), CINZA_CLARO))

        # Outliers em vermelho claro
        for i, a in enumerate(dados.amostras, start=1):
            if a.outlier:
                estilo.append(("BACKGROUND", (0, i), (-1, i), VERMELHO_CLARO))

        tabela.setStyle(TableStyle(estilo))
        elementos.append(tabela)
        elementos.append(Spacer(1, 12))

    def _adicionar_qualidade_dados(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona seção de qualidade dos dados ao relatório."""
        from app.services.motor_estatistico import relatorio_qualidade_amostras

        elementos.append(Paragraph("QUALIDADE DOS DADOS", self._bloco_titulo_style))

        precos = [a.preco_unitario for a in dados.amostras]
        if precos:
            qualidade = relatorio_qualidade_amostras(precos)
            elementos.append(
                Paragraph(
                    f"<b>Nível de Qualidade:</b> {qualidade['nivel_qualidade']}",
                    self._campo_style,
                )
            )
            cv = qualidade.get("coeficiente_variacao")
            cv_str = f"{cv:.4f}" if cv is not None else "N/D"
            elementos.append(
                Paragraph(
                    f"<b>Coeficiente de Variação:</b> {cv_str}",
                    self._campo_style,
                )
            )
            if qualidade["recomendacoes"]:
                elementos.append(
                    Paragraph("<b>Recomendações:</b>", self._campo_style)
                )
                for rec in qualidade["recomendacoes"]:
                    elementos.append(
                        Paragraph(f"  • {rec}", self._campo_style)
                    )
        else:
            elementos.append(
                Paragraph("Sem amostras disponíveis para avaliação.", self._campo_style)
            )
        elementos.append(Spacer(1, 8))

    def _adicionar_conformidade_in65(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona checklist de conformidade com a IN SEGES/ME nº 65/2021."""
        elementos.append(
            Paragraph("CONFORMIDADE IN 65/2021", self._bloco_titulo_style)
        )

        # Verificar parâmetros
        tem_pncp = any(
            a.qualidade and "HOMOLOGADO" in a.qualidade.upper()
            for a in dados.amostras
        )
        tem_tabela_oficial = any(
            a.qualidade and "TABELA" in a.qualidade.upper()
            for a in dados.amostras
        )

        param_i = "✓" if tem_pncp else "✗"
        param_ii = "✓"  # sempre, pois vem de fonte pública
        param_iii = "✓" if tem_tabela_oficial else "✗"

        checklist = [
            f"Parâmetro I: preços de contratações anteriores {param_i}",
            f"Parâmetro II: pesquisa publicada {param_ii} (fonte pública)",
            f"Parâmetro III: preços de referência oficial {param_iii}",
        ]
        for item in checklist:
            elementos.append(Paragraph(item, self._campo_style))
        elementos.append(Spacer(1, 8))

    def _adicionar_correcao_ipca(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona seção de correção monetária IPCA ao relatório."""
        from app.services.correcao_monetaria import CorrecaoMonetariaService

        _correcao = CorrecaoMonetariaService()

        elementos.append(Paragraph("CORREÇÃO MONETÁRIA (IPCA)", self._bloco_titulo_style))

        try:
            fator = _correcao.fator_correcao(dados.periodo_inicio, dados.periodo_fim)
            variacao = round((fator - 1) * 100, 2)
            elementos.append(
                Paragraph(f"<b>Período:</b> {dados.periodo_inicio} a {dados.periodo_fim}", self._campo_style)
            )
            elementos.append(
                Paragraph(f"<b>Fator IPCA acumulado:</b> {fator:.6f}", self._campo_style)
            )
            elementos.append(
                Paragraph(f"<b>Variação acumulada:</b> {variacao}%", self._campo_style)
            )
            if dados.preco_referencial is not None:
                corrigido = round(dados.preco_referencial * fator, 2)
                valor_str = f"R$ {corrigido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                elementos.append(
                    Paragraph(f"<b>Preço ref. corrigido para data final:</b> {valor_str}", self._campo_style)
                )
        except Exception:
            elementos.append(
                Paragraph("Dados IPCA indisponíveis para o período informado.", self._campo_style)
            )
        elementos.append(Spacer(1, 8))

    def _adicionar_benchmark_regional(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona seção de benchmark regional ao relatório."""
        from app.services.benchmark_regional import BenchmarkRegionalService

        elementos.append(Paragraph("BENCHMARK REGIONAL", self._bloco_titulo_style))

        cat = dados.categoria_nome
        if not cat:
            elementos.append(Paragraph("Categoria não definida — benchmark indisponível.", self._campo_style))
            elementos.append(Spacer(1, 8))
            return

        svc = BenchmarkRegionalService()
        comp = svc.comparar_por_uf(cat)
        ranking = comp.get("ranking", [])

        if not ranking:
            elementos.append(Paragraph(f"Sem dados de benchmark para {cat}.", self._campo_style))
            elementos.append(Spacer(1, 8))
            return

        stats = comp.get("estatisticas", {})
        elementos.append(
            Paragraph(
                f"<b>UFs analisadas:</b> {comp['total_ufs']} | "
                f"<b>Média nacional:</b> {self._formatar_valor(stats.get('media'))} | "
                f"<b>Mais barata:</b> {stats.get('uf_mais_barata', 'N/D')} | "
                f"<b>Mais cara:</b> {stats.get('uf_mais_cara', 'N/D')}",
                self._campo_style,
            )
        )

        # Posição da UF filtrada
        if dados.uf_filtro:
            perc = svc.percentil_uf(cat, dados.uf_filtro)
            if perc.get("rank"):
                elementos.append(
                    Paragraph(
                        f"<b>{dados.uf_filtro}:</b> posição {perc['rank']}/{comp['total_ufs']} "
                        f"(percentil {perc.get('percentil', 'N/D')})",
                        self._campo_style,
                    )
                )

        elementos.append(Spacer(1, 8))

    def _adicionar_alertas_sobrepreco(self, elementos: list, dados: RelatorioInput) -> None:
        """Adiciona seção de alertas de sobrepreço ao relatório."""
        from app.services.alerta_sobrepreco import AlertaSobreprecoService

        elementos.append(Paragraph("ALERTAS DE SOBREPREÇO", self._bloco_titulo_style))

        if dados.preco_referencial is None:
            elementos.append(
                Paragraph("Preço referencial não definido — análise de sobrepreço indisponível.", self._campo_style)
            )
            elementos.append(Spacer(1, 8))
            return

        svc = AlertaSobreprecoService()
        resultado = svc.avaliar_preco(
            dados.item_descricao,
            dados.preco_referencial,
            dados.uf_filtro,
            dados.categoria_nome,
        )

        status = resultado.get("status", "SEM_REFERENCIA")
        elementos.append(
            Paragraph(f"<b>Status:</b> {status}", self._campo_style)
        )

        desvio = resultado.get("desvio_mediana_pct")
        if desvio is not None:
            elementos.append(
                Paragraph(f"<b>Desvio da mediana:</b> {desvio}%", self._campo_style)
            )

        for alerta in resultado.get("alertas", []):
            elementos.append(Paragraph(f"  • {alerta}", self._campo_style))

        elementos.append(Spacer(1, 8))

    def _adicionar_rodape(self, elementos: list) -> None:
        """Adiciona disclaimers no final do relatório."""
        elementos.append(Spacer(1, 20))
        # Linha separadora
        linha = Table([[""]],  colWidths=[16.5 * cm], rowHeights=[1])
        linha.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, CINZA_TEXTO),
        ]))
        elementos.append(linha)
        elementos.append(Spacer(1, 8))

        disclaimers = [
            "Este relatório constitui apoio técnico à pesquisa de preços, elaborado com base em fontes públicas rastreáveis.",
            "A definição final do preço estimado permanece sob responsabilidade do órgão demandante.",
            "Estruturado para atender aos parâmetros da IN SEGES/ME nº 65/2021.",
        ]
        for texto in disclaimers:
            elementos.append(Paragraph(texto, self._rodape_style))

        elementos.append(Spacer(1, 4))
        elementos.append(
            Paragraph(
                "Banco de Preços v0.8 — Araticum Comércio",
                self._rodape_style,
            )
        )

    @staticmethod
    def _rodape_pagina(canvas: object, doc: object) -> None:
        """Adiciona versão do sistema e número de página no rodapé."""
        canvas.saveState()  # type: ignore[attr-defined]
        canvas.setFont("Helvetica", 8)  # type: ignore[attr-defined]
        canvas.setFillColor(CINZA_TEXTO)  # type: ignore[attr-defined]
        # Versão à esquerda
        canvas.drawString(  # type: ignore[attr-defined]
            2 * cm,
            1.2 * cm,
            "Banco de Preços v0.8 — Araticum Comércio",
        )
        # Página X de Y (Y será preenchido com _total_pages)
        canvas.drawRightString(  # type: ignore[attr-defined]
            A4[0] - 2 * cm,
            1.2 * cm,
            f"Página {doc.page}",  # type: ignore[attr-defined]
        )
        canvas.restoreState()  # type: ignore[attr-defined]

    def gerar_xlsx(self, dados: RelatorioInput) -> bytes:
        """Gera arquivo CSV (UTF-8-BOM) com dados das amostras.

        Usa formato CSV com BOM para compatibilidade com Excel.

        Args:
            dados: Dados de entrada do relatório.

        Returns:
            Conteúdo do CSV em bytes (UTF-8-BOM).
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_MINIMAL)

        # Cabeçalho
        writer.writerow([
            "Nº Controle",
            "Órgão",
            "Data",
            "Preço Unitário",
            "Unidade",
            "UF",
            "Qualidade",
            "Outlier",
        ])

        # Dados
        for a in dados.amostras:
            writer.writerow([
                a.numero_controle or "",
                a.orgao_origem or "",
                a.data_referencia or "",
                f"{a.preco_unitario:.2f}",
                a.unidade or "",
                a.uf or "",
                a.qualidade or "",
                "Sim" if a.outlier else "Não",
            ])

        csv_str = buffer.getvalue()
        buffer.close()

        # UTF-8 BOM + conteúdo
        bom = b"\xef\xbb\xbf"
        return bom + csv_str.encode("utf-8")

    @staticmethod
    def _formatar_valor(valor: float | None) -> str:
        """Formata valor numérico para exibição."""
        if valor is None:
            return "N/D"
        return f"{valor:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _truncar(texto: str, max_len: int) -> str:
        """Trunca texto se exceder tamanho máximo."""
        if len(texto) <= max_len:
            return texto
        return texto[: max_len - 3] + "..."
