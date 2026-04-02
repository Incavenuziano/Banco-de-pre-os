"""Router FastAPI para busca de itens e categorias."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.busca import BuscaResponse, CategoriaResponse, ItemBusca
from app.seeds.categorias import CATEGORIAS
from app.services.embeddings_service import EmbeddingsService

_embeddings = EmbeddingsService()

router = APIRouter(prefix="/api/v1/busca", tags=["busca"])

# Mock data com 30 itens de exemplo
ITENS_MOCK: list[dict] = [
    {"id": 1, "descricao": "Papel Sulfite A4 75g/m² - Resma 500 folhas", "categoria": "Papel A4", "preco_mediano": 22.50, "n_amostras": 45, "uf": "SP", "data_ultima_atualizacao": "2025-12-01"},
    {"id": 2, "descricao": "Detergente Líquido Neutro 500ml", "categoria": "Detergente", "preco_mediano": 2.80, "n_amostras": 38, "uf": "SP", "data_ultima_atualizacao": "2025-11-15"},
    {"id": 3, "descricao": "Gasolina Comum - Litro", "categoria": "Gasolina Comum", "preco_mediano": 5.89, "n_amostras": 120, "uf": "SP", "data_ultima_atualizacao": "2025-12-10"},
    {"id": 4, "descricao": "Toner HP CF258A compatível", "categoria": "Toner para Impressora", "preco_mediano": 89.90, "n_amostras": 22, "uf": "RJ", "data_ultima_atualizacao": "2025-10-20"},
    {"id": 5, "descricao": "Cadeira de Escritório Giratória com Braço", "categoria": "Cadeira de Escritório", "preco_mediano": 450.00, "n_amostras": 15, "uf": "MG", "data_ultima_atualizacao": "2025-09-30"},
    {"id": 6, "descricao": "Arroz Tipo 1 - Pacote 5kg", "categoria": "Arroz", "preco_mediano": 25.90, "n_amostras": 60, "uf": "RS", "data_ultima_atualizacao": "2025-12-05"},
    {"id": 7, "descricao": "Feijão Carioca Tipo 1 - Pacote 1kg", "categoria": "Feijão", "preco_mediano": 8.50, "n_amostras": 55, "uf": "PR", "data_ultima_atualizacao": "2025-11-28"},
    {"id": 8, "descricao": "Pneu 175/70 R13 para veículo leve", "categoria": "Pneu", "preco_mediano": 320.00, "n_amostras": 18, "uf": "SP", "data_ultima_atualizacao": "2025-10-15"},
    {"id": 9, "descricao": "Uniforme Escolar Camiseta Manga Curta", "categoria": "Uniforme Escolar", "preco_mediano": 28.00, "n_amostras": 30, "uf": "BA", "data_ultima_atualizacao": "2025-08-20"},
    {"id": 10, "descricao": "Notebook 15.6 polegadas 8GB RAM 256GB SSD", "categoria": "Notebook", "preco_mediano": 3200.00, "n_amostras": 25, "uf": "SP", "data_ultima_atualizacao": "2025-12-01"},
    {"id": 11, "descricao": "Álcool Gel 70% - Frasco 500ml", "categoria": "Álcool Gel", "preco_mediano": 7.90, "n_amostras": 42, "uf": "SP", "data_ultima_atualizacao": "2025-11-10"},
    {"id": 12, "descricao": "Caneta Esferográfica Azul", "categoria": "Caneta Esferográfica", "preco_mediano": 1.20, "n_amostras": 50, "uf": "RJ", "data_ultima_atualizacao": "2025-10-05"},
    {"id": 13, "descricao": "Cimento Portland CP-II 50kg", "categoria": "Cimento Portland", "preco_mediano": 34.00, "n_amostras": 28, "uf": "MG", "data_ultima_atualizacao": "2025-09-15"},
    {"id": 14, "descricao": "Diesel S10 - Litro", "categoria": "Diesel S10", "preco_mediano": 6.29, "n_amostras": 95, "uf": "SP", "data_ultima_atualizacao": "2025-12-10"},
    {"id": 15, "descricao": "Luva de Procedimento Látex M - Caixa 100un", "categoria": "Luva de Procedimento", "preco_mediano": 32.00, "n_amostras": 35, "uf": "SP", "data_ultima_atualizacao": "2025-11-20"},
    {"id": 16, "descricao": "Impressora Multifuncional Laser Mono", "categoria": "Impressora", "preco_mediano": 1800.00, "n_amostras": 12, "uf": "SP", "data_ultima_atualizacao": "2025-10-01"},
    {"id": 17, "descricao": "Desinfetante Lavanda 2 Litros", "categoria": "Desinfetante", "preco_mediano": 6.50, "n_amostras": 40, "uf": "PR", "data_ultima_atualizacao": "2025-11-05"},
    {"id": 18, "descricao": "Óleo de Soja Refinado 900ml", "categoria": "Óleo de Soja", "preco_mediano": 7.80, "n_amostras": 48, "uf": "GO", "data_ultima_atualizacao": "2025-12-02"},
    {"id": 19, "descricao": "Tinta Acrílica Branca 18L", "categoria": "Tinta Acrílica", "preco_mediano": 189.00, "n_amostras": 20, "uf": "MG", "data_ultima_atualizacao": "2025-09-20"},
    {"id": 20, "descricao": "Lâmpada LED Bulbo 9W E27", "categoria": "Lâmpada LED", "preco_mediano": 8.50, "n_amostras": 33, "uf": "SP", "data_ultima_atualizacao": "2025-10-25"},
    {"id": 21, "descricao": "Papel Higiênico Folha Dupla 30m - Fardo 64 rolos", "categoria": "Papel Higiênico", "preco_mediano": 52.00, "n_amostras": 36, "uf": "SP", "data_ultima_atualizacao": "2025-11-18"},
    {"id": 22, "descricao": "Mesa de Escritório 120x60cm MDP", "categoria": "Mesa de Escritório", "preco_mediano": 380.00, "n_amostras": 14, "uf": "RJ", "data_ultima_atualizacao": "2025-08-30"},
    {"id": 23, "descricao": "Monitor LED 21.5 polegadas Full HD", "categoria": "Monitor", "preco_mediano": 680.00, "n_amostras": 19, "uf": "SP", "data_ultima_atualizacao": "2025-11-25"},
    {"id": 24, "descricao": "Açúcar Cristal 5kg", "categoria": "Açúcar", "preco_mediano": 18.90, "n_amostras": 44, "uf": "SP", "data_ultima_atualizacao": "2025-12-03"},
    {"id": 25, "descricao": "Leite Integral UHT 1 Litro", "categoria": "Leite", "preco_mediano": 5.20, "n_amostras": 52, "uf": "MG", "data_ultima_atualizacao": "2025-12-08"},
    {"id": 26, "descricao": "Saco de Lixo 100L Preto - Pacote 100un", "categoria": "Saco de Lixo", "preco_mediano": 28.00, "n_amostras": 30, "uf": "SP", "data_ultima_atualizacao": "2025-10-12"},
    {"id": 27, "descricao": "Máscara Cirúrgica Tripla - Caixa 50un", "categoria": "Máscara Cirúrgica", "preco_mediano": 12.00, "n_amostras": 38, "uf": "SP", "data_ultima_atualizacao": "2025-11-08"},
    {"id": 28, "descricao": "Etanol Hidratado - Litro", "categoria": "Etanol", "preco_mediano": 3.89, "n_amostras": 85, "uf": "SP", "data_ultima_atualizacao": "2025-12-10"},
    {"id": 29, "descricao": "Bota de Segurança PVC Cano Médio", "categoria": "Bota de Segurança", "preco_mediano": 45.00, "n_amostras": 16, "uf": "SC", "data_ultima_atualizacao": "2025-09-10"},
    {"id": 30, "descricao": "Envelope Pardo A4 - Pacote 250un", "categoria": "Envelope", "preco_mediano": 65.00, "n_amostras": 21, "uf": "RJ", "data_ultima_atualizacao": "2025-10-30"},
]


@router.get("/itens")
def buscar_itens(
    q: str = Query(..., min_length=3, description="Texto de busca (mínimo 3 caracteres)"),
    uf: str | None = Query(None, description="Filtro por UF"),
    categoria_id: int | None = Query(None, description="Filtro por ID de categoria"),
    data_inicio: str | None = Query(None, description="Data início (YYYY-MM-DD)"),
    data_fim: str | None = Query(None, description="Data fim (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> BuscaResponse:
    """Busca itens por texto livre com filtros opcionais.

    Realiza busca textual na descrição dos itens mockados.
    """
    q_lower = q.lower()
    resultados = [
        item for item in ITENS_MOCK
        if q_lower in item["descricao"].lower()
    ]

    # Filtro por UF
    if uf:
        uf_upper = uf.upper()
        resultados = [item for item in resultados if item.get("uf") == uf_upper]

    # Busca semântica quando query tem mais de 3 tokens e busca textual não achou
    tokens_query = _embeddings._tokenizar(q)
    if len(tokens_query) > 3 and not resultados:
        corpus = [item["descricao"] for item in ITENS_MOCK]
        similares = _embeddings.buscar_similares(q, corpus, top_n=10)
        indices = [s["indice"] for s in similares if s["score"] > 0]
        resultados = [ITENS_MOCK[i] for i in indices]
        if uf:
            uf_upper = uf.upper()
            resultados = [item for item in resultados if item.get("uf") == uf_upper]

    total = len(resultados)
    inicio = (page - 1) * page_size
    fim = inicio + page_size
    pagina = resultados[inicio:fim]

    return BuscaResponse(
        total=total,
        page=page,
        page_size=page_size,
        itens=[ItemBusca(**item) for item in pagina],
    )


@router.get("/semantica")
def busca_semantica(
    q: str = Query(..., min_length=3, description="Texto de busca semântica"),
    top_n: int = Query(10, ge=1, le=50, description="Número de resultados"),
) -> dict:
    """Busca por similaridade semântica (TF-IDF + cosseno).

    Retorna os itens mais similares à query ordenados por score.
    """
    corpus = [item["descricao"] for item in ITENS_MOCK]
    similares = _embeddings.buscar_similares(q, corpus, top_n=top_n)

    resultados = []
    for s in similares:
        if s["score"] > 0:
            item = ITENS_MOCK[s["indice"]]
            resultados.append({
                **item,
                "score_similaridade": round(s["score"], 4),
            })

    return {
        "query": q,
        "metodo": "semantica",
        "total": len(resultados),
        "resultados": resultados,
    }


@router.get("/full-text")
def busca_full_text(
    q: str = Query(..., min_length=2, description="Texto para busca full-text"),
    uf: str | None = Query(None, description="Filtro por UF"),
) -> dict:
    """Busca textual simples (substring match, case-insensitive).

    Simula ts_vector do PostgreSQL FTS.
    """
    q_lower = q.lower()
    # Tokenizar query para busca por termos individuais
    tokens = _embeddings._tokenizar(q)

    resultados = []
    for item in ITENS_MOCK:
        desc_lower = item["descricao"].lower()
        # Match: substring ou todos os tokens presentes
        if q_lower in desc_lower or all(t in desc_lower for t in tokens):
            if uf and item.get("uf", "").upper() != uf.upper():
                continue
            # Score baseado em quantos tokens aparecem
            matches = sum(1 for t in tokens if t in desc_lower)
            score = round(matches / max(len(tokens), 1), 4)
            resultados.append({**item, "score_relevancia": score})

    resultados.sort(key=lambda x: x["score_relevancia"], reverse=True)

    return {
        "query": q,
        "metodo": "full_text",
        "total": len(resultados),
        "resultados": resultados,
    }


@router.get("/combinada")
def busca_combinada(
    q: str = Query(..., min_length=3, description="Texto de busca"),
    peso_semantica: float = Query(0.6, ge=0, le=1, description="Peso da busca semântica"),
    top_n: int = Query(10, ge=1, le=50),
) -> dict:
    """Busca híbrida: combina semântica + full-text com score ponderado."""
    peso_textual = round(1 - peso_semantica, 2)

    # Busca semântica
    corpus = [item["descricao"] for item in ITENS_MOCK]
    similares = _embeddings.buscar_similares(q, corpus, top_n=30)
    scores_semantica: dict[int, float] = {}
    for s in similares:
        scores_semantica[s["indice"]] = s["score"]

    # Busca full-text
    q_lower = q.lower()
    tokens = _embeddings._tokenizar(q)
    scores_textual: dict[int, float] = {}
    for i, item in enumerate(ITENS_MOCK):
        desc_lower = item["descricao"].lower()
        if q_lower in desc_lower or any(t in desc_lower for t in tokens):
            matches = sum(1 for t in tokens if t in desc_lower)
            scores_textual[i] = matches / max(len(tokens), 1)

    # Combinar scores
    todos_indices = set(scores_semantica.keys()) | set(scores_textual.keys())
    combinados = []
    for idx in todos_indices:
        s_sem = scores_semantica.get(idx, 0)
        s_txt = scores_textual.get(idx, 0)
        score_final = round(s_sem * peso_semantica + s_txt * peso_textual, 4)
        if score_final > 0:
            combinados.append({
                **ITENS_MOCK[idx],
                "score_combinado": score_final,
                "score_semantica": round(s_sem, 4),
                "score_textual": round(s_txt, 4),
            })

    combinados.sort(key=lambda x: x["score_combinado"], reverse=True)

    return {
        "query": q,
        "metodo": "combinada",
        "pesos": {"semantica": peso_semantica, "textual": peso_textual},
        "total": len(combinados[:top_n]),
        "resultados": combinados[:top_n],
    }


@router.get("/categorias")
def listar_categorias() -> list[CategoriaResponse]:
    """Retorna lista das 50 categorias prioritárias para compras municipais."""
    return [
        CategoriaResponse(
            id=i + 1,
            nome=cat["nome"],
            familia=cat["familia"],
            descricao=cat["descricao"],
        )
        for i, cat in enumerate(CATEGORIAS)
    ]
