/**
 * BenchmarkRegional — Ranking visual de preços por UF.
 */

import React from "react";

interface RankingItem {
  uf: string;
  preco_medio: number;
  rank: number;
  n_amostras?: number;
}

interface BenchmarkRegionalProps {
  categoria: string;
  ranking: RankingItem[];
  estatisticas?: {
    media: number;
    mediana: number;
    uf_mais_barata: string;
    uf_mais_cara: string;
  };
}

function formatarPreco(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export const BenchmarkRegional: React.FC<BenchmarkRegionalProps> = ({
  categoria,
  ranking,
  estatisticas,
}) => {
  if (ranking.length === 0) {
    return (
      <div data-testid="benchmark-vazio" className="text-center text-sm text-gray-400 py-8">
        Sem dados de benchmark para {categoria}
      </div>
    );
  }

  const maxPreco = Math.max(...ranking.map((r) => r.preco_medio));

  return (
    <div data-testid="benchmark-regional" className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">
        Benchmark Regional — {categoria}
      </h3>

      {estatisticas && (
        <div className="mb-3 flex gap-4 text-xs text-gray-500" data-testid="benchmark-stats">
          <span>Média: {formatarPreco(estatisticas.media)}</span>
          <span>Mediana: {formatarPreco(estatisticas.mediana)}</span>
          <span>Mais barata: {estatisticas.uf_mais_barata}</span>
          <span>Mais cara: {estatisticas.uf_mais_cara}</span>
        </div>
      )}

      <div className="space-y-1.5" data-testid="benchmark-barras">
        {ranking.map((item) => {
          const larguraPct = (item.preco_medio / maxPreco) * 100;
          const cor =
            item.rank <= 3
              ? "bg-green-400"
              : item.rank <= ranking.length - 3
                ? "bg-blue-400"
                : "bg-orange-400";
          return (
            <div key={item.uf} className="flex items-center gap-2 text-xs">
              <span className="w-6 font-medium text-gray-600 text-right">{item.rank}</span>
              <span className="w-6 font-bold text-gray-800">{item.uf}</span>
              <div className="flex-1">
                <div
                  className={`h-4 rounded ${cor} transition-all`}
                  style={{ width: `${larguraPct}%` }}
                  title={formatarPreco(item.preco_medio)}
                />
              </div>
              <span className="w-20 text-right font-medium text-gray-700">
                {formatarPreco(item.preco_medio)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
