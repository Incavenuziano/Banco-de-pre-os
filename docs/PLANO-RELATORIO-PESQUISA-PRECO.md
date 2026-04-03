# Plano: Módulo de Relatório de Pesquisa de Preço
## Conformidade IN 65/2021 TCU + Lei 14.133/2021 + Regras Estaduais

> Criado: 2026-04-03
> Status: Planejamento
> Objetivo: Automatizar a geração de relatório de pesquisa de preço conforme exigências legais, com suporte a variações por estado

---

## Contexto e Motivação

Municípios pequenos têm dificuldade em realizar pesquisa de preço porque:
1. O processo manual é trabalhoso e sujeito a erro (cotações em planilhas, sem metodologia documentada)
2. A IN 65/2021 e a Lei 14.133/2021 exigem metodologia específica que poucos servidores dominam
3. TCU tem jurisprudência consolidada sobre o que aceita e o que glosa
4. Estados têm órgãos de controle próprios (TCE, CGE) com entendimentos complementares
5. O risco de autuação por pesquisa de preço mal feita é alto e recorrente

O Banco de Preços já tem o dado — falta o mecanismo de transformar esse dado em documento válido.

---

## Visão do Produto

Aba **"Pesquisa de Preço"** na interface:
1. Usuário seleciona o item (ou pesquisa por descrição)
2. Seleciona a área geográfica (UF, microrregião, município, nacional)
3. Define parâmetros (período, tipo de objeto, modalidade)
4. Clica em **"Gerar Relatório"**
5. Recebe PDF + XLSX prontos para juntar ao processo

O relatório já:
- Cita a base legal correta
- Aplica a metodologia exigida pela IN 65
- Documenta as fontes (PNCP, com links)
- Calcula e justifica o preço referencial
- Alerta sobre amostras insuficientes ou dispersão alta
- Adapta o texto para o estado selecionado (quando há regra própria)

---

## Referências Legais Mapeadas

### Lei 14.133/2021 (Nova Lei de Licitações)
- **Art. 23**: Valor estimado baseado em pesquisa de preços de mercado
- **Art. 169**: Responsabilidade do agente de contratação pela pesquisa
- **Art. 184**: Irregularidade na estimativa de preço como causa de sanção

### IN 65/2021 (SEGES/ME) — Pesquisa de Preços
- **Art. 5º**: Fontes prioritárias (painel de preços gov, PNCP, contratações similares)
- **Art. 6º**: Metodologia de cálculo (média, mediana, menor preço)
- **Art. 7º**: Documentação mínima obrigatória no processo
- **Art. 9º**: Dispensas e vedações
- **Art. 10**: Assinatura do responsável

### Acórdãos TCU relevantes
- **Acórdão 1977/2013-TCU-Plenário**: Pesquisa não pode ter apenas 1 fonte
- **Acórdão 2450/2016-TCU-Plenário**: Mediana como metodologia preferencial
- **Acórdão 1347/2018-TCU-Plenário**: Necessidade de descrever a metodologia no processo
- **Acórdão 1064/2019-TCU-Plenário**: Dispensas de baixo valor e pesquisa simplificada
- **Acórdão 2622/2020-TCU-Plenário**: PNCP como fonte válida e preferencial
- **Acórdão 825/2023-TCU-Plenário**: Atualização com IPCA quando dados têm mais de 12 meses

### Regras por Estado (a mapear — seção crescente)
- **GO**: TCE-GO, Resolução 004/2019 — mínimo 3 fontes para valores acima de R$17k
- **SP**: TCE-SP, Instrução 02/2016 — exige planilha orçamentária em separado para serviços
- **DF**: TCDF — entendimento de que PNCP substitui pesquisa direta quando há 5+ contratos similares
- **MG**: TCE-MG — preferência por menor preço para commodities
- *(demais estados: a pesquisar e preencher)*

---

## Arquitetura Técnica

```
Frontend (React)
└── Aba "Pesquisa de Preço"
    ├── Componente ItemSelector (busca semântica + filtros)
    ├── Componente RegiaoSelector (UF / microrregião / município)
    ├── Componente ParametrosForm (período, tipo, modalidade)
    └── Componente RelatorioPreview (prévia antes de gerar)

Backend (FastAPI)
└── Router: /api/v1/relatorio-pesquisa/
    ├── POST /gerar              → gera e salva relatório
    ├── GET  /{id}               → recupera relatório salvo
    ├── GET  /{id}/download/pdf  → PDF
    └── GET  /{id}/download/xlsx → planilha

Services
├── PesquisaPrecoService        → orquestra a geração
├── MetodologiaService          → aplica cálculos (mediana, IQR, IPCA)
├── ConformidadeService         → valida regras IN 65 + regras estaduais
├── RelatorioPDFService         → gera PDF (WeasyPrint ou Reportlab)
└── RelatorioXLSXService        → gera planilha (openpyxl)

Models (PostgreSQL)
├── relatorios_pesquisa         → registro de cada relatório gerado
├── regras_estaduais            → tabela de regras por UF
└── templates_relatorio         → templates de texto por UF
```

---

## Estrutura do Relatório Gerado (PDF)

### Seção 1 — Identificação
```
RELATÓRIO DE PESQUISA DE PREÇOS DE MERCADO
Órgão: [nome do tenant]
CNPJ: [cnpj]
Data de elaboração: [data]
Responsável: [nome do agente de contratação]
Processo: [número SEI/SIGED — preenchimento manual ou integração]
```

### Seção 2 — Objeto Pesquisado
```
Descrição do item: [descrição completa]
Unidade de medida: [un]
Quantidade prevista: [qtd]
Tipo de objeto: Material / Serviço / Obra
Código CATMAT/CATSER: [se disponível]
```

### Seção 3 — Base Legal
```
A presente pesquisa de preços foi realizada em conformidade com:
- Art. 23 da Lei 14.133/2021
- Instrução Normativa SEGES/ME nº 65/2021, arts. 5º, 6º e 7º
- Acórdão TCU nº 2622/2020-Plenário (PNCP como fonte válida)
[+ regras estaduais aplicáveis quando selecionada a UF]
```

### Seção 4 — Metodologia
```
Fontes consultadas: PNCP (Portal Nacional de Contratações Públicas)
Período de referência: [data_inicio] a [data_fim]
Área geográfica: [UF / microrregião / nacional]
Número de contratos encontrados: [n]
Número de contratos utilizados após filtragem: [n_filtrado]
Critério de exclusão de outliers: [IQR / Percentil 5-95 / DP, conforme CV]
Estatística utilizada: Mediana (recomendada pelo Acórdão TCU 2450/2016)
Atualização monetária: IPCA acumulado [%] — período [meses]
```

### Seção 5 — Resultado
```
Preço unitário referencial: R$ [valor]
Preço total estimado (qtd × referencial): R$ [total]
Desvio padrão: R$ [dp]
Coeficiente de variação: [cv]%
Nível de confiança: [alto/médio/baixo] — [justificativa]
```

### Seção 6 — Fontes Detalhadas (tabela)
| Órgão | CNPJ | UF | Data | Descrição | Qtd | Unit (R$) | Link PNCP |
|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... |

### Seção 7 — Alertas e Observações
```
[gerado automaticamente quando aplicável]
- ⚠️ Amostra reduzida (n < 5): recomenda-se complementar com cotação direta
- ⚠️ Alta dispersão (CV > 30%): preço referencial deve ser justificado no processo
- ⚠️ Dados com mais de 12 meses: atualização IPCA aplicada conforme Acórdão 825/2023
- ⚠️ Regra estadual GO (TCE-GO Res. 004/2019): valor acima de R$17k exige mínimo 3 fontes distintas
```

### Seção 8 — Assinatura
```
[Espaço para assinatura do agente de contratação]
Nome:
Cargo:
Matrícula:
Data:
```

---

## Planilha XLSX Gerada

**Aba 1 — Resumo**
- Dados da pesquisa, resultado, base legal

**Aba 2 — Dados Brutos**
- Todos os contratos usados na amostra com link PNCP

**Aba 3 — Cálculo**
- Série de preços, exclusões, mediana, IPCA, resultado final
- Fórmulas visíveis para auditoria

**Aba 4 — Base Legal**
- Transcrição dos artigos aplicados

---

## Templates por Estado

Cada estado terá um template de texto que sobrescreve/complementa a seção de base legal e alertas:

```
templates_relatorio
├── default.md          (federal, aplica-se a todos)
├── GO.md               (adiciona: TCE-GO Res. 004/2019, mínimo 3 fontes > R$17k)
├── SP.md               (adiciona: TCE-SP Instrução 02/2016)
├── DF.md               (adiciona: TCDF entendimento PNCP)
├── MG.md               (adiciona: TCE-MG preferência menor preço commodities)
└── ...
```

---

## Plano de Execução — Checklist Detalhado

### FASE 0 — Pré-requisitos (antes de qualquer código)
- [ ] 0.1 Gerar embeddings para os 156k itens existentes (batch, background) — **bloqueador da busca**
- [ ] 0.2 Classificar itens sem categoria usando embeddings (152k itens)
- [ ] 0.3 Adicionar coluna `tipo_objeto` à tabela `itens` (material/serviço/obra)
- [ ] 0.4 Preencher `tipo_objeto` a partir de heurísticas (CATMAT → material, CATSER → serviço)
- [ ] 0.5 Confirmar que a busca semântica está retornando resultados corretos após embeddings
- [ ] 0.6 Migração Alembic para colunas novas

---

### FASE 1 — Backend: Motor de Pesquisa de Preço
- [ ] 1.1 Criar router `/api/v1/relatorio-pesquisa/`
- [ ] 1.2 Criar model `RelatoriosPesquisa` (id, tenant_id, item_id, params_json, resultado_json, created_at, pdf_path, xlsx_path)
- [ ] 1.3 Criar model `RegrasEstaduais` (uf, descricao, regra_json, fonte, vigencia)
- [ ] 1.4 Criar model `TemplatesRelatorio` (uf, secao, texto_template)
- [ ] 1.5 Migração Alembic para as 3 novas tabelas
- [ ] 1.6 Implementar `MetodologiaService`:
  - [ ] 1.6.1 Busca de contratos por item (semântica + filtros)
  - [ ] 1.6.2 Filtragem por período e área geográfica
  - [ ] 1.6.3 Exclusão de outliers (IQR / percentil / DP conforme CV)
  - [ ] 1.6.4 Cálculo de mediana, média, desvio padrão, CV
  - [ ] 1.6.5 Aplicação de IPCA (já existe no sistema, reutilizar)
  - [ ] 1.6.6 Classificação de nível de confiança (alto/médio/baixo baseado em n e CV)
- [ ] 1.7 Implementar `ConformidadeService`:
  - [ ] 1.7.1 Validar n mínimo de contratos (< 5 → alerta)
  - [ ] 1.7.2 Validar dispersão (CV > 30% → alerta)
  - [ ] 1.7.3 Validar idade dos dados (> 12 meses → alerta IPCA)
  - [ ] 1.7.4 Aplicar regras da UF selecionada (carregar de `regras_estaduais`)
  - [ ] 1.7.5 Retornar lista de alertas com severidade (info/aviso/crítico)
- [ ] 1.8 Implementar `PesquisaPrecoService` (orquestrador):
  - [ ] 1.8.1 Receber parâmetros, chamar MetodologiaService e ConformidadeService
  - [ ] 1.8.2 Montar objeto `resultado_json` completo (dados + alertas + fontes)
  - [ ] 1.8.3 Salvar no banco e retornar ID
- [ ] 1.9 Implementar `RelatorioPDFService`:
  - [ ] 1.9.1 Definir template HTML/CSS base (seções 1–8)
  - [ ] 1.9.2 Injetar dados do `resultado_json`
  - [ ] 1.9.3 Carregar template do estado (de `templates_relatorio`)
  - [ ] 1.9.4 Gerar PDF via WeasyPrint
  - [ ] 1.9.5 Salvar em storage (local ou S3)
- [ ] 1.10 Implementar `RelatorioXLSXService`:
  - [ ] 1.10.1 Gerar aba Resumo
  - [ ] 1.10.2 Gerar aba Dados Brutos (com links PNCP clicáveis)
  - [ ] 1.10.3 Gerar aba Cálculo (com fórmulas visíveis)
  - [ ] 1.10.4 Gerar aba Base Legal
  - [ ] 1.10.5 Salvar em storage
- [ ] 1.11 Endpoints de download (PDF e XLSX)
- [ ] 1.12 Seed inicial de `regras_estaduais` (GO, SP, DF, MG — dados mapeados acima)
- [ ] 1.13 Seed inicial de `templates_relatorio` (default + 4 estados)
- [ ] 1.14 Testes unitários: MetodologiaService (>90% cobertura)
- [ ] 1.15 Testes unitários: ConformidadeService
- [ ] 1.16 Testes de integração: endpoint POST /gerar → verifica PDF e XLSX gerados
- [ ] 1.17 Documentação OpenAPI dos novos endpoints

---

### FASE 2 — Frontend: Aba Pesquisa de Preço
- [ ] 2.1 Criar rota `/pesquisa-preco` no React Router
- [ ] 2.2 Criar componente `ItemSelector`:
  - [ ] 2.2.1 Campo de busca com debounce (500ms)
  - [ ] 2.2.2 Busca semântica no backend enquanto usuário digita
  - [ ] 2.2.3 Lista de sugestões com descrição + categoria + unidade
  - [ ] 2.2.4 Seleção confirma o item
- [ ] 2.3 Criar componente `RegiaoSelector`:
  - [ ] 2.3.1 Dropdown UF (todos os estados)
  - [ ] 2.3.2 Opção "microrregião IBGE" (select dependente da UF)
  - [ ] 2.3.3 Opção "município específico"
  - [ ] 2.3.4 Opção "nacional" (sem filtro geográfico)
- [ ] 2.4 Criar componente `ParametrosForm`:
  - [ ] 2.4.1 Período (data início / data fim, padrão: últimos 12 meses)
  - [ ] 2.4.2 Tipo de objeto (material / serviço / obra / todos)
  - [ ] 2.4.3 Quantidade prevista (para cálculo do total)
  - [ ] 2.4.4 Nome do responsável e cargo (para assinatura no PDF)
  - [ ] 2.4.5 Número do processo (opcional, aparece no cabeçalho)
- [ ] 2.5 Criar componente `RelatorioPreview`:
  - [ ] 2.5.1 Card com preço referencial (mediana) em destaque
  - [ ] 2.5.2 Gráfico de dispersão dos preços da amostra (boxplot ou scatter)
  - [ ] 2.5.3 Badge de nível de confiança (verde/amarelo/vermelho)
  - [ ] 2.5.4 Lista de alertas de conformidade
  - [ ] 2.5.5 Tabela de contratos da amostra (paginada)
  - [ ] 2.5.6 Botões "Baixar PDF" e "Baixar XLSX"
- [ ] 2.6 Integração com backend (React Query):
  - [ ] 2.6.1 Hook `useGerarRelatorio` (POST /gerar)
  - [ ] 2.6.2 Hook `useDownloadRelatorio` (GET /{id}/download/*)
  - [ ] 2.6.3 Estado de loading com skeleton enquanto processa
- [ ] 2.7 Testes de componente (Vitest + Testing Library):
  - [ ] 2.7.1 ItemSelector renderiza sugestões
  - [ ] 2.7.2 ParametrosForm valida campos obrigatórios
  - [ ] 2.7.3 RelatorioPreview exibe alertas corretamente
- [ ] 2.8 Testes E2E (Playwright):
  - [ ] 2.8.1 Fluxo completo: busca item → seleciona região → gera → baixa PDF

---

### FASE 3 — Regras Estaduais (expansão contínua)
- [ ] 3.1 Pesquisar e mapear regras de cada estado:
  - [ ] 3.1.1 GO — TCE-GO Resolução 004/2019
  - [ ] 3.1.2 SP — TCE-SP Instrução 02/2016
  - [ ] 3.1.3 DF — TCDF jurisprudência PNCP
  - [ ] 3.1.4 MG — TCE-MG orientações técnicas
  - [ ] 3.1.5 BA, RS, PR, CE, PE, MA (pesquisa a fazer)
  - [ ] 3.1.6 Demais 16 estados
- [ ] 3.2 Criar templates de texto para cada estado mapeado
- [ ] 3.3 Implementar interface de admin para gerenciar regras estaduais (CRUD)
- [ ] 3.4 Criar sistema de versão para regras (quando uma norma é alterada, o relatório antigo preserva a regra vigente na época)
- [ ] 3.5 Publicar guia público de quais estados têm regras específicas e quais fontes foram consultadas

---

### FASE 4 — Qualidade e Validação Jurídica
- [ ] 4.1 Revisão do texto-base do relatório por advogado/especialista em licitações
- [ ] 4.2 Validação da metodologia de cálculo contra os Acórdãos TCU mapeados
- [ ] 4.3 Teste com usuário real (servidor de prefeitura pequena):
  - [ ] 4.3.1 Consegue gerar o relatório sem treinamento?
  - [ ] 4.3.2 O PDF gerado é aceito pelo jurídico da prefeitura?
  - [ ] 4.3.3 Quanto tempo levou vs. pesquisa manual?
- [ ] 4.4 Ajustes pós-feedback de usuário
- [ ] 4.5 Documentar limitações do sistema (o que não cobre, quando o servidor precisa complementar)

---

### FASE 5 — Go-to-market (pós-validação)
- [ ] 5.1 Cadastrar primeiro tenant (prefeitura piloto)
- [ ] 5.2 Criar onboarding guiado (tour interativo)
- [ ] 5.3 Criar página de ajuda com exemplos de relatórios gerados
- [ ] 5.4 Definir modelo de precificação (por relatório, por mês, por usuário)
- [ ] 5.5 Integrar com SEI (via API) para juntar relatório ao processo automaticamente — fase futura

---

## Estimativas de Esforço

| Fase | Estimativa | Dependências |
|------|-----------|--------------|
| 0 (Pré-requisitos) | 3–5 dias (geração de embeddings é o gargalo) | Nenhuma |
| 1 (Backend) | 8–12 dias dev | Fase 0 concluída |
| 2 (Frontend) | 6–8 dias dev | Fase 1 concluída |
| 3 (Regras estaduais) | Contínuo (pesquisa jurídica) | Paralelo com 1 e 2 |
| 4 (Validação) | 2–3 dias + feedback | Fases 1+2 concluídas |
| 5 (Go-to-market) | Indefinido | Fase 4 aprovada |

**Total mínimo para MVP**: ~20 dias dev + validação jurídica

---

## Decisões de Design

1. **PNCP como fonte primária**: já temos os dados, é fonte aceita pelo TCU, tem links rastreáveis
2. **Mediana como estatística padrão**: recomendada pelo Acórdão 2450/2016, mais robusta a outliers que média
3. **IPCA aplicado automaticamente**: para dados com mais de 12 meses, conforme Acórdão 825/2023
4. **Alertas, não bloqueios**: sistema não impede geração com amostra pequena, mas alerta — o servidor tem autonomia
5. **Templates por estado como texto, não código**: facilita atualização quando norma muda, sem deploy
6. **Relatório imutável**: uma vez gerado, o PDF/XLSX não muda — preserva a situação no momento da pesquisa
7. **Assinatura física obrigatória**: campo para nome/cargo mas sem assinatura digital (por ora) — reduz complexidade

---

## Próximos Passos Imediatos

1. Resolver Fase 0 (embeddings + categorias) — bloqueador técnico
2. Pesquisar regras estaduais para GO, SP, DF, MG (pode ser paralelo)
3. Repassar plano ao agente `dev` para implementação das Fases 1 e 2
4. Agendar sessão de validação com especialista em licitações

---

*Este documento deve ser revisado a cada fase concluída.*
