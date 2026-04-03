"""Classifica itens sem categoria usando ClassificadorRegex.

Busca itens sem associação em item_categoria, aplica regex e insere
os resultados com score >= 0.5 em batches de 100.
"""

import sys
import os

# Adiciona o backend ao path para importar o classificador
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import psycopg2
import psycopg2.extras
from app.services.classificador_regex import ClassificadorRegex

DB_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://bancodeprecos:bancodeprecos_dev@localhost:5435/bancodeprecos",
)

BATCH_SIZE = 100


def main():
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Carregar categorias para o mapeamento nome→id
        cur.execute("SELECT id, nome FROM categorias")
        categorias = [{"id": str(row["id"]), "nome": row["nome"]} for row in cur.fetchall()]
        cat_map = {c["nome"]: c["id"] for c in categorias}
        print(f"Categorias carregadas: {len(categorias)}")

        classificador = ClassificadorRegex(categorias)

        # Buscar itens sem categoria
        cur.execute("""
            SELECT i.id, i.descricao
            FROM itens i
            LEFT JOIN item_categoria ic ON i.id = ic.item_id
            WHERE ic.item_id IS NULL
              AND i.descricao IS NOT NULL
        """)
        itens_sem_cat = cur.fetchall()
        print(f"Itens sem categoria: {len(itens_sem_cat)}")

        classificados = 0
        nao_classificados = 0
        batch = []

        for item in itens_sem_cat:
            resultado = classificador.classificar(item["descricao"])
            if resultado and resultado.get("score", 0) >= 0.5:
                cat_id = resultado.get("categoria_id")
                if not cat_id:
                    # Tentar buscar pelo nome da categoria
                    cat_id = cat_map.get(resultado["categoria_nome"])
                if cat_id:
                    batch.append((
                        str(item["id"]),
                        str(cat_id),
                        resultado["score"],
                        resultado["metodo"],
                    ))
                    classificados += 1
                else:
                    nao_classificados += 1
            else:
                nao_classificados += 1

            if len(batch) >= BATCH_SIZE:
                _inserir_batch(cur, batch)
                conn.commit()
                print(f"  Batch inserido: {len(batch)} registros")
                batch = []

        # Inserir batch restante
        if batch:
            _inserir_batch(cur, batch)
            conn.commit()
            print(f"  Batch final inserido: {len(batch)} registros")

    conn.close()
    print(f"\nResultado: {classificados} classificados, {nao_classificados} não classificados")


def _inserir_batch(cur, batch):
    """Insere batch de classificações em item_categoria."""
    for item_id, cat_id, score, metodo in batch:
        cur.execute("""
            INSERT INTO item_categoria (item_id, categoria_id, score_confianca, metodo_classificacao)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (item_id, categoria_id) DO NOTHING
        """, (item_id, cat_id, score, metodo))


if __name__ == "__main__":
    main()
