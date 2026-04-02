# PLANO V3 — Banco de Preços / Licitação as a Service

<!-- PROGRESSO ATUAL — atualizado 2026-03-31 -->
<!--
SEMANAS CONCLUÍDAS:
  [x] Semana 1  — Fundação (stack, Docker, CI)
  [x] Semana 2  — Coleta raw PNCP + pipeline de ingestão
  [x] Semana 3  — FastAPI, migrations, seeds, normalizacao.py → 46 testes
  [x] Semana 4  — classificador_regex, catmat_mapper, scoring → 111 testes
  [x] Semana 5  — motor_estatistico, routers/precos, schemas → 146 testes
  [x] Semana 6  — gerador_relatorio (PDF), routers relatorios+busca → 167 testes
  [x] Semana 7  — pncp_conector, pipeline_piloto, routers/piloto → 190 testes
  [x] Semana 8  — calibrar_outlier, compatibilidade_unidades, exportacao xlsx, melhorias PDF, sinônimos → 229 testes
  [x] Semana 9  — Auth JWT, tenants, papéis, test_auth.py → (264 testes)
  [x] Semana 10 — Dashboard + Métricas, test_dashboard.py → 264 testes ✅
  [x] Semana 11 — Billing e Planos persistentes, uso_mensal, página comercial → 335 testes
  [x] Semana 12 — Beta fechado: convites, checklist persistente, beta_report → 343 testes

PRÓXIMA: Semana 13
STATUS: 343/343 testes passando
-->



**Versão:** 3.0  
**Data:** 29/03/2026  
**Responsável:** Siriguejo 🦀 / Araticum Comércio LTDA  
**Base de referência:** plano v2 encontrado em `siriguejo/projetos/banco-de-precos/PLANO.md` + protótipo `pncp_mvp.py`

---

## 1. Objetivo executivo

Construir um **Banco de Preços / Licitação as a Service (LaaS)** para municípios, câmaras, autarquias e consultorias, capaz de:

1. consolidar preços públicos e de mercado a partir de fontes oficiais e complementares;
2. normalizar descrições de itens e serviços com rastreabilidade;
3. gerar **relatórios de pesquisa de preços auditáveis**, aderentes à Lei nº 14.133/2021, art. 23, e à IN SEGES/ME nº 65/2021;
4. reduzir tempo operacional da equipe de compras;
5. reduzir risco de sobrepreço, glosa, impugnação e questionamento por órgãos de controle;
6. criar uma oferta comercial escalável para a Araticum.

---

## 2. Premissas e suposições

### 2.1 Premissas assumidas

- O **PNCP** será a fonte primária do produto no MVP.
- O produto será desenhado para atender primeiro **compras municipais**, não o mercado federal amplo.
- O sistema precisará sustentar **rastreabilidade completa** de cada preço utilizado em relatório.
- O produto deverá cobrir pelo menos os parâmetros **I, II e III** da IN 65/2021, deixando o parâmetro IV como apoio operacional ao pregoeiro.
- O time inicial será enxuto, então a arquitetura precisa equilibrar robustez com velocidade de entrega.
- Existe um protótipo inicial (`pncp_mvp.py`) útil para aprendizado, mas **não serve como base de produção** sem reestruturação.

### 2.2 Restrições

- Dados do PNCP possuem lacunas, principalmente em homologação por item, unidade e CATMAT/CATSER.
- Fontes como TCEs, NFe e alguns portais estaduais têm alto custo de integração.
- A pesquisa direta com fornecedores não é plenamente automatizável de forma juridicamente segura.
- O produto não pode vender a ideia de “substituir o julgamento do pregoeiro”; ele deve vender **suporte técnico e base referencial auditável**.

### 2.3 Decisão estratégica

O produto será construído em **três camadas evolutivas**:

1. **MVP operacional**: PNCP + relatórios + busca textual/semântica + piloto real.
2. **Beta comercial**: múltiplas fontes, usuários reais pagantes, billing, autenticação, auditoria madura.
3. **GA / produto completo**: cobertura nacional, benchmark regional, APIs externas, integrações com sistemas de compras e módulos premium.

---

## 3. Proposta de valor

### 3.1 Proposta principal

Entregar ao setor de compras uma base de preços referencial **mais barata, mais simples e mais focada em municípios** do que soluções tradicionais, com:

- pesquisa rápida por item/serviço;
- mediana, média, desvio e histórico;
- amostras rastreáveis;
- classificação de qualidade da evidência;
- relatório pronto para instrução processual.

### 3.2 Proposta secundária

Para consultorias, o sistema funcionará como **motor de produção de pesquisas de preços** com:

- marca branca em relatórios;
- trilha de auditoria;
- histórico por cliente;
- produtividade elevada na elaboração de pareceres e instruções.

---

## 4. Escolha de stack final

## 4.1 Stack escolhida

### Backend principal
- **FastAPI (Python)**

### ETL / coleta / normalização / jobs
- **Python**

### Frontend
- **Next.js + TypeScript + TailwindCSS + shadcn/ui**

### Banco de dados
- **PostgreSQL + pgvector**

### Filas / processamento assíncrono
- **RQ ou Celery com Redis** no beta; no MVP pode iniciar com jobs agendados simples e fila leve.

### Infraestrutura
- **Docker Compose** no MVP e beta inicial
- Evolução para ambiente gerenciado posteriormente

### Observabilidade
- **Sentry + Prometheus/Grafana + logs estruturados JSON**

### Autenticação
- **JWT + sessão de aplicação** com controle de tenants

### Billing
- módulo interno simples no beta, preparado para integração com gateway de pagamento

## 4.2 Justificativa

A escolha por **FastAPI + Python** é a melhor para este projeto porque:

1. o núcleo do produto é **dados, ETL, NLP, normalização e estatística**, áreas em que Python é superior em produtividade;
2. o protótipo já está em Python (`pncp_mvp.py`), o que reduz fricção;
3. bibliotecas para ingestão, scraping, processamento, embeddings e análise estatística são maduras em Python;
4. a API HTTP com FastAPI é suficientemente robusta, rápida e bem documentável para SaaS B2G;
5. manter ETL e backend principal no mesmo ecossistema reduz custo cognitivo do time.

**Decisão final:** não dividir backend principal entre Node e Python. O backend será **Python/ FastAPI**, e o frontend será **Next.js**.

---

## 5. Arquitetura alvo

## 5.1 Visão em alto nível

```text
[ Fontes Externas ]
   ├─ PNCP
   ├─ Compras.gov
   ├─ SINAPI / SICRO / BPS / CMED / SUS / CUB
   ├─ IBGE/IPCA
   ├─ Sites de domínio amplo
   └─ Portais/TCEs (fase posterior)

                ↓

[ Camada de Ingestão ]
   ├─ conectores HTTP/API
   ├─ scraping controlado onde necessário
   ├─ jobs agendados
   └─ staging raw

                ↓

[ Camada de Processamento ]
   ├─ limpeza textual
   ├─ deduplicação
   ├─ normalização de unidade
   ├─ classificação CATMAT/CATSER
   ├─ categorização semântica
   ├─ cálculo estatístico
   ├─ score de qualidade do preço
   └─ trilha de auditoria

                ↓

[ Camada de Persistência ]
   ├─ PostgreSQL relacional
   ├─ pgvector
   ├─ snapshots de evidência
   └─ storage de artefatos (PDF/screenshots)

                ↓

[ Camada de Aplicação ]
   ├─ API FastAPI
   ├─ autenticação e tenants
   ├─ busca textual/semântica
   ├─ geração de relatórios
   ├─ dashboard operacional
   └─ administração interna

                ↓

[ Camada de Interface ]
   ├─ painel web do pregoeiro
   ├─ painel da consultoria
   ├─ área admin
   └─ exportações PDF/Excel/CSV
```

## 5.2 Princípios arquiteturais

- **Fonte rastreável ou não entra no relatório**.
- **Toda transformação precisa ser auditável**.
- **Preço referencial sem contexto é risco**; o produto sempre deve expor metadados.
- **MVP simples, dados corretos, UX suficiente**; evitar complexidade prematura.
- **Domínio de dados é o coração do negócio**; frontend é consequência.

---

## 6. Modelo de domínio e dados

## 6.1 Entidades centrais

### Entidades obrigatórias
- `orgaos`
- `contratacoes`
- `itens`
- `fontes_preco`
- `evidencias`
- `categorias`
- `item_categoria`
- `estatisticas_preco`
- `relatorios`
- `relatorio_itens`
- `tenants`
- `usuarios`
- `auditoria_eventos`

## 6.2 Ajustes sobre o modelo v2

Além das tabelas já previstas no v2, o v3 deve introduzir explicitamente:

### `fontes_preco`
Tabela unificadora para representar cada amostra válida de preço, independentemente da origem.

Campos sugeridos:
- `id`
- `fonte_tipo` (`PNCP`, `COMPRAS_GOV`, `SINAPI`, `BPS`, `MERCADO`, etc.)
- `fonte_referencia`
- `item_id` ou referência canônica
- `preco_unitario`
- `preco_total`
- `quantidade`
- `unidade_original`
- `unidade_normalizada`
- `data_referencia`
- `municipio`
- `uf`
- `esfera`
- `url_origem`
- `qualidade_tipo` (`HOMOLOGADO`, `ESTIMADO`, `TABELA_OFICIAL`, `MERCADO`)
- `score_confianca`
- `outlier_flag`
- `ativo`

### `evidencias`
Para anexar prova documental e viabilizar auditoria.

Campos sugeridos:
- `id`
- `fonte_preco_id`
- `tipo_evidencia` (`JSON_RAW`, `HTML`, `PDF`, `SCREENSHOT`, `LINK`, `ATA`) 
- `storage_path`
- `hash_sha256`
- `capturado_em`
- `metadados_json`

### `auditoria_eventos`
Para trilha completa de alteração.

Campos sugeridos:
- `id`
- `entidade`
- `entidade_id`
- `acao`
- `usuario_id` ou `job_id`
- `payload_before`
- `payload_after`
- `timestamp`

## 6.3 Chaves naturais e deduplicação

### Estratégia principal

**Chave natural de contratação PNCP:**
- `numero_controle_pncp`

**Chave natural de item PNCP:**
- `numero_controle_pncp + numero_item`

**Chave natural de amostra de preço:**
- `fonte_tipo + identificador_externo + item_ref + data_referencia + preco_unitario + quantidade`

### Regras de deduplicação

- [ ] Rejeitar inserção duplicada exata por chave natural.
- [ ] Detectar duplicatas prováveis por similaridade textual + mesma fonte + mesma data + mesmo preço.
- [ ] Manter snapshots raw para reprocessamento futuro.
- [ ] Nunca apagar linha crua; apenas marcar `ativo=false` quando invalidada.

## 6.4 Normalização de unidade

Problema recorrente:
- UN
- UND
- UNIDADE
- CX com 12
- PACOTE 500G
- LITRO / ML

### Estratégia

Criar uma camada de **canonização de unidade** com:
- tabela `unidades_canonicas`
- fatores de conversão
- regras por categoria
- bloqueio de comparação quando conversão não for segura

Exemplo:
- `500 ml` → `0.5 L`
- `caixa com 12 unidades` → manter como embalagem, não comparar automaticamente com unidade avulsa sem regra explícita

---

## 7. Estratégia de ingestão e ETL

## 7.1 Camadas do pipeline

### Camada 1 — Raw ingest
Responsável por capturar dados sem interpretação de negócio.

- [ ] consumir endpoint de publicações PNCP
- [ ] consumir endpoint de itens PNCP
- [ ] guardar payload bruto JSON
- [ ] registrar hash do payload
- [ ] registrar carimbo de tempo da coleta
- [ ] registrar status HTTP e versão do conector

### Camada 2 — Staging normalizado
Transforma payload bruto em colunas estruturadas.

- [ ] parsear campos relevantes
- [ ] padronizar datas
- [ ] normalizar CNPJ, UF, município
- [ ] separar contratação e itens
- [ ] mapear modalidade e esfera

### Camada 3 — Enriquecimento
Aplica inteligência e regras.

- [ ] limpeza de descrição
- [ ] extração de atributos
- [ ] tentativa de match por CATMAT/CATSER
- [ ] embedding semântico
- [ ] categorização
- [ ] normalização de unidade
- [ ] score de confiança

### Camada 4 — Analytics / serving
Gera dados prontos para uso de aplicação.

- [ ] estatísticas agregadas
- [ ] mediana
- [ ] média
- [ ] faixas interquartis
- [ ] outliers
- [ ] baseline por UF / esfera / período

## 7.2 Frequência de coleta

### MVP
- coleta PNCP diária, madrugada
- possibilidade de reprocessamento manual
- rotina incremental por data de publicação

### Beta
- coleta incremental múltiplas vezes ao dia
- jobs separados por UF e modalidade
- fila de reprocessamento por falha

### GA
- orquestração madura por jobs particionados
- backfill automatizado
- alertas de atraso por fonte

## 7.3 Estratégia por fonte

### PNCP
- fonte primária de contratação e itens
- coleta incremental + backfill histórico
- endpoint de publicação para descoberta
- endpoint de itens para granularidade

### Compras.gov
- complementar para histórico federal e atas
- priorizar integração com valor de RP/homologação quando disponível

### Tabelas oficiais
- ingestão por tabela específica, não unificar à força no raw
- cada tabela com conector próprio e mapeamento de escopo

### Sites de domínio amplo
- apenas para parâmetro III
- uso controlado e com screenshot obrigatório
- separar claramente no scoring para não contaminar análise pública com mercado aberto

---

## 8. Estratégia de qualidade e scoring

## 8.1 Classificação de qualidade da amostra

Toda amostra deve receber:

### Tipo de qualidade
- **A — Homologado por item**
- **B — Homologado agregado com decomposição confiável**
- **C — Estimado do edital**
- **D — Tabela oficial**
- **E — Mercado aberto**
- **F — Manual / excepcional**

### Score de confiança (0-100)
Componentes:
- completude dos campos
- confiabilidade da fonte
- existência de URL rastreável
- existência de artefato de evidência
- unidade normalizada com segurança
- categorização com alta confiança
- proximidade temporal

## 8.2 Política de outliers

### Regras mínimas
- [ ] calcular mediana
- [ ] calcular Q1 e Q3
- [ ] calcular IQR
- [ ] marcar outliers por regra estatística definida
- [ ] não excluir fisicamente
- [ ] exigir justificativa quando relatório incluir item com base reduzida

### Regra recomendada no MVP
Usar combinação de:
- IQR para detecção robusta
- desvio percentual em relação à mediana
- mínimo de amostras para confiabilidade

## 8.3 Regra de elegibilidade para relatório

Uma amostra entra no relatório se:
- [ ] possuir fonte identificável
- [ ] tiver data válida
- [ ] tiver valor unitário ou mecanismo seguro de cálculo unitário
- [ ] estiver ligada a categoria coerente
- [ ] unidade estiver normalizada ou explicitamente compatível
- [ ] não estiver invalidada por regra de auditoria

---

## 9. Estratégia de normalização e categorização

## 9.1 Pipeline de normalização

### Etapa 1 — Limpeza textual
- uppercase/normalização Unicode
- remoção de ruído (`conforme edital`, `demais especificações`, etc.)
- remoção de pontuação inútil
- normalização de números e medidas

### Etapa 2 — Extração de atributos
Extrair quando possível:
- marca
- modelo
- capacidade
- volume
- dimensão
- material/serviço
- unidade
- quantidade por embalagem

### Etapa 3 — Match por vocabulário controlado
- dicionário de sinônimos
- dicionário por categoria
- regex específicas por família

### Etapa 4 — Match por CATMAT/CATSER
- usar como sinal forte quando presente
- manter tabela de mapeamento curada

### Etapa 5 — Embedding semântico
- gerar embedding da descrição limpa
- buscar categoria mais próxima
- aceitar só acima de threshold conservador

### Etapa 6 — Revisão assistida
- filas de baixa confiança
- interface interna para revisão humana
- feedback loop para enriquecer regras

## 9.2 Estratégia de categorias

### Fase 1
Criar catálogo de **50 categorias prioritárias** com alta demanda municipal.

### Fase 2
Expandir para 150-200 categorias.

### Fase 3
Criar taxonomia viva com:
- família
- subfamília
- categoria canônica
- atributos obrigatórios por categoria

## 9.3 Definição de pronto — Motor de normalização
- [ ] 50 categorias implementadas
- [ ] score de classificação disponível
- [ ] taxa de acerto validada por amostragem > 85% nas categorias alvo do MVP
- [ ] fila de revisão manual funcional
- [ ] trilha de auditoria das correções manuais

---

## 10. Relatórios e compliance

## 10.1 Princípios do relatório

O relatório deve:
- ser entendível por pregoeiro;
- ser defensável perante controle interno e externo;
- deixar explícita a fonte e a metodologia;
- separar claramente preço homologado, estimado, tabela oficial e mercado;
- registrar exclusão de outliers e justificativa.

## 10.2 Estrutura mínima do relatório

- identificação do órgão/cliente
- item pesquisado
- período de referência
- abrangência geográfica
- parâmetros utilizados da IN 65/2021
- metodologia de seleção de amostras
- estatísticas calculadas
- preço referencial recomendado
- tabela de amostras
- observações sobre qualidade dos dados
- disclaimer jurídico
- data de emissão
- hash/ID do relatório

## 10.3 Texto sugerido de disclaimer

### Disclaimer operacional
> Este relatório constitui apoio técnico à pesquisa de preços, elaborado com base em fontes públicas e complementares rastreáveis. A definição final do preço estimado e a justificativa administrativa permanecem sob responsabilidade do órgão demandante e do agente público competente.

### Disclaimer de qualidade dos dados
> As informações foram consolidadas a partir de bases oficiais e complementares disponíveis na data da emissão. Eventuais lacunas, divergências cadastrais ou inconsistências de origem foram tratadas conforme a metodologia descrita neste documento, sem substituição do juízo técnico-administrativo do pregoeiro.

### Disclaimer de conformidade
> O relatório foi estruturado para atender aos parâmetros de pesquisa de preços previstos no art. 23 da Lei nº 14.133/2021 e na IN SEGES/ME nº 65/2021, observadas as limitações de disponibilidade e qualidade das bases consultadas.

## 10.4 Definição de pronto — Relatórios
- [ ] template PDF institucional aprovado
- [ ] geração automática por item/categoria funcional
- [ ] listagem de evidências incluída
- [ ] estatísticas reproduzíveis
- [ ] disclaimers jurídicos incluídos
- [ ] exportação PDF e XLSX disponível

---

## 11. Produto: módulos funcionais

## 11.1 Módulos do MVP
- [ ] busca de preços por texto livre
- [ ] filtros por UF, município, modalidade, período e esfera
- [ ] visualização de amostras
- [ ] estatísticas básicas
- [ ] geração de relatório PDF
- [ ] painel administrativo interno

## 11.2 Módulos do beta
- [ ] autenticação e multi-tenant
- [ ] gestão de usuários e permissões
- [ ] favoritos/histórico de consulta
- [ ] exportação XLSX/CSV
- [ ] dashboard de cobertura
- [ ] alertas de sobrepreço
- [ ] billing e controle de limites

## 11.3 Módulos do GA
- [ ] benchmark regional
- [ ] histórico de evolução temporal
- [ ] API externa para integração
- [ ] marca branca para consultorias
- [ ] relatórios customizados com brasão/logo
- [ ] módulo de revisão humana assistida
- [ ] PWA/mobile responsivo

---

## 12. Segurança, auditoria e governança

## 12.1 Segurança

### Controles mínimos
- [ ] autenticação forte
- [ ] hash seguro de senhas
- [ ] segregação por tenant
- [ ] autorização por papel
- [ ] criptografia em trânsito (TLS)
- [ ] backups automáticos
- [ ] storage com controle de acesso
- [ ] logs de acesso e ação crítica

## 12.2 Auditoria

Registrar no mínimo:
- geração de relatório
- alteração de categoria/manual override
- invalidação de amostra
- alteração de parâmetros de cálculo
- upload ou captura de evidência
- exportação sensível

## 12.3 Governança de dados
- [ ] catálogo de fontes mantido
- [ ] política de retenção de raw definida
- [ ] política de versionamento de regras definida
- [ ] data owner responsável pelo domínio
- [ ] changelog de conectores e metodologia

---

## 13. CI/CD, ambientes e observabilidade

## 13.1 Ambientes
- **dev**
- **staging**
- **prod**

## 13.2 Pipeline CI/CD
- [ ] lint backend/frontend
- [ ] testes unitários
- [ ] testes de integração
- [ ] migrations automatizadas em staging
- [ ] build de containers
- [ ] deploy automatizado com aprovação manual para produção

## 13.3 Observabilidade

### Métricas obrigatórias
- taxa de sucesso por conector
- latência por fonte
- volume coletado por execução
- taxa de categorização automática
- taxa de erro por relatório
- tempo médio de geração de relatório
- volume de consultas por tenant

### Alertas obrigatórios
- falha de coleta PNCP
- queda abrupta de volume
- aumento de erro de parsing
- fila travada
- storage de evidências com falha
- banco sem backup recente

---

## 14. Estratégia de QA

## 14.1 Tipos de teste

### Backend / dados
- [ ] testes unitários de parser
- [ ] testes de normalização textual
- [ ] testes de deduplicação
- [ ] testes de cálculo estatístico
- [ ] testes de geração de relatório

### Integração
- [ ] testes com mocks de PNCP
- [ ] testes de conectores reais em janela controlada
- [ ] testes de storage de evidência

### Frontend
- [ ] testes de componentes críticos
- [ ] smoke tests do fluxo de busca e relatório

### QA funcional
- [ ] validação manual por amostragem
- [ ] comparação com editais reais
- [ ] validação com equipe usuária do piloto

## 14.2 Critérios mínimos de aceite

### MVP
- taxa de erro de relatório < 2%
- tempo de resposta de busca < 3 s em consultas típicas
- tempo de geração de PDF < 30 s
- 50 categorias prioritárias cobertas

### Beta
- autenticação estável
- billing funcional
- cobertura multi-UF crescente
- logs e observabilidade maduros

---

## 15. Backlog por épicos

## Épico 1 — Fundação técnica
- [ ] definir stack final
- [ ] criar monorepo ou estrutura de repositórios
- [ ] configurar Docker Compose
- [ ] configurar banco PostgreSQL + pgvector
- [ ] configurar FastAPI base
- [ ] configurar Next.js base
- [ ] configurar CI inicial

## Épico 2 — Ingestão PNCP
- [ ] conector de publicações
- [ ] conector de itens
- [ ] staging raw
- [ ] parser estruturado
- [ ] deduplicação base
- [ ] scheduler

## Épico 3 — Modelo de domínio
- [ ] migrations iniciais
- [ ] tabelas core
- [ ] tabelas de evidência e auditoria
- [ ] seeds de categorias iniciais

## Épico 4 — Normalização e categorização
- [ ] limpeza textual
- [ ] regras por regex
- [ ] mapeamento CATMAT/CATSER
- [ ] embeddings
- [ ] interface de revisão manual

## Épico 5 — Estatística e motor referencial
- [ ] cálculo de mediana/média
- [ ] outliers
- [ ] score de confiança
- [ ] recomendação de preço

## Épico 6 — Relatórios
- [ ] template PDF
- [ ] exportação PDF
- [ ] exportação XLSX
- [ ] hash e trilha de auditoria

## Épico 7 — Frontend do usuário
- [ ] página de busca
- [ ] filtros avançados
- [ ] visualização de amostras
- [ ] dashboard básico

## Épico 8 — Multi-tenant e billing
- [ ] auth
- [ ] tenants
- [ ] limites por plano
- [ ] gestão de assinaturas

## Épico 9 — Expansão de fontes
- [ ] Compras.gov
- [ ] IBGE/IPCA
- [ ] tabelas oficiais prioritárias
- [ ] sites de domínio amplo

## Épico 10 — Operação e go-live
- [ ] observabilidade
- [ ] playbooks operacionais
- [ ] suporte
- [ ] onboarding piloto

---

## 16. Plano semanal minucioso

## Semana 1 — Kickoff e fundação
- [ ] definir escopo fechado do MVP
- [ ] escolher stack final formalmente
- [ ] criar arquitetura inicial do repositório
- [ ] provisionar ambiente local com Docker Compose
- [ ] criar banco e migrations iniciais
- [ ] configurar FastAPI e Next.js base
- [ ] configurar CI lint/test

**Definição de pronto da semana 1:** ambiente sobe localmente com backend, frontend e banco; migrations aplicam sem erro.

## Semana 2 — Coleta raw PNCP
- [ ] implementar cliente PNCP robusto
- [ ] coletar publicações por período/UF/modalidade
- [ ] coletar itens por contratação
- [ ] persistir JSON raw
- [ ] persistir staging estruturado
- [ ] criar rotina incremental diária

**Definição de pronto da semana 2:** coleta PNCP funcionando fim a fim com persistência raw e estruturada.

## Semana 3 — Modelo de dados de serving
- [ ] modelar orgaos/contratacoes/itens/fontes_preco/evidencias
- [ ] implementar deduplicação
- [ ] criar seeds de categorias prioritárias
- [ ] criar normalização básica de datas, unidades e CNPJ

**Definição de pronto da semana 3:** dados estruturados navegáveis e deduplicados no banco.

## Semana 4 — Normalização v1
- [ ] pipeline de limpeza textual
- [ ] regras regex para top categorias
- [ ] mapeamento CATMAT/CATSER
- [ ] geração de embeddings
- [ ] classificação assistida

**Definição de pronto da semana 4:** itens principais de teste classificados com acurácia aceitável.

## Semana 5 — Motor estatístico
- [ ] cálculo de mediana, média, quartis e desvio
- [ ] marcação de outliers
- [ ] score de qualidade
- [ ] API de consulta por item/categoria

**Definição de pronto da semana 5:** API retorna amostras e estatísticas coerentes.

## Semana 6 — Relatório PDF e interface MVP
- [ ] busca web mínima
- [ ] filtros por período/UF/modalidade
- [ ] visualização de amostras
- [ ] geração de relatório PDF
- [ ] hash/ID de emissão

**Definição de pronto da semana 6:** MVP demonstrável para uso interno.

## Semana 7 — Piloto controlado
- [ ] ingestão focada em Santo Antônio do Descoberto
- [ ] ingestão focada em Anápolis
- [ ] selecionar 20 itens mais recorrentes
- [ ] emitir relatórios amostra
- [ ] comparar com editais reais

**Definição de pronto da semana 7:** case piloto com evidência comparativa real.

## Semana 8 — Ajustes de qualidade
- [ ] revisar erros de classificação
- [ ] calibrar outliers
- [ ] corrigir templates
- [ ] melhorar unidade e compatibilidade
- [ ] fechar lista de gaps jurídicos e técnicos

## Semana 9 — Auth e tenants
- [ ] login
- [ ] papéis
- [ ] organização/tenant
- [ ] segregação de dados

## Semana 10 — Exportação e dashboard
- [ ] XLSX/CSV
- [ ] dashboard de uso e cobertura
- [ ] dashboard admin interno

## Semana 11 — Billing e planos
- [ ] modelagem dos planos
- [ ] limites por consulta/relatório
- [ ] página comercial/assinatura

## Semana 12 — Beta fechado
- [x] onboarding de poucos clientes reais
- [x] suporte inicial
- [x] coleta de feedback estruturado
- [x] congelamento do escopo do beta

## Semanas 13-16 — Expansão
- [ ] ampliar UFs prioritárias
- [ ] integrar Compras.gov
- [ ] integrar IPCA/IBGE
- [ ] melhorar busca semântica
- [ ] alertas de sobrepreço

## Semanas 17-20 — Preparação para GA
- [ ] hardening de segurança
- [ ] observabilidade madura
- [ ] playbook de incidentes
- [ ] otimização de custos
- [ ] benchmark regional
- [ ] API externa inicial

---

## 17. MVP, Beta e GA

## 17.1 MVP

### Escopo
- PNCP como núcleo
- top 50 categorias
- busca web básica
- estatística básica
- PDF de pesquisa de preços
- piloto em 2 municípios

### Não entra no MVP
- billing completo
- API externa pública
- white-label avançado
- integração massiva com TCEs
- PWA/mobile

## 17.2 Beta

### Escopo
- multi-tenant
- billing
- exportações
- Compras.gov
- IPCA
- dashboard operacional
- primeiros clientes pagantes

## 17.3 GA

### Escopo
- cobertura nacional progressiva
- benchmark regional
- API externa
- white-label
- integrações ampliadas
- operação estável e escalável

---

## 18. Critérios de go-live

## 18.1 Critérios técnicos
- [ ] backup testado
- [ ] restore testado
- [ ] monitoramento ativo
- [ ] logs estruturados operando
- [ ] tempos de resposta dentro da meta
- [ ] jobs críticos com alerta

## 18.2 Critérios de dados
- [ ] top categorias com qualidade validada
- [ ] pipeline incremental estável
- [ ] taxa de duplicidade sob controle
- [ ] amostras auditáveis

## 18.3 Critérios de negócio
- [ ] pricing validado
- [ ] piloto com prova de valor
- [ ] onboarding documentado
- [ ] suporte mínimo definido

## 18.4 Critérios jurídicos/operacionais
- [ ] disclaimers revisados
- [ ] metodologia documentada
- [ ] política de uso definida
- [ ] termos comerciais aprovados

---

## 19. Custos e capacidade

## 19.1 Custo estimado inicial

### Infraestrutura MVP/Beta inicial
- VPS + banco + storage: R$ 200 a R$ 500/mês
- observabilidade e serviços auxiliares: R$ 100 a R$ 300/mês
- suporte humano parcial: R$ 2.000 a R$ 4.000/mês
- marketing/comercial inicial: R$ 500 a R$ 2.000/mês

## 19.2 Alocação mínima de time
- 1 backend/data engineer
- 1 frontend/fullstack
- 1 pessoa de produto/negócio
- 1 apoio jurídico/consultivo sob demanda
- QA compartilhado inicialmente

---

## 20. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Lacunas no PNCP | Alto | score de qualidade, fallback para estimado, fontes complementares |
| Classificação ruim de itens | Alto | top categorias priorizadas, revisão humana, feedback loop |
| Falta de homologado por item | Alto | camadas de qualidade e transparência no relatório |
| Integrações externas instáveis | Médio | conectores desacoplados, retry/backoff, staging raw |
| Questionamento jurídico do relatório | Alto | metodologia explícita, disclaimers, rastreabilidade |
| Crescimento desorganizado da taxonomia | Médio | governança de categorias e ownership |
| Produto ficar “genérico demais” | Alto | foco municipal e priorização por casos reais |
| Sobrecarga operacional do time | Médio | limitar escopo do MVP e adiar integrações caras |

---

## 21. Checklists finais por macroentrega

## 21.1 Fundação
- [ ] stack definida
- [ ] ambientes criados
- [ ] CI básico rodando
- [ ] migrations criadas

## 21.2 Dados
- [ ] ingestão PNCP pronta
- [ ] deduplicação pronta
- [ ] normalização inicial pronta
- [ ] score de qualidade pronto

## 21.3 Produto MVP
- [ ] busca pronta
- [ ] filtros prontos
- [ ] estatísticas prontas
- [ ] relatório PDF pronto

## 21.4 Piloto
- [ ] municípios carregados
- [ ] itens priorizados
- [ ] relatórios emitidos
- [ ] comparação com casos reais documentada

## 21.5 Beta
- [ ] auth pronta
- [ ] tenants prontos
- [ ] billing pronto
- [ ] suporte mínimo pronto

## 21.6 Go-live
- [ ] backups testados
- [ ] observabilidade ativa
- [ ] metodologia publicada
- [ ] checklist jurídico concluído

---

## 22. Recomendação final

A execução deve começar **imediatamente pelo MVP baseado em PNCP**, com foco obsessivo em:

1. **qualidade do dado**, 
2. **rastreabilidade**, 
3. **normalização de itens**, 
4. **relatório juridicamente defensável**.

A maior armadilha do projeto é tentar construir “um grande banco nacional” cedo demais. O caminho correto é:

- dominar 2 municípios;
- fechar 50 categorias críticas;
- provar economia/segurança jurídica;
- converter isso em produto;
- só depois escalar cobertura e integrações.

Se o time mantiver essa disciplina, o Banco de Preços terá boa chance de se tornar uma linha de receita recorrente sólida e uma vantagem competitiva real para a Araticum.
