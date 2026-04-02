# Playbook Operacional — Banco de Preços

## Rotinas Diárias

### Monitoramento de Saúde do Sistema

1. **Verificar endpoint /health** — Confirmar que o status retorna "ok" e que banco e storage estão conectados.
2. **Consultar /metrics** — Avaliar volume de consultas, relatórios gerados e taxa de erros nas últimas 24 horas.
3. **Verificar logs de auditoria** — Acessar GET /api/v1/admin/auditoria para identificar ações incomuns ou tentativas de acesso não autorizado.
4. **Validar rate limiter** — Confirmar que nenhum tenant está sendo bloqueado indevidamente.

### Coleta de Dados

1. Verificar status da coleta do PNCP — pipeline de integração deve executar diariamente.
2. Conferir novas amostras por UF — acessar cobertura/indice para verificar evolução.
3. Validar qualidade das amostras — verificar percentual de outliers e coeficiente de variação.

## Alertas Críticos

### Sobrepreço Detectado (Nível CRÍTICO)

- **Ação imediata:** Notificar gestor do órgão comprador.
- **Evidências:** Coletar relatório de alertas com estatísticas de referência.
- **Prazo:** Resolver em até 48 horas úteis.
- **Escalação:** Se não resolvido, escalar para o comitê de governança.

### Banco de Dados Indisponível

- **Ação imediata:** Verificar conexão PostgreSQL e status do container Docker.
- **Comando:** `docker ps` para verificar se o container está rodando.
- **Fallback:** Sistema opera em modo degradado com dados em cache.
- **Escalação:** Equipe de infraestrutura em até 15 minutos.

### Taxa de Erros Acima de 5%

- **Ação:** Analisar /metrics para identificar endpoints com maior taxa de erro.
- **Diagnóstico:** Verificar logs de aplicação e auditoria.
- **Correção:** Aplicar hotfix se necessário, com deploy em staging antes de produção.

## Troubleshooting Comum

### API retornando 500

1. Verificar logs do uvicorn/gunicorn.
2. Confirmar que o banco está acessível via `pg_isready`.
3. Verificar se há migrações pendentes com `alembic current`.

### Consulta retornando poucos resultados

1. Verificar índice de cobertura da UF em questão.
2. Confirmar que a categoria está mapeada no classificador regex.
3. Ampliar período de busca ou expandir UFs consultadas.

### Token JWT inválido

1. Verificar se o token não está expirado (8h de validade).
2. Confirmar que a SECRET_KEY é a mesma em todos os serviços.
3. Solicitar novo token via POST /api/v1/auth/login.

### Rate Limiter bloqueando requisições legítimas

1. Verificar status via GET /api/v1/admin/rate-limit/status?key=<chave>.
2. Se necessário, resetar o contador via administração.
3. Considerar ajuste do limite para o plano do tenant.

## Backup e Recuperação

### Backup do Banco de Dados

- **Frequência:** Backup completo diário, incremental a cada 6 horas.
- **Comando:** `pg_dump -Fc banco_precos > backup_$(date +%Y%m%d).dump`
- **Retenção:** 30 dias de backups diários, 12 meses de backups mensais.

### Restauração

1. Parar a aplicação: `docker compose stop app`
2. Restaurar: `pg_restore -d banco_precos backup_YYYYMMDD.dump`
3. Verificar migrações: `alembic current`
4. Reiniciar: `docker compose up -d app`
5. Validar: acessar /health e executar testes de fumaça.

### Dados de Auditoria

- Exportar periodicamente via GET /api/v1/admin/auditoria/export (CSV).
- Armazenar exports em storage externo (S3 ou equivalente).
- Auditoria é append-only — nunca deletar registros.
