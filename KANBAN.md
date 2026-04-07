# Kanban ? Banco de Precos

## Todo

- [ ] P0 Formalizar regra de negocio de precos
  - Definir `valor_estimado`, `valor_homologado`, `valor_unitario` e `tipo_preco`
  - Alinhar regra com backend, scripts e relatorios

- [x] P0 Criar migration de `tipo_objeto`
  - Separar `material`, `servico` e `obra`
  - Prever default para legado e backfill inicial

- [x] P0 Aplicar `tipo_objeto` no calculo referencial
  - Impedir mistura de objetos incompatveis
  - Atualizar consultas de mediana, dispersao e comparativos

- [x] P0 Garantir preservacao de `valor_estimado`
  - Proteger historico da fase de estimativa
  - Cobrir com testes de regressao

- [ ] P1 Atualizar setup real no README
  - Refletir fluxo que funciona no WSL
  - Documentar subida local de banco, backend e frontend

- [ ] P1 Corrigir execucao do frontend no WSL
  - Fazer `npm run dev` e `npm test` funcionarem sem problema de UNC

- [ ] P1 Criar comando unico de subida local
  - Reduzir atrito para boot local do projeto

- [ ] P1 Criar relatorio de qualidade por UF
  - Medir cobertura, homologados, categorias e erros

- [ ] P1 Consolidar GO como baseline confiavel
  - Fechar ingestao, atualizacao homologada e checagens

- [ ] P1 Escolher 2 a 4 UFs prioritarias
  - Expandir cobertura com foco e volume

- [ ] P1 Melhorar classificador atual
  - Atacar categorias de maior frequencia
  - Reduzir itens sem categoria

- [ ] P1 Criar batch de recategorizacao
  - Reprocessar base existente com log resumido

- [ ] P1 Validar busca com termos reais
  - Medir utilidade pratica da busca textual

- [ ] P2 Simplificar tela principal
  - Busca, mediana, dispersao, confianca e link PNCP

- [ ] P2 Melhorar exportacoes
  - Tornar PDF e planilhas mais uteis ao processo administrativo

- [ ] P2 Criar checklist de piloto
  - Separar bloqueadores de itens desejaveis

- [ ] P2 Adicionar observabilidade do pipeline
  - Registrar volume, tempo e falhas por rotina

## Doing

- [x] P0 Versionar e estabilizar `scripts/atualizar_precos_homologados.py`
  - Padronizar parsing numerico e contadores de execucao
  - Garantir preservacao de `valor_estimado`

- [x] P0 Auditar integracao PNCP
  - Remover qualquer uso antigo de `/resultado`
  - Validar consistencia com `/resultados`

- [x] P0 Link PNCP no comparativo
  - Validar geracao de URL e consumo no frontend

## Done

- [x] Diagnostico tecnico consolidado em `docs/ANALISE-ESTADO-ATUAL.md`
- [x] Logs recentes confirmam ingestao e atualizacao de dados em abril de 2026
- [x] Backend com suite ampla de testes coletavel localmente
- [x] Primeira especificacao operacional de regras de preco criada em `docs/REGRAS_PRECO.md`

- [x] Primeira entrega de `tipo_objeto` aplicada no schema, ingestao e consultas principais
