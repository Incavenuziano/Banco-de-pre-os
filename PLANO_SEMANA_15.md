# Semana 15 — Integração IPCA/IBGE + Correção Monetária

**Status: ✅ CONCLUÍDA**
**Data início:** 2026-04-01
**Data conclusão:** 2026-04-01
**Base:** S14 concluída — 677 testes (634 backend + 43 frontend), dashboard funcional
**Resultado:** 787 testes (715 backend + 72 frontend)
**Responsável:** dev

---

## Objetivo

Integrar dados do IPCA (IBGE) ao banco de preços para permitir:
1. Correção monetária de preços históricos para data atual
2. Deflação de séries temporais para comparação real
3. Endpoint de preço corrigido por IPCA
4. Indicador de variação inflacionária no dashboard

---

## Entregáveis obrigatórios

### 1. Conector IBGE/IPCA (`app/services/ibge_service.py`)
- Consumir API IBGE SIDRA: tabela 1737 (IPCA mensal) — https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/all/variaveis/63
- Persistir séries históricas em tabela `indices_preco` (PostgreSQL)
- Atualização incremental diária (só busca meses não coletados)
- Cache local: não bater na API IBGE a cada requisição

### 2. Migration — tabela `indices_preco`
```sql
CREATE TABLE indices_preco (
    id SERIAL PRIMARY KEY,
    fonte VARCHAR(20) NOT NULL DEFAULT 'IPCA',  -- IPCA, IGPM, etc.
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,  -- 1-12
    variacao_mensal NUMERIC(8,4),  -- ex: 0.83 (%)
    variacao_acumulada_ano NUMERIC(8,4),
    indice_acumulado NUMERIC(12,6),  -- base 100 em Jan/1993 ou base configurável
    fonte_url TEXT,
    coletado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(fonte, ano, mes)
);
```

### 3. Serviço de correção monetária (`app/services/correcao_monetaria.py`)
- `corrigir_preco(valor, data_origem, data_destino)` → valor corrigido
- `fator_correcao(data_origem, data_destino)` → fator multiplicador
- `variacao_periodo(data_inicio, data_fim)` → variação % acumulada
- Tratamento de meses sem dado (interpolação ou erro explícito)

### 4. Novos endpoints REST (`app/routers/correcao.py`, prefixo `/api/v1/correcao`)

| Endpoint | Método | Descrição |
|---|---|---|
| `/api/v1/correcao/ipca` | GET | Série histórica IPCA (filtros: ano_inicio, ano_fim) |
| `/api/v1/correcao/fator` | GET | Fator IPCA entre duas datas |
| `/api/v1/correcao/preco` | POST | Corrige um preço para data atual |
| `/api/v1/analise/precos-corrigidos` | GET | Lista preços da S14 com coluna `preco_corrigido_hoje` |

### 5. Frontend — novo componente `IndicadorIPCA`
- Card no dashboard com variação IPCA últimos 12 meses
- Coluna opcional "Preço corrigido hoje" na `TabelaPrecos`
- Toggle: exibir preços nominais ou corrigidos

### 6. Testes
- `tests/test_ibge_service.py` — mock da API IBGE, parsing, persistência
- `tests/test_correcao_monetaria.py` — cálculos de correção com casos conhecidos
- `tests/test_correcao_router.py` — endpoints REST
- Meta: +60 testes novos → total ≥ 737

---

## Critérios de aceite (Definição de Pronto)

- [x] API IBGE consultada e série IPCA 2020-2026 persistida no banco
- [x] `corrigir_preco(100, "2020-01-01", "2026-01-01")` retorna valor plausível (~150+)
- [x] Endpoint `/api/v1/correcao/fator?data_inicio=2023-01-01&data_fim=2026-01-01` funciona
- [x] Endpoint `/api/v1/analise/precos-corrigidos` retorna campo `preco_corrigido_hoje`
- [x] Dashboard exibe card com IPCA acumulado 12 meses
- [x] Todos os testes existentes continuam passando (zero regressões)
- [x] ≥ 737 testes no total (resultado: 787 — 715 backend + 72 frontend)

---

## Stack / dependências novas

- `httpx` (já presente) — para chamadas IBGE
- Nenhuma nova dependência obrigatória

---

## Estrutura de arquivos esperada

```
backend/
  app/
    services/
      ibge_service.py          # NOVO
      correcao_monetaria.py    # NOVO
    routers/
      correcao.py              # NOVO
    models/
      indice_preco.py          # NOVO (SQLAlchemy model)
    migrations/
      xxxx_create_indices_preco.py  # NOVO (Alembic)
  tests/
    test_ibge_service.py       # NOVO
    test_correcao_monetaria.py # NOVO
    test_correcao_router.py    # NOVO
frontend/
  src/
    components/
      IndicadorIPCA.tsx        # NOVO
```

---

## Notas

- API IBGE SIDRA é pública, sem autenticação
- Persistir dados localmente para evitar dependência em produção
- Separar claramente preço nominal vs corrigido em todos os outputs
- Não usar IPCA para "garantir" preço em relatório jurídico — apenas como referência analítica
