# Correção Monetária — IPCA

## Visão Geral

O Banco de Preços utiliza o IPCA (Índice Nacional de Preços ao Consumidor Amplo) do IBGE para correção monetária de preços históricos, permitindo comparações reais entre períodos distintos.

## Fonte de Dados

- **Origem:** API IBGE SIDRA — Tabela 1737 (IPCA mensal)
- **Endpoint:** `https://servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/all/variaveis/63`
- **Cobertura:** Janeiro/2020 a Março/2026
- **Atualização:** Dados mockados localmente para independência da API IBGE em produção

## Como Funciona

### Fator de Correção

O fator IPCA acumulado entre duas datas é calculado como o produto das variações mensais:

```
fator = Π (1 + variação_mensal/100) para cada mês no intervalo
```

### Endpoints Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/correcao/ipca` | GET | Série histórica IPCA (params: ano_inicio, ano_fim) |
| `/api/v1/correcao/fator` | GET | Fator entre duas datas |
| `/api/v1/correcao/preco` | POST | Corrige um preço {valor, data_origem, data_destino} |

### Exemplo

```
corrigir_preco(100.00, "2020-01-01", "2026-01-01") → ~146.00
```

## Limitações Jurídicas

- O IPCA é utilizado **apenas como referência analítica**, não como garantia de preço
- Relatórios não substituem análise jurídica formal
- A correção monetária serve para comparação de poder aquisitivo, não para reajuste contratual
- Para reajustes contratuais, consultar cláusulas específicas do instrumento convocatório

## Dados Armazenados

Tabela `indices_preco`:
- fonte (IPCA), ano, mês
- variacao_mensal (%), variacao_acumulada_ano (%)
- indice_acumulado (base 100)
- fonte_url, coletado_em
