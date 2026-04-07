#!/usr/bin/env python3
"""Atualiza itens existentes com preco homologado da API PNCP.

Mantem AMBOS os valores:
  - valor_estimado: preco original da fase de estimativa
  - valor_homologado: preco do resultado (adjudicacao)
  - valor_unitario: melhor preco (homologado se existir, senao estimado)
  - tipo_preco: 'homologado' se tem resultado, senao 'estimado'

Para cada contratacao no banco:
1. Busca /itens da API e verifica situacaoCompraItem e temResultado
2. Se temResultado, busca /resultados para obter valorUnitarioHomologado
3. Atualiza valor_homologado, valor_unitario e tipo_preco no banco
   preservando o valor_estimado original

Uso:
  python3 scripts/atualizar_precos_homologados.py --limit 100 --dry-run
  python3 scripts/atualizar_precos_homologados.py
  python3 scripts/atualizar_precos_homologados.py --uf GO
"""

from __future__ import annotations

import argparse
import functools
import logging
import os
import time

import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
print = functools.partial(print, flush=True)
logger = logging.getLogger(__name__)

DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://bancodeprecos:bancodeprecos_dev@localhost:5435/bancodeprecos"
    "?keepalives=1&keepalives_idle=60&keepalives_interval=10&keepalives_count=5",
)

ITEMS_URL_TPL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens"
RESULTADO_URL_TPL = "https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens/{item}/resultados"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

TIMEOUT = 60
SLEEP_ENTRE_CONTRATACOES = 0.3
SLEEP_ENTRE_RESULTADOS = 0.15


def _float_positive(value: object) -> float | None:
    """Converte valor numerico da API para float positivo.

    Retorna ``None`` para ausente, invalido, zero ou negativo.
    """
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip().replace(",", ".")
        if not cleaned:
            return None
    else:
        cleaned = value

    try:
        parsed = float(cleaned)
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


def _get_json(url: str, retries: int = 2):
    for i in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code in (204, 404):
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.warning("Timeout %s (tentativa %d)", url, i + 1)
            if i < retries:
                time.sleep(2 ** i)
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            logger.warning("HTTP %s: %s", code, url)
            if e.response is not None and e.response.status_code == 429:
                logger.warning("Rate limit - aguardando 10s")
                time.sleep(10)
                continue
            return None
        except Exception as e:
            logger.error("Erro %s: %s", url, e)
            return None
    return None


def _parse_numero_controle(numero_controle: str) -> tuple[int, int]:
    """Extrai sequencial e ano do numero de controle PNCP."""
    parts = numero_controle.split("-")
    seq_ano = parts[-1]
    seq_str, ano_str = seq_ano.split("/")
    return int(seq_str), int(ano_str)


def main():
    parser = argparse.ArgumentParser(description="Atualizar precos homologados PNCP")
    parser.add_argument("--limit", type=int, default=0, help="Limite de contratacoes (0=todas)")
    parser.add_argument("--uf", default=None, help="Filtrar por UF")
    parser.add_argument("--dry-run", action="store_true", help="Nao atualiza banco")
    parser.add_argument(
        "--skip-done",
        action="store_true",
        default=True,
        help="Pular contratacoes que ja tem itens homologados (default: True)",
    )
    parser.add_argument(
        "--recover-estimado",
        action="store_true",
        help="Recuperar valor_estimado dos itens ja atualizados para homologado",
    )
    args = parser.parse_args()

    def get_conn():
        import time as _time

        for attempt in range(5):
            try:
                c = psycopg2.connect(
                    DB_DSN,
                    connect_timeout=10,
                    keepalives=1,
                    keepalives_idle=60,
                    keepalives_interval=10,
                    keepalives_count=5,
                )
                c.autocommit = False
                return c
            except Exception as e:
                logger.warning("Conexao falhou (tentativa %d/5): %s", attempt + 1, e)
                _time.sleep(5 * (attempt + 1))
        raise RuntimeError("Nao foi possivel conectar ao banco apos 5 tentativas")

    conn = get_conn()

    def refresh_conn_if_needed():
        nonlocal conn
        try:
            if conn.closed:
                conn = get_conn()
                return
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except psycopg2.OperationalError:
            try:
                conn.close()
            except Exception:
                pass
            conn = get_conn()

    def db_execute(sql, params=()):
        """Executa SQL com reconexao automatica em caso de conexao quebrada."""
        nonlocal conn
        for attempt in range(5):
            try:
                refresh_conn_if_needed()
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    conn.commit()
                return True
            except psycopg2.OperationalError as e:
                logger.warning("OperationalError (tentativa %d/5), reconectando: %s", attempt + 1, e)
                try:
                    conn.rollback()
                except Exception:
                    pass
                try:
                    conn.close()
                except Exception:
                    pass
                conn = get_conn()
                time.sleep(min(5 * (attempt + 1), 30))
        logger.error("Falha persistente ao executar SQL apos 5 tentativas")
        return False

    if args.recover_estimado:
        _recover_estimado(conn, args.dry_run)
        conn.close()
        return

    refresh_conn_if_needed()
    with conn.cursor() as cur:
        sql = """
            SELECT DISTINCT ct.id, o.cnpj, ct.numero_controle_pncp
            FROM contratacoes ct
            JOIN orgaos o ON ct.orgao_id = o.id
            JOIN itens i ON i.contratacao_id = ct.id
            WHERE i.valor_homologado IS NULL
        """
        params = []
        if args.uf:
            sql += " AND o.uf = %s"
            params.append(args.uf)
        if args.skip_done:
            sql += """
                AND EXISTS (
                    SELECT 1 FROM itens i2
                    WHERE i2.contratacao_id = ct.id AND i2.valor_homologado IS NULL
                )
            """
        sql += " ORDER BY ct.id"
        if args.limit > 0:
            sql += f" LIMIT {args.limit}"

        cur.execute(sql, params)
        contratacoes = cur.fetchall()

    total = len(contratacoes)
    logger.info(
        "Contratacoes a processar: %d (uf=%s, limit=%d, dry_run=%s)",
        total,
        args.uf or "todas",
        args.limit,
        args.dry_run,
    )

    stats = {
        "processadas": 0,
        "itens_atualizados": 0,
        "itens_sem_resultado": 0,
        "estimados_preenchidos": 0,
        "contratacoes_com_homologado": 0,
        "erros_api": 0,
    }

    for idx, (ct_id, cnpj, numero_controle) in enumerate(contratacoes, 1):
        try:
            seq, ano = _parse_numero_controle(numero_controle)
        except Exception as e:
            logger.warning("Nao consegui parsear %s: %s", numero_controle, e)
            stats["erros_api"] += 1
            continue

        refresh_conn_if_needed()
        url_itens = ITEMS_URL_TPL.format(cnpj=cnpj, ano=ano, seq=seq)
        api_itens = _get_json(url_itens)
        if not api_itens:
            stats["erros_api"] += 1
            time.sleep(SLEEP_ENTRE_CONTRATACOES)
            continue

        items_list = api_itens if isinstance(api_itens, list) else api_itens.get("data", [])

        tem_homologado = False
        for api_item in items_list:
            numero_item = int(api_item.get("numeroItem", 0))
            valor_estimado = _float_positive(api_item.get("valorUnitarioEstimado"))
            situacao = api_item.get("situacaoCompraItem", 0)
            tem_resultado = api_item.get("temResultado", False)

            if valor_estimado is not None and not args.dry_run:
                updated = db_execute(
                    """
                        UPDATE itens
                        SET valor_estimado = %s
                        WHERE contratacao_id = %s AND numero_item = %s
                          AND valor_estimado IS NULL
                    """,
                    (valor_estimado, str(ct_id), numero_item),
                )
                if updated:
                    stats["estimados_preenchidos"] += 1

            if situacao != 2 or not tem_resultado:
                stats["itens_sem_resultado"] += 1
                continue

            url_resultado = RESULTADO_URL_TPL.format(cnpj=cnpj, ano=ano, seq=seq, item=numero_item)
            resultado = _get_json(url_resultado, retries=1)
            if not resultado:
                stats["itens_sem_resultado"] += 1
                time.sleep(SLEEP_ENTRE_RESULTADOS)
                continue

            results = resultado if isinstance(resultado, list) else [resultado]
            for r in results:
                valor_homologado = _float_positive(r.get("valorUnitarioHomologado"))
                if valor_homologado is None:
                    continue

                if not args.dry_run:
                    db_execute(
                        """
                            UPDATE itens
                            SET valor_homologado = %s,
                                valor_unitario = %s,
                                tipo_preco = 'homologado'
                            WHERE contratacao_id = %s AND numero_item = %s
                        """,
                        (valor_homologado, valor_homologado, str(ct_id), numero_item),
                    )
                stats["itens_atualizados"] += 1
                tem_homologado = True
                break

            time.sleep(SLEEP_ENTRE_RESULTADOS)

        if tem_homologado:
            stats["contratacoes_com_homologado"] += 1

        stats["processadas"] += 1
        time.sleep(SLEEP_ENTRE_CONTRATACOES)

        if idx % 100 == 0 or idx == total:
            logger.info(
                "[%d/%d] atualiz=%d estimados=%d sem_resultado=%d erros=%d",
                idx,
                total,
                stats["itens_atualizados"],
                stats["estimados_preenchidos"],
                stats["itens_sem_resultado"],
                stats["erros_api"],
            )

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Contratacoes processadas: {stats['processadas']}/{total}")
    print(f"Contratacoes com homologado: {stats['contratacoes_com_homologado']}")
    print(f"Itens atualizados para homologado: {stats['itens_atualizados']}")
    print(f"Valor estimado preenchido: {stats['estimados_preenchidos']}")
    print(f"Itens sem resultado: {stats['itens_sem_resultado']}")
    print(f"Erros API: {stats['erros_api']}")
    if args.dry_run:
        print("(DRY RUN - nenhuma alteracao no banco)")


def _recover_estimado(conn, dry_run: bool):
    """Recupera valor_estimado dos itens que ja foram atualizados para homologado."""
    try:
        if conn.closed:
            conn = psycopg2.connect(DB_DSN, connect_timeout=10)
            conn.autocommit = False
    except Exception:
        conn = psycopg2.connect(DB_DSN, connect_timeout=10)
        conn.autocommit = False

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ct.id, o.cnpj, ct.numero_controle_pncp, i.numero_item
            FROM itens i
            JOIN contratacoes ct ON ct.id = i.contratacao_id
            JOIN orgaos o ON o.id = ct.orgao_id
            WHERE i.tipo_preco = 'homologado' AND i.valor_estimado IS NULL
            ORDER BY ct.id, i.numero_item
            """
        )
        rows = cur.fetchall()

    logger.info("Itens para recuperar valor_estimado: %d", len(rows))
    recovered = 0
    errors = 0

    from itertools import groupby

    for (ct_id, cnpj, numero_controle), group in groupby(rows, key=lambda r: (r[0], r[1], r[2])):
        items_to_fix = [r[3] for r in group]

        try:
            seq, ano = _parse_numero_controle(numero_controle)
        except Exception:
            errors += len(items_to_fix)
            continue

        url_itens = ITEMS_URL_TPL.format(cnpj=cnpj, ano=ano, seq=seq)
        api_itens = _get_json(url_itens)
        if not api_itens:
            errors += len(items_to_fix)
            time.sleep(SLEEP_ENTRE_CONTRATACOES)
            continue

        items_list = api_itens if isinstance(api_itens, list) else api_itens.get("data", [])
        api_map = {int(it.get("numeroItem", 0)): it for it in items_list}

        for num_item in items_to_fix:
            api_item = api_map.get(num_item)
            if not api_item:
                errors += 1
                continue

            valor_estimado = _float_positive(api_item.get("valorUnitarioEstimado"))
            if valor_estimado is None:
                errors += 1
                continue

            if not dry_run:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                            UPDATE itens
                            SET valor_estimado = %s
                            WHERE contratacao_id = %s AND numero_item = %s
                        """,
                        (valor_estimado, str(ct_id), num_item),
                    )
                    conn.commit()
            recovered += 1

        time.sleep(SLEEP_ENTRE_CONTRATACOES)

    logger.info("Recuperados: %d, erros: %d", recovered, errors)


if __name__ == "__main__":
    main()
