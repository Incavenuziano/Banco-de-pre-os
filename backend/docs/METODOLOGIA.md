# Metodologia de Cálculo de Preço Referencial

## Visão Geral

O Banco de Preços utiliza uma metodologia estatística robusta para o cálculo de preços referenciais em licitações municipais, em conformidade com a Instrução Normativa nº 65/2021 e a Lei nº 14.133/2021 (Nova Lei de Licitações).

## Fontes de Dados

As amostras de preços são coletadas de múltiplas fontes oficiais:

- **PNCP (Portal Nacional de Contratações Públicas):** Principal fonte de dados, com preços praticados em contratações públicas de todo o Brasil.
- **Compras.gov.br:** Portal de Compras do Governo Federal, com dados complementares de pregões e atas de registro de preços.
- **Atas de Registro de Preços:** Preços vigentes em atas de registro de preços de órgãos públicos.

## Tratamento de Dados

### Normalização

Antes do cálculo estatístico, os dados passam por etapas de normalização:

1. **Limpeza textual:** Remoção de caracteres especiais, padronização de espaços e conversão para maiúsculas.
2. **Normalização de unidades:** Conversão para unidades padrão (UN, KG, L, M, M², M³, etc.) com mapeamento de mais de 100 variações.
3. **Classificação por categoria:** Agrupamento por categoria de material usando regras regex e correspondência textual.

### Detecção de Outliers

A detecção de outliers é realizada por três métodos, sendo o IQR o padrão:

- **Método IQR (Interquartil):** Outlier se preço < Q1 - 1.5×IQR ou preço > Q3 + 1.5×IQR. Recomendado para amostras com alta dispersão (CV > 0.5).
- **Método Percentil:** Outlier se preço < percentil 5 ou preço > percentil 95. Adequado para distribuições com baixa variação (CV < 0.3).
- **Método Desvio Padrão:** Outlier se |preço - média| > 2 × desvio padrão. Utilizado em amostras pequenas (n < 5).

O método é selecionado automaticamente com base no coeficiente de variação da amostra.

## Cálculo do Preço Referencial

O preço referencial é calculado como a **mediana** das amostras válidas (após exclusão de outliers). A escolha da mediana (em vez da média) se dá por sua maior robustez a valores extremos, conforme recomendação da IN 65/2021.

## Score de Confiança

Cada preço referencial recebe um nível de confiança:

| Nível         | Critério                                      |
|---------------|-----------------------------------------------|
| ALTA          | n ≥ 10 amostras e CV < 0.3                    |
| MEDIA         | n ≥ 5 amostras                                |
| BAIXA         | n ≥ 2 amostras                                |
| INSUFICIENTE  | n < 2 amostras                                |

O coeficiente de variação (CV) indica a dispersão relativa dos preços. Quanto menor o CV, mais homogênea é a amostra e maior a confiabilidade do preço referencial.

## Alertas de Sobrepreço

O sistema gera alertas automáticos comparando o preço proposto com a mediana de referência:

- **CRÍTICO:** Preço proposto > 150% da mediana
- **ATENÇÃO:** Preço proposto entre 120% e 150% da mediana
- **OK:** Preço proposto ≤ 120% da mediana

## Limitações Conhecidas

- Amostras com menos de 3 itens são consideradas insuficientes para relatórios formais.
- A classificação por categoria depende de regras regex, podendo haver itens não classificados.
- Preços de serviços têm maior variabilidade regional que materiais de consumo.
