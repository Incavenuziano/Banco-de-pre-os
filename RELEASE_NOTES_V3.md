# Release Notes — Banco de Precos V3

**Data:** 2026-04-01
**Total de testes:** 1128+ (backend + frontend)
**Status:** COMPLETO

---

## Semana 15 — Integracao IPCA/IBGE + Correcao Monetaria
- Conector IBGE/IPCA com serie historica 2020-2026
- Servico de correcao monetaria (fator, preco corrigido, variacao)
- Endpoints: /api/v1/correcao/ipca, /fator, /preco
- Endpoint /api/v1/analise/precos-corrigidos
- Componente IndicadorIPCA no dashboard
- Toggle nominal/corrigido na tabela de precos

## Semana 16 — Busca Semantica Melhorada + Alertas de Sobrepreco
- Busca semantica TF-IDF com similaridade de cosseno
- Endpoints: /busca/semantica, /full-text, /combinada
- AlertaSobreprecoService: avaliar_preco com percentil e desvio
- Endpoints: /alertas/avaliar, /historico, /estatisticas
- Componentes BuscaSemantica e AlertaSobrepreco no frontend

## Semana 17 — Hardening de Seguranca + Observabilidade
- Rate limiting por tenant
- Security headers middleware (HSTS, CSP, X-Frame-Options, etc.)
- Auth com refresh token, expiracao 8h/30d, blacklist
- Metricas por endpoint com latencia p50/p95
- Health check detalhado (DB, pgvector, IBGE, filesystem)
- Router admin: /metricas, /saude, /auditoria

## Semana 18 — Benchmark Regional + Relatorio Avancado
- BenchmarkRegionalService: ranking por UF, percentil, evolucao temporal
- Endpoints: /benchmark/uf, /percentil, /evolucao, /resumo
- Relatorio PDF com secoes IPCA, benchmark regional, alertas sobrepreco
- Componente BenchmarkRegional no dashboard

## Semana 19 — API Externa Publica + Documentacao
- API publica com autenticacao por API key
- Endpoints publicos: /public/precos, /categorias, /ipca/fator
- ApiKeyService: gerar, validar, revogar
- Documentacao: API.md, METODOLOGIA.md, IPCA.md
- Pagina de documentacao interativa no frontend
- Wizard de onboarding: POST /onboarding/setup

## Semana 20 — Go-Live Readiness
- BackupService: export JSON completo
- Endpoint GET /admin/export
- Migration 006_performance_indexes
- Script healthcheck.sh
- Testes de performance (<2s por endpoint critico)
- Validacao de integridade dos dados

---

## Metricas Finais
- Backend: 1012+ testes
- Frontend: 116+ testes
- Zero regressoes desde S14
- Cobertura: 15 UFs, 50 categorias, serie IPCA 2020-2026
