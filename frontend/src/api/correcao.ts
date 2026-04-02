/**
 * Cliente API para endpoints de correção monetária IPCA.
 */

const API_BASE = (import.meta.env.VITE_API_URL ?? "") + "/api/v1";

export interface DadoIPCA {
  ano: number;
  mes: number;
  variacao_mensal: number;
  variacao_acumulada_ano: number;
  indice_acumulado: number;
}

export interface SerieIPCAResponse {
  indice: string;
  periodo: { ano_inicio: number; ano_fim: number };
  total_meses: number;
  dados: DadoIPCA[];
}

export interface FatorCorrecaoResponse {
  fator: number;
  variacao_percentual: number;
  data_inicio: string;
  data_fim: string;
  indice: string;
}

export interface CorrecaoPrecoResponse {
  valor_original: number;
  valor_corrigido: number;
  fator: number;
  variacao_percentual: number;
  data_origem: string;
  data_destino: string;
  indice: string;
}

async function fetchJSON<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const urlObj = new URL(url, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        urlObj.searchParams.set(key, String(value));
      }
    }
  }
  const resp = await fetch(urlObj.toString());
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  }
  return resp.json();
}

export const correcaoAPI = {
  /** Série histórica IPCA. */
  serieIPCA: (anoInicio?: number, anoFim?: number) =>
    fetchJSON<SerieIPCAResponse>(`${API_BASE}/correcao/ipca`, {
      ano_inicio: anoInicio,
      ano_fim: anoFim,
    }),

  /** Fator de correção entre duas datas. */
  fatorCorrecao: (dataInicio: string, dataFim: string) =>
    fetchJSON<FatorCorrecaoResponse>(`${API_BASE}/correcao/fator`, {
      data_inicio: dataInicio,
      data_fim: dataFim,
    }),
};
