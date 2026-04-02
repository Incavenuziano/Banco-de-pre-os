# Semana 14 — Integração com Plataforma de Análise & Dashboard

## Status: ✅ CONCLUÍDA

**Data:** 2026-03-31
**Testes:** 634 backend (pytest) + 43 frontend (Vitest) = **677 total**
**Testes novos adicionados:** 92 backend + 43 frontend = **135 novos**
**Testes anteriores:** 542 (todos passando, sem regressões)

---

## Entregáveis

### 1. Backend — Novos Endpoints REST (8+)

**Novo router:** `app/routers/analise.py` (prefixo `/api/v1/analise`)

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/v1/analise/precos` | GET | Lista preços com filtros avançados + paginação |
| `/api/v1/analise/tendencias` | GET | Série temporal de preços por categoria × UF |
| `/api/v1/analise/comparativo` | GET | Ranking de preços entre UFs para uma categoria |
| `/api/v1/analise/dashboard` | GET | KPIs agregados para o dashboard |
| `/api/v1/analise/exportar/csv` | GET | Exportação CSV (UTF-8-BOM, compatível Excel) |
| `/api/v1/analise/categorias` | GET | Lista de categorias disponíveis |
| `/api/v1/analise/ufs` | GET | Lista de UFs validadas |
| `/api/v1/analise/mapa/precos` | GET | Dados para mapa coroplético por UF |

**Filtros disponíveis em `/precos` e `/exportar/csv`:**
- `uf` — sigla da UF (ex: SP, RJ)
- `categoria` — nome da categoria
- `data_inicio` / `data_fim` — formato YYYY-MM-DD
- `preco_min` / `preco_max` — faixa de preço
- `pagina` / `por_pagina` — paginação

### 2. Backend — Novo Serviço

**Arquivo:** `app/services/analise_service.py`

- `AnaliseService` com 7 métodos principais
- 15 categorias cobertas, 20 UFs (inclui as 15 validadas)
- Preços realistas baseados em dados de mercado brasileiro
- Variação determinística por mês/ano (sem randomness)
- Exportação CSV com UTF-8-BOM

### 3. Frontend React (Vite + TypeScript + Tailwind)

**Localização:** `frontend/`  
**Porta:** 3000  
**Proxy:** `/api` → `http://localhost:8000`

#### Componentes (8+)

| Componente | Arquivo | Descrição |
|---|---|---|
| `KPICard` | `components/KPICard.tsx` | Card de indicador com cor, ícone e subtítulo |
| `FiltrosAvancados` | `components/FiltrosAvancados.tsx` | Formulário de filtros: UF, categoria, datas, preço |
| `TabelaPrecos` | `components/TabelaPrecos.tsx` | Tabela responsiva com paginação |
| `GraficoTendencias` | `components/GraficoTendencias.tsx` | LineChart (Recharts) multi-UF |
| `GraficoComparativo` | `components/GraficoComparativo.tsx` | BarChart com ranking por UF |
| `BotaoExportar` | `components/BotaoExportar.tsx` | Dispara download CSV com filtros ativos |
| `SeletorCategoria` | `components/SeletorCategoria.tsx` | Select reutilizável de categoria |
| `LoadingSpinner` | `components/LoadingSpinner.tsx` | Spinner acessível (role=status) |
| `ErroAlerta` | `components/ErroAlerta.tsx` | Alerta de erro (role=alert) |

#### Página Principal

`pages/Dashboard.tsx` — Dashboard completo com:
- KPIs: total registros, UFs cobertas, categorias, última atualização
- Gráfico de tendências (Recharts LineChart)
- Gráfico comparativo entre UFs (Recharts BarChart)
- Tabela com filtros avançados e paginação
- Botão de exportação CSV

#### API Client

`api/analise.ts` — Wrapper typed para todos os endpoints

### 4. Testes

#### Backend (pytest) — 92 novos

- `tests/test_analise_service.py` — 49 testes do serviço
- `tests/test_api_analise.py` — 43 testes dos endpoints API

**Inclui:**
- Testes de performance (< 1s) para todos os endpoints principais
- Testes de filtros (UF, categoria, data, faixa de preço)
- Testes de paginação
- Testes de exportação CSV

#### Frontend (Vitest) — 43 novos

- `src/test/components.test.tsx` — Todos os 9 componentes testados

**Inclui:**
- Testes de renderização
- Testes de interação (filtrar, limpar, exportar, paginar)
- Testes de estados (carregando, vazio, erro)
- Testes de acessibilidade (roles: alert, status, combobox)

### 5. Performance

Todos os endpoints testados com `< 1s` de latência:
- `/analise/precos` — sem banco de dados, pure Python ✓
- `/analise/tendencias` — cálculo determinístico ✓
- `/analise/comparativo` — ranking in-memory ✓
- `/analise/dashboard` — agregação in-memory ✓
- `/analise/mapa/precos` — chamada interna ao comparativo ✓

---

## Como Executar

### Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev   # localhost:3000
```

### Testes
```bash
# Backend
cd backend
python3 -m pytest

# Frontend
cd frontend
npm test
```

### Documentação API
Acesse: `http://localhost:8000/docs` (Swagger/OpenAPI automático via FastAPI)

---

## Próximos Passos (Semana 15)

- [ ] Conectar ao banco PostgreSQL real (substituir dados mock)
- [ ] Autenticação por tenant nos novos endpoints
- [ ] Cache Redis para queries do dashboard
- [ ] Relatório PDF com gráficos embutidos
- [ ] PWA offline-first para acesso mobile
