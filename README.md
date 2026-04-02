# Banco de Preços — LaaS (Licitações as a Service)

Sistema de referência de preços para licitações públicas, com correção monetária IPCA, busca semântica, alertas de sobrepreço e API pública.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + Python 3.12 |
| Banco | PostgreSQL 15 + pgvector |
| Frontend | React + Vite + TypeScript + Tailwind |
| Migrations | Alembic |
| Testes | pytest (backend) + vitest (frontend) |

## Estrutura

```
banco-de-precos/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app + routers
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routers/           # Endpoints REST
│   │   ├── services/          # Lógica de negócio
│   │   ├── middleware/        # Security headers
│   │   └── core/              # Config, database
│   ├── alembic/               # Migrations
│   ├── scripts/               # healthcheck.sh, etc.
│   ├── docs/                  # API.md, METODOLOGIA.md, IPCA.md
│   └── tests/                 # 1066 testes pytest
├── frontend/
│   └── src/
│       ├── components/        # BuscaSemantica, AlertaSobrepreco, etc.
│       └── pages/             # Dashboard, Documentacao
├── TASK_S15_S20.md            # Checklist semanas 15–20
├── RELEASE_NOTES_V3.md        # Changelog completo V3
└── README.md                  # Este arquivo
```

## Rodando localmente

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Banco de dados

```
Host: localhost:5435
DB:   bancodeprecos
User: bancodeprecos
Pass: bancodeprecos_dev
```

## Testes

```bash
# Backend (1066 testes)
cd backend && python3 -m pytest --tb=short -q

# Frontend (116 testes)
cd frontend && npm test -- --run
```

## API Principal

| Rota | Descrição |
|------|-----------|
| `GET /api/v1/analise/precos` | Consulta de preços com filtros |
| `POST /api/v1/analise/relatorio` | Gera relatório PDF |
| `GET /api/v1/correcao/ipca` | Série histórica IPCA |
| `POST /api/v1/correcao/preco` | Corrige valor pelo IPCA |
| `GET /api/v1/busca/semantica` | Busca semântica por pgvector |
| `GET /api/v1/busca/combinada` | Busca híbrida (semântica + FTS) |
| `POST /api/v1/alertas/avaliar` | Avalia sobrepreço |
| `GET /api/v1/admin/saude` | Health check detalhado |
| `GET /api/v1/admin/export` | Export JSON completo |
| `GET /api/v1/public/precos` | API pública com API key |
| `POST /api/v1/onboarding/setup` | Wizard novo tenant |

## Healthcheck

```bash
cd backend && bash scripts/healthcheck.sh
```

## Versão

**V3** — Semanas 1–20 concluídas | 1066 testes backend | 116 testes frontend
