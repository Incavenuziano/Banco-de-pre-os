/**
 * ComparativoItem — Página para comparar preços de um item entre UFs.
 *
 * Campo de busca por descrição (debounce 300ms), dropdown UF opcional,
 * tabela de histórico com badges estimado/homologado,
 * gráfico de evolução de preço e benchmark por UF.
 */

import React, { useEffect, useState, useRef, useCallback } from "react";
import { analiseAPI } from "../api/analise";
import type { ComparativoItemResponse } from "../api/analise";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function formatarPreco(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(iso: string): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

const UFS_DISPONIVEIS = [
  "", "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
  "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
  "RO", "RR", "RS", "SC", "SE", "SP", "TO",
];

export const ComparativoItem: React.FC = () => {
  const [descricao, setDescricao] = useState("");
  const [ufSelecionada, setUfSelecionada] = useState("");
  const [dados, setDados] = useState<ComparativoItemResponse | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const buscar = useCallback(async (desc: string, uf: string) => {
    if (desc.trim().length < 2) return;
    setCarregando(true);
    setErro(null);
    try {
      const result = await analiseAPI.getComparativoItem(desc, uf || undefined);
      setDados(result);
    } catch {
      setErro("Erro ao buscar comparativo. Verifique a conexão.");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (descricao.trim().length < 2) return;
    debounceRef.current = setTimeout(() => {
      buscar(descricao, ufSelecionada);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [descricao, ufSelecionada, buscar]);

  // Dados para gráfico de linha (evolução temporal)
  const dadosGrafico =
    dados?.historico_local
      .filter((h) => h.data)
      .sort((a, b) => a.data.localeCompare(b.data))
      .map((h) => ({
        data: h.data,
        preco: h.preco,
      })) ?? [];

  const benchmarkEntries = dados
    ? Object.entries(dados.benchmark_por_uf).sort(([a], [b]) => a.localeCompare(b))
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Comparativo de Item
            </h1>
            <p className="mt-0.5 text-sm text-gray-500">
              Compare preços de um item entre diferentes UFs e contratações
            </p>
          </div>
          <a
            href="#/"
            className="rounded bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200"
          >
            Voltar ao Dashboard
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        {/* Busca */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição do item
            </label>
            <input
              type="text"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              placeholder="Ex: papel sulfite, gasolina, detergente..."
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              data-testid="input-descricao"
            />
          </div>
          <div className="w-32">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              UF (opcional)
            </label>
            <select
              value={ufSelecionada}
              onChange={(e) => setUfSelecionada(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              data-testid="select-uf"
            >
              {UFS_DISPONIVEIS.map((uf) => (
                <option key={uf} value={uf}>
                  {uf || "Todas"}
                </option>
              ))}
            </select>
          </div>
        </div>

        {carregando && (
          <div className="flex justify-center py-8">
            <div className="text-gray-500">Buscando dados...</div>
          </div>
        )}

        {erro && (
          <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {erro}
          </div>
        )}

        {dados && !carregando && (
          <>
            {/* Estatísticas gerais */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <div className="text-xs text-gray-500 uppercase">Média Geral</div>
                <div className="text-lg font-bold text-gray-900">
                  {formatarPreco(dados.estatisticas.media_geral)}
                </div>
              </div>
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <div className="text-xs text-gray-500 uppercase">Mediana</div>
                <div className="text-lg font-bold text-gray-900">
                  {formatarPreco(dados.estatisticas.mediana)}
                </div>
              </div>
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <div className="text-xs text-gray-500 uppercase">Desvio Padrão</div>
                <div className="text-lg font-bold text-gray-900">
                  {formatarPreco(dados.estatisticas.desvio_padrao)}
                </div>
              </div>
            </div>

            {/* Gráfico de evolução */}
            {dadosGrafico.length > 1 && (
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-gray-700">
                  Evolução do preço ao longo do tempo
                </h2>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dadosGrafico}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="data"
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: string) => {
                        const parts = v.split("-");
                        return parts.length >= 2 ? `${parts[1]}/${parts[0]}` : v;
                      }}
                    />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v: number) =>
                        v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
                      }
                    />
                    <Tooltip
                      formatter={(value: number) => [formatarPreco(value), "Preço"]}
                      labelFormatter={(label: string) => `Data: ${formatarData(label)}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="preco"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Benchmark por UF */}
            {benchmarkEntries.length > 0 && (
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-gray-700">
                  Benchmark por UF
                </h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {["UF", "Média", "Mínimo", "Máximo", "Amostras"].map((h) => (
                          <th
                            key={h}
                            className="px-4 py-2 text-left text-xs font-semibold uppercase text-gray-600"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {benchmarkEntries.map(([uf, stats]) => (
                        <tr key={uf} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-medium">{uf}</td>
                          <td className="px-4 py-2">{formatarPreco(stats.media)}</td>
                          <td className="px-4 py-2">{formatarPreco(stats.min)}</td>
                          <td className="px-4 py-2">{formatarPreco(stats.max)}</td>
                          <td className="px-4 py-2">{stats.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Histórico local */}
            <div className="rounded-lg border bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-gray-700">
                Histórico de contratações ({dados.historico_local.length} registros)
              </h2>
              {dados.historico_local.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhum registro encontrado.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {["Data", "Preço Unit.", "Tipo", "Órgão", "Município", "UF"].map((h) => (
                          <th
                            key={h}
                            className="px-3 py-2 text-left text-xs font-semibold uppercase text-gray-600"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {dados.historico_local.map((h, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-3 py-2">{formatarData(h.data)}</td>
                          <td className="px-3 py-2 font-medium">{formatarPreco(h.preco)}</td>
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
                          <td className="max-w-[200px] truncate px-3 py-2" title={h.orgao}>
                            {h.orgao}
                          </td>
                          <td className="px-3 py-2">{h.municipio}</td>
                          <td className="px-3 py-2">{h.uf}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
};
