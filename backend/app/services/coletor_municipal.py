"""Coletor periódico de preços municipais via PNCP.

Estratégia:
1. Busca contratações homologadas por UF (foco inicial: GO)
2. Para cada contratação de município, busca itens com preço homologado
3. Persiste em orgaos + contratacoes + itens, com deduplicação por numero_controle_pncp
4. Calcula e expõe médias de preço por município e entorno (raio IBGE)

Endpoint principal:
  GET /api/consulta/v1/contratacoes/proposta
  (requer User-Agent de browser + codigoModalidadeContratacao obrigatório)

Uso:
  python -m app.services.coletor_municipal --uf GO --dias 30
  python -m app.services.coletor_municipal --uf GO --dias 7 --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
import psycopg2
import psycopg2.extras
import os

from app.services.classificador_tipo_objeto import inferir_tipo_objeto
from app.services.validacao_ingestao import StatusValidacao, validar_item

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────

CONSULT_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
ITEMS_URL_TPL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens"
RESULTADO_URL_TPL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens/{item}/resultados"

# PNCP bloqueia curl/scripts sem User-Agent de browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Modalidades de interesse para banco de preços
# 6=Pregão Eletrônico, 8=Dispensa Eletrônica
MODALIDADES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]  # todas as modalidades PNCP

# Situações com preço homologado (1=Divulgada, 2=Homologada)
# Vamos pegar as duas e filtrar pelos itens com resultado
SITUACAO_HOMOLOGADA = 2

DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://bancodeprecos:bancodeprecos_dev@localhost:5435/bancodeprecos"
)

TIMEOUT_API = 60  # segundos
PAGE_SIZE = 50
MAX_PAGES_POR_UF = 2000  # limite de segurança por run
SLEEP_ENTRE_PAGINAS = 0.5  # segundos (evitar rate limit)
SLEEP_ENTRE_ITENS = 0.2


# ─────────────────────────────────────────────────────────
# Municipios GO com código IBGE (para entorno/raio)
# Lista dos 246 municípios de GO — aqui os top 20 por volume
# ─────────────────────────────────────────────────────────
MUNICIPIOS_GO_IBGE = {
    "Goiânia": "5208707",
    "Aparecida de Goiânia": "5201405",
    "Anápolis": "5201108",
    "Rio Verde": "5218805",
    "Luziânia": "5212501",
    "Águas Lindas de Goiás": "5200258",
    "Valparaíso de Goiás": "5221858",
    "Trindade": "5221403",
    "Formosa": "5207600",
    "Novo Gama": "5214838",
    "Catalão": "5205109",
    "Jataí": "5211909",
    "Itumbiara": "5211503",
    "Senador Canedo": "5220454",
    "Caldas Novas": "5204508",
    "Planaltina": "5217609",
    "Goianésia": "5208301",
    "Mineiros": "5213103",
    "Inhumas": "5210000",
    "Quirinópolis": "5218508",
}


# ─────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────

@dataclass
class ContratacaoRaw:
    numero_controle_pncp: str
    cnpj: str
    razao_social: str
    esfera: str
    uf: str
    municipio: str
    codigo_ibge: str
    modalidade: str
    objeto: str
    valor_total_estimado: float | None
    valor_total_homologado: float | None
    data_publicacao: str
    ano_compra: int
    sequencial_compra: int
    situacao_id: int


@dataclass
class ItemRaw:
    numero_item: int
    descricao: str
    quantidade: float | None
    unidade: str | None
    valor_unitario: float | None
    valor_total: float | None
    catmat: str | None
    tipo_preco: str = "estimado"
    tipo_objeto: str = "material"
    objeto_contratacao: str | None = None  # contexto para validação de cópia indevida


@dataclass
class ResultadoColeta:
    uf: str
    total_contratacoes: int = 0
    total_itens: int = 0
    novas_contratacoes: int = 0
    novos_itens: int = 0
    quarentena: int = 0   # itens suspeitos que aguardam revisão
    rejeitados: int = 0   # itens inválidos descartados
    erros: list[str] = field(default_factory=list)
    duracao_s: float = 0.0


# ─────────────────────────────────────────────────────────
# Funções de API
# ─────────────────────────────────────────────────────────

def _get_json(url: str, params: dict | None = None, max_retries: int = 2) -> Any:
    """GET com retry e User-Agent de browser."""
    for tentativa in range(max_retries + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_API)
            if resp.status_code == 204:
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning("Timeout %s (tentativa %d)", url, tentativa + 1)
            if tentativa < max_retries:
                time.sleep(2 ** tentativa)
        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP %s para %s", e.response.status_code if e.response else "?", url)
            return None
        except Exception as e:
            logger.error("Erro inesperado %s: %s", url, e)
            return None
    return None


def buscar_contratacoes_uf(
    uf: str,
    data_inicio: str,
    data_fim: str,
    modalidade: int,
    situacao: int = 2,
) -> list[ContratacaoRaw]:
    """Busca todas as contratações homologadas de uma UF/modalidade."""
    resultados: list[ContratacaoRaw] = []
    pagina = 1

    while pagina <= MAX_PAGES_POR_UF:
        params = {
            "dataInicial": data_inicio,
            "dataFinal": data_fim,
            "codigoModalidadeContratacao": modalidade,
            "uf": uf,
            "situacao": situacao,
            "pagina": pagina,
            "tamanhoPagina": PAGE_SIZE,
        }
        data = _get_json(CONSULT_URL, params)
        if not data or not data.get("data"):
            break

        for item in data["data"]:
            org = item.get("orgaoEntidade") or {}
            un = item.get("unidadeOrgao") or {}

            # Aceitar todas as esferas (M=municipal, E=estadual, F=federal)
            esfera = org.get("esferaId", "")

            # Filtrar UF
            uf_item = un.get("ufSigla", "")
            if uf_item != uf:
                continue

            resultados.append(ContratacaoRaw(
                numero_controle_pncp=item.get("numeroControlePNCP", ""),
                cnpj=org.get("cnpj", ""),
                razao_social=org.get("razaoSocial", ""),
                esfera=esfera,
                uf=uf_item,
                municipio=un.get("municipioNome", ""),
                codigo_ibge=un.get("codigoIbge", ""),
                modalidade=item.get("modalidadeNome", ""),
                objeto=item.get("objetoCompra", "")[:2000],
                valor_total_estimado=_float_safe(item.get("valorTotalEstimado")),
                valor_total_homologado=_float_safe(item.get("valorTotalHomologado")),
                data_publicacao=item.get("dataPublicacaoPncp", "")[:10],
                ano_compra=int(item.get("anoCompra", 0)),
                sequencial_compra=int(item.get("sequencialCompra", 0)),
                situacao_id=int(item.get("situacaoCompraId", 0)),
            ))

        total_paginas = int(data.get("totalPaginas") or 1)
        logger.info("UF=%s modalidade=%d página %d/%d — %d contratos coletados",
                    uf, modalidade, pagina, total_paginas, len(resultados))

        if pagina >= total_paginas:
            break

        pagina += 1
        time.sleep(SLEEP_ENTRE_PAGINAS)

    return resultados


def buscar_itens(
    cnpj: str,
    ano: int,
    seq: int,
    objeto_contratacao: str | None = None,
) -> list[ItemRaw]:
    """Busca itens de uma contratação, incluindo resultado homologado."""
    url = ITEMS_URL_TPL.format(cnpj=cnpj, ano=ano, seq=seq)
    data = _get_json(url)
    if not data:
        return []

    itens = []
    # API retorna lista direta ou dict com 'data'
    items_list = data if isinstance(data, list) else data.get("data", [])

    for it in items_list:
        numero_item = int(it.get("numeroItem", 0))
        valor_unitario = _float_safe(it.get("valorUnitarioEstimado"))
        tipo_preco = "estimado"

        # Tentar buscar resultado homologado
        try:
            resultado_url = RESULTADO_URL_TPL.format(
                cnpj=cnpj, ano=ano, seq=seq, item=numero_item
            )
            resultado = _get_json(resultado_url, max_retries=1)
            if resultado:
                items_resultado = resultado if isinstance(resultado, list) else [resultado]
                for r in items_resultado:
                    vh = _float_safe(r.get("valorUnitarioHomologado"))
                    if vh and vh > 0:
                        valor_unitario = vh
                        tipo_preco = "homologado"
                        break
        except Exception:
            pass

        descricao_item = (it.get("descricao") or "")[:2000]
        itens.append(ItemRaw(
            numero_item=numero_item,
            descricao=descricao_item,
            quantidade=_float_safe(it.get("quantidade")),
            unidade=it.get("unidadeMedida", {}).get("nomeUnidadeMedida") if isinstance(it.get("unidadeMedida"), dict) else it.get("unidadeMedida"),
            valor_unitario=valor_unitario,
            valor_total=_float_safe(it.get("valorTotal")),
            catmat=it.get("catalogoAquisicao", {}).get("codigo") if isinstance(it.get("catalogoAquisicao"), dict) else None,
            tipo_preco=tipo_preco,
            tipo_objeto=inferir_tipo_objeto(descricao_item),
            objeto_contratacao=objeto_contratacao,
        ))
        time.sleep(SLEEP_ENTRE_ITENS)

    return itens


# ─────────────────────────────────────────────────────────
# Persistência
# ─────────────────────────────────────────────────────────

def upsert_orgao(cur, contratacao: ContratacaoRaw) -> str:
    """Upsert órgão e retorna UUID."""
    cur.execute("""
        INSERT INTO orgaos (cnpj, razao_social, esfera, uf, municipio)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (cnpj) DO UPDATE SET
            razao_social = EXCLUDED.razao_social,
            uf = EXCLUDED.uf,
            municipio = EXCLUDED.municipio
        RETURNING id
    """, (
        contratacao.cnpj,
        contratacao.razao_social,
        contratacao.esfera,
        contratacao.uf,
        contratacao.municipio,
    ))
    return cur.fetchone()[0]


def upsert_contratacao(cur, orgao_id: str, contratacao: ContratacaoRaw) -> tuple[str, bool]:
    """Upsert contratação. Retorna (uuid, is_nova)."""
    cur.execute("""
        INSERT INTO contratacoes
            (orgao_id, numero_controle_pncp, modalidade, objeto,
             valor_total, data_publicacao, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (numero_controle_pncp) DO NOTHING
        RETURNING id
    """, (
        orgao_id,
        contratacao.numero_controle_pncp,
        contratacao.modalidade,
        contratacao.objeto,
        contratacao.valor_total_homologado or contratacao.valor_total_estimado,
        contratacao.data_publicacao or None,
        "homologada" if contratacao.situacao_id == 2 else "divulgada",
    ))
    row = cur.fetchone()
    if row:
        return str(row[0]), True  # nova

    # Já existia — buscar id
    cur.execute(
        "SELECT id FROM contratacoes WHERE numero_controle_pncp = %s",
        (contratacao.numero_controle_pncp,)
    )
    return str(cur.fetchone()[0]), False


def insert_itens(
    cur,
    contratacao_id: str,
    itens: list[ItemRaw],
    uf: str = "",
    cnpj: str = "",
) -> tuple[int, int, int]:
    """Insere itens com portão de qualidade.

    Cada item passa por validação antes do INSERT:
      - REJEITADO  → descartado, contado em `rejeitados`
      - QUARENTENA → salvo em itens_quarentena para revisão manual
      - ACEITO     → inserido normalmente em itens

    Returns:
        Tupla (novos_validos, quarentena, rejeitados)
    """
    novos = 0
    quarentena = 0
    rejeitados = 0
    novos_ids: list[tuple[str, str]] = []  # (item_id, descricao)

    for it in itens:
        # ── Portão de qualidade ──────────────────────────────────────
        validacao = validar_item(
            descricao=it.descricao,
            preco_unitario=it.valor_unitario,
            quantidade=it.quantidade,
            unidade=it.unidade,
            data_referencia=None,          # data vem da contratação, não do item
            cnpj=cnpj or None,
            objeto_contratacao=it.objeto_contratacao,
            categoria_nome=None,           # será classificado após insert
            tipo_preco=it.tipo_preco,
        )

        if validacao.rejeitado:
            rejeitados += 1
            logger.debug(
                "Item %d rejeitado: %s",
                it.numero_item,
                "; ".join(validacao.motivos_rejeicao),
            )
            continue

        if validacao.em_quarentena:
            quarentena += 1
            _inserir_quarentena(cur, it, uf, cnpj, validacao.motivos_quarentena)
            continue

        # ── INSERT normal ────────────────────────────────────────────
        cur.execute("""
            INSERT INTO itens
                (contratacao_id, numero_item, descricao, quantidade,
                 unidade, valor_unitario, valor_total, catmat_catser, tipo_preco, tipo_objeto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (
            contratacao_id,
            it.numero_item,
            it.descricao,
            it.quantidade,
            it.unidade,
            it.valor_unitario,
            it.valor_total,
            it.catmat,
            it.tipo_preco,
            it.tipo_objeto,
        ))
        if cur.rowcount > 0:
            novos += 1
            row = cur.fetchone()
            if row:
                novos_ids.append((str(row[0]), it.descricao or ""))

    # Classificar novos itens automaticamente
    if novos_ids:
        _classificar_itens_novos(cur, novos_ids)

    return novos, quarentena, rejeitados


def _inserir_quarentena(
    cur,
    it: ItemRaw,
    uf: str,
    cnpj: str,
    motivos: list[str],
) -> None:
    """Persiste item suspeito na tabela de quarentena."""
    item_raw = {
        "numero_item": it.numero_item,
        "descricao": it.descricao,
        "quantidade": it.quantidade,
        "unidade": it.unidade,
        "valor_unitario": it.valor_unitario,
        "valor_total": it.valor_total,
        "catmat": it.catmat,
        "tipo_preco": it.tipo_preco,
        "tipo_objeto": it.tipo_objeto,
    }
    try:
        cur.execute(
            """
            INSERT INTO itens_quarentena (uf, cnpj, item_raw, motivo, status, criado_em)
            VALUES (%s, %s, %s, %s, 'pendente', NOW())
            """,
            (uf or None, cnpj or None, json.dumps(item_raw), "; ".join(motivos)),
        )
    except Exception as e:
        logger.warning("Falha ao inserir quarentena item %d: %s", it.numero_item, e)


def _classificar_itens_novos(cur, itens: list[tuple[str, str]]) -> None:
    """Classifica itens recém-inseridos usando ClassificadorRegex."""
    try:
        from app.services.classificador_regex import ClassificadorRegex

        # Carregar categorias
        cur.execute("SELECT id, nome FROM categorias")
        categorias = [{"id": str(r[0]), "nome": r[1]} for r in cur.fetchall()]
        cat_map = {c["nome"]: c["id"] for c in categorias}
        classificador = ClassificadorRegex(categorias)

        for item_id, descricao in itens:
            resultado = classificador.classificar(descricao)
            if resultado and resultado.get("score", 0) >= 0.5:
                cat_id = resultado.get("categoria_id") or cat_map.get(resultado["categoria_nome"])
                if cat_id:
                    cur.execute("""
                        INSERT INTO item_categoria (item_id, categoria_id, score_confianca, metodo_classificacao)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (item_id, categoria_id) DO NOTHING
                    """, (item_id, str(cat_id), resultado["score"], resultado["metodo"]))
    except Exception as e:
        logger.warning("Erro ao classificar itens: %s", e)


# ─────────────────────────────────────────────────────────
# View materializada de médias municipais
# ─────────────────────────────────────────────────────────

SQL_CREATE_VIEW_MEDIA_MUNICIPAL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_media_preco_municipal AS
SELECT
    o.uf,
    o.municipio,
    i.descricao,
    COUNT(*) AS qtd_referencias,
    ROUND(AVG(i.valor_unitario)::numeric, 4) AS media_unitario,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY i.valor_unitario)::numeric, 4) AS mediana_unitario,
    ROUND(MIN(i.valor_unitario)::numeric, 4) AS min_unitario,
    ROUND(MAX(i.valor_unitario)::numeric, 4) AS max_unitario,
    ROUND(STDDEV(i.valor_unitario)::numeric, 4) AS desvio_padrao,
    MAX(c.data_publicacao) AS data_ultima_ref
FROM itens i
JOIN contratacoes c ON c.id = i.contratacao_id
JOIN orgaos o ON o.id = c.orgao_id
WHERE i.valor_unitario IS NOT NULL
  AND i.valor_unitario > 0
  AND i.descricao IS NOT NULL
GROUP BY o.uf, o.municipio, i.descricao
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_media_municipal
    ON mv_media_preco_municipal (uf, municipio, descricao);

CREATE INDEX IF NOT EXISTS idx_mv_media_uf
    ON mv_media_preco_municipal (uf);
"""

SQL_REFRESH_VIEW = "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_media_preco_municipal;"


def garantir_view_media_municipal(conn) -> None:
    """Cria ou atualiza a materialized view de médias municipais."""
    with conn.cursor() as cur:
        try:
            cur.execute(SQL_CREATE_VIEW_MEDIA_MUNICIPAL)
            conn.commit()
            logger.info("View mv_media_preco_municipal criada/verificada.")
        except Exception as e:
            conn.rollback()
            # Se já existe, tentar apenas refresh
            logger.warning("Create view: %s — tentando refresh.", e)
            try:
                cur.execute(SQL_REFRESH_VIEW)
                conn.commit()
                logger.info("View atualizada via REFRESH.")
            except Exception as e2:
                conn.rollback()
                logger.error("Falha no refresh da view: %s", e2)


# ─────────────────────────────────────────────────────────
# Orquestrador principal
# ─────────────────────────────────────────────────────────

def coletar_uf(
    uf: str,
    dias: int = 30,
    dry_run: bool = False,
    dsn: str = DB_DSN,
    data_inicio_str: str | None = None,
    data_fim_str: str | None = None,
) -> ResultadoColeta:
    """Coleta contratações municipais de uma UF e persiste no banco.

    Args:
        data_inicio_str: data no formato YYYY-MM-DD (sobrescreve --dias)
        data_fim_str: data no formato YYYY-MM-DD (sobrescreve --dias)
    """
    inicio = time.time()
    resultado = ResultadoColeta(uf=uf)

    if data_inicio_str and data_fim_str:
        str_inicio = data_inicio_str.replace("-", "")
        str_fim = data_fim_str.replace("-", "")
    else:
        data_fim = datetime.now(timezone.utc)
        data_inicio = data_fim - timedelta(days=dias)
        str_inicio = data_inicio.strftime("%Y%m%d")
        str_fim = data_fim.strftime("%Y%m%d")

    logger.info("Iniciando coleta UF=%s período=%s→%s dry_run=%s", uf, str_inicio, str_fim, dry_run)

    # Coleta todas as modalidades
    todas_contratacoes: list[ContratacaoRaw] = []
    for mod in MODALIDADES:
        contratacoes = buscar_contratacoes_uf(uf, str_inicio, str_fim, mod)
        todas_contratacoes.extend(contratacoes)
        logger.info("Modalidade %d: %d contratações municipais", mod, len(contratacoes))

    resultado.total_contratacoes = len(todas_contratacoes)

    if dry_run:
        logger.info("[DRY RUN] %d contratações coletadas, sem persistência.", len(todas_contratacoes))
        for c in todas_contratacoes[:5]:
            logger.info("  %s | %s | %s | R$ %s", c.municipio, c.modalidade, c.objeto[:60], c.valor_total_estimado)
        resultado.duracao_s = time.time() - inicio
        return resultado

    # Persistência
    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False

        for contratacao in todas_contratacoes:
            try:
                with conn.cursor() as cur:
                    orgao_id = upsert_orgao(cur, contratacao)
                    contratacao_id, is_nova = upsert_contratacao(cur, orgao_id, contratacao)

                    if is_nova:
                        resultado.novas_contratacoes += 1
                        # Buscar itens apenas para novas contratações
                        itens = buscar_itens(
                            contratacao.cnpj,
                            contratacao.ano_compra,
                            contratacao.sequencial_compra,
                            objeto_contratacao=contratacao.objeto,
                        )
                        resultado.total_itens += len(itens)
                        novos_itens, n_quarentena, n_rejeitados = insert_itens(
                            cur, contratacao_id, itens,
                            uf=uf, cnpj=contratacao.cnpj,
                        )
                        resultado.novos_itens += novos_itens
                        resultado.quarentena += n_quarentena
                        resultado.rejeitados += n_rejeitados

                    conn.commit()

            except Exception as e:
                conn.rollback()
                msg = f"Erro em {contratacao.numero_controle_pncp}: {e}"
                logger.error(msg)
                resultado.erros.append(msg)

        # Atualizar view de médias
        garantir_view_media_municipal(conn)
        conn.close()

    except Exception as e:
        msg = f"Falha na conexão com banco: {e}"
        logger.error(msg)
        resultado.erros.append(msg)

    resultado.duracao_s = time.time() - inicio
    logger.info(
        "Coleta finalizada UF=%s | contratos=%d novos=%d | "
        "itens=%d novos=%d quarentena=%d rejeitados=%d | erros=%d | %.1fs",
        uf, resultado.total_contratacoes, resultado.novas_contratacoes,
        resultado.total_itens, resultado.novos_itens,
        resultado.quarentena, resultado.rejeitados,
        len(resultado.erros), resultado.duracao_s,
    )
    return resultado


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _float_safe(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None



# ─────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="Coletor PNCP municipal")
    parser.add_argument("--uf", default="GO", help="Sigla da UF (default: GO)")
    parser.add_argument("--dias", type=int, default=30, help="Janela em dias (default: 30)")
    parser.add_argument("--data-inicio", default=None, help="Data inicial YYYY-MM-DD (sobrescreve --dias)")
    parser.add_argument("--data-fim", default=None, help="Data final YYYY-MM-DD (sobrescreve --dias)")
    parser.add_argument("--dry-run", action="store_true", help="Não persiste, apenas loga")
    args = parser.parse_args()

    resultado = coletar_uf(
        args.uf,
        args.dias,
        args.dry_run,
        data_inicio_str=args.data_inicio,
        data_fim_str=args.data_fim,
    )
    print(f"\n{'='*60}")
    print(f"UF: {resultado.uf}")
    print(f"Contratações coletadas: {resultado.total_contratacoes} ({resultado.novas_contratacoes} novas)")
    print(f"Itens coletados:  {resultado.total_itens}")
    print(f"  → Aceitos:      {resultado.novos_itens}")
    print(f"  → Quarentena:   {resultado.quarentena}")
    print(f"  → Rejeitados:   {resultado.rejeitados}")
    print(f"Erros: {len(resultado.erros)}")
    print(f"Duração: {resultado.duracao_s:.1f}s")
    if resultado.erros:
        print("Primeiros erros:")
        for e in resultado.erros[:3]:
            print(f"  - {e}")
