/**
 * Testes de componentes React — Semana 15.
 * Cobre: IndicadorIPCA, TabelaPrecos (toggle corrigido).
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import { IndicadorIPCA } from "../components/IndicadorIPCA";
import { TabelaPrecos } from "../components/TabelaPrecos";
import type { ListarPrecosResponse } from "../api/analise";
import type { SerieIPCAResponse } from "../api/correcao";

// Mock de dados IPCA
const dadosIPCAMock: SerieIPCAResponse = {
  indice: "IPCA",
  periodo: { ano_inicio: 2025, ano_fim: 2026 },
  total_meses: 12,
  dados: [
    { ano: 2025, mes: 4, variacao_mensal: 0.43, variacao_acumulada_ano: 2.48, indice_acumulado: 140.5 },
    { ano: 2025, mes: 5, variacao_mensal: 0.36, variacao_acumulada_ano: 2.85, indice_acumulado: 141.0 },
    { ano: 2025, mes: 6, variacao_mensal: 0.22, variacao_acumulada_ano: 3.08, indice_acumulado: 141.3 },
    { ano: 2025, mes: 7, variacao_mensal: 0.30, variacao_acumulada_ano: 3.39, indice_acumulado: 141.7 },
    { ano: 2025, mes: 8, variacao_mensal: 0.28, variacao_acumulada_ano: 3.68, indice_acumulado: 142.1 },
    { ano: 2025, mes: 9, variacao_mensal: 0.35, variacao_acumulada_ano: 4.04, indice_acumulado: 142.6 },
    { ano: 2025, mes: 10, variacao_mensal: 0.42, variacao_acumulada_ano: 4.48, indice_acumulado: 143.2 },
    { ano: 2025, mes: 11, variacao_mensal: 0.38, variacao_acumulada_ano: 4.88, indice_acumulado: 143.7 },
    { ano: 2025, mes: 12, variacao_mensal: 0.48, variacao_acumulada_ano: 5.38, indice_acumulado: 144.4 },
    { ano: 2026, mes: 1, variacao_mensal: 0.39, variacao_acumulada_ano: 0.39, indice_acumulado: 145.0 },
    { ano: 2026, mes: 2, variacao_mensal: 0.72, variacao_acumulada_ano: 1.11, indice_acumulado: 146.0 },
    { ano: 2026, mes: 3, variacao_mensal: 0.45, variacao_acumulada_ano: 1.57, indice_acumulado: 146.7 },
  ],
};

// Mock de dados de preços
const precosMock: ListarPrecosResponse = {
  itens: [
    {
      id: 1,
      uf: "SP",
      categoria: "Papel A4",
      descricao: "Resma 500fls",
      preco_unitario: 24.5,
      unidade: "resma",
      data_referencia: "2025-01-01",
      orgao: "Prefeitura SP",
      confianca: "ALTA",
    },
  ],
  total: 1,
  pagina: 1,
  por_pagina: 20,
  total_paginas: 1,
  filtros_aplicados: {},
};

// ---------------------------------------------------------------------------
// IndicadorIPCA
// ---------------------------------------------------------------------------
describe("IndicadorIPCA", () => {
  it("renderiza com dados mock", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByTestId("indicador-ipca")).toBeInTheDocument();
  });

  it("mostra acumulado 12 meses", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByTestId("ipca-acumulado")).toBeInTheDocument();
    const texto = screen.getByTestId("ipca-acumulado").textContent ?? "";
    // Deve conter um número com %
    expect(texto).toMatch(/\d+\.\d+%/);
  });

  it("mostra variação do último mês", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByTestId("ipca-ultimo-mes")).toBeInTheDocument();
  });

  it("mostra barras de variação", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByTestId("ipca-barras")).toBeInTheDocument();
  });

  it("mostra título IPCA", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByText("IPCA — Inflação")).toBeInTheDocument();
  });

  it("mostra texto acumulado 12 meses", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByText("acumulado 12 meses")).toBeInTheDocument();
  });

  it("mostra estado de carregamento", () => {
    render(<IndicadorIPCA dadosMock={undefined} />);
    // Quando dadosMock é undefined, o componente tenta buscar da API
    // e mostra loading state
    expect(screen.getByTestId("ipca-carregando")).toBeInTheDocument();
  });

  it("mostra erro quando dados são null", () => {
    render(<IndicadorIPCA dadosMock={null} />);
    // null dados: variação 0.00%
    expect(screen.getByTestId("indicador-ipca")).toBeInTheDocument();
  });

  it("barras tem 12 filhos para 12 meses", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    const barras = screen.getByTestId("ipca-barras");
    expect(barras.children.length).toBe(12);
  });

  it("último mês mostra +0.45%", () => {
    render(<IndicadorIPCA dadosMock={dadosIPCAMock} />);
    expect(screen.getByTestId("ipca-ultimo-mes").textContent).toContain("0.45");
  });
});

// ---------------------------------------------------------------------------
// TabelaPrecos — toggle corrigido
// ---------------------------------------------------------------------------
describe("TabelaPrecos toggle corrigido", () => {
  it("não mostra toggle sem callback", () => {
    render(<TabelaPrecos dados={precosMock} />);
    expect(screen.queryByTestId("toggle-corrigido")).toBeNull();
  });

  it("mostra toggle com callback", () => {
    render(<TabelaPrecos dados={precosMock} onToggleCorrigido={() => {}} />);
    expect(screen.getByTestId("toggle-corrigido")).toBeInTheDocument();
  });

  it("toggle mostra 'Nominal' por padrão", () => {
    render(<TabelaPrecos dados={precosMock} onToggleCorrigido={() => {}} />);
    expect(screen.getByTestId("toggle-corrigido").textContent).toBe("Nominal");
  });

  it("toggle mostra 'Corrigido IPCA' quando ativo", () => {
    render(
      <TabelaPrecos
        dados={precosMock}
        mostrarCorrigido={true}
        onToggleCorrigido={() => {}}
      />
    );
    expect(screen.getByTestId("toggle-corrigido").textContent).toBe("Corrigido IPCA");
  });

  it("chama onToggleCorrigido ao clicar", () => {
    const fn = vi.fn();
    render(<TabelaPrecos dados={precosMock} onToggleCorrigido={fn} />);
    fireEvent.click(screen.getByTestId("toggle-corrigido"));
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("não mostra coluna corrigido por padrão", () => {
    render(<TabelaPrecos dados={precosMock} />);
    expect(screen.queryByText("Corrigido Hoje")).toBeNull();
  });

  it("mostra coluna corrigido quando ativado", () => {
    render(
      <TabelaPrecos
        dados={precosMock}
        mostrarCorrigido={true}
        onToggleCorrigido={() => {}}
      />
    );
    expect(screen.getByText("Corrigido Hoje")).toBeInTheDocument();
  });
});
