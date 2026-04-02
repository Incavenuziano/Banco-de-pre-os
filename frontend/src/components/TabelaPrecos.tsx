/**
 * TabelaPrecos — Tabela de listagem de preços com paginação e ordenação.
 * Colunas Preço Unit. e Data suportam sort asc/desc via callback onOrdenar.
 */

import React from "react";
import type { ListarPrecosResponse, PrecoItem } from "../api/analise";

export type CampoOrdenacao = "preco" | "data";
export type DirecaoOrdenacao = "asc" | "desc";

interface TabelaPrecosProps {
  dados: ListarPrecosResponse | null;
  carregando?: boolean;
  onMudarPagina?: (pagina: number) => void;
  mostrarCorrigido?: boolean;
  onToggleCorrigido?: () => void;
  /** Campo atualmente ordenado */
  ordenarPor?: CampoOrdenacao;
  /** Direção atual da ordenação */
  ordemAtual?: DirecaoOrdenacao;
  /** Callback ao clicar em coluna ordenável */
  onOrdenar?: (campo: CampoOrdenacao, direcao: DirecaoOrdenacao) => void;
  /** Callback ao clicar em "ver histórico" de um item */
  onVerHistorico?: (item: PrecoItem) => void;
}

const CONFIANCA_CLASSES: Record<string, string> = {
  ALTA: "bg-green-100 text-green-800",
  MEDIA: "bg-yellow-100 text-yellow-800",
  BAIXA: "bg-red-100 text-red-800",
};

function formatarPreco(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarData(iso: string | undefined | null): string {
  if (!iso) return "—";
  // iso: "YYYY-MM-DD"
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

/** Ícone de seta para indicar ordenação */
function SortIcon({ campo, ordenarPor, ordemAtual }: {
  campo: CampoOrdenacao;
  ordenarPor?: CampoOrdenacao;
  ordemAtual?: DirecaoOrdenacao;
}) {
  const ativo = ordenarPor === campo;
  if (!ativo) return <span className="ml-1 text-gray-300">⇅</span>;
  return (
    <span className="ml-1 text-blue-600">
      {ordemAtual === "asc" ? "↑" : "↓"}
    </span>
  );
}

/**
 * Tabela responsiva de preços com paginação e ordenação por preço/data.
 */
export const TabelaPrecos: React.FC<TabelaPrecosProps> = ({
  dados,
  carregando = false,
  onMudarPagina,
  mostrarCorrigido = false,
  onToggleCorrigido,
  ordenarPor,
  ordemAtual = "desc",
  onOrdenar,
  onVerHistorico,
}) => {
  /** Ao clicar numa coluna ordenável: alterna direção se já ativa, senão ativa desc */
  function handleSort(campo: CampoOrdenacao) {
    if (!onOrdenar) return;
    const novaDir: DirecaoOrdenacao =
      ordenarPor === campo && ordemAtual === "desc" ? "asc" : "desc";
    onOrdenar(campo, novaDir);
  }

  if (carregando) {
    return (
      <div className="flex items-center justify-center py-12" data-testid="tabela-carregando">
        <div className="text-gray-500">Carregando preços...</div>
      </div>
    );
  }

  if (!dados || dados.itens.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-400" data-testid="tabela-vazia">
        Nenhum preço encontrado para os filtros selecionados.
      </div>
    );
  }

  return (
    <div data-testid="tabela-precos">
      {/* Header com contagem e toggle */}
      <div className="mb-2 flex items-center justify-between text-sm text-gray-600">
        <span>
          {dados.total} registro{dados.total !== 1 ? "s" : ""} encontrado{dados.total !== 1 ? "s" : ""}
        </span>
        <div className="flex items-center gap-3">
          {onToggleCorrigido && (
            <button
              onClick={onToggleCorrigido}
              data-testid="toggle-corrigido"
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                mostrarCorrigido
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {mostrarCorrigido ? "Corrigido IPCA" : "Nominal"}
            </button>
          )}
          <span>
            Página {dados.pagina} de {dados.total_paginas}
          </span>
        </div>
      </div>

      {/* Tabela — scroll horizontal em mobile */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {/* Colunas fixas */}
              {["UF", "Categoria"].map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600"
                >
                  {col}
                </th>
              ))}

              {/* Descrição */}
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                Descrição
              </th>

              {/* Preço Unit. — ordenável */}
              <th
                className={`px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide cursor-pointer select-none ${
                  ordenarPor === "preco" ? "text-blue-700" : "text-gray-600 hover:text-blue-600"
                }`}
                onClick={() => handleSort("preco")}
                data-testid="th-preco"
                title="Ordenar por preço"
              >
                Preço Unit.
                <SortIcon campo="preco" ordenarPor={ordenarPor} ordemAtual={ordemAtual} />
              </th>

              {/* Corrigido Hoje (opcional) */}
              {mostrarCorrigido && (
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Corrigido Hoje
                </th>
              )}

              {/* Unidade */}
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                Unidade
              </th>

              {/* Data contratação — ordenável */}
              <th
                className={`px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide cursor-pointer select-none ${
                  ordenarPor === "data" ? "text-blue-700" : "text-gray-600 hover:text-blue-600"
                }`}
                onClick={() => handleSort("data")}
                data-testid="th-data"
                title="Ordenar por data da contratação"
              >
                Data Contratação
                <SortIcon campo="data" ordenarPor={ordenarPor} ordemAtual={ordemAtual} />
              </th>

              {/* Tipo preço */}
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                Tipo
              </th>

              {/* Colunas finais */}
              {["Órgão", "Contratação", "Confiança"].map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600"
                >
                  {col}
                </th>
              ))}
              {onVerHistorico && (
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">
                  Histórico
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {dados.itens.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 font-medium text-gray-900">{item.uf}</td>
                <td className="px-3 py-2 text-gray-700">{item.categoria}</td>
                <td className="max-w-[260px] truncate px-3 py-2 text-gray-600" title={item.descricao}>
                  {item.descricao}
                </td>
                <td className="px-3 py-2 font-medium text-gray-900">
                  {formatarPreco(item.preco_unitario)}
                </td>
                {mostrarCorrigido && (
                  <td className="px-3 py-2 font-medium text-blue-700" data-testid="preco-corrigido">
                    {formatarPreco(
                      ((item as unknown) as { preco_corrigido_hoje?: number }).preco_corrigido_hoje
                      ?? item.preco_unitario
                    )}
                  </td>
                )}
                <td className="px-3 py-2 text-gray-600">{item.unidade}</td>
                <td className="px-3 py-2 text-gray-600">{formatarData(item.data_referencia)}</td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      item.tipo_preco === "homologado"
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                    data-testid="badge-tipo-preco"
                  >
                    {item.tipo_preco === "homologado" ? "Homologado" : "Estimado"}
                  </span>
                </td>
                <td className="max-w-[150px] truncate px-3 py-2 text-gray-600" title={item.orgao}>
                  {item.orgao}
                </td>
                <td className="px-3 py-2">
                  {item.pncp_url ? (
                    <a
                      href={item.pncp_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={item.numero_controle_pncp ?? "Ver no PNCP"}
                      className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
                      data-testid="link-pncp"
                    >
                      🔗 PNCP
                    </a>
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      CONFIANCA_CLASSES[item.confianca] ?? "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {item.confianca}
                  </span>
                </td>
                {onVerHistorico && (
                  <td className="px-3 py-2">
                    <button
                      onClick={() => onVerHistorico(item)}
                      className="rounded px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-50 hover:text-blue-800"
                      data-testid="btn-historico"
                      title="Ver histórico de preços"
                    >
                      📈
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginação */}
      {dados.total_paginas > 1 && onMudarPagina && (
        <div className="mt-3 flex items-center justify-center gap-2">
          <button
            onClick={() => onMudarPagina(dados.pagina - 1)}
            disabled={dados.pagina <= 1}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-100 disabled:opacity-40"
            aria-label="Página anterior"
          >
            ‹ Anterior
          </button>

          {Array.from({ length: Math.min(dados.total_paginas, 7) }, (_, i) => {
            const pg = i + 1;
            return (
              <button
                key={pg}
                onClick={() => onMudarPagina(pg)}
                className={`rounded border px-3 py-1 text-sm ${
                  pg === dados.pagina
                    ? "border-blue-500 bg-blue-600 text-white"
                    : "hover:bg-gray-100"
                }`}
              >
                {pg}
              </button>
            );
          })}

          <button
            onClick={() => onMudarPagina(dados.pagina + 1)}
            disabled={dados.pagina >= dados.total_paginas}
            className="rounded border px-3 py-1 text-sm hover:bg-gray-100 disabled:opacity-40"
            aria-label="Próxima página"
          >
            Próxima ›
          </button>
        </div>
      )}
    </div>
  );
};
