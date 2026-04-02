/**
 * ModalHistoricoPrecos — Modal com gráfico e tabela do histórico de preços de um item.
 */

import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { analiseAPI } from "../api/analise";
import type { HistoricoItemEntry } from "../api/analise";
import { LoadingSpinner } from "./LoadingSpinner";

interface ModalHistoricoPrecosProps {
  descricao: string;
  uf?: string;
  onFechar: () => void;
}

function formatarPreco(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(iso: string): string {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export const ModalHistoricoPrecos: React.FC<ModalHistoricoPrecosProps> = ({
  descricao,
  uf,
  onFechar,
}) => {
  const [historico, setHistorico] = useState<HistoricoItemEntry[] | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      try {
        const data = await analiseAPI.getHistoricoItem(descricao, uf, 200);
        // Ordenar cronologicamente
        const sorted = [...data.historico].sort(
          (a, b) => new Date(a.data).getTime() - new Date(b.data).getTime()
        );
        setHistorico(sorted);
      } catch {
        setHistorico([]);
      } finally {
        setCarregando(false);
      }
    };
    carregar();
  }, [descricao, uf]);

  // Fechar com ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onFechar();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onFechar]);

  const dadosGrafico = historico?.map((h) => ({
    data: formatarData(h.data),
    preco: h.preco,
  }));

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      data-testid="modal-historico-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onFechar();
      }}
    >
      <div
        className="relative mx-4 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white p-6 shadow-xl"
        data-testid="modal-historico"
      >
        {/* Header */}
        <div className="mb-4 flex items-start justify-between">
          <h2
            className="max-w-[90%] truncate text-lg font-semibold text-gray-900"
            title={descricao}
            data-testid="modal-historico-titulo"
          >
            Histórico: {descricao}
          </h2>
          <button
            onClick={onFechar}
            className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            aria-label="Fechar"
            data-testid="modal-historico-fechar"
          >
            ×
          </button>
        </div>

        {/* Conteúdo */}
        {carregando ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner mensagem="Carregando histórico..." />
          </div>
        ) : !historico || historico.length === 0 ? (
          <p className="py-8 text-center text-gray-500" data-testid="historico-vazio">
            Nenhum registro encontrado para este item.
          </p>
        ) : (
          <>
            {/* Gráfico */}
            <div className="mb-6 h-64" data-testid="historico-grafico">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dadosGrafico}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="data" tick={{ fontSize: 11 }} />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v: number) => formatarPreco(v)}
                  />
                  <Tooltip
                    formatter={(value) => [formatarPreco(Number(value)), "Preço"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="preco"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Tabela */}
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm" data-testid="historico-tabela">
                <thead className="bg-gray-50">
                  <tr>
                    {["Data", "Preço", "Órgão", "Município", "UF", "Tipo", "Link PNCP"].map(
                      (col) => (
                        <th
                          key={col}
                          className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600"
                        >
                          {col}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {historico.map((h, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-700">{formatarData(h.data)}</td>
                      <td className="px-3 py-2 font-medium text-gray-900">
                        {formatarPreco(h.preco)}
                      </td>
                      <td className="max-w-[150px] truncate px-3 py-2 text-gray-600" title={h.orgao}>
                        {h.orgao}
                      </td>
                      <td className="px-3 py-2 text-gray-600">{h.municipio}</td>
                      <td className="px-3 py-2 text-gray-600">{h.uf}</td>
                      <td className="px-3 py-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            h.tipo_preco === "homologado"
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {h.tipo_preco === "homologado" ? "Homologado" : "Estimado"}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        {h.pncp_url ? (
                          <a
                            href={h.pncp_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline"
                          >
                            🔗 PNCP
                          </a>
                        ) : (
                          <span className="text-xs text-gray-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
