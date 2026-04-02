# Gaps Jurídicos e Técnicos — Banco de Preços

Lista de lacunas identificadas, ordenadas por criticidade (Alta → Baixa).

## Criticidade Alta

1. **Ausência de assinatura digital em relatórios PDF** — A IN 65/2021 recomenda que pesquisas de preços tenham validade documental. Relatórios gerados pelo sistema não possuem assinatura digital ICP-Brasil, o que pode comprometer a aceitação em processos formais de licitação.

2. **SECRET_KEY hardcoded no código-fonte** — A chave de assinatura JWT está fixa no código (`bdp_secret_2026_dev`). Em ambiente de produção, isso representa risco de segurança crítico. Deve ser migrada para variável de ambiente ou serviço de gerenciamento de segredos (ex: AWS Secrets Manager, HashiCorp Vault).

3. **Ausência de criptografia de dados sensíveis em repouso** — Senhas são armazenadas com SHA-256 + salt fixo, que não é considerado seguro para produção. Recomenda-se migrar para bcrypt ou argon2. Dados de tenants e usuários não possuem criptografia em repouso no banco de dados.

4. **LGPD — Tratamento de dados pessoais** — O sistema armazena e-mails e nomes de usuários sem política formal de tratamento de dados pessoais, consentimento explícito ou mecanismo de exclusão (direito ao esquecimento).

## Criticidade Média

5. **Falta de rastreabilidade completa da pesquisa de preços** — A IN 65/2021 (Art. 5º) exige rastreabilidade da pesquisa. Embora o sistema registre fontes, não há link permanente para o documento original da contratação no PNCP, que pode ser removido ou alterado.

6. **Ausência de validação de CNPJ/CPF** — Órgãos e tenants não possuem validação de CNPJ. Dados inválidos podem comprometer a confiabilidade dos relatórios e a conformidade com exigências legais.

7. **Rate limiting sem persistência** — O rate limiter usa armazenamento in-memory. Em caso de restart do serviço, todos os contadores são zerados, permitindo burst de requisições. Deve ser migrado para Redis ou equivalente.

8. **Ausência de multi-fator de autenticação (MFA)** — Para usuários com papel 'admin', não há exigência de segundo fator de autenticação, contrariando boas práticas de segurança para sistemas governamentais.

## Criticidade Baixa

9. **Cobertura geográfica limitada** — Apenas 10 UFs possuem municípios prioritários cadastrados. Para atender à demanda nacional, é necessário expandir para todas as 27 UFs, com priorização por volume de licitações.

10. **Classificação de itens por regex** — A classificação de itens utiliza regras regex estáticas, que não cobrem a totalidade dos itens CATMAT/CATSER. Itens fora das 50 categorias prioritárias não são classificados automaticamente.

11. **Ausência de versionamento semântico na API** — Embora os endpoints usem prefixo `/api/v1/`, não há mecanismo formal de deprecação ou suporte a múltiplas versões simultâneas da API.

12. **Documentação de API incompleta** — Os schemas OpenAPI gerados automaticamente pelo FastAPI não possuem exemplos de request/response para todos os endpoints, dificultando a integração por consumidores externos.

13. **Ausência de testes de carga** — Não há testes de performance ou stress test documentados. Para produção, é necessário validar que o sistema suporta a carga esperada de consultas simultâneas por tenant.
