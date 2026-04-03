# PLANO SPRINT AUTÔNOMO — Banco de Preços

**Início:** 2026-04-02 ~00:04  
**Janela:** 8 horas sem consulta ao usuário  
**Proibido:** push GitHub até nova autorização

## Tarefas (em ordem, testar cada uma antes de avançar)

### T1 — Categoria em branco
**Problema:** 76 itens reais, 0 com categoria (item_categoria vazio para dados PNCP)  
**Solução:** Implementar auto-classificação por regex/keywords na ingestão e retroativamente nos itens existentes  
- Criar `classificador_auto.py`: mapa keyword→categoria (usando lista CATEGORIAS do analise_service.py)  
- Rodar classificação em batch para todos itens sem categoria (76 atualmente)  
- Integrar no coletor_municipal.py: após insert_itens, auto-classificar  
- **Teste:** `SELECT COUNT(*) FROM item_categoria` deve ser > 0 após rodar

### T2 — Histórico por item (múltiplas contratações)
**Problema:** A listagem mostra apenas 1 registro por item. Precisa histórico completo.  
**Solução:**  
- Novo endpoint: `GET /api/v1/analise/historico/{descricao_normalizada}` — retorna TODOS os registros históricos agrupados por período  
- Schema: `{descricao, historico: [{data, preco, orgao, municipio, uf, pncp_url, tipo_preco, contratacao_id}]}`  
- Também `GET /api/v1/analise/historico-item?item_id=<uuid>` — histórico de um item específico  
- **Teste:** curl deve retornar lista com datas diferentes quando existirem

### T3 — Tipo de preço: ESTIMADO vs HOMOLOGADO
**Problema:** Sem distinção entre preço estimado (valorUnitarioEstimado) e homologado (resultado da disputa)  
**Solução:**  
- Adicionar coluna `tipo_preco` em itens: `estimado | homologado`  
- Migration SQL: `ALTER TABLE itens ADD COLUMN tipo_preco VARCHAR(20) DEFAULT 'estimado'`  
- Atualizar coletor: verificar endpoint `/resultado` — se tem `valorHomologado`, marcar como `homologado`  
- API listar_precos: incluir campo `tipo_preco` na resposta  
- Frontend: badge/pill visual — 🟡 Estimado | 🟢 Homologado  
- **Teste:** registros da Fonte A (fontes_preco) = homologado; Fonte B (itens diretos sem resultado) = estimado

### T4 — Seleção de item + comparação histórico vs outros lugares
**Problema:** Sem interface para selecionar um item e ver comparativo  
**Solução:**  
- Novo componente `ComparativoItem.tsx`:  
  - Input: busca/seleção de item por descrição  
  - Painel esquerdo: histórico local (todas as contratações do banco com esse item)  
  - Painel direito: benchmark regional (média por UF para descrição similar)  
  - Gráfico linha: evolução do preço ao longo do tempo  
  - Tabela: detalhes de cada ocorrência (data, preço, órgão, município, tipo: estimado/homologado)  
- Novo endpoint: `GET /api/v1/analise/comparativo-item?descricao=<texto>&uf=<opcional>` — retorna histórico + benchmark  
- Adicionar rota `/comparar` no App.tsx  
- **Teste:** buscar "Papel A4" deve retornar histórico + comparativo por UF

### T5 — Coleta massiva GO 2025+2026
**Requisito:** Todos os itens de todas as contratações de 2025 e 2026 no Estado de Goiás  
**Solução:**  
- Script `scripts/coletar_go_completo.py`:  
  - Modalidades: 6 (Pregão), 8 (Dispensa), também 4 (Concorrência) e 5 (Concurso)  
  - Data: 2025-01-01 → hoje  
  - Sem filtro por esfera (pegar municipal + estadual)  
  - Situação: 1 (divulgada) e 2 (homologada)  
  - Buscar resultado de cada item (tipo_preco)  
  - Log de progresso em tmp/outputs/coleta_go_YYYYMMDD.txt  
  - Checkpoint: salvar progresso em tmp/coleta_go_checkpoint.json (retomável)  
- Após coleta: rodar classificação automática nos novos itens  
- Após classificação: refresh mv_media_preco_municipal  
- **Teste:** COUNT(*) FROM itens deve crescer significativamente

## Regras de execução
1. Testar antes de avançar: se falhar, corrigir até passar
2. Não fazer push GitHub
3. Logs em tmp/outputs/sprint_autonomo_YYYYMMDD.txt
4. Rebuild Docker após mudanças de backend
5. Testes existentes não podem regredir (1066 backend, 116 frontend)

## Critério de sucesso final
- [ ] Todos os itens PNCP com categoria preenchida  
- [ ] Endpoint /historico funcionando  
- [ ] Campo tipo_preco presente na API e no frontend  
- [ ] Componente de comparação funcionando  
- [ ] Banco populado com dados reais GO 2025+2026  
