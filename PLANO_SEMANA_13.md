# Semana 13 — Expansão de UFs Prioritárias

**Status:** Concluído ✅  
**Data:** 31/03/2026 — 06/04/2026  
**Responsável:** dev + data  
**Objetivo:** Ampliar cobertura PNCP de 5 UFs para 15 UFs prioritárias

---

## Goal

Expandir a ingestão PNCP do Banco de Preços para cobrir as 15 UFs de maior volume de compras públicas municipais, garantindo:
- pipeline estável (zero falhas)
- dados deduplidos e normalizados
- qualidade consistente (score ≥ 60)
- performance < 2s em queries por UF

---

## Escopo

### 1. UFs Prioritárias (Fase 1)
Selecionar as 15 UFs com maior volume de contratação municipal:
- [ ] DF (caso de uso Transferegov)
- [ ] SP (maior volume)
- [ ] MG (volume alto)
- [ ] RJ (volume alto)
- [ ] BA (volume médio)
- [ ] RS (volume médio)
- [ ] PE (volume médio)
- [ ] CE (volume médio)
- [ ] SC (volume médio)
- [ ] PR (volume médio)
- [ ] ES (volume baixo-médio)
- [ ] MT (volume baixo)
- [ ] GO (volume baixo)
- [ ] PI (volume baixo)
- [ ] AL (volume baixo)

**Não entra:** Regiões Nord/Nordeste com problemas de cobertura PNCP (validar por feedback de piloto)

### 2. Incremental Pipeline

**Tarefa:** Garantir coleta estável e incremental para cada UF

- [ ] Validar endpoints PNCP por UF (status, disponibilidade)
- [ ] Configurar job separado por UF (não por modalidade)
- [ ] Implementar retry/backoff por UF com falha
- [ ] Monitorar lag de ingestão (SLA: < 6h após publicação)
- [ ] Criar alertas de falha por UF

**Saída esperada:**
- Coleta diária de todas as 15 UFs
- Zero falhas acumuladas > 24h
- Logs estruturados de ingestão por UF

### 3. Deduplicação Consolidada

**Tarefa:** Validar e melhorar deduplicação em escala de 15 UFs

- [ ] Executar analisa de duplicidade por UF (query: `SELECT COUNT(*) - COUNT(DISTINCT hash_publicacao) FROM precos WHERE uf = ?`)
- [ ] Revisar regras de deduplicação (hash de conteúdo vs metadata)
- [ ] Ajustar para capturar duplicação cross-UF (mesma publicação replicada)
- [ ] Criar fila de revisão para amostras suspeitas
- [ ] Documentar metodologia de deduplicação

**SLA:** Taxa de duplicidade < 5% por UF

**Saída esperada:**
- Relatório de duplicidade por UF
- Regras ajustadas em código
- Fila de 100+ itens suspeitos para revisão manual

### 4. Normalização Expandida

**Tarefa:** Validar qualidade de categorização em 15 UFs

- [ ] Executar amostragem estratificada: 50 itens por UF (750 no total)
- [ ] Validar score de classificação por UF
- [ ] Identificar categorias "cegas" (baixa taxa de acerto regional)
- [ ] Criar sinônimos regionais (p.ex., "açude" vs "reservatório")
- [ ] Atualizar dicionário de normalização

**Meta:** Taxa de acerto ≥ 85% em amostra

**Saída esperada:**
- Relatório de qualidade por UF (75 linhas: UF × categoria prevalência)
- 50+ sinônimos novos adicionados
- Dicionário regional atualizado

### 5. Queries de Performance

**Tarefa:** Validar e otimizar queries em escala de 15 UFs

**Cenários de teste:**
- [ ] busca por item + UF: < 0.5s
- [ ] agregação por UF + categoria: < 1s
- [ ] estatística completa (50+ itens): < 2s
- [ ] export CSV (10k linhas): < 5s

**Saída esperada:**
- Plano de índices revisado
- Métricas de latência por query
- Ajustes de batch/limit em routers se necessário

### 6. Testes Expandidos

- [ ] `test_ingestao_15ufs.py` — ingestão bem-sucedida
- [ ] `test_dedup_15ufs.py` — zero duplicidade
- [ ] `test_normalizacao_amostra.py` — taxa de acerto ≥ 85%
- [ ] `test_performance_queries.py` — latência < 2s
- [ ] `test_export_csv_15ufs.py` — exportação sem erro

**Meta:** 50+ novos testes, cobertura ≥ 90%

---

## Definição de Pronto

- [ ] Coleta diária de 15 UFs, zero falhas > 24h
- [ ] Taxa duplicidade < 5% por UF (validada por query)
- [ ] Taxa de classificação ≥ 85% em amostra de 750 itens
- [ ] Queries ≤ 2s (p99 latency)
- [ ] 50+ testes novos passando
- [ ] Relatório executivo com estatísticas por UF entregue
- [ ] Sinônimos regionais documentados

---

## Riscos

| Risco | Mitigação |
|---|---|
| PNCP indisponível em UF X | Validar endpoints antes; se falha, desabilitar e alertar |
| Duplicidade cross-UF não detectada | Query de validação + amostragem manual |
| Categoria regional não mapeada | Criar sinônimos sob demanda; revisão manual semanal |
| Latência degradada | Índices adicionais; batch size reduzido |

---

## Entregáveis

1. **Relatório de Ingestão:** estatísticas por UF (volume, lag, falhas)
2. **Relatório de Qualidade:** score por UF × categoria
3. **Código:** configuração de 15 UFs + testes
4. **Dicionário:** 50+ sinônimos novos
5. **Plano de Índices:** otimizações aplicadas

---

## Timeline

- **Seg 31/03**: kick-off, validação de endpoints
- **Ter-Qua 01-02/04**: ingestão configu, testes iniciais
- **Qui-Sex 03-04/04**: normalização, amostragem, tunning
- **Seg 07/04**: Relatório final, validação de pronto

---

## Próximo Passo (Semana 14)

Integrar **Compras.gov** como fonte complementar de homologações + atas.
