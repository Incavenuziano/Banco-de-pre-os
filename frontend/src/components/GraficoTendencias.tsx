/**
 * GraficoTendencias — Gráfico de tendência de preços ao longo do tempo.
 * Usa Recharts LineChart. Suporta múltiplas UFs no mesmo gráfico.
 */

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { TendenciasResponse } from "../api/analise";

interface GraficoTendenciasProps {
  dados: TendenciasResponse | null;
  carregando?: boolean;
}

const CORES_UF = [
  "#3b82f6", // azul
  "#10b981", // verde
  "#f59e0b", // amarelo
  "#ef4444", // vermelho
  "#8b5cf6", // roxo
  "#06b6d4", // ciano
  "#f97316", // laranja
];

function formatarPreco(valor: number): string {
  return `R$ ${valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Gráfico de linha com tendências de preço por UF.
 * @param dados - Dados de tendência retornados pela API
 * @param carregando - Estado de carregamento
 */
export const GraficoTendencias: React.FC<GraficoTendenciasProps> = ({
  dados,
  carregando = false,
}) => {
  if (carregando) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400" data-testid="grafico-carregando">
        Carregando gráfico...
      </div>
    );
  }

  if (!dados) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400" data-testid="grafico-vazio">
        Selecione uma categoria para visualizar a tendência.
      </div>
    );
  }

  // Montar dados para o Recharts: array de { periodo, UF1, UF2, ... }
  const periodos = dados.ufs_analisadas.length > 0
    ? (dados.serie_temporal[dados.ufs_analisadas[0]] ?? []).map((p) => p.periodo)
    : [];

  const chartData = periodos.map((periodo) => {
    const ponto: Record<string, string | number> = { periodo };
    dados.ufs_analisadas.forEach((uf) => {
      const serie = dados.serie_temporal[uf] ?? [];
      const item = serie.find((p) => p.periodo === periodo);
      ponto[uf] = item?.preco ?? 0;
    });
    return ponto;
  });

  return (
    <div data-testid="grafico-tendencias">
      <div className="mb-2 flex flex-wrap items-center gap-4">
        <h3 className="text-sm font-semibold text-gray-700">
          Tendência: {dados.categoria}
        </h3>
        <span className="text-xs text-gray-500">
          Média geral: {formatarPreco(dados.media_geral)}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="periodo"
            tick={{ fontSize: 11 }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => `R$ ${Number(v).toFixed(0)}`}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            formatter={(value, name) => [formatarPreco(Number(value)), String(name)]}
            labelFormatter={(label) => `Período: ${label}`}
          />
          <Legend />
          {dados.ufs_analisadas.map((uf, idx) => (
            <Line
              key={uf}
              type="monotone"
              dataKey={uf}
              stroke={CORES_UF[idx % CORES_UF.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Resumo de tendências por UF */}
      <div className="mt-3 flex flex-wrap gap-2">
        {dados.ufs_analisadas.map((uf, idx) => {
          const resumo = dados.resumo_por_uf[uf];
          const cor = CORES_UF[idx % CORES_UF.length];
          const badge =
            resumo?.tendencia === "ALTA"
              ? "↑"
              : resumo?.tendencia === "QUEDA"
              ? "↓"
              : "→";
          return (
            <span
              key={uf}
              className="rounded-full px-2 py-0.5 text-xs font-medium"
              style={{ backgroundColor: `${cor}20`, color: cor }}
            >
              {uf} {badge} {resumo?.variacao_total_pct > 0 ? "+" : ""}
              {resumo?.variacao_total_pct?.toFixed(1)}%
            </span>
          );
        })}
      </div>
    </div>
  );
};
