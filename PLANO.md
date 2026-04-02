# 📊 Plano de Produto: Banco de Preços Referenciais para Municípios

**Versão:** 2.0 | **Data:** 26/03/2026
**Autor:** Mercado 📊 — Inteligência de Mercado B2G, Araticum Comércio LTDA
**Municípios-piloto:** Santo Antônio do Descoberto/GO e Anápolis/GO

---

## 1. VISÃO DO PRODUTO

### 1.1 Problema

Municípios pequenos e médios (< 200 mil hab) enfrentam um gargalo crítico na fase de pesquisa de preços das licitações:

- **Não usam o Compras.gov.br** (plataforma federal) — a maioria licita por sistemas próprios ou portais estaduais
- **Não têm acesso ao Painel de Preços** do governo federal (restrito a servidores com certificado digital gov.br)
- **Fazem pesquisa de preços artesanal** — 3 cotações por e-mail com fornecedores, muitas vezes recebendo preços inflados
- **Risco de sobrepreço** — sem base comparativa confiável, o preço estimado pode ser 30-80% acima do mercado
- **Risco jurídico** — pesquisa mal fundamentada pode gerar impugnações e questionamentos dos tribunais de contas

### 1.2 Solução

Plataforma web (SaaS) que oferece **preços referenciais auditáveis** com base em contratações públicas reais, extraídos automaticamente de fontes oficiais. O produto gera relatórios de pesquisa de preços prontos para anexar ao processo licitatório, em conformidade com a **IN SEGES/ME nº 65/2021** e a **Lei 14.133/2021 (art. 23, §1º)**.

### 1.3 Público-alvo

| Segmento | Perfil | Dor principal |
|----------|--------|---------------|
| Prefeituras pequenas (< 50 mil hab) | Pregoeiros, CPL, Setor de compras | Sem ferramenta de pesquisa de preços |
| Prefeituras médias (50-200 mil hab) | Diretoria de compras | Ferramenta cara ou ineficiente |
| Câmaras municipais | Setor administrativo | Volume baixo, não justifica ferramenta cara |
| Autarquias/fundações municipais | Compras e licitações | Mesmo problema das prefeituras |
| Consultorias de licitação | Empresas como a Araticum | Ferramenta de valor agregado para clientes |

### 1.4 Concorrentes

| Concorrente | Preço mensal | Foco | Fraqueza |
|-------------|-------------|------|----------|
| Banco de Preços S.A. | R$ 500-2.000/mês | Grandes órgãos federais | Caro para municípios pequenos |
| NeoGrid (Neogrid BPP) | R$ 800-3.000/mês | Indústria + governo | Interface complexa |
| Painel de Preços (gov) | Gratuito | Federal exclusivo | Acesso restrito, sem municipal |
| Licitanet/Bolsa de Compras | R$ 300-800/mês | Portal de licitação | Banco de preços é acessório |

**Diferencial Araticum:** preço acessível para município pequeno (a partir de R$ 99/mês), foco total em compras municipais, relatórios prontos para anexar ao processo, e consultoria integrada.

---

## 2. FONTES DE DADOS

### 2.1 Fonte primária: PNCP (Portal Nacional de Contratações Públicas)

**Status validado em 26/03/2026:**

| Dado | Disponibilidade | Qualidade |
|------|----------------|-----------|
| Contratações por UF/município | ✅ API pública | Boa cobertura (2235 pregões GO/2026) |
| Esfera (Federal/Estadual/Municipal) | ✅ Campo `esferaId` | 82% são municipais na amostra GO |
| Itens com descrição | ✅ Endpoint `/itens` | Descrições variam entre órgãos |
| Valor unitário estimado | ✅ Campo `valorUnitarioEstimado` | Presente em todos os itens |
| Valor homologado | ⚠️ Campo `valorTotalHomologado` | ~60% preenchido (estimativa) |
| Quantidade | ✅ Campo `quantidade` | Presente |
| Unidade de medida | ✅ Campo `unidadeMedida` | Presente mas inconsistente |
| CATMAT/CATSER | ⚠️ Nem sempre preenchido | Quando presente, é confiável |
| Modalidade | ✅ Campo `modalidadeId` | 6=Pregão, 8=Dispensa |
| Data | ✅ Campos de data | Precisas |
| SRP (Registro de Preços) | ✅ Campo `srp` | Boolean |

**Endpoints confirmados funcionais:**
```
GET /api/consulta/v1/contratacoes/publicacao
  ?dataInicial=YYYYMMDD&dataFinal=YYYYMMDD
  &codigoModalidadeContratacao=6  (6=Pregão, 8=Dispensa)
  &uf=XX
  &pagina=N&tamanhoPagina=50

GET /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens
  ?pagina=1&tamanhoPagina=50
```

### 2.2 Fontes complementares obrigatórias (conformidade IN 65/2021 + TCU)

A IN SEGES/ME nº 65/2021 (art. 5º) define **4 parâmetros** para pesquisa de preços, com ordem de prioridade. O banco deve cobrir **no mínimo 3 dos 4** para ser defensável perante TCU (Acórdão 1.445/2015 e 2.170/2017 — Plenário).

| Parâmetro IN 65 | Descrição | Banco cobre? | Como |
|-----------------|-----------|-------------|------|
| **I** — Painel de Preços / banco de preços em saúde | Composição de custos ≤ mediana | ✅ Sim | PNCP + BPS/CMED (saúde) |
| **II** — Contratações similares (últimos 12 meses, corrigido IPCA) | Preços de licitações reais | ✅ Sim (core do produto) | PNCP + Compras.gov |
| **III** — Mídia especializada / sites de domínio amplo | Preços de mercado aberto | ✅ Sim (integração) | APIs de e-commerce |
| **IV** — Pesquisa direta com ≥3 fornecedores | Cotações diretas | ❌ Não automatizável | Template p/ pregoeiro |

#### 2.2.1 Tabelas de referência oficiais (obrigatórias)

| Tabela | Órgão | Aplicação | Atualização | Acesso |
|--------|-------|-----------|-------------|--------|
| **SINAPI** | Caixa/IBGE | Obras e serviços de engenharia | Mensal | Público (caixa.gov.br) |
| **SICRO** | DNIT | Obras rodoviárias | Mensal | Público (dnit.gov.br) |
| **BPS** | Min. Saúde | Medicamentos e insumos | Contínua | Público (bps.saude.gov.br) |
| **CMED** | ANVISA | Preço máximo de medicamentos | Anual + ajustes | Público (anvisa.gov.br) |
| **Tabela SUS** | Min. Saúde | Procedimentos de saúde | Periódica | Público (sigtap.datasus.gov.br) |
| **CUB** | Sinduscon | Custo unitário de construção | Mensal | Público (sinduscon estaduais) |

#### 2.2.2 Sites de domínio amplo (Parâmetro III)

| Fonte | Tipo | Integração |
|-------|------|-----------|
| Magazine Luiza / KaBuM / Amazon BR | E-commerce | API ou scraping de preços |
| Buscapé / Zoom | Comparador de preços | API disponível |
| Mercado Livre | Marketplace | API oficial disponível |
| Google Shopping | Agregador | API paga |

**Nota:** O TCU aceita "print de tela" de sites de domínio amplo como evidência. O banco pode automatizar: capturar preço + URL + data + screenshot como prova.

#### 2.2.3 Outras fontes complementares

| Fonte | O que agrega | Dificuldade |
|-------|-------------|-------------|
| Compras.gov.br (SIASG) | Histórico federal desde 2005, atas de RP | Média — API existe mas mais restrita |
| TCE estaduais (dados abertos) | Contratos e preços auditados | Alta — cada TCE tem formato diferente |
| NFe (notas fiscais eletrônicas) | Preço real de mercado praticado | Alta — acesso via SEFAZ estadual, restrito |
| IBGE (deflator/IPCA) | Correção monetária obrigatória (IN 65, art. 5º, §2º) | Baixa — API pública |
| Portais estaduais (BEC, CELIC, etc) | Atas estaduais vigentes | Média — scraping em alguns |

### 2.3 Tratamento de lacunas de dados

#### Valor homologado ausente (~40% dos registros PNCP)

| Camada | Estratégia | Cobertura adicional |
|--------|-----------|-------------------|
| 1ª | Valor homologado por item (quando disponível no PNCP) | ~60% |
| 2ª | Atas de RP vigentes (Compras.gov + PNCP campo `srp=true`) | +15% |
| 3ª | Resultado da sessão via `linkSistemaOrigem` do Comprasnet | +10% |
| 4ª | Valor estimado como proxy (com flag "⚠️ estimativa") | Restante |

**Regra:** Todo preço no banco terá um **indicador de qualidade**:
- 🟢 **Homologado** — preço contratado real
- 🟡 **Estimado** — preço de referência do edital (não contratado)
- 🔵 **Tabela oficial** — SINAPI, SICRO, BPS, CMED
- 🟠 **Mercado** — site de domínio amplo (com URL rastreável)

#### Valor homologado agregado (múltiplos itens)

O endpoint `/itens` do PNCP retorna valor **por item individual** (campo `valorUnitarioEstimado` e `valorTotal`). O valor homologado por item depende do resultado da sessão. Estratégia:
- Usar endpoint de itens (granularidade unitária) — sempre disponível
- Quando resultado da sessão existir, extrair preço unitário homologado
- Quando não existir, usar estimado com flag de qualidade

### 2.4 Conformidade TCU — Análise Detalhada

**Acórdãos de referência:**
- **Acórdão 1.445/2015 — Plenário:** Pesquisa deve usar preferencialmente mais de um parâmetro
- **Acórdão 2.170/2017 — Plenário:** Uso de apenas um parâmetro deve ser justificado
- **Acórdão 1.926/2021 — Plenário:** Reforça necessidade de mediana e tratamento de outliers
- **Acórdão 2.443/2022 — Plenário:** Aceita banco de preços como fonte válida do parâmetro I/II

**O que o produto entrega vs. o que o TCU exige:**

| Exigência TCU | Produto cobre? | Como |
|---------------|---------------|------|
| Múltiplos parâmetros (≥2) | ✅ | Parâmetros I, II e III integrados |
| Mediana como referência | ✅ | Cálculo automático |
| Correção IPCA para preços > 1 ano | ✅ | Integração API IBGE |
| Exclusão de outliers (metodologia definida) | ✅ | Desvio > 2σ da mediana = excluído com justificativa |
| Rastreabilidade (fonte + data + link) | ✅ | Cada preço tem fonte, URL, data da contratação |
| Cotação direta com fornecedores (parâmetro IV) | ❌ | Responsabilidade do pregoeiro — produto oferece template |

**Posicionamento honesto:** O banco cobre 3/4 parâmetros da IN 65. O parâmetro IV (cotação direta) é inerentemente presencial. O produto oferece template padronizado para o pregoeiro preencher e anexar ao relatório.

---

## 3. ARQUITETURA TÉCNICA

### 3.1 Stack proposto

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND (Web)                  │
│  Next.js + TailwindCSS + Shadcn/UI              │
│  → Busca de preços, relatórios, dashboard       │
└────────────────────┬────────────────────────────┘
                     │ API REST
┌────────────────────┴────────────────────────────┐
│                  BACKEND (API)                   │
│  FastAPI (Python) ou Node.js                     │
│  → Autenticação, busca, geração de relatórios   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────┐
│              BANCO DE DADOS                      │
│  PostgreSQL + pgvector                           │
│  → Dados estruturados + busca semântica          │
│  → Tabelas: itens, contratações, preços, órgãos │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────┐
│           PIPELINE DE COLETA (ETL)               │
│  Python (requests + pandas)                      │
│  → Coleta diária PNCP (cron)                    │
│  → Normalização de descrições (NLP)              │
│  → Cálculo de estatísticas                       │
└─────────────────────────────────────────────────┘
```

### 3.2 Modelo de dados (core)

```sql
-- Órgãos licitantes
CREATE TABLE orgaos (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    razao_social TEXT NOT NULL,
    esfera CHAR(1),           -- F, E, M, N
    uf CHAR(2),
    municipio TEXT,
    codigo_ibge VARCHAR(7),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contratações (compras)
CREATE TABLE contratacoes (
    id SERIAL PRIMARY KEY,
    orgao_id INT REFERENCES orgaos(id),
    numero_controle_pncp VARCHAR(50) UNIQUE,
    ano_compra INT,
    sequencial_compra INT,
    modalidade_id INT,         -- 6=Pregão, 8=Dispensa, etc.
    objeto TEXT,
    valor_total_estimado NUMERIC(15,2),
    valor_total_homologado NUMERIC(15,2),
    srp BOOLEAN DEFAULT FALSE,
    data_publicacao DATE,
    data_abertura DATE,
    data_encerramento DATE,
    situacao_id INT,
    link_sistema_origem TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Itens (granularidade de preço)
CREATE TABLE itens (
    id SERIAL PRIMARY KEY,
    contratacao_id INT REFERENCES contratacoes(id),
    numero_item INT,
    descricao TEXT NOT NULL,
    descricao_normalizada TEXT,  -- via NLP
    catmat_catser VARCHAR(20),
    material_ou_servico CHAR(1), -- M ou S
    quantidade NUMERIC(15,4),
    unidade_medida VARCHAR(30),
    valor_unitario_estimado NUMERIC(15,4),
    valor_unitario_homologado NUMERIC(15,4),
    valor_total NUMERIC(15,2),
    criterio_julgamento VARCHAR(30),
    tipo_beneficio VARCHAR(50),
    situacao VARCHAR(30),
    data_referencia DATE,       -- data da publicação/homologação
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice de busca semântica
CREATE TABLE itens_embedding (
    id SERIAL PRIMARY KEY,
    item_id INT REFERENCES itens(id),
    embedding vector(256),      -- embeddinggemma ou similar
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categorias normalizadas (agrupamento de itens similares)
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,          -- ex: "Câmera fotográfica digital"
    palavras_chave TEXT[],      -- ["câmera", "fotográfica", "mirrorless"]
    catmat_codes TEXT[],        -- CNAEs associados quando disponível
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Relação item ↔ categoria
CREATE TABLE item_categoria (
    item_id INT REFERENCES itens(id),
    categoria_id INT REFERENCES categorias(id),
    score FLOAT,                -- confiança da classificação
    PRIMARY KEY (item_id, categoria_id)
);

-- Estatísticas pré-calculadas (materialização)
CREATE TABLE estatisticas_preco (
    id SERIAL PRIMARY KEY,
    categoria_id INT REFERENCES categorias(id),
    uf CHAR(2),
    periodo_inicio DATE,
    periodo_fim DATE,
    qtd_amostras INT,
    preco_minimo NUMERIC(15,4),
    preco_maximo NUMERIC(15,4),
    preco_medio NUMERIC(15,4),
    preco_mediana NUMERIC(15,4),
    desvio_padrao NUMERIC(15,4),
    percentil_25 NUMERIC(15,4),
    percentil_75 NUMERIC(15,4),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.3 Pipeline de normalização de descrições

Este é o componente **mais crítico** do produto. A mesma "caneta esferográfica azul" aparece no PNCP como:
- "Caneta esferográfica, cor azul, ponta média"
- "CANETA ESFEROGRÁFICA AZUL"
- "Material de escritório - caneta azul"
- "Caneta tipo BIC cristal azul"

**Abordagem em 3 camadas:**

1. **Limpeza textual** (regex): uppercase, remover pontuação extra, normalizar unidades
2. **Classificação por CATMAT** (quando disponível): agrupar por código
3. **Embedding semântico** (pgvector): itens sem CATMAT são classificados por similaridade vetorial com categorias conhecidas

```python
# Pseudocódigo da normalização
def normalizar_item(descricao_raw):
    # Camada 1: limpeza
    desc = descricao_raw.upper().strip()
    desc = re.sub(r'\s+', ' ', desc)
    desc = remover_especificacoes_irrelevantes(desc)  # "conforme edital", etc.
    
    # Camada 2: CATMAT
    if catmat_code:
        categoria = CATMAT_MAP.get(catmat_code)
        if categoria:
            return categoria, 1.0  # confiança máxima
    
    # Camada 3: embedding
    emb = gerar_embedding(desc)
    matches = buscar_similares(emb, threshold=0.85)
    if matches:
        return matches[0].categoria, matches[0].score
    
    # Sem match — marcar para revisão manual
    return None, 0.0
```

---

## 4. FASES DE DESENVOLVIMENTO

### FASE 1 — MVP (Semanas 1-6)

**Objetivo:** Coletar dados do PNCP para GO, normalizar os 50 itens mais licitados, e gerar relatórios de pesquisa de preços em PDF.

#### Semana 1-2: Pipeline de coleta

| Tarefa | Detalhe |
|--------|---------|
| Script de coleta PNCP | Python + requests, paginação automática, todas as modalidades |
| Cron de coleta diária | Rodar 1x/dia às 4h, coletar últimas 24h por UF |
| Schema PostgreSQL | Criar tabelas conforme modelo acima |
| Ingestão inicial | Coletar todo GO dos últimos 12 meses (~26.000 pregões × ~10 itens = ~260.000 registros de preço) |
| Deduplicação | Evitar itens duplicados por `numero_controle_pncp + numero_item` |

**Estimativa de volume (GO, 12 meses):**
- ~2.235 pregões/trimestre × 4 = ~8.940 pregões/ano
- ~10 itens/pregão em média = ~89.400 registros de itens
- Com dispensa eletrônica (mod 8): +30% = ~116.000 registros

#### Semana 3-4: Normalização e categorização

| Tarefa | Detalhe |
|--------|---------|
| Top 50 categorias | Identificar os 50 itens/serviços mais licitados em GO |
| Normalização manual | Criar regras para as 50 categorias (regex + keywords) |
| Embedding pipeline | Gerar embeddings para itens sem CATMAT |
| Classificação automática | Classificar itens nas categorias com score de confiança |
| Validação | Amostrar 100 itens aleatórios, verificar taxa de acerto (meta: >85%) |

**Top 10 categorias esperadas (municípios GO — estimativa):**
1. Combustíveis (gasolina, diesel, etanol)
2. Material de escritório (papel, caneta, toner)
3. Material de limpeza
4. Medicamentos
5. Gêneros alimentícios
6. Material de construção
7. Equipamentos de informática
8. Veículos e peças automotivas
9. Uniformes e EPIs
10. Serviços de manutenção predial

#### Semana 5-6: Relatórios e interface mínima

| Tarefa | Detalhe |
|--------|---------|
| Gerador de relatório PDF | Template conforme IN 65/2021, com: fonte dos dados, mediana, média, desvio padrão, justificativa de preço |
| API de consulta | Endpoint: `GET /precos?item=caneta+azul&uf=GO&meses=12` |
| Interface web mínima | Busca por texto livre, filtro por UF, período, modalidade |
| Dashboard básico | Total de registros, cobertura por UF, últimas atualizações |

**Formato do relatório de pesquisa de preços (IN 65/2021):**

```
┌──────────────────────────────────────────────────────┐
│         RELATÓRIO DE PESQUISA DE PREÇOS              │
│         (Art. 23, §1º, Lei 14.133/2021)              │
├──────────────────────────────────────────────────────┤
│ Item: Câmera Fotográfica Digital Mirrorless          │
│ Período de referência: Mar/2025 a Mar/2026           │
│ UF: GO | Abrangência: Municipal + Estadual + Federal │
├──────────────────────────────────────────────────────┤
│ FONTES CONSULTADAS:                                  │
│ ☑ I - Painel de Preços/banco de preços (PNCP)       │
│ ☑ II - Contratações similares (Administração)        │
│ ☐ III - Mídia especializada                          │
│ ☐ IV - Pesquisa direta com fornecedores              │
├──────────────────────────────────────────────────────┤
│ RESULTADO:                                           │
│                                                      │
│ Nº amostras: 12                                      │
│ Preço mínimo:    R$ 14.200,00                        │
│ Preço máximo:    R$ 19.800,00                        │
│ Preço médio:     R$ 16.450,00                        │
│ PREÇO MEDIANA:   R$ 16.822,75  ← REFERÊNCIA         │
│ Desvio padrão:   R$ 1.320,00                        │
│ Coef. variação:  8,02%                               │
│                                                      │
│ DETALHAMENTO DAS AMOSTRAS:                           │
│ 1. GAPBR/DF — Pregão 380/2026 — R$ 16.822,75        │
│ 2. PM Anápolis — Pregão 45/2025 — R$ 15.990,00      │
│ 3. PM Goiânia — Pregão 112/2025 — R$ 17.500,00      │
│ ...                                                  │
├──────────────────────────────────────────────────────┤
│ Gerado por: Banco de Preços Araticum                 │
│ Data: 26/03/2026 | Fonte: PNCP (dados públicos)      │
└──────────────────────────────────────────────────────┘
```

### FASE 2 — Expansão (Semanas 7-12)

| Tarefa | Detalhe |
|--------|---------|
| Ampliar UFs | Adicionar DF, MG, SP, BA (os maiores mercados) |
| Integrar Compras.gov.br | Atas federais vigentes como referência adicional |
| Correção monetária | Aplicar IPCA/INPC para preços > 6 meses |
| API de embedding melhorada | Busca semântica: "computador desktop" encontra "microcomputador" |
| Alertas de sobrepreço | Comparar valor estimado do edital vs. mediana do banco → flag |
| Exportação Excel/CSV | Para pregoeiros que preferem planilha |
| Autenticação e planos | Login, assinatura mensal, controle de uso |

### FASE 3 — Produto completo (Semanas 13-20)

| Tarefa | Detalhe |
|--------|---------|
| Todas as UFs | Cobertura nacional (27 UFs) |
| Integração com TCEs | Dados auditados quando disponíveis |
| API para sistemas de compras | Permitir que portais municipais consultem automaticamente |
| Relatórios personalizados | Template com brasão/logo do município |
| Histórico de preços | Gráfico de evolução temporal por item |
| Benchmark regional | Comparar preço do município vs. média da região |
| App mobile (PWA) | Para pregoeiros em campo |
| Módulo de consultoria | Araticum revisa e valida pesquisas complexas |

---

## 5. PILOTO: SANTO ANTÔNIO DO DESCOBERTO E ANÁPOLIS

### 5.1 Por que esses municípios

| Aspecto | Santo Antônio do Descoberto | Anápolis |
|---------|----------------------------|----------|
| População | ~80 mil | ~400 mil |
| Porte | Pequeno (Entorno DF) | Médio-grande |
| Desafio | Pouca estrutura de compras | Volume alto, precisa de eficiência |
| Proximidade | Entorno de Brasília (acesso fácil) | 150km de Brasília |
| Representatividade | Típico município do Entorno | Típico município médio de GO |

### 5.2 Plano de validação

1. **Coletar todos os pregões** desses 2 municípios nos últimos 12 meses
2. **Identificar os 20 itens mais licitados** por cada um
3. **Gerar relatórios de pesquisa de preços** para esses itens usando o banco
4. **Comparar** com os preços estimados que os municípios usaram nos editais reais
5. **Quantificar a economia potencial** — se tivessem usado a mediana do banco vs. o preço que usaram
6. **Apresentar para a Prefeitura** como case de valor

### 5.3 Métricas de sucesso do piloto

| Métrica | Meta |
|---------|------|
| Itens categorizados automaticamente | > 85% |
| Precisão da classificação | > 80% |
| Tempo para gerar relatório | < 30 segundos |
| Economia média identificada | > 10% vs. preço estimado do município |
| Satisfação do pregoeiro (NPS) | > 7/10 |

---

## 6. MODELO DE NEGÓCIO

### 6.1 Precificação

| Plano | Preço/mês | Público | Inclui |
|-------|-----------|---------|--------|
| Básico | R$ 99/mês | Câmaras, autarquias pequenas | 50 consultas/mês, 10 relatórios PDF |
| Profissional | R$ 299/mês | Prefeituras < 100 mil hab | Ilimitado, relatórios PDF, exportação Excel |
| Premium | R$ 599/mês | Prefeituras 100-500 mil hab | Tudo + API, alertas, dashboard customizado |
| Enterprise | R$ 999/mês | Prefeituras > 500 mil hab | Tudo + integração com sistema de compras, suporte dedicado |
| Consultor | R$ 199/mês | Consultorias de licitação | 200 consultas/mês, marca branca nos relatórios |

### 6.2 Projeção de receita (12 meses)

**Cenário conservador (50 clientes):**
- 30 × Básico (R$ 99) = R$ 2.970/mês
- 15 × Profissional (R$ 299) = R$ 4.485/mês
- 5 × Premium (R$ 599) = R$ 2.995/mês
- **Total: ~R$ 10.450/mês = R$ 125.400/ano**

**Cenário otimista (200 clientes):**
- 100 × Básico = R$ 9.900/mês
- 60 × Profissional = R$ 17.940/mês
- 30 × Premium = R$ 17.970/mês
- 10 × Enterprise = R$ 9.990/mês
- **Total: ~R$ 55.800/mês = R$ 669.600/ano**

### 6.3 Custos operacionais estimados

| Item | Custo/mês |
|------|-----------|
| Infraestrutura (VPS + banco) | R$ 200-500 |
| API do PNCP | Gratuita |
| Domínio + SSL | R$ 15 |
| Suporte (1 pessoa part-time) | R$ 2.000-4.000 |
| Marketing digital | R$ 500-2.000 |
| **Total** | **R$ 2.715 - 6.515/mês** |

---

## 7. ASPECTOS LEGAIS E COMPLIANCE

### 7.1 Base legal para o produto

- **Lei 14.133/2021, Art. 23, §1º:** Define os parâmetros para pesquisa de preços — o produto atende os incisos I e II
- **IN SEGES/ME nº 65/2021:** Regulamenta a pesquisa de preços — o relatório gerado segue esse formato
- **Lei 12.527/2011 (LAI):** Todos os dados usados são públicos, acesso garantido por lei
- **LGPD:** Não há dados pessoais no produto (apenas dados de contratações públicas)

### 7.2 Riscos legais

| Risco | Mitigação |
|-------|-----------|
| Dados incorretos gerarem preço estimado errado | Disclaimer: "referencial, não substitui análise do pregoeiro" |
| Órgão de controle questionar a fonte | Citar PNCP como fonte oficial, com link rastreável |
| Concorrente alegar propriedade sobre dados | Dados públicos por força de lei — não há propriedade |
| PNCP mudar a API | Monitorar changelog, adaptar rapidamente |

---

## 8. CRONOGRAMA RESUMIDO

```
Semana 1-2:   Pipeline de coleta PNCP + schema PostgreSQL
Semana 3-4:   Normalização e categorização (Top 50 itens)
Semana 5-6:   API + interface web mínima + gerador de relatórios PDF
Semana 7:     Piloto — Santo Antônio do Descoberto e Anápolis
Semana 8:     Ajustes pós-piloto + feedback pregoeiros
Semana 9-10:  Expansão para DF, MG, SP
Semana 11-12: Autenticação, planos, landing page
Semana 13:    Lançamento beta público
Semana 14-16: Integração Compras.gov + correção monetária
Semana 17-20: Cobertura nacional + produto final
```

---

## 9. PRÓXIMOS PASSOS IMEDIATOS

1. **Validar volume de dados** — Coletar todos os pregões de Santo Antônio do Descoberto e Anápolis (últimos 12 meses) e quantificar itens disponíveis
2. **Prototipar normalização** — Pegar os 500 itens mais comuns de GO e testar a pipeline de classificação
3. **Gerar 5 relatórios de amostra** — Para itens como "combustível", "material de escritório", "equipamento de informática"
4. **Definir stack final** — FastAPI vs. Node.js, hospedagem, CI/CD
5. **Decidir nome do produto** — Sugestões: *Veredas Preços*, *PrecificaGov*, *Referencial*, *PreçoBase*

---

*Mercado 📊 — Araticum Comércio LTDA*
*"Inteligência de mercado que gera resultado."*
