/**
 * Cliente API para os endpoints de análise de preços — Banco de Preços.
 * Todos os endpoints são do backend FastAPI em localhost:8000.
 */

const API_BASE = (import.meta.env.VITE_API_URL ?? "") + "/api/v1";

export interface PrecoItem {
  id: number;
  uf: string;
  categoria: string;
  descricao: string;
  preco_unitario: number;
  unidade: string;
  data_referencia: string;
  orgao: string;
  confianca: string;
  /** Número de controle PNCP, ex: "12345678000195-1-000123/2026" */
  numero_controle_pncp?: string;
  /** URL direta para o edital no PNCP */
  pncp_url?: string;
  /** Tipo de preço: estimado ou homologado */
  tipo_preco?: string;
}

export interface ListarPrecosResponse {
  itens: PrecoItem[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
  filtros_aplicados: Record<string, unknown>;
}

export interface FiltrosPrecos {
  uf?: string;
  categoria?: string;
  municipio?: string;
  data_inicio?: string;
  data_fim?: string;
  preco_min?: number;
  preco_max?: number;
  pagina?: number;
  por_pagina?: number;
  /** Campo de ordenação: 'data' ou 'preco' */
  ordenar_por?: "data" | "preco";
  /** Direção: 'asc' ou 'desc' */
  ordem?: "asc" | "desc";
}

export interface PontoTendencia {
  periodo: string;
  preco: number;
  variacao_pct: number;
}

export interface ResumoUF {
  preco_atual: number;
  preco_inicial: number;
  variacao_total_pct: number;
  tendencia: "ALTA" | "QUEDA" | "ESTAVEL";
  minimo: number;
  maximo: number;
}

export interface TendenciasResponse {
  categoria: string;
  ufs_analisadas: string[];
  meses: number;
  serie_temporal: Record<string, PontoTendencia[]>;
  resumo_por_uf: Record<string, ResumoUF>;
  media_geral: number;
  periodo_inicio: string;
  periodo_fim: string;
}

export interface ComparativoItem {
  uf: string;
  preco_base: number;
  preco_atual: number;
  variacao_pct: number;
  rank: number;
  diferenca_media_pct: number;
}

export interface ComparativoResponse {
  categoria: string;
  ufs_analisadas: string[];
  comparativo: ComparativoItem[];
  estatisticas: {
    media: number;
    mediana: number;
    desvio_padrao: number;
    minimo: number;
    maximo: number;
    uf_mais_barata: string;
    uf_mais_cara: string;
  };
}

export interface DashboardKPIs {
  total_registros: number;
  total_categorias: number;
  total_ufs: number;
  ultima_atualizacao: string;
  cobertura_pct: number;
}

export interface DashboardResponse {
  kpis: DashboardKPIs;
  kpis_por_uf: Array<{
    uf: string;
    total_itens: number;
    media_preco: number;
    ultima_atualizacao: string;
  }>;
  top_categorias: Array<{ categoria: string; n_registros: number }>;
  ufs_cobertas: string[];
}

export interface Categoria {
  nome: string;
  n_ufs: number;
  n_registros: number;
  ultima_atualizacao: string;
}

export interface UFItem {
  uf: string;
  n_categorias: number;
  n_registros: number;
  status: string;
}

export interface BenchmarkRankingItem {
  uf: string;
  preco_medio: number;
  rank: number;
  n_amostras: number;
}

export interface BenchmarkUFResponse {
  categoria: string;
  ranking: BenchmarkRankingItem[];
  estatisticas: {
    media: number;
    mediana: number;
    desvio_padrao: number;
    minimo: number;
    maximo: number;
    uf_mais_barata: string;
    uf_mais_cara: string;
  };
  total_ufs: number;
}

export interface HistoricoItemEntry {
  data: string;
  preco: number;
  orgao: string;
  municipio: string;
  uf: string;
  pncp_url: string;
  tipo_preco: string;
}

export interface HistoricoItemResponse {
  descricao: string;
  total: number;
  historico: HistoricoItemEntry[];
}

export interface ComparativoItemResponse {
  descricao: string;
  historico_local: HistoricoItemEntry[];
  benchmark_por_uf: Record<
    string,
    { media: number; min: number; max: number; count: number }
  >;
  estatisticas: {
    media_geral: number;
    mediana: number;
    desvio_padrao: number;
  };
}

export interface BenchmarkEvolucaoResponse {
  categoria: string;
  ufs: string[];
  meses: number;
  serie: Record<string, Array<{ periodo: string; preco: number; variacao_pct: number }>>;
}

async function fetchJSON<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const urlObj = new URL(url, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        if (Array.isArray(value)) {
          value.forEach((v) => urlObj.searchParams.append(key, String(v)));
        } else {
          urlObj.searchParams.set(key, String(value));
        }
      }
    }
  }

  const resp = await fetch(urlObj.toString());
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  }
  return resp.json();
}

export const analiseAPI = {
  /** Lista preços com filtros avançados. */
  listarPrecos: (filtros?: FiltrosPrecos) =>
    fetchJSON<ListarPrecosResponse>(`${API_BASE}/analise/precos`, filtros as Record<string, unknown>),

  /** Obtém tendências de preço por categoria e UF. */
  obterTendencias: (categoria: string, ufs?: string[], meses?: number) =>
    fetchJSON<TendenciasResponse>(`${API_BASE}/analise/tendencias`, {
      categoria,
      ufs,
      meses,
    }),

  /** Compara preços entre UFs para uma categoria. */
  obterComparativo: (categoria: string, ufs?: string[]) =>
    fetchJSON<ComparativoResponse>(`${API_BASE}/analise/comparativo`, { categoria, ufs }),

  /** Retorna KPIs do dashboard. */
  obterDashboard: (ufs?: string[], categoria?: string) =>
    fetchJSON<DashboardResponse>(`${API_BASE}/analise/dashboard`, { ufs, categoria }),

  /** Lista categorias disponíveis. */
  listarCategorias: () => fetchJSON<Categoria[]>(`${API_BASE}/analise/categorias`),

  /** Lista UFs validadas. */
  listarUFs: () => fetchJSON<UFItem[]>(`${API_BASE}/analise/ufs`),

  /** Lista municípios (opcionalmente filtrando por UF). */
  listarMunicipios: (uf?: string) =>
    fetchJSON<{ municipio: string; uf: string }[]>(`${API_BASE}/analise/municipios`, uf ? { uf } : undefined),

  /** Benchmark regional: ranking por UF. */
  obterBenchmarkUF: (categoria: string) =>
    fetchJSON<BenchmarkUFResponse>(`${API_BASE}/analise/benchmark/uf`, { categoria }),

  /** Benchmark regional: evolução temporal. */
  obterBenchmarkEvolucao: (categoria: string, ufs?: string[], meses?: number) =>
    fetchJSON<BenchmarkEvolucaoResponse>(`${API_BASE}/analise/benchmark/evolucao`, { categoria, ufs, meses }),

  /** Histórico de preços de um item. */
  getHistoricoItem: (descricao: string, uf?: string, limite?: number) =>
    fetchJSON<import("./analise").HistoricoItemResponse>(
      `${API_BASE}/analise/historico`,
      { descricao, uf, limite },
    ),

  /** Comparativo de item por UF. */
  getComparativoItem: (descricao: string, uf?: string) =>
    fetchJSON<import("./analise").ComparativoItemResponse>(
      `${API_BASE}/analise/comparativo-item`,
      { descricao, uf },
    ),

  /** Retorna URL de exportação CSV com filtros. */
  urlExportarCSV: (filtros?: FiltrosPrecos): string => {
    const urlObj = new URL(`${API_BASE}/analise/exportar/csv`);
    if (filtros) {
      for (const [key, value] of Object.entries(filtros)) {
        if (value !== undefined && value !== null && value !== "") {
          urlObj.searchParams.set(key, String(value));
        }
      }
    }
    return urlObj.toString();
  },
};
