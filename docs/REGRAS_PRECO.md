# Regras de Preco

## Objetivo

Padronizar o uso dos campos de preco para evitar perda de historico e mistura de fontes no calculo referencial.

## Campos

### `valor_estimado`
- Representa o preco originalmente divulgado na fase de estimativa da contratacao.
- Deve ser preservado mesmo quando existir resultado homologado.
- Pode ser preenchido pela coleta inicial ou recuperado depois pela API de itens do PNCP.

### `valor_homologado`
- Representa o preco adjudicado ou homologado no resultado da compra.
- So deve ser preenchido quando houver evidencia de resultado no PNCP.
- Nao substitui nem apaga `valor_estimado`.

### `valor_unitario`
- Campo operacional usado nas consultas e listagens correntes.
- Regra: usar `valor_homologado` quando disponivel; caso contrario usar `valor_estimado`.
- Em ingestao e atualizacao, ele funciona como o melhor preco conhecido do item naquele momento.

### `tipo_preco`
- `estimado`: item ainda sem resultado homologado confirmado.
- `homologado`: item com `valor_homologado` valido.
- O tipo precisa refletir a origem do valor atualmente exposto em `valor_unitario`.

## Regras operacionais

1. Nunca sobrescrever `valor_estimado` com `valor_homologado`.
2. Ao encontrar homologacao valida, atualizar `valor_homologado`, atualizar `valor_unitario` e marcar `tipo_preco = homologado`.
3. Se so existir estimativa valida, manter `valor_unitario = valor_estimado` e `tipo_preco = estimado`.
4. Calculos referenciais futuros devem respeitar tambem `tipo_objeto` para evitar mistura entre material, servico e obra.

## Proximos passos vinculados

- Criar migration de `tipo_objeto`.
- Aplicar filtro por `tipo_objeto` nas consultas referenciais.
- Cobrir as regras acima com testes de regressao no backend e nos scripts de ingestao.
