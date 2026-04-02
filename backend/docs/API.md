# API — Banco de Preços

## Base URL
`http://localhost:8000/api/v1`

## Autenticação
- Endpoints `/public/*`: API key via header `X-API-Key` (opcional para demo)
- Endpoints privados: JWT via header `Authorization: Bearer <token>`

## Endpoints Públicos

### GET /public/precos
Consulta pública de preços.
- `uf` (str, opcional): Filtro por UF
- `categoria` (str, opcional): Filtro por categoria
- `pagina` (int, default 1)
- `por_pagina` (int, default 20, max 50)

### GET /public/categorias
Lista categorias disponíveis.

### GET /public/ipca/fator
Fator de correção IPCA entre duas datas.
- `data_inicio` (str, obrigatório): YYYY-MM-DD
- `data_fim` (str, obrigatório): YYYY-MM-DD

## Endpoints de Análise

### GET /analise/precos
Lista preços com filtros avançados.

### GET /analise/tendencias
Tendências de preço por categoria/UF.

### GET /analise/comparativo
Comparativo entre UFs.

### GET /analise/benchmark/uf
Ranking de preços por UF.

### GET /analise/benchmark/evolucao
Série temporal regional.

### GET /analise/precos-corrigidos
Preços com correção monetária IPCA.

## Endpoints de Correção Monetária

### GET /correcao/ipca
Série histórica IPCA.

### GET /correcao/fator
Fator de correção entre duas datas.

### POST /correcao/preco
Corrige um preço pelo IPCA.
Body: `{ "valor": 100, "data_origem": "2020-01-01", "data_destino": "2026-01-01" }`

## Endpoints de Alertas

### POST /alertas/avaliar
Avalia sobrepreço.
Body: `{ "item_descricao": "...", "valor": 30.0, "uf": "SP", "categoria": "Papel A4" }`

### GET /alertas/historico
Histórico de alertas por tenant.

### GET /alertas/estatisticas
Resumo por categoria/UF.

## Endpoints Admin

### GET /admin/metricas
Métricas de uso (requer admin).

### GET /admin/saude
Health check detalhado.

### GET /admin/auditoria
Log de ações (paginado).
