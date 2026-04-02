/**
 * Testes de componentes React — Semana 16.
 * Cobre: BuscaSemantica, AlertaSobrepreco.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import { BuscaSemantica } from "../components/BuscaSemantica";
import { AlertaSobrepreco } from "../components/AlertaSobrepreco";
import type { StatusAlerta } from "../components/AlertaSobrepreco";

// ---------------------------------------------------------------------------
// BuscaSemantica
// ---------------------------------------------------------------------------
describe("BuscaSemantica", () => {
  const mockResultados = [
    { id: 1, descricao: "Papel A4 resma", categoria: "Papel A4", score_combinado: 0.95 },
    { id: 2, descricao: "Caneta azul", categoria: "Caneta", score_combinado: 0.45 },
  ];

  it("renderiza com testid", () => {
    render(<BuscaSemantica resultadosMock={[]} />);
    expect(screen.getByTestId("busca-semantica")).toBeInTheDocument();
  });

  it("renderiza input de busca", () => {
    render(<BuscaSemantica resultadosMock={[]} />);
    expect(screen.getByTestId("busca-input")).toBeInTheDocument();
  });

  it("mostra resultados quando há dados", () => {
    render(<BuscaSemantica resultadosMock={mockResultados} />);
    expect(screen.getByTestId("busca-resultados")).toBeInTheDocument();
  });

  it("não mostra resultados quando vazio", () => {
    render(<BuscaSemantica resultadosMock={[]} />);
    expect(screen.queryByTestId("busca-resultados")).toBeNull();
  });

  it("mostra descrição dos resultados", () => {
    render(<BuscaSemantica resultadosMock={mockResultados} />);
    expect(screen.getByText("Papel A4 resma")).toBeInTheDocument();
  });

  it("mostra score em porcentagem", () => {
    render(<BuscaSemantica resultadosMock={mockResultados} />);
    expect(screen.getByText("95%")).toBeInTheDocument();
  });

  it("chama onSelecionar ao clicar item", () => {
    const fn = vi.fn();
    render(<BuscaSemantica resultadosMock={mockResultados} onSelecionar={fn} />);
    fireEvent.click(screen.getByTestId("busca-item-0"));
    expect(fn).toHaveBeenCalledTimes(1);
    expect(fn).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
  });

  it("tem placeholder no input", () => {
    render(<BuscaSemantica resultadosMock={[]} />);
    expect(screen.getByPlaceholderText("Buscar item ou serviço...")).toBeInTheDocument();
  });

  it("mostra categoria no resultado", () => {
    render(<BuscaSemantica resultadosMock={mockResultados} />);
    expect(screen.getByText("Papel A4")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AlertaSobrepreco
// ---------------------------------------------------------------------------
describe("AlertaSobrepreco", () => {
  it("renderiza badge com testid", () => {
    render(<AlertaSobrepreco status="NORMAL" />);
    expect(screen.getByTestId("alerta-badge")).toBeInTheDocument();
  });

  it("mostra label Normal", () => {
    render(<AlertaSobrepreco status="NORMAL" />);
    expect(screen.getByText("Normal")).toBeInTheDocument();
  });

  it("mostra label Atenção", () => {
    render(<AlertaSobrepreco status="ATENCAO" />);
    expect(screen.getByText("Atenção")).toBeInTheDocument();
  });

  it("mostra label Crítico", () => {
    render(<AlertaSobrepreco status="CRITICO" />);
    expect(screen.getByText("Crítico")).toBeInTheDocument();
  });

  it("mostra label sem referência", () => {
    render(<AlertaSobrepreco status="SEM_REFERENCIA" />);
    expect(screen.getByText("S/ ref.")).toBeInTheDocument();
  });

  it("tem data-status correto", () => {
    render(<AlertaSobrepreco status="CRITICO" />);
    expect(screen.getByTestId("alerta-badge")).toHaveAttribute("data-status", "CRITICO");
  });

  it("mostra desvio quando ativado", () => {
    render(<AlertaSobrepreco status="ATENCAO" desvio={35.2} mostrarDesvio />);
    expect(screen.getByTestId("alerta-desvio")).toBeInTheDocument();
    expect(screen.getByTestId("alerta-desvio").textContent).toContain("35.2");
  });

  it("não mostra desvio por padrão", () => {
    render(<AlertaSobrepreco status="NORMAL" desvio={5} />);
    expect(screen.queryByTestId("alerta-desvio")).toBeNull();
  });

  it("desvio negativo mostra sem sinal +", () => {
    render(<AlertaSobrepreco status="NORMAL" desvio={-10.5} mostrarDesvio />);
    expect(screen.getByTestId("alerta-desvio").textContent).toContain("-10.5");
  });

  it("desvio positivo mostra com +", () => {
    render(<AlertaSobrepreco status="ATENCAO" desvio={25.0} mostrarDesvio />);
    expect(screen.getByTestId("alerta-desvio").textContent).toContain("+25.0");
  });
});
