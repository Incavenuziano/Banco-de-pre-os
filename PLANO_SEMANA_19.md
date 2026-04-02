# Semana 19 — API Externa Pública + Documentação

**Status: ✅ CONCLUÍDA**
**Data conclusão:** 2026-04-01
**Base:** S18 concluída — 1101 testes (985 backend + 116 frontend)
**Resultado:** 1128 testes (1012 backend + 116 frontend)

---

## Entregáveis

### API Externa Pública
- [x] Router api_publica.py: /public/precos, /categorias, /ipca/fator
- [x] Autenticação por API key (X-API-Key header)
- [x] ApiKeyService: gerar, validar, revogar, listar

### Documentação
- [x] backend/docs/API.md — documentação completa dos endpoints
- [x] backend/docs/METODOLOGIA.md — fontes, normalização, outliers, confiança
- [x] backend/docs/IPCA.md — correção monetária, limitações jurídicas
- [x] frontend/src/pages/Documentacao.tsx — UI interativa com abas

### Onboarding
- [x] POST /api/v1/onboarding/setup — wizard completo
- [x] Fluxo: convite, aceite, checklist, feedback

### Testes
- [x] test_api_publica.py — 18 testes
- [x] test_api_key_service.py — 21 testes
- [x] test_onboarding.py — 23 testes
