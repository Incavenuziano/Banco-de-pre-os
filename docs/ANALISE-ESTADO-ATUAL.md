# Análise — Banco de Preços: Estado Atual e Gaps

> Gerado em: 2026-04-03
> Autor: Siriguejo (análise técnica)
> Contexto: 156.113 itens no banco (GO completo jan–ago/25, outras UFs amostras de 49 itens cada)

---

## O que foi construído (V3)

- FastAPI + React + pgvector, PostgreSQL 15
- 1.182 testes (1066 backend + 116 frontend)
- Multi-tenant, IPCA, alertas de sobrepreço
- API pública, relatório PDF, busca semântica (infra pronta), benchmark regional
- Arquitetura sólida, bem testada

---

## Lacunas Críticas (bloqueia uso em produção)

### 1. Embeddings zerados — busca semântica inoperante
- 155.000+ itens sem embedding gerado (coluna existe, todos NULL)
- Busca por similaridade não funciona
- "cadeira de escritório" não encontra "cadeira giratória ergonômica 120kg"
- **Bloqueador do diferencial técnico do produto**

### 2. 97,8% dos itens sem categoria
- 152.689 de 156.113 sem categoria
- Motor de classificação regex sub-cobre o vocabulário real
- Relatórios por categoria retornam apenas os ~2,4k classificados
- Usuário não encontra itens por navegação temática

### 3. Ticket médio distorcido — R$86k médio por item
- Itens de obra/serviço misturados com material de consumo
- Sem filtro por tipo de objeto (material / serviço / obra)
- Preço referencial calculado sobre conjunto heterogêneo = ruído
- **Metodologia de cálculo está correta, mas o dado de entrada é incorreto**

### 4. Zero tenants cadastrados
- Produto pronto, nenhum cliente no banco
- MVP nunca saiu do localhost

### 5. Cobertura geográfica desequilibrada
- GO: 154.609 contratações, 154.609 itens (completo jan–ago/25)
- Outras 21 UFs: ~49 itens cada (amostra do cron diário)
- Para municípios de SP, MG, BA, etc.: banco está essencialmente vazio

---

## Sugestões de Melhoria

### 🔴 Crítico (sem isso o produto não funciona)

| # | Ação |
|---|------|
| 1 | Gerar embeddings em batch para os 156k itens existentes |
| 2 | Reescrever classificador — usar embeddings para categorizar os 152k sem categoria |
| 3 | Adicionar coluna `tipo_objeto` (material/serviço/obra) ao schema e filtrar no cálculo de preço |

### 🟡 Alto valor para público-alvo (municípios pequenos)

| # | Ação |
|---|------|
| 4 | Ingestão completa para SP, MG, BA, RS, PR (volume alto, cobertura nacional) |
| 5 | Interface simplificada: campo único → mediana + dispersão + nível de confiança |
| 6 | Exportar resultado como XLSX e PDF formatado para pesquisa de preço (IN 65/2021) |
| 7 | Busca tolerante a variações: "papel A4 75g", "folha a4", "resma papel" → mesmo resultado |

### 🟢 Diferencial competitivo (médio prazo)

| # | Ação |
|---|------|
| 8 | Atualização diária automática por UF (cron GO já existe, expandir) |
| 9 | Comparação por porte de município (cruzar com IBGE população) |
| 10 | Alerta de sobrepreço integrado ao fluxo: usuário cola proposta, sistema avalia |
| 11 | Canal de acesso low-code: pesquisa via WhatsApp/Telegram para prefeituras menores |

---

## Notas

- A metodologia de preço referencial (mediana + IQR) está bem implementada e é defensável perante TCU
- O maior risco de produto não é técnico: é cobertura de dados e UX para usuários não técnicos
- Prioridade sugerida antes do go-to-market: resolver embeddings + categorias + tipo_objeto + cobertura geográfica
