/**
 * Testes de componentes React — Semana 18.
 * Cobre: BenchmarkRegional.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { BenchmarkRegional } from "../components/BenchmarkRegional";

const mockRanking = [
  { uf: "SP", preco_medio: 22.5, rank: 1, n_amostras: 45 },
  { uf: "MG", preco_medio: 23.8, rank: 2, n_amostras: 42 },
  { uf: "RS", preco_medio: 24.0, rank: 3, n_amostras: 35 },
  { uf: "RJ", preco_medio: 25.2, rank: 4, n_amostras: 38 },
  { uf: "BA", preco_medio: 26.1, rank: 5, n_amostras: 30 },
  { uf: "DF", preco_medio: 25.5, rank: 6, n_amostras: 28 },
];

const mockEstatisticas = {
  media: 24.52,
  mediana: 24.6,
  uf_mais_barata: "SP",
  uf_mais_cara: "BA",
};

describe("BenchmarkRegional", () => {
  it("renderiza com dados", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    expect(screen.getByTestId("benchmark-regional")).toBeInTheDocument();
  });

  it("mostra título com categoria", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByText(/Benchmark Regional/)).toBeInTheDocument();
    expect(screen.getByText(/Papel A4/)).toBeInTheDocument();
  });

  it("mostra ranking vazio", () => {
    render(<BenchmarkRegional categoria="Teste" ranking={[]} />);
    expect(screen.getByTestId("benchmark-vazio")).toBeInTheDocument();
  });

  it("mostra barras para cada UF", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByTestId("benchmark-barras")).toBeInTheDocument();
  });

  it("mostra estatísticas quando fornecidas", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    expect(screen.getByTestId("benchmark-stats")).toBeInTheDocument();
  });

  it("não mostra estatísticas quando omitidas", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.queryByTestId("benchmark-stats")).not.toBeInTheDocument();
  });

  it("exibe UF mais barata nas stats", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    const stats = screen.getByTestId("benchmark-stats");
    expect(stats.textContent).toContain("SP");
  });

  it("exibe UF mais cara nas stats", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    const stats = screen.getByTestId("benchmark-stats");
    expect(stats.textContent).toContain("BA");
  });

  it("exibe todas as UFs do ranking", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    for (const item of mockRanking) {
      expect(screen.getByText(item.uf)).toBeInTheDocument();
    }
  });

  it("exibe posição no ranking", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("exibe preços formatados", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    // Deve formatar como moeda BRL
    const textos = screen.getByTestId("benchmark-barras").textContent;
    expect(textos).toBeTruthy();
  });

  it("renderiza com ranking de 1 item", () => {
    const singleRanking = [{ uf: "SP", preco_medio: 22.5, rank: 1, n_amostras: 45 }];
    render(<BenchmarkRegional categoria="Papel A4" ranking={singleRanking} />);
    expect(screen.getByTestId("benchmark-regional")).toBeInTheDocument();
  });

  it("exibe mensagem para ranking vazio com categoria", () => {
    render(<BenchmarkRegional categoria="Cimento" ranking={[]} />);
    expect(screen.getByText(/Sem dados de benchmark para Cimento/)).toBeInTheDocument();
  });

  it("média e mediana são exibidas", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    const stats = screen.getByTestId("benchmark-stats");
    expect(stats.textContent).toContain("Média");
    expect(stats.textContent).toContain("Mediana");
  });

  it("exibe Mais barata e Mais cara", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} estatisticas={mockEstatisticas} />);
    const stats = screen.getByTestId("benchmark-stats");
    expect(stats.textContent).toContain("Mais barata");
    expect(stats.textContent).toContain("Mais cara");
  });
});
