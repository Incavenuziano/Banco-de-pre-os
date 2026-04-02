/**
 * Testes de componentes React — Banco de Preços Semana 14.
 * Cobre: KPICard, TabelaPrecos, FiltrosAvancados, BotaoExportar,
 *        SeletorCategoria, LoadingSpinner, ErroAlerta, GraficoTendencias,
 *        GraficoComparativo.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import { KPICard } from "../components/KPICard";
import { TabelaPrecos } from "../components/TabelaPrecos";
import { FiltrosAvancados } from "../components/FiltrosAvancados";
import { BotaoExportar } from "../components/BotaoExportar";
import { SeletorCategoria } from "../components/SeletorCategoria";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErroAlerta } from "../components/ErroAlerta";
import { GraficoTendencias } from "../components/GraficoTendencias";
import { GraficoComparativo } from "../components/GraficoComparativo";
import type { ListarPrecosResponse, TendenciasResponse, ComparativoResponse } from "../api/analise";

// ---------------------------------------------------------------------------
// KPICard
// ---------------------------------------------------------------------------
describe("KPICard", () => {
  it("renderiza título e valor", () => {
    render(<KPICard titulo="Total" valor={123} />);
    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("123")).toBeInTheDocument();
  });

  it("renderiza subtítulo quando fornecido", () => {
    render(<KPICard titulo="UFs" valor="15/27" subtitulo="55.6% cobertura" />);
    expect(screen.getByText("55.6% cobertura")).toBeInTheDocument();
  });

  it("renderiza ícone quando fornecido", () => {
    render(<KPICard titulo="Registros" valor={500} icone="📋" />);
    expect(screen.getByText("📋")).toBeInTheDocument();
  });

  it("tem data-testid correto", () => {
    render(<KPICard titulo="X" valor="Y" />);
    expect(screen.getByTestId("kpi-card")).toBeInTheDocument();
  });

  it("aplica cor verde", () => {
    const { container } = render(<KPICard titulo="X" valor="Y" cor="verde" />);
    expect(container.firstChild).toHaveClass("border-l-green-500");
  });
});

// ---------------------------------------------------------------------------
// LoadingSpinner
// ---------------------------------------------------------------------------
describe("LoadingSpinner", () => {
  it("renderiza com testid", () => {
    render(<LoadingSpinner />);
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("renderiza mensagem quando fornecida", () => {
    render(<LoadingSpinner mensagem="Aguarde..." />);
    expect(screen.getByText("Aguarde...")).toBeInTheDocument();
  });

  it("tem role status para acessibilidade", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ErroAlerta
// ---------------------------------------------------------------------------
describe("ErroAlerta", () => {
  it("renderiza mensagem de erro", () => {
    render(<ErroAlerta mensagem="Erro de conexão" />);
    expect(screen.getByText("Erro de conexão")).toBeInTheDocument();
  });

  it("tem role alert para acessibilidade", () => {
    render(<ErroAlerta mensagem="Erro" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("chama onFechar ao clicar no botão de fechar", () => {
    const onFechar = vi.fn();
    render(<ErroAlerta mensagem="Erro" onFechar={onFechar} />);
    fireEvent.click(screen.getByRole("button", { name: /fechar/i }));
    expect(onFechar).toHaveBeenCalledOnce();
  });

  it("não renderiza botão quando onFechar não é fornecido", () => {
    render(<ErroAlerta mensagem="Erro" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// SeletorCategoria
// ---------------------------------------------------------------------------
describe("SeletorCategoria", () => {
  const cats = ["Papel A4", "Gasolina Comum", "Arroz"];

  it("renderiza todas as categorias como opções", () => {
    render(
      <SeletorCategoria
        categorias={cats}
        categoriaSelecionada="Papel A4"
        onChange={() => {}}
      />
    );
    cats.forEach((cat) => {
      expect(screen.getByRole("option", { name: cat })).toBeInTheDocument();
    });
  });

  it("chama onChange ao selecionar categoria", () => {
    const onChange = vi.fn();
    render(
      <SeletorCategoria
        categorias={cats}
        categoriaSelecionada="Papel A4"
        onChange={onChange}
      />
    );
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "Arroz" } });
    expect(onChange).toHaveBeenCalledWith("Arroz");
  });

  it("renderiza label personalizado", () => {
    render(
      <SeletorCategoria
        categorias={cats}
        categoriaSelecionada="Papel A4"
        onChange={() => {}}
        label="Escolha"
      />
    );
    expect(screen.getByText(/escolha/i)).toBeInTheDocument();
  });

  it("tem data-testid correto", () => {
    render(
      <SeletorCategoria categorias={cats} categoriaSelecionada="Arroz" onChange={() => {}} />
    );
    expect(screen.getByTestId("seletor-categoria")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// FiltrosAvancados
// ---------------------------------------------------------------------------
describe("FiltrosAvancados", () => {
  const categorias = ["Papel A4", "Gasolina Comum"];
  const ufs = ["SP", "RJ", "MG"];

  it("renderiza formulário com testid", () => {
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={() => {}} />
    );
    expect(screen.getByTestId("filtros-avancados")).toBeInTheDocument();
  });

  it("renderiza select de UF com opções", () => {
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={() => {}} />
    );
    expect(screen.getByLabelText("UF")).toBeInTheDocument();
    ufs.forEach((uf) => {
      expect(screen.getByRole("option", { name: uf })).toBeInTheDocument();
    });
  });

  it("renderiza select de categoria", () => {
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={() => {}} />
    );
    expect(screen.getByLabelText("Categoria")).toBeInTheDocument();
  });

  it("chama onFiltrar ao submeter", () => {
    const onFiltrar = vi.fn();
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={onFiltrar} />
    );
    fireEvent.click(screen.getByRole("button", { name: /filtrar/i }));
    expect(onFiltrar).toHaveBeenCalledOnce();
  });

  it("limpa filtros ao clicar em Limpar", () => {
    const onFiltrar = vi.fn();
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={onFiltrar} />
    );
    fireEvent.click(screen.getByRole("button", { name: /limpar/i }));
    expect(onFiltrar).toHaveBeenCalledWith({});
  });

  it("desabilita botão quando carregando", () => {
    render(
      <FiltrosAvancados categorias={categorias} ufs={ufs} onFiltrar={() => {}} carregando />
    );
    expect(screen.getByRole("button", { name: /buscando/i })).toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// BotaoExportar
// ---------------------------------------------------------------------------
describe("BotaoExportar", () => {
  it("renderiza com testid", () => {
    render(<BotaoExportar />);
    expect(screen.getByTestId("botao-exportar")).toBeInTheDocument();
  });

  it("renderiza label padrão", () => {
    render(<BotaoExportar />);
    expect(screen.getByText("Exportar CSV")).toBeInTheDocument();
  });

  it("renderiza label personalizado", () => {
    render(<BotaoExportar label="Baixar Dados" />);
    expect(screen.getByText("Baixar Dados")).toBeInTheDocument();
  });

  it("fica desabilitado quando disabled=true", () => {
    render(<BotaoExportar disabled />);
    expect(screen.getByTestId("botao-exportar")).toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// TabelaPrecos
// ---------------------------------------------------------------------------
const dadosPrecos: ListarPrecosResponse = {
  itens: [
    {
      id: 1,
      uf: "SP",
      categoria: "Papel A4",
      descricao: "Papel A4 lote 1",
      preco_unitario: 24.5,
      unidade: "UN",
      data_referencia: "2026-01-15",
      orgao: "Prefeitura SP-1",
      confianca: "ALTA",
    },
    {
      id: 2,
      uf: "RJ",
      categoria: "Papel A4",
      descricao: "Papel A4 lote 2",
      preco_unitario: 25.2,
      unidade: "UN",
      data_referencia: "2026-01-20",
      orgao: "Câmara RJ-2",
      confianca: "MEDIA",
    },
  ],
  total: 2,
  pagina: 1,
  por_pagina: 20,
  total_paginas: 1,
  filtros_aplicados: {},
};

describe("TabelaPrecos", () => {
  it("renderiza dados com testid", () => {
    render(<TabelaPrecos dados={dadosPrecos} />);
    expect(screen.getByTestId("tabela-precos")).toBeInTheDocument();
  });

  it("mostra UFs dos itens", () => {
    render(<TabelaPrecos dados={dadosPrecos} />);
    expect(screen.getByText("SP")).toBeInTheDocument();
    expect(screen.getByText("RJ")).toBeInTheDocument();
  });

  it("mostra estado de carregamento", () => {
    render(<TabelaPrecos dados={null} carregando />);
    expect(screen.getByTestId("tabela-carregando")).toBeInTheDocument();
  });

  it("mostra estado vazio quando sem dados", () => {
    render(<TabelaPrecos dados={null} />);
    expect(screen.getByTestId("tabela-vazia")).toBeInTheDocument();
  });

  it("mostra estado vazio quando lista vazia", () => {
    render(
      <TabelaPrecos dados={{ ...dadosPrecos, itens: [], total: 0 }} />
    );
    expect(screen.getByTestId("tabela-vazia")).toBeInTheDocument();
  });

  it("mostra badge de confiança ALTA", () => {
    render(<TabelaPrecos dados={dadosPrecos} />);
    expect(screen.getByText("ALTA")).toBeInTheDocument();
  });

  it("mostra total de registros", () => {
    render(<TabelaPrecos dados={dadosPrecos} />);
    expect(screen.getByText(/2 registros/i)).toBeInTheDocument();
  });

  it("chama onMudarPagina quando paginação visível", () => {
    const dadosMultiPagina = {
      ...dadosPrecos,
      total: 100,
      total_paginas: 5,
    };
    const onMudarPagina = vi.fn();
    render(<TabelaPrecos dados={dadosMultiPagina} onMudarPagina={onMudarPagina} />);
    fireEvent.click(screen.getByRole("button", { name: /próxima/i }));
    expect(onMudarPagina).toHaveBeenCalledWith(2);
  });
});

// ---------------------------------------------------------------------------
// GraficoTendencias
// ---------------------------------------------------------------------------
const dadosTendencias: TendenciasResponse = {
  categoria: "Papel A4",
  ufs_analisadas: ["SP", "RJ"],
  meses: 3,
  serie_temporal: {
    SP: [
      { periodo: "2025-10", preco: 24.0, variacao_pct: -0.5 },
      { periodo: "2025-11", preco: 24.5, variacao_pct: 0.0 },
      { periodo: "2025-12", preco: 24.8, variacao_pct: 0.5 },
    ],
    RJ: [
      { periodo: "2025-10", preco: 25.0, variacao_pct: -0.3 },
      { periodo: "2025-11", preco: 25.2, variacao_pct: 0.2 },
      { periodo: "2025-12", preco: 25.5, variacao_pct: 0.6 },
    ],
  },
  resumo_por_uf: {
    SP: { preco_atual: 24.8, preco_inicial: 24.0, variacao_total_pct: 3.3, tendencia: "ALTA", minimo: 24.0, maximo: 24.8 },
    RJ: { preco_atual: 25.5, preco_inicial: 25.0, variacao_total_pct: 2.0, tendencia: "ALTA", minimo: 25.0, maximo: 25.5 },
  },
  media_geral: 24.9,
  periodo_inicio: "2025-10",
  periodo_fim: "2025-12",
};

describe("GraficoTendencias", () => {
  it("renderiza estado de carregamento", () => {
    render(<GraficoTendencias dados={null} carregando />);
    expect(screen.getByTestId("grafico-carregando")).toBeInTheDocument();
  });

  it("renderiza estado vazio quando sem dados", () => {
    render(<GraficoTendencias dados={null} />);
    expect(screen.getByTestId("grafico-vazio")).toBeInTheDocument();
  });

  it("renderiza com dados", () => {
    render(<GraficoTendencias dados={dadosTendencias} />);
    expect(screen.getByTestId("grafico-tendencias")).toBeInTheDocument();
  });

  it("mostra nome da categoria", () => {
    render(<GraficoTendencias dados={dadosTendencias} />);
    expect(screen.getByText(/Papel A4/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// GraficoComparativo
// ---------------------------------------------------------------------------
const dadosComparativo: ComparativoResponse = {
  categoria: "Gasolina Comum",
  ufs_analisadas: ["SP", "RJ", "AC"],
  comparativo: [
    { uf: "SP", preco_base: 5.85, preco_atual: 5.87, variacao_pct: 0.3, rank: 1, diferenca_media_pct: -3.2 },
    { uf: "RJ", preco_base: 6.10, preco_atual: 6.13, variacao_pct: 0.5, rank: 2, diferenca_media_pct: 1.2 },
    { uf: "AC", preco_base: 7.20, preco_atual: 7.22, variacao_pct: 0.3, rank: 3, diferenca_media_pct: 19.1 },
  ],
  estatisticas: {
    media: 6.41,
    mediana: 6.13,
    desvio_padrao: 0.73,
    minimo: 5.87,
    maximo: 7.22,
    uf_mais_barata: "SP",
    uf_mais_cara: "AC",
  },
};

describe("GraficoComparativo", () => {
  it("renderiza estado de carregamento", () => {
    render(<GraficoComparativo dados={null} carregando />);
    expect(screen.getByTestId("comparativo-carregando")).toBeInTheDocument();
  });

  it("renderiza estado vazio quando sem dados", () => {
    render(<GraficoComparativo dados={null} />);
    expect(screen.getByTestId("comparativo-vazio")).toBeInTheDocument();
  });

  it("renderiza com dados", () => {
    render(<GraficoComparativo dados={dadosComparativo} />);
    expect(screen.getByTestId("grafico-comparativo")).toBeInTheDocument();
  });

  it("mostra UF mais barata", () => {
    render(<GraficoComparativo dados={dadosComparativo} />);
    expect(screen.getByText(/SP/)).toBeInTheDocument();
  });

  it("mostra nome da categoria", () => {
    render(<GraficoComparativo dados={dadosComparativo} />);
    expect(screen.getByText(/Gasolina Comum/)).toBeInTheDocument();
  });
});
