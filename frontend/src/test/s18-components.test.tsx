/**
 * Testes de componentes React — Semana 18.
 * Cobre: BenchmarkRegional.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { BenchmarkRegional } from "../components/BenchmarkRegional";

const mockRanking = [
  { uf: "SC", preco_medio: 23.5, rank: 1, n_amostras: 35 },
  { uf: "MG", preco_medio: 23.8, rank: 2, n_amostras: 42 },
  { uf: "RS", preco_medio: 24.0, rank: 3, n_amostras: 35 },
  { uf: "SP", preco_medio: 24.5, rank: 4, n_amostras: 45 },
  { uf: "RJ", preco_medio: 25.2, rank: 5, n_amostras: 38 },
];

const mockStats = {
  media: 24.2,
  mediana: 24.0,
  uf_mais_barata: "SC",
  uf_mais_cara: "RJ",
};

describe("BenchmarkRegional", () => {
  it("renderiza com testid", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByTestId("benchmark-regional")).toBeInTheDocument();
  });

  it("mostra título com categoria", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByText(/Benchmark Regional.*Papel A4/)).toBeInTheDocument();
  });

  it("mostra barras de ranking", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByTestId("benchmark-barras")).toBeInTheDocument();
  });

  it("mostra todas as UFs", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.getByText("SC")).toBeInTheDocument();
    expect(screen.getByText("RJ")).toBeInTheDocument();
    expect(screen.getByText("SP")).toBeInTheDocument();
  });

  it("mostra ranks", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    const barras = screen.getByTestId("benchmark-barras");
    expect(barras.children.length).toBe(5);
  });

  it("mostra estatísticas quando fornecidas", () => {
    render(
      <BenchmarkRegional
        categoria="Papel A4"
        ranking={mockRanking}
        estatisticas={mockStats}
      />
    );
    expect(screen.getByTestId("benchmark-stats")).toBeInTheDocument();
  });

  it("mostra uf mais barata nas stats", () => {
    render(
      <BenchmarkRegional
        categoria="Papel A4"
        ranking={mockRanking}
        estatisticas={mockStats}
      />
    );
    expect(screen.getByText(/Mais barata: SC/)).toBeInTheDocument();
  });

  it("mostra uf mais cara nas stats", () => {
    render(
      <BenchmarkRegional
        categoria="Papel A4"
        ranking={mockRanking}
        estatisticas={mockStats}
      />
    );
    expect(screen.getByText(/Mais cara: RJ/)).toBeInTheDocument();
  });

  it("mostra vazio quando sem ranking", () => {
    render(<BenchmarkRegional categoria="Nenhuma" ranking={[]} />);
    expect(screen.getByTestId("benchmark-vazio")).toBeInTheDocument();
  });

  it("não mostra stats quando não fornecidas", () => {
    render(<BenchmarkRegional categoria="Papel A4" ranking={mockRanking} />);
    expect(screen.queryByTestId("benchmark-stats")).toBeNull();
  });
});
