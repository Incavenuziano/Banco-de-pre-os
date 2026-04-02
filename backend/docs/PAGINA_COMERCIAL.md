# Página Comercial — Planos e Assinatura

Sugestão de conteúdo JSX/HTML para a página de planos do Banco de Preços.

## Tabela Comparativa de Planos

```jsx
export default function PaginaPlanos() {
  const planos = [
    {
      id: "free",
      nome: "Free",
      preco: "R$ 0",
      periodo: "/mês",
      destaque: false,
      recursos: [
        "10 consultas/mês",
        "2 relatórios/mês",
        "Cobertura: DF",
        "Sem suporte dedicado",
      ],
      cta: "Começar grátis",
    },
    {
      id: "basico",
      nome: "Básico",
      preco: "R$ 197",
      periodo: "/mês",
      destaque: false,
      recursos: [
        "100 consultas/mês",
        "20 relatórios/mês",
        "Cobertura: DF, GO, SP, MG, BA",
        "Sem suporte dedicado",
      ],
      cta: "Assinar Básico",
    },
    {
      id: "profissional",
      nome: "Profissional",
      preco: "R$ 497",
      periodo: "/mês",
      destaque: true,
      recursos: [
        "500 consultas/mês",
        "100 relatórios/mês",
        "Cobertura: todas as UFs",
        "Suporte dedicado",
      ],
      cta: "Assinar Profissional",
    },
    {
      id: "enterprise",
      nome: "Enterprise",
      preco: "R$ 1.497",
      periodo: "/mês",
      destaque: false,
      recursos: [
        "Consultas ilimitadas",
        "Relatórios ilimitados",
        "Cobertura: todas as UFs",
        "Suporte dedicado + SLA",
      ],
      cta: "Falar com comercial",
    },
  ];

  return (
    <section className="py-16 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-center mb-4">
          Planos e Preços
        </h2>
        <p className="text-center text-gray-600 mb-12">
          Pesquisa de preços para licitações com rastreabilidade e conformidade.
          Pague anual e ganhe 2 meses grátis.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {planos.map((plano) => (
            <div
              key={plano.id}
              className={`rounded-2xl p-6 shadow-md ${
                plano.destaque
                  ? "border-2 border-blue-600 bg-white"
                  : "bg-white"
              }`}
            >
              {plano.destaque && (
                <span className="text-xs font-semibold text-blue-600 uppercase">
                  Mais popular
                </span>
              )}
              <h3 className="text-xl font-semibold mt-2">{plano.nome}</h3>
              <p className="text-3xl font-bold mt-4">
                {plano.preco}
                <span className="text-base font-normal text-gray-500">
                  {plano.periodo}
                </span>
              </p>

              <ul className="mt-6 space-y-3">
                {plano.recursos.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-green-500 mt-0.5">✓</span>
                    {r}
                  </li>
                ))}
              </ul>

              <button
                className={`mt-8 w-full py-2 rounded-lg font-medium ${
                  plano.destaque
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-gray-100 text-gray-800 hover:bg-gray-200"
                }`}
              >
                {plano.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-500 mt-8">
          Enterprise: entre em contato pelo e-mail comercial@araticum.com.br
        </p>
      </div>
    </section>
  );
}
```

## Notas de implementação

- Os preços estão alinhados com `billing_service.py` (free/básico/profissional/enterprise).
- O desconto anual (paga 10, ganha 12) está mencionado no subtítulo.
- O CTA do Enterprise direciona para contato comercial.
- Usar Tailwind CSS para estilização (padrão Next.js do projeto).
