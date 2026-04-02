/**
 * GraficoComparativo — Gráfico de barras comparando preços entre UFs.
 * Usa Recharts BarChart. Destaca a UF mais barata e mais cara.
 */

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ComparativoResponse } from "../api/analise";

interface GraficoComparativoProps {
  dados: ComparativoResponse | null;
  carregando?: boolean;
}

function formatarPreco(valor: number): string {
  return `R$ ${valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Gráfico de barras comparando preços de uma categoria entre UFs.
 * Barra verde = mais barata, vermelha = mais cara, azul = demais.
 */
export const GraficoComparativo: React.FC<GraficoComparativoProps> = ({
  dados,
  carregando = false,
}) => {
  if (carregando) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400" data-testid="comparativo-carregando">
        Carregando comparativo...
      </div>
    );
  }

  if (!dados) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400" data-testid="comparativo-vazio">
        Selecione uma categoria para comparar entre UFs.
      </div>
    );
  }

  const ufMaisBarata = dados.estatisticas.uf_mais_barata;
  const ufMaisCara = dados.estatisticas.uf_mais_cara;

  return (
    <div data-testid="grafico-comparativo">
      <div className="mb-2 flex flex-wrap items-center gap-4">
        <h3 className="text-sm font-semibold text-gray-700">
          Comparativo por UF: {dados.categoria}
        </h3>
        <span className="text-xs text-green-600">
          🏆 Mais barata: {ufMaisBarata} ({formatarPreco(dados.estatisticas.minimo)})
        </span>
        <span className="text-xs text-red-600">
          💸 Mais cara: {ufMaisCara} ({formatarPreco(dados.estatisticas.maximo)})
        </span>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={dados.comparativo}
          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="uf" tick={{ fontSize: 11 }} tickLine={false} />
          <YAxis
            tickFormatter={(v) => `R$${Number(v).toFixed(0)}`}
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            formatter={(value) => [formatarPreco(Number(value)), "Preço"]}
            labelFormatter={(label) => `UF: ${label}`}
          />
          <Bar dataKey="preco_atual" radius={[3, 3, 0, 0]}>
            {dados.comparativo.map((item) => (
              <Cell
                key={item.uf}
                fill={
                  item.uf === ufMaisBarata
                    ? "#10b981"
                    : item.uf === ufMaisCara
                    ? "#ef4444"
                    : "#3b82f6"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Estatísticas resumidas */}
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          { label: "Média", valor: dados.estatisticas.media },
          { label: "Mediana", valor: dados.estatisticas.mediana },
          { label: "Mín.", valor: dados.estatisticas.minimo },
          { label: "Máx.", valor: dados.estatisticas.maximo },
        ].map(({ label, valor }) => (
          <div key={label} className="rounded bg-gray-50 p-2 text-center">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-sm font-semibold text-gray-800">{formatarPreco(valor)}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
