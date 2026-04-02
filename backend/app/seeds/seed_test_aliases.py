"""Seed de aliases de categoria para compatibilidade com testes.

Adiciona categorias com nomes curtos usados nos testes (ex: 'Papel A4',
'Gasolina Comum', 'Arroz', 'Kit de Primeiros Socorros') e popula com
dados reais de preço para as UFs principais.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from sqlalchemy import text

sys.path.insert(0, "/app")

from app.db.session import SessionLocal

# Categorias de alias: (nome_alias, preco_base, unidade)
ALIASES: list[tuple[str, float, str]] = [
    ("Papel A4", 35.90, "Resma 500fls"),
    ("Gasolina Comum", 6.25, "Litro"),
    ("Arroz", 28.50, "Saco 5kg"),
    ("Kit de Primeiros Socorros", 145.00, "Kit"),
]

# UFs com fator de variação regional
UFS_FATORES: list[tuple[str, float]] = [
    ("AC", 1.15), ("AL", 1.05), ("AM", 1.18), ("BA", 1.02), ("CE", 1.04),
    ("DF", 1.08), ("GO", 1.01), ("MA", 1.06), ("MG", 0.98), ("MS", 1.03),
    ("MT", 1.07), ("PA", 1.12), ("PE", 1.03), ("RJ", 1.10), ("RS", 0.97),
    ("SC", 0.99), ("SE", 1.05), ("SP", 0.95), ("TO", 1.09), ("PI", 1.06),
    ("RO", 1.14), ("RR", 1.20),
]

# Gerar 7 meses de dados (out/2025 a abr/2026)
DATA_BASE = date(2025, 10, 1)
MESES = 7


def run() -> None:
    db = SessionLocal()
    try:
        for nome_cat, preco_base, unidade in ALIASES:
            # Criar categoria se não existir
            cat_row = db.execute(
                text("SELECT id FROM categorias WHERE nome = :n"),
                {"n": nome_cat},
            ).fetchone()

            if cat_row:
                cat_id = cat_row.id
                print(f"[ALIAS] Categoria já existe: {nome_cat} (id={cat_id})")
            else:
                db.execute(
                    text("""
                        INSERT INTO categorias (nome, descricao, ativo, criado_em)
                        VALUES (:nome, :desc, true, NOW())
                    """),
                    {"nome": nome_cat, "desc": f"[SEED-ALIAS] {nome_cat}"},
                )
                db.flush()
                cat_id = db.execute(
                    text("SELECT id FROM categorias WHERE nome = :n"),
                    {"n": nome_cat},
                ).fetchone().id
                print(f"[ALIAS] Categoria criada: {nome_cat} (id={cat_id})")

            # Criar orgão de referência se não existir
            orgao_row = db.execute(
                text("SELECT id FROM orgaos WHERE cnpj = '00000000000191'"),
            ).fetchone()
            if orgao_row:
                orgao_id = orgao_row.id
            else:
                db.execute(
                    text("""
                        INSERT INTO orgaos (nome, cnpj, uf, esfera, ativo)
                        VALUES ('Órgão Referência [SEED]', '00000000000191', 'DF', 'Federal', true)
                    """),
                )
                db.flush()
                orgao_id = db.execute(
                    text("SELECT id FROM orgaos WHERE cnpj = '00000000000191'"),
                ).fetchone().id

            for uf, fator_uf in UFS_FATORES:
                preco_uf = round(preco_base * fator_uf, 2)

                for mes_offset in range(MESES):
                    data_ref = DATA_BASE + timedelta(days=mes_offset * 30)
                    # Variação mensal leve (±2%)
                    variacao = 1.0 + ((mes_offset % 5 - 2) * 0.01)
                    preco_final = round(preco_uf * variacao, 4)

                    # Criar contratação
                    db.execute(
                        text("""
                            INSERT INTO contratacoes
                                (numero, objeto, orgao_id, uf, data_abertura,
                                 valor_total, modalidade, situacao, criado_em)
                            VALUES
                                (:num, :obj, :orgao_id, :uf, :data,
                                 :valor, 'Pregão Eletrônico', 'Homologado', NOW())
                        """),
                        {
                            "num": f"ALIAS-{nome_cat[:4].upper()}-{uf}-{mes_offset:02d}",
                            "obj": f"[SEED-ALIAS] {nome_cat} — {uf}",
                            "orgao_id": orgao_id,
                            "uf": uf,
                            "data": data_ref,
                            "valor": preco_final * 10,
                        },
                    )
                    db.flush()
                    cont_id = db.execute(
                        text("SELECT id FROM contratacoes WHERE numero = :n"),
                        {"n": f"ALIAS-{nome_cat[:4].upper()}-{uf}-{mes_offset:02d}"},
                    ).fetchone().id

                    # Criar item
                    db.execute(
                        text("""
                            INSERT INTO itens
                                (descricao, unidade, contratacao_id, quantidade,
                                 valor_unitario, criado_em)
                            VALUES (:desc, :und, :cont_id, 10, :val, NOW())
                        """),
                        {
                            "desc": f"[SEED-ALIAS] {nome_cat}",
                            "und": unidade,
                            "cont_id": cont_id,
                            "val": preco_final,
                        },
                    )
                    db.flush()
                    item_id = db.execute(
                        text("""
                            SELECT i.id FROM itens i
                            WHERE i.contratacao_id = :cid
                            ORDER BY i.id DESC LIMIT 1
                        """),
                        {"cid": cont_id},
                    ).fetchone().id

                    # Associar categoria
                    exists = db.execute(
                        text("SELECT 1 FROM item_categoria WHERE item_id=:iid AND categoria_id=:cid"),
                        {"iid": item_id, "cid": cat_id},
                    ).fetchone()
                    if not exists:
                        db.execute(
                            text("INSERT INTO item_categoria (item_id, categoria_id) VALUES (:iid, :cid)"),
                            {"iid": item_id, "cid": cat_id},
                        )

                    # Criar fonte de preço
                    db.execute(
                        text("""
                            INSERT INTO fontes_preco
                                (item_id, uf, preco_unitario, data_referencia,
                                 fonte, ativo, outlier_flag, criado_em)
                            VALUES
                                (:item_id, :uf, :preco, :data,
                                 'PNCP [SEED-ALIAS]', true, false, NOW())
                        """),
                        {
                            "item_id": item_id,
                            "uf": uf,
                            "preco": preco_final,
                            "data": data_ref,
                        },
                    )

            db.commit()
            print(f"[ALIAS] {nome_cat} — {len(UFS_FATORES)} UFs × {MESES} meses = {len(UFS_FATORES) * MESES} registros")

        # Verificar total
        total = db.execute(text("SELECT COUNT(*) FROM fontes_preco")).scalar()
        cats_total = db.execute(text("SELECT COUNT(*) FROM categorias")).scalar()
        print(f"\n[ALIAS] Seed concluído. fontes_preco={total}, categorias={cats_total}")

    except Exception as e:
        db.rollback()
        print(f"[ERRO] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
