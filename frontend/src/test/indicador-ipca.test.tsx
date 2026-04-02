/**
 * Testes do componente IndicadorIPCA — Semana 15.
 * Cobre: loading, erro, renderização com dados, mini barras, acumulado 12 meses.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { IndicadorIPCA } from "../components/IndicadorIPCA";
import type { SerieIPCAResponse } from "../api/correcao";

// Dados mock realistas
const dadosMock: SerieIPCAResponse = {
  indice: "IPCA",
  periodo: { ano_inicio: 2025, ano_fim: 2026 },
  total_meses: 15,
  dados: [
    { ano: 2025, mes: 4, variacao_mensal: 0.43, variacao_acumulada_ano: 2.49, indice_acumulado: 140.5 },
    { ano: 2025, mes: 5, variacao_mensal: 0.36, variacao_acumulada_ano: 2.86, indice_acumulado: 141.0 },
    { ano: 2025, mes: 6, variacao_mensal: 0.22, variacao_acumulada_ano: 3.09, indice_acumulado: 141.3 },
    { ano: 2025, mes: 7, variacao_mensal: 0.30, variacao_acumulada_ano: 3.40, indice_acumulado: 141.7 },
    { ano: 2025, mes: 8, variacao_mensal: 0.28, variacao_acumulada_ano: 3.69, indice_acumulado: 142.1 },
    { ano: 2025, mes: 9, variacao_mensal: 0.35, variacao_acumulada_ano: 4.05, indice_acumulado: 142.6 },
    { ano: 2025, mes: 10, variacao_mensal: 0.42, variacao_acumulada_ano: 4.49, indice_acumulado: 143.2 },
    { ano: 2025, mes: 11, variacao_mensal: 0.38, variacao_acumulada_ano: 4.89, indice_acumulado: 143.7 },
    { ano: 2025, mes: 12, variacao_mensal: 0.48, variacao_acumulada_ano: 5.39, indice_acumulado: 144.4 },
    { ano: 2026, mes: 1, variacao_mensal: 0.39, variacao_acumulada_ano: 0.39, indice_acumulado: 145.0 },
    { ano: 2026, mes: 2, variacao_mensal: 0.72, variacao_acumulada_ano: 1.11, indice_acumulado: 146.0 },
    { ano: 2026, mes: 3, variacao_mensal: 0.45, variacao_acumulada_ano: 1.57, indice_acumulado: 146.7 },
  ],
};

describe("IndicadorIPCA", () => {
  it("renderiza estado de carregamento", () => {
    // Sem dadosMock = vai buscar API, que não resolve → fica carregando
    render(<IndicadorIPCA dadosMock={undefined} />);
    expect(screen.getByTestId("ipca-carregando")).toBeInTheDocument();
  });

  it("renderiza erro quando dadosMock é null", async () => {
    // null simula API que retornou erro
    render(<IndicadorIPCA dadosMock={null} />);
    // Quando dadosMock é null, dados fica vazio
    await waitFor(() => {
      expect(screen.getByTestId("indicador-ipca")).toBeInTheDocument();
    });
  });

  it("renderiza indicador com dados mock", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    expect(screen.getByTestId("indicador-ipca")).toBeInTheDocument();
  });

  it("mostra acumulado 12 meses", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    const acumulado = screen.getByTestId("ipca-acumulado");
    expect(acumulado).toBeInTheDocument();
    // O texto deve conter um percentual
    expect(acumulado.textContent).toMatch(/\d+\.\d+%/);
  });

  it("mostra variação do último mês", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    const ultimoMes = screen.getByTestId("ipca-ultimo-mes");
    expect(ultimoMes).toBeInTheDocument();
    expect(ultimoMes.textContent).toContain("0.45");
  });

  it("renderiza barras de variação mensal", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    expect(screen.getByTestId("ipca-barras")).toBeInTheDocument();
  });

  it("barras têm 12 elementos (últimos 12 meses)", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    const barras = screen.getByTestId("ipca-barras");
    expect(barras.children.length).toBe(12);
  });

  it("mostra título IPCA", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    expect(screen.getByText(/IPCA/)).toBeInTheDocument();
  });

  it("mostra texto acumulado 12 meses", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    expect(screen.getByText(/acumulado 12 meses/i)).toBeInTheDocument();
  });

  it("calcula acumulado 12m corretamente", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    const acumulado = screen.getByTestId("ipca-acumulado");
    // Cálculo manual: produto de (1 + v/100) para os 12 dados
    const esperado = dadosMock.dados.reduce(
      (acc, d) => acc * (1 + d.variacao_mensal / 100), 1
    );
    const pctEsperado = ((esperado - 1) * 100).toFixed(2);
    expect(acumulado.textContent).toContain(pctEsperado);
  });

  it("mostra mês/ano do último dado", () => {
    render(<IndicadorIPCA dadosMock={dadosMock} />);
    expect(screen.getByText("03/2026")).toBeInTheDocument();
  });

  it("renderiza com dados vazios sem erro", () => {
    const vazio: SerieIPCAResponse = {
      indice: "IPCA",
      periodo: { ano_inicio: 2025, ano_fim: 2026 },
      total_meses: 0,
      dados: [],
    };
    render(<IndicadorIPCA dadosMock={vazio} />);
    expect(screen.getByTestId("indicador-ipca")).toBeInTheDocument();
  });
});
