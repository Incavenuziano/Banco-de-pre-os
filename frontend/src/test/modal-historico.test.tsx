/**
 * Testes — ModalHistoricoPrecos.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import { ModalHistoricoPrecos } from "../components/ModalHistoricoPrecos";

const mockHistorico = [
  {
    data: "2026-01-15",
    preco: 25.5,
    orgao: "Prefeitura de Florianópolis",
    municipio: "Florianópolis",
    uf: "SC",
    pncp_url: "https://pncp.gov.br/123",
    tipo_preco: "homologado",
  },
  {
    data: "2026-02-20",
    preco: 27.0,
    orgao: "Prefeitura de Joinville",
    municipio: "Joinville",
    uf: "SC",
    pncp_url: "",
    tipo_preco: "estimado",
  },
];

vi.mock("../api/analise", () => ({
  analiseAPI: {
    getHistoricoItem: vi.fn(),
  },
}));

// Mock Recharts to avoid canvas issues in tests
vi.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CartesianGrid: () => null,
}));

import { analiseAPI } from "../api/analise";

const mockOnFechar = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ModalHistoricoPrecos", () => {
  it("renderiza modal com a descrição no título", async () => {
    vi.mocked(analiseAPI.getHistoricoItem).mockResolvedValue({
      descricao: "Papel A4",
      total: 2,
      historico: mockHistorico,
    });

    render(
      <ModalHistoricoPrecos descricao="Papel A4" onFechar={mockOnFechar} />
    );

    expect(screen.getByTestId("modal-historico-titulo")).toHaveTextContent(
      "Histórico: Papel A4"
    );
  });

  it("exibe spinner enquanto carrega", () => {
    // Never-resolving promise to keep loading state
    vi.mocked(analiseAPI.getHistoricoItem).mockReturnValue(new Promise(() => {}));

    render(
      <ModalHistoricoPrecos descricao="Papel A4" onFechar={mockOnFechar} />
    );

    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("exibe tabela com dados após load", async () => {
    vi.mocked(analiseAPI.getHistoricoItem).mockResolvedValue({
      descricao: "Papel A4",
      total: 2,
      historico: mockHistorico,
    });

    render(
      <ModalHistoricoPrecos descricao="Papel A4" onFechar={mockOnFechar} />
    );

    await waitFor(() => {
      expect(screen.getByTestId("historico-tabela")).toBeInTheDocument();
    });

    expect(screen.getByText("15/01/2026")).toBeInTheDocument();
    expect(screen.getByText("20/02/2026")).toBeInTheDocument();
    expect(screen.getByText("Florianópolis")).toBeInTheDocument();
    expect(screen.getByText("Joinville")).toBeInTheDocument();
  });

  it("botão × chama onFechar", async () => {
    vi.mocked(analiseAPI.getHistoricoItem).mockResolvedValue({
      descricao: "Papel A4",
      total: 2,
      historico: mockHistorico,
    });

    render(
      <ModalHistoricoPrecos descricao="Papel A4" onFechar={mockOnFechar} />
    );

    fireEvent.click(screen.getByTestId("modal-historico-fechar"));
    expect(mockOnFechar).toHaveBeenCalledTimes(1);
  });

  it("clicar no backdrop chama onFechar", async () => {
    vi.mocked(analiseAPI.getHistoricoItem).mockResolvedValue({
      descricao: "Papel A4",
      total: 2,
      historico: mockHistorico,
    });

    render(
      <ModalHistoricoPrecos descricao="Papel A4" onFechar={mockOnFechar} />
    );

    fireEvent.click(screen.getByTestId("modal-historico-backdrop"));
    expect(mockOnFechar).toHaveBeenCalledTimes(1);
  });
});
