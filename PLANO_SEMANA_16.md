# Semana 16 — Busca Semântica Melhorada + Alertas de Sobrepreço

**Status: ✅ CONCLUÍDA**
**Data conclusão:** 2026-04-01
**Base:** S15 concluída — 787 testes (715 backend + 72 frontend)
**Resultado:** 871 testes (780 backend + 91 frontend)

---

## Entregáveis

### Busca Semântica
- [x] EmbeddingsService com TF-IDF + similaridade de cosseno
- [x] GET `/api/v1/busca/semantica` — busca por similaridade
- [x] GET `/api/v1/busca/full-text` — busca textual
- [x] GET `/api/v1/busca/combinada` — busca híbrida ponderada

### Alertas de Sobrepreço
- [x] AlertaSobreprecoService: avaliar_preco, obter_historico, obter_estatisticas
- [x] POST `/api/v1/alertas/avaliar` — avalia preço vs referências
- [x] GET `/api/v1/alertas/historico` — histórico por tenant
- [x] GET `/api/v1/alertas/estatisticas` — resumo por categoria/UF

### Frontend
- [x] BuscaSemantica.tsx — busca com sugestões em tempo real
- [x] AlertaSobrepreco.tsx — badge colorido (verde/amarelo/vermelho)
- [x] Componentes integrados no Dashboard

### Testes
- [x] test_busca_semantica.py — 20 testes
- [x] test_alerta_sobrepreco.py — 27 testes
- [x] test_busca_router.py — 18 testes
