# 📋 Checklist — Banco de Preços (Semanas 3-6)

**Data:** 30/03/2026  
**Status:** Semanas 1-2 ✅ | Semana 3+ 🔄  
**Responsável:** Siriguejo 🦀 + Dev Team

---

## 🎯 Próximos Passos Imediatos

### Semana 3 — Modelo de Dados de Serving
**Objetivo:** Dados estruturados, navegáveis e deduplicados no banco.

#### Backend / Banco
- [ ] **Migrations criadas**
  - [ ] tabela `orgaos` (id, nome, cnpj, uf, esfera)
  - [ ] tabela `contratacoes` (id, numero_controle_pncp, data_publicacao, modalidade, orgao_id)
  - [ ] tabela `itens` (id, numero_item, descricao, categoria_id, contratacao_id)
  - [ ] tabela `categorias` (id, nome, descricao, familia)
  - [ ] tabela `fontes_preco` (id, fonte_tipo, preco_unitario, data_referencia, municipio, uf, qualidade_tipo, score_confianca)
  - [ ] tabela `evidencias` (id, fonte_preco_id, tipo_evidencia, storage_path, hash_sha256, capturado_em)
  - [ ] tabela `auditoria_eventos` (id, entidade, entidade_id, acao, usuario_id, timestamp)

- [ ] **Seeds de categorias** (top 50 prioritárias)
  - [ ] Importação de lista inicial (Excel ou SQL)
  - [ ] Validação de CATMAT/CATSER mapping

- [ ] **Normalização base**
  - [ ] Função de normalização de datas (ISO 8601)
  - [ ] Função de normalização de CNPJ (XX.XXX.XXX/XXXX-XX)
  - [ ] Função de normalização de unidades (conversão básica: UN → UND)
  - [ ] Função de limpeza de descrição (uppercase, Unicode, pontuação)

- [ ] **Deduplicação**
  - [ ] Índices de chave natural para contratação (numero_controle_pncp)
  - [ ] Índices de chave natural para item (numero_controle_pncp + numero_item)
  - [ ] Índices de chave natural para amostra (fonte_tipo + identificador + data + preco)
  - [ ] Query de detecção de duplicata exata
  - [ ] Query de detecção de duplicata provável (similaridade)

#### Tests / QA
- [ ] Teste unitário: normalização de data
- [ ] Teste unitário: normalização de CNPJ
- [ ] Teste unitário: normalização de unidade
- [ ] Teste de integração: inserção + deduplicação

**Definição de Pronto S3:** Dados navegáveis e deduplicados no postgres + testes passando.

---

### Semana 4 — Normalização v1
**Objetivo:** Itens principais de teste classificados com acurácia aceitável.

#### Backend / Normalização
- [ ] **Pipeline de limpeza textual**
  - [ ] Remove `conforme edital`, `demais especificações`, etc.
  - [ ] Normaliza números (1000 → mil ou mantém?)
  - [ ] Remove pontuação inútil
  - [ ] Trata acrônimos (ex: `MDF-e` → `MDF`)

- [ ] **Regras de regex por top 10 categorias**
  - [ ] Papel/Cópia (ISO 75g, A4, etc.)
  - [ ] Limpeza/Higiene (detergente, álcool gel, etc.)
  - [ ] Combustível (gasolina aditivada, diesel S10, etc.)
  - [ ] Toner/Cartuchos
  - [ ] Alimentos (arroz 5kg, leite 1L, etc.)
  - [ ] Serviços de Limpeza
  - [ ] Pneus/Borracha
  - [ ] Equipamentos de Proteção
  - [ ] Placas de Sinalização
  - [ ] Água Mineral

- [ ] **Mapeamento CATMAT/CATSER** (se houver PNCP com código)
  - [ ] Tabela de lookup
  - [ ] Teste de hit rate

- [ ] **Embeddings semânticos** (usando Ollama ou API local)
  - [ ] Geração de embedding por descrição limpa
  - [ ] Indexação em pgvector
  - [ ] Query de similaridade

- [ ] **Classificação assistida**
  - [ ] Score de confiança
  - [ ] Fila de baixa confiança para revisão manual

#### Frontend / UI Interna
- [ ] **Interface de revisão manual** (simples)
  - [ ] Lista de itens sem categoria
  - [ ] Campo dropdown de categoria
  - [ ] Botão salvar + feedback

#### Tests / QA
- [ ] Teste: limpeza textual com sample de 100 descrições PNCP
- [ ] Teste: regex top 10 categorias com taxa de acerto > 80%
- [ ] Teste: embedding e similaridade

**Definição de Pronto S4:** 50 itens principais testados, 85%+ acurácia em categorias alvo.

---

### Semana 5 — Motor Estatístico
**Objetivo:** API retorna amostras e estatísticas coerentes.

#### Backend / Estatística
- [ ] **Cálculo de métricas agregadas**
  - [ ] Mediana por item
  - [ ] Média por item
  - [ ] Q1, Q3, IQR
  - [ ] Desvio-padrão
  - [ ] Min/Max (sem outliers)

- [ ] **Detecção de outliers**
  - [ ] Regra de IQR (outlier = < Q1 - 1.5*IQR ou > Q3 + 1.5*IQR)
  - [ ] Flag na tabela `fontes_preco` (outlier_flag boolean)
  - [ ] Query de rejeição em cálculos de média/mediana

- [ ] **Score de qualidade**
  - [ ] Componentes: completude, confiabilidade, URL rastreável, artefato, unidade normalizada, categoria, proximidade temporal
  - [ ] Ponderação final 0-100

- [ ] **API de consulta**
  - [ ] GET `/api/precos/busca?item_id=X&uf=XX&periodo=YYYY-MM` → lista de amostras
  - [ ] GET `/api/precos/item/{id}/estatisticas` → mediana, média, Q1, Q3, desvio, min/max, outlier_count
  - [ ] GET `/api/precos/categoria/{id}/cobertura` → quantos itens, quantas amostras

#### Tests / QA
- [ ] Teste: cálculo de mediana com dataset conhecido
- [ ] Teste: detecção de outliers com casos extremos
- [ ] Teste: score de qualidade correlação com fonte
- [ ] Teste de carga: 10k queries de busca em < 3s

**Definição de Pronto S5:** API estável, testes de carga passando, estatísticas auditáveis.

---

### Semana 6 — Relatório PDF e Interface MVP
**Objetivo:** MVP demonstrável para uso interno.

#### Frontend / Busca e Relatórios
- [ ] **Página de busca**
  - [ ] Input textual (busca livre)
  - [ ] Dropdown de categoria
  - [ ] Filtros: UF, Período (data_inicio/data_fim), Modalidade
  - [ ] Botão "Buscar"
  - [ ] Resultado: tabela de amostras + estatísticas resumidas

- [ ] **Visualização de amostras**
  - [ ] Tabela com colunas: fonte, preco_unitario, quantidade, unidade, data, qualidade_tipo, score
  - [ ] Link para evidência (se houver)
  - [ ] Badge de outlier

- [ ] **Dashboard resumido**
  - [ ] Total de itens no banco
  - [ ] Total de amostras
  - [ ] Cobertura por UF (mapa simples)
  - [ ] Top 10 categorias por volume

- [ ] **Geração de relatório PDF**
  - [ ] Template (estatísticas calculadas)
  - [ ] Header: órgão, período, abrangência
  - [ ] Seção "Metodologia de Seleção"
  - [ ] Tabela de amostras utilizada
  - [ ] Estatísticas: mediana, média, Q1, Q3, desvio
  - [ ] Campo "Preço Referencial Recomendado"
  - [ ] Observações sobre outliers
  - [ ] Disclaimers jurídicos (3 parágrafos)
  - [ ] Hash/ID de emissão (SHA256 de conteúdo)
  - [ ] Data/hora de emissão

- [ ] **Exportação XLSX**
  - [ ] Abas: resumo, amostras, estatísticas

#### Backend / PDF
- [ ] **Serviço de geração de PDF**
  - [ ] Usar `reportlab` ou `weasyprint`
  - [ ] Template base
  - [ ] Hash de integridade

#### Tests / QA
- [ ] Teste: geração de PDF com 1.000 amostras < 30s
- [ ] Teste: integridade do hash (PDF não muda, hash não muda)
- [ ] Teste: XLSX exporta sem erro com 10k linhas
- [ ] Teste funcional: fluxo completo (busca → visualização → PDF gerado)

**Definição de Pronto S6:** MVP fim-a-fim rodando. Relatório PDF pronto. Demo com Danilo OK.

---

## 📊 Resumo de Dependências

| Semana | Depende de | Bloqueadores Conhecidos |
|--------|-----------|------------------------|
| 3 | Dados PNCP da S2 | Nenhum |
| 4 | Tabela `itens`, `categorias` da S3 | Qualidade de categorização |
| 5 | Normalização S4, tabela `fontes_preco` da S3 | Edge cases em outliers |
| 6 | API S5, Frontend base | Template de PDF completo |

---

## 🚦 Critérios de Go/No-Go por Semana

### ✅ Semana 3 — Go se:
- [ ] Migrations aplicam sem erro
- [ ] PostgreSQL + pgvector rodando
- [ ] Seeds de 50 categorias inseridos
- [ ] Teste de deduplicação passa

### ✅ Semana 4 — Go se:
- [ ] Taxa de categorização > 85% em top 10
- [ ] Fila de revisão manual funcional
- [ ] 100 itens com categoria e score

### ✅ Semana 5 — Go se:
- [ ] API de busca respondendo < 500ms
- [ ] Cálculo de mediana validado
- [ ] Outliers detectados corretamente

### ✅ Semana 6 — Go se:
- [ ] PDF gerado com sucesso
- [ ] Demo com Danilo aprovada
- [ ] Zero erros de testes de aceitação

---

## 📝 Notas Operacionais

- **Daily:** reunião 10 min de status (segunda, quarta, sexta)
- **Repo:** usar branches `semana-3`, `semana-4`, etc.
- **Documentação:** atualizar daily no `PROGRESS.md` da pasta do projeto
- **Escalações:** avisar Siriguejo se algum bloqueador
- **Nada é finito:** cada semana tem revisão de qualidade antes de passar para a próxima

---

## 🎁 Entregáveis Esperados

### Semana 3
- Código migrado (git commit)
- Banco com dados PNCP estruturados e deduplicados

### Semana 4
- PR fechado com motor de normalização
- 50 categorias testadas

### Semana 5
- API de busca e estatísticas documentada
- Postman collection com exemplos

### Semana 6
- MVP rodando localmente
- PDF de exemplo gerado
- Demo gravada ou apresentada

---

**Próxima revisão:** 2026-04-06 (fim da Semana 3)
