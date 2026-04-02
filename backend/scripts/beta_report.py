#!/usr/bin/env python3
"""Relatório do beta fechado — stats de onboarding, feedbacks e convites.

Uso:
    python scripts/beta_report.py

Para stats reais, configure DATABASE_URL e instale as dependências do projeto.
"""

from __future__ import annotations

import os


def main() -> None:
    """Imprime relatório do beta fechado."""
    db_url = os.getenv("DATABASE_URL", "não configurada")
    print("=" * 60)
    print("BANCO DE PREÇOS — Beta Fechado Report")
    print("=" * 60)
    print(f"DATABASE_URL: {db_url}")
    print()

    if db_url == "não configurada":
        print("⚠️  DATABASE_URL não configurada.")
        print("   Configure e rode novamente para stats reais.")
        print()
        print("Tabelas monitoradas:")
        print("  - feedbacks       (bug / sugestao / elogio, nota 1-5)")
        print("  - convites        (token único, aceito/pendente)")
        print("  - checklist_tenant (etapas por tenant)")
        return

    try:
        import sqlalchemy as sa

        engine = sa.create_engine(db_url)
        with engine.connect() as conn:
            total_feedbacks = conn.execute(sa.text("SELECT COUNT(*) FROM feedbacks")).scalar()
            media_nota = conn.execute(sa.text("SELECT ROUND(AVG(nota)::numeric, 2) FROM feedbacks")).scalar()
            por_tipo = conn.execute(
                sa.text("SELECT tipo, COUNT(*) FROM feedbacks GROUP BY tipo ORDER BY tipo")
            ).fetchall()
            convites_total = conn.execute(sa.text("SELECT COUNT(*) FROM convites")).scalar()
            convites_pendentes = conn.execute(
                sa.text("SELECT COUNT(*) FROM convites WHERE aceito = false")
            ).scalar()

        print(f"Feedbacks total : {total_feedbacks}")
        print(f"Nota média      : {media_nota}")
        print("Por tipo:")
        for tipo, qtd in por_tipo:
            print(f"  {tipo:15s} {qtd}")
        print()
        print(f"Convites total    : {convites_total}")
        print(f"Convites pendentes: {convites_pendentes}")
    except Exception as exc:
        print(f"Erro ao conectar no banco: {exc}")


if __name__ == "__main__":
    main()
