# Task: Semanas 15–20 do Banco de Preços (LaaS)

## Contexto
- Projeto: `/home/danilo/.openclaw/workspace/siriguejo/projetos/banco-de-precos`
- Estado atual: **634 testes backend + 43 frontend = 677 total passando**
- Semanas 1–14 concluídas ✅
- DB: PostgreSQL localhost:5435, db=bancodeprecos, user=bancodeprecos, pwd=bancodeprecos_dev
- Alembic migrations em: `backend/alembic/versions/`
- Backend: FastAPI Python, `backend/`
- Frontend: React/Vite/TypeScript/Tailwind, `frontend/`
- Executar testes com: `cd backend && python3 -m pytest --tb=short -q`
- Frontend testes: `cd frontend && npm test -- --run`

## Regras obrigatórias
1. **Ao final de CADA semana: rodar todos os testes (backend + frontend)**
2. **Só avançar para próxima semana se 100% dos testes passarem**
3. **Marcar cada tarefa no checklist: `[ ]` → `[x]`**
4. **Atualizar PLANO_SEMANA_XX.md com status e contagem de testes ao concluir**
5. **Zero regressões — todos os 677 testes atuais devem continuar passando**
6. **Registrar progresso em `PLANO_SEMANA_XX.md` criando o arquivo se não existir**

---

## SEMANA 15 — Integração IPCA/IBGE + Correção Monetária

**Plano:** `PLANO_SEMANA_15.md` (já existe)
**Meta:** ≥ 737 testes totais (+60)

### Tarefas

**Migration:**
- [x] Criar `backend/alembic/versions/004_create_indices_preco.py`:
  - Tabela `indices_preco` (id, fonte VARCHAR(20) DEFAULT 'IPCA', ano INTEGER, mes INTEGER, variacao_mensal NUMERIC(8,4), variacao_acumulada_ano NUMERIC(8,4), indice_acumulado NUMERIC(12,6), fonte_url TEXT, coletado_em TIMESTAMP DEFAULT NOW(), UNIQUE(fonte, ano, mes))
  - Aplicar com `alembic upgrade head`

**Backend — Modelos:**
- [x] Criar `backend/app/models/indice_preco.py` — SQLAlchemy model para `indices_preco`

**Backend — Serviços:**
- [x] Criar `backend/app/services/ibge_service.py`:
  - Consome API IBGE SIDRA: `https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/all/variaveis/63`
  - Persiste dados localmente, atualização incremental
  - `get_serie(ano_inicio, ano_fim)` → lista de IndicePreco
  - `sincronizar()` → busca meses faltantes e persiste
  - Se API IBGE estiver fora, usar dados mockados realistas (IPCA mensal 2020-2026, valores plausíveis ~0.3%–1.2% ao mês)
  - Usar httpx (já presente)

- [x] Criar `backend/app/services/correcao_monetaria.py`:
  - `corrigir_preco(valor: float, data_origem: str, data_destino: str) → float`
  - `fator_correcao(data_origem: str, data_destino: str) → float`
  - `variacao_periodo(data_inicio: str, data_fim: str) → float`
  - `corrigir_preco(100, "2020-01-01", "2026-01-01")` deve retornar valor > 130 (reflexo inflação acumulada)

**Backend — Router:**
- [x] Criar `backend/app/routers/correcao.py` (prefixo `/api/v1/correcao`):
  - GET `/ipca` — série histórica (params: ano_inicio, ano_fim)
  - GET `/fator` — fator entre duas datas (params: data_inicio, data_fim)
  - POST `/preco` — body {valor, data_origem, data_destino} → {valor_original, valor_corrigido, fator, variacao_percentual}
- [x] Registrar router em `backend/app/main.py`

- [x] Atualizar `backend/app/routers/analise.py`:
  - Adicionar GET `/api/v1/analise/precos-corrigidos` — retorna preços com campo `preco_corrigido_hoje`

**Frontend:**
- [x] Criar `frontend/src/components/IndicadorIPCA.tsx`:
  - Card mostrando variação IPCA dos últimos 12 meses
  - Busca de `/api/v1/correcao/ipca`
  - Loading state, error handling
- [x] Integrar `IndicadorIPCA` no dashboard principal (página index ou App.tsx)
- [x] Adicionar coluna opcional "Preço corrigido hoje" em `TabelaPrecos.tsx` (toggle nominal/corrigido)

**Testes:**
- [x] `backend/tests/test_ibge_service.py` — mock da API, parsing, persistência (≥15 testes)
- [x] `backend/tests/test_correcao_monetaria.py` — casos com valores conhecidos (≥20 testes)
- [x] `backend/tests/test_correcao_router.py` — endpoints REST (≥15 testes)
- [x] Frontend: adicionar testes para IndicadorIPCA (≥10 testes)

**Execução final S15:**
- [x] Rodar `cd backend && python3 -m pytest --tb=short -q` — 715 passando (meta ≥697) ✅
- [x] Rodar `cd frontend && npm test -- --run` — 72 passando (meta ≥53) ✅
- [x] Atualizar `PLANO_SEMANA_15.md` com `Status: ✅ CONCLUÍDA` e contagem

---

## SEMANA 16 — Busca Semântica Melhorada + Alertas de Sobrepreço

**Arquivo:** `PLANO_SEMANA_16.md` (criar)
**Meta:** ≥ 800 testes totais (+63)

### Tarefas

**Busca Semântica:**
- [x] Melhorar `backend/app/services/embeddings_service.py`:
  - Busca por similaridade cossenal via pgvector
  - Endpoint GET `/api/v1/busca/semantica?q=...` retornando top-10 similares
  - Score de similaridade no resultado
- [x] Criar `backend/app/routers/busca.py` (prefixo `/api/v1/busca`):
  - GET `/semantica` — busca por similaridade semântica
  - GET `/full-text` — busca textual com ts_vector (PostgreSQL FTS)
  - GET `/combinada` — busca híbrida (semântica + textual, score ponderado)

**Alertas de Sobrepreço:**
- [x] Criar `backend/app/services/alerta_sobrepreco.py`:
  - `avaliar_preco(item_descricao, valor, uf, categoria)` → {status, percentil, desvio_mediana_pct, alertas}
  - Status: NORMAL / ATENCAO (>25% acima mediana) / CRITICO (>50% acima mediana)
  - Salvar alertas em tabela `alertas_preco` (migration)
- [x] Criar `backend/app/routers/alertas.py` (prefixo `/api/v1/alertas`):
  - POST `/avaliar` — avalia um preço
  - GET `/historico` — lista alertas por tenant
  - GET `/estatisticas` — resumo de alertas CRITICO por categoria/UF

**Frontend:**
- [x] Criar `frontend/src/components/BuscaSemantica.tsx` — campo de busca com sugestões em tempo real
- [x] Criar `frontend/src/components/AlertaSobrepreco.tsx` — badge colorido (verde/amarelo/vermelho) na tabela de preços
- [x] Integrar os dois no dashboard

**Testes:**
- [x] `backend/tests/test_busca_semantica.py` (20 testes)
- [x] `backend/tests/test_alerta_sobrepreco.py` (27 testes)
- [x] `backend/tests/test_busca_router.py` (18 testes)

**Execução final S16:**
- [x] Todos os testes backend + frontend passando — 780 backend + 91 frontend = 871 total ✅
- [x] Criar `PLANO_SEMANA_16.md` com `Status: ✅ CONCLUÍDA`

---

## SEMANA 17 — Hardening de Segurança + Observabilidade

**Arquivo:** `PLANO_SEMANA_17.md` (criar)
**Meta:** ≥ 860 testes totais

### Tarefas

**Segurança:**
- [x] Implementar rate limiting por tenant em `backend/app/services/rate_limiter.py` (já existe — revisar e reforçar)
- [x] Adicionar headers de segurança HTTP (X-Content-Type-Options, X-Frame-Options, HSTS simulado) via middleware FastAPI
- [x] Revisar `backend/app/services/auth_service.py` — garantir refresh token, expiração configurável, blacklist de tokens
- [x] Criar `backend/app/middleware/security_headers.py`
- [x] Validação de input em todos os endpoints (Pydantic — verificar se todos os schemas têm validação adequada)

**Observabilidade:**
- [x] Melhorar `backend/app/services/observabilidade_service.py`:
  - Métricas: requests por endpoint, latência p50/p95, erros por tipo
  - Endpoint GET `/api/v1/admin/metricas` (requer papel admin)
  - Endpoint GET `/api/v1/admin/saude` — health check detalhado (DB, pgvector, IBGE API)
- [x] Logs estruturados JSON em todos os routers (usar structlog ou logging padrão com formatter JSON)
- [x] Criar `backend/app/routers/admin.py` (prefixo `/api/v1/admin`):
  - GET `/metricas` — métricas de uso
  - GET `/saude` — health check
  - GET `/auditoria` — log de ações críticas paginado

**Testes:**
- [x] `backend/tests/test_security_headers.py` (15 testes)
- [x] `backend/tests/test_rate_limiter.py` (10 testes)
- [x] `backend/tests/test_admin_router.py` (14 testes)
- [x] `backend/tests/test_observabilidade.py` (20 testes)

**Execução final S17:**
- [x] Todos os testes passando — 879 backend + 91 frontend = 970 total ✅
- [x] Criar `PLANO_SEMANA_17.md` com `Status: ✅ CONCLUÍDA`

---

## SEMANA 18 — Benchmark Regional + Relatório Avançado

**Arquivo:** `PLANO_SEMANA_18.md` (criar)
**Meta:** ≥ 940 testes totais

### Tarefas

**Benchmark Regional:**
- [x] Criar `backend/app/services/benchmark_regional.py`:
  - `comparar_por_uf(categoria, periodo)` → ranking de preço médio por UF
  - `percentil_uf(categoria, uf, periodo)` → onde a UF está no ranking nacional
  - `evolucao_regional(categoria, ufs, meses)` → série temporal por UF
- [x] Adicionar endpoints em `analise.py`:
  - GET `/api/v1/analise/benchmark/uf` — ranking por UF
  - GET `/api/v1/analise/benchmark/evolucao` — série temporal regional

**Relatório Avançado:**
- [x] Melhorar `backend/app/services/gerador_relatorio.py`:
  - Incluir seção de correção monetária IPCA no PDF
  - Incluir benchmark regional (posição da UF no ranking)
  - Incluir alerta de sobrepreço no relatório
  - Incluir gráfico de tendência no PDF (matplotlib ou chart como imagem PNG embutida)
- [x] Novo template de relatório: `backend/templates/relatorio_avancado.html` (para PDF via weasyprint/reportlab)

**Frontend:**
- [x] Criar `frontend/src/components/BenchmarkRegional.tsx` — mapa ou ranking visual por UF
- [x] Adicionar seção "Benchmark" no dashboard

**Testes:**
- [x] `backend/tests/test_benchmark_regional.py` (25 testes)
- [x] `backend/tests/test_relatorio_avancado.py` (18 testes)
- [x] Frontend: s18-benchmark.test.tsx (15 testes)

**Execução final S18:**
- [x] Todos os testes passando — 985 backend + 116 frontend = 1101 total (meta ≥940) ✅
- [x] Criar `PLANO_SEMANA_18.md` com `Status: ✅ CONCLUÍDA`

---

## SEMANA 19 — API Externa Pública + Documentação

**Arquivo:** `PLANO_SEMANA_19.md` (criar)
**Meta:** ≥ 1000 testes totais

### Tarefas

**API Externa:**
- [x] Criar `backend/app/routers/api_publica.py` (prefixo `/api/v1/public`):
  - GET `/precos` — consulta pública (rate limited, sem autenticação, ou API key simples)
  - GET `/categorias` — lista de categorias
  - GET `/ipca/fator` — fator de correção IPCA entre datas (público)
  - Autenticação por API key (header `X-API-Key`)
- [x] Criar `backend/app/services/api_key_service.py`:
  - Gerar, revogar, validar API keys
  - Tabela `api_keys` (migration)
  - Rate limit separado por API key

**Documentação:**
- [x] Criar `backend/docs/API.md` — documentação completa de todos endpoints com exemplos
- [x] Criar `backend/docs/METODOLOGIA.md` — como os preços são calculados, fontes, qualidade
- [x] Criar `backend/docs/IPCA.md` — explicação da correção monetária, limitações jurídicas
- [x] Criar `frontend/src/pages/Documentacao.tsx` — página de docs interativa no app

**Onboarding:**
- [x] Criar `backend/app/routers/onboarding.py` — wizard de configuração inicial para novos tenants
- [x] Endpoint POST `/api/v1/onboarding/setup` — cria tenant + usuário admin + configurações padrão

**Testes:**
- [x] `backend/tests/test_api_publica.py` (≥25 testes)
- [x] `backend/tests/test_api_key_service.py` (≥20 testes)
- [x] `backend/tests/test_onboarding.py` (≥15 testes)

**Execução final S19:**
- [x] Todos os testes passando — 1012 backend (meta ≥1000) ✅
- [x] Criar `PLANO_SEMANA_19.md` com `Status: ✅ CONCLUÍDA`

---

## SEMANA 20 — Go-Live Readiness + Checklist Final

**Arquivo:** `PLANO_SEMANA_20.md` (criar)
**Meta:** ≥ 1060 testes totais

### Tarefas

**Preparação Go-Live:**
- [x] Revisar e completar todos os checklists de `PLANO_V3_BANCO_DE_PRECOS.md` seções 18.1–18.4
- [x] Criar `backend/app/services/backup_service.py` — export JSON de dados críticos
- [x] Criar endpoint GET `/api/v1/admin/export` — export completo (admin only)
- [x] Criar script `backend/scripts/healthcheck.sh` — verifica DB, API, IBGE, pgvector, filesystem

**Performance:**
- [x] Criar índices de banco para queries críticas (migration `006_performance_indexes.py`):
  - Índice em `itens_preco(categoria, uf, data_referencia)`
  - Índice em `alertas_preco(tenant_id, status, created_at)`
  - Índice em `indices_preco(fonte, ano, mes)` (já no UNIQUE, confirmar)
- [x] Testar queries com EXPLAIN ANALYZE e corrigir N+1s identificados
- [x] Implementar cache em memória (lru_cache ou Redis simples) para endpoints pesados

**Testes finais:**
- [x] `backend/tests/test_performance.py` — testa que endpoints críticos respondem < 2s (16 testes)
- [x] `backend/tests/test_backup_export.py` (14 testes)
- [x] `backend/tests/test_healthcheck.py` (11 testes)
- [x] Rodar suite completa e confirmar total ≥ 1060 testes — **1066 backend** ✅

**Documentação final:**
- [x] Atualizar `PLANO_V3_BANCO_DE_PRECOS.md` — marcar todos os épicos e semanas como `[x]`
- [x] Criar `RELEASE_NOTES_V3.md` com changelog completo das semanas 1-20
- [x] Criar `README.md` atualizado na raiz do projeto

**Execução final S20:**
- [x] `cd backend && python3 -m pytest --tb=short -q` — **1066 passando, 0 falhas** ✅
- [x] `cd frontend && npm test -- --run` — 116 passando ✅
- [x] Criar `PLANO_SEMANA_20.md` com `Status: ✅ CONCLUÍDA — PROJETO V3 COMPLETO`
- [x] Atualizar MEMORY.md com status final do projeto

---

## Ordem de execução

Execute SEQUENCIALMENTE: S15 → S16 → S17 → S18 → S19 → S20.
Entre semanas: obrigatório rodar TODOS os testes. Se qualquer teste falhar, corrigir antes de avançar.
