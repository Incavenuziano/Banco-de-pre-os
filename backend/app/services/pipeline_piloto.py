"""Pipeline de ingestão piloto para o Banco de Preços.

Orquestra a coleta de contratações do PNCP, normalização de descrições,
classificação por categoria e cálculo de scores para municípios-alvo.
"""

from __future__ import annotations

import logging
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.classificador_regex import ClassificadorRegex
from app.services.gerador_relatorio import GeradorRelatorio
from app.services.motor_estatistico import calcular_estatisticas, calcular_preco_referencial
from app.services.normalizacao import limpar_descricao, normalizar_unidade
from app.services.pncp_conector import PNCPConector
from app.services.scoring import calcular_score_fonte
from app.schemas.relatorios import AmostraRelatorio, RelatorioInput

logger = logging.getLogger(__name__)


@dataclass
class ItemProcessado:
    """Representa um item de contratação após processamento completo."""

    numero_controle: str
    descricao_original: str
    descricao_normalizada: str
    categoria_nome: str | None = None
    categoria_score: float | None = None
    preco_unitario: float | None = None
    unidade_normalizada: str | None = None
    score_confianca: int = 0
    uf: str = ""
    municipio: str = ""
    data_referencia: str | None = None


class PipelinePiloto:
    """Pipeline de ingestão focada para piloto controlado.

    Coleta contratações de municípios específicos via PNCP,
    processa itens, normaliza, classifica e calcula scores.
    """

    def __init__(self, conector: PNCPConector | None = None) -> None:
        """Inicializa o pipeline.

        Args:
            conector: Instância de PNCPConector. Se None, cria uma nova.
        """
        self.conector = conector or PNCPConector()
        self.classificador = ClassificadorRegex()
        self.gerador_relatorio = GeradorRelatorio()

    def executar_municipio(
        self,
        uf: str,
        municipio: str,
        data_inicio: str,
        data_fim: str,
    ) -> dict[str, Any]:
        """Executa o pipeline completo para um município.

        Coleta contratações, processa itens, normaliza descrições,
        classifica e calcula scores.

        Args:
            uf: Sigla da UF (ex: 'GO').
            municipio: Nome do município.
            data_inicio: Data inicial (YYYYMMDD).
            data_fim: Data final (YYYYMMDD).

        Returns:
            Dicionário com resultados do processamento.
        """
        erros: list[str] = []
        itens_processados: list[ItemProcessado] = []
        total_contratacoes = 0

        # Coleta paginada de contratações
        pagina = 1
        while True:
            resp = self.conector.buscar_contratacoes(
                uf=uf,
                municipio=municipio,
                data_inicio=data_inicio,
                data_fim=data_fim,
                pagina=pagina,
            )

            contratacoes = resp.get("data", [])
            if not contratacoes:
                break

            total_contratacoes += len(contratacoes)

            for contratacao in contratacoes:
                try:
                    itens = self._processar_contratacao(contratacao, uf, municipio)
                    itens_processados.extend(itens)
                except Exception as exc:
                    erro_msg = f"Erro ao processar contratação: {exc}"
                    logger.warning(erro_msg)
                    erros.append(erro_msg)

            # Verifica se há mais páginas
            total_registros = resp.get("totalRegistros", 0)
            if pagina * 50 >= total_registros:
                break
            pagina += 1

        return {
            "municipio": municipio,
            "uf": uf,
            "total_contratacoes": total_contratacoes,
            "total_itens": len(itens_processados),
            "itens_processados": itens_processados,
            "erros": erros,
        }

    def _processar_contratacao(
        self,
        contratacao: dict[str, Any],
        uf: str,
        municipio: str,
    ) -> list[ItemProcessado]:
        """Processa uma contratação individual, coletando e normalizando seus itens."""
        cnpj = contratacao.get("cnpjOrgao", contratacao.get("orgaoEntidade", {}).get("cnpj", ""))
        ano = contratacao.get("anoCompra", 0)
        numero_seq = contratacao.get("sequencialCompra", 0)
        data_pub = contratacao.get("dataPublicacaoPncp", "")
        numero_controle = contratacao.get("numeroControlePNCP", f"{cnpj}-{ano}-{numero_seq}")

        if not cnpj or not ano or not numero_seq:
            return []

        itens_raw = self.conector.buscar_itens_contratacao(cnpj, ano, numero_seq)
        resultado: list[ItemProcessado] = []

        for item_raw in itens_raw:
            descricao_original = item_raw.get("descricao", "")
            if not descricao_original:
                continue

            descricao_normalizada = limpar_descricao(descricao_original)
            unidade_original = item_raw.get("unidadeMedida", "")
            unidade_norm = normalizar_unidade(unidade_original) if unidade_original else None

            # Classificação por regex
            classificacao = self.classificador.classificar(descricao_normalizada)
            categoria_nome = classificacao["categoria_nome"] if classificacao else None
            categoria_score = classificacao["score"] if classificacao else None

            # Preço unitário
            preco = item_raw.get("valorUnitarioEstimado") or item_raw.get("valorTotal")
            if preco is not None:
                try:
                    preco = float(preco)
                except (ValueError, TypeError):
                    preco = None

            # Score de confiança
            fonte_dados = {
                "url_origem": f"https://pncp.gov.br",
                "data_referencia": data_pub or None,
                "quantidade": item_raw.get("quantidade"),
                "qualidade_tipo": "HOMOLOGADO" if contratacao.get("situacaoCompraId") == 1 else "ESTIMADO",
                "storage_path": None,
                "hash_sha256": None,
                "unidade_normalizada": unidade_norm,
                "categoria_id": 1 if categoria_nome else None,
                "score_classificacao": categoria_score,
            }
            score = calcular_score_fonte(fonte_dados)

            item = ItemProcessado(
                numero_controle=numero_controle,
                descricao_original=descricao_original,
                descricao_normalizada=descricao_normalizada,
                categoria_nome=categoria_nome,
                categoria_score=categoria_score,
                preco_unitario=preco,
                unidade_normalizada=unidade_norm,
                score_confianca=score,
                uf=uf,
                municipio=municipio,
                data_referencia=data_pub or None,
            )
            resultado.append(item)

        return resultado

    def selecionar_top_itens(
        self,
        itens: list[dict[str, Any]],
        n: int = 20,
    ) -> list[dict[str, Any]]:
        """Seleciona os n itens mais frequentes agrupados por categoria/descrição.

        Agrupa itens por categoria_nome + descricao_normalizada,
        conta ocorrências e calcula preço mediano por grupo.

        Args:
            itens: Lista de dicts ou ItemProcessado convertidos a dict.
            n: Número máximo de itens a retornar (default 20).

        Returns:
            Lista dos n itens mais frequentes com estatísticas.
        """
        if not itens:
            return []

        grupos: dict[str, dict[str, Any]] = {}

        for item in itens:
            # Suporta tanto dict quanto ItemProcessado
            if hasattr(item, "__dataclass_fields__"):
                categoria = item.categoria_nome or "Sem Categoria"
                descricao = item.descricao_normalizada
                preco = item.preco_unitario
            else:
                categoria = item.get("categoria_nome") or "Sem Categoria"
                descricao = item.get("descricao_normalizada", "")
                preco = item.get("preco_unitario")

            chave = f"{categoria}|{descricao}"

            if chave not in grupos:
                grupos[chave] = {
                    "descricao_normalizada": descricao,
                    "categoria": categoria,
                    "ocorrencias": 0,
                    "precos": [],
                }

            grupos[chave]["ocorrencias"] += 1
            if preco is not None and preco > 0:
                grupos[chave]["precos"].append(preco)

        # Ordena por ocorrências (desc) e seleciona top n
        ordenados = sorted(grupos.values(), key=lambda g: g["ocorrencias"], reverse=True)

        resultado: list[dict[str, Any]] = []
        for grupo in ordenados[:n]:
            preco_mediano = (
                statistics.median(grupo["precos"]) if grupo["precos"] else None
            )
            resultado.append({
                "descricao_normalizada": grupo["descricao_normalizada"],
                "categoria": grupo["categoria"],
                "ocorrencias": grupo["ocorrencias"],
                "precos": grupo["precos"],
                "preco_mediano": preco_mediano,
            })

        return resultado

    def gerar_relatorio_piloto(
        self,
        municipio: str,
        uf: str,
        top_itens: list[dict[str, Any]],
    ) -> bytes:
        """Gera PDF de relatório piloto para um município.

        Args:
            municipio: Nome do município.
            uf: Sigla da UF.
            top_itens: Lista dos itens mais frequentes.

        Returns:
            Bytes do PDF gerado.
        """
        # Monta amostras a partir dos top itens
        amostras: list[AmostraRelatorio] = []
        todos_precos: list[float] = []

        for item in top_itens:
            for preco in item.get("precos", []):
                amostras.append(AmostraRelatorio(
                    numero_controle=None,
                    orgao_origem=f"Prefeitura de {municipio}",
                    data_referencia=None,
                    preco_unitario=preco,
                    unidade=None,
                    uf=uf,
                    qualidade="HOMOLOGADO",
                    outlier=False,
                ))
                todos_precos.append(preco)

        # Calcula estatísticas agregadas
        stats = calcular_estatisticas(todos_precos) if todos_precos else {}
        ref = calcular_preco_referencial(todos_precos) if todos_precos else {}

        dados = RelatorioInput(
            orgao_nome=f"Prefeitura de {municipio}",
            orgao_cnpj=None,
            item_descricao=f"Relatório Piloto — Top {len(top_itens)} itens",
            categoria_nome="Diversas",
            periodo_inicio="2025-01-01",
            periodo_fim="2025-12-31",
            uf_filtro=uf,
            amostras=amostras[:50],  # Limita amostras no PDF
            estatisticas=stats,
            preco_referencial=ref.get("preco_referencial"),
            confianca=ref.get("confianca", "INSUFICIENTE"),
            n_outliers_excluidos=ref.get("n_outliers_excluidos", 0),
            id_relatorio=str(uuid.uuid4()),
            emitido_em=datetime.now().isoformat(),
        )

        return self.gerador_relatorio.gerar(dados)
