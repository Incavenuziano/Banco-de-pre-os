/**
 * BuscaSemantica — Campo de busca com sugestões em tempo real.
 */

import React, { useState, useEffect, useRef } from "react";

interface ResultadoBusca {
  id: number;
  descricao: string;
  categoria?: string;
  preco_mediano?: number;
  score_combinado?: number;
  uf?: string;
}

interface BuscaSemanticaProps {
  /** Dados mock para testes. */
  resultadosMock?: ResultadoBusca[] | null;
  onSelecionar?: (item: ResultadoBusca) => void;
}

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export const BuscaSemantica: React.FC<BuscaSemanticaProps> = ({
  resultadosMock,
  onSelecionar,
}) => {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState<ResultadoBusca[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [aberto, setAberto] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (resultadosMock !== undefined) {
      setResultados(resultadosMock ?? []);
      setAberto((resultadosMock?.length ?? 0) > 0);
      return;
    }

    if (query.length < 3) {
      setResultados([]);
      setAberto(false);
      return;
    }

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setCarregando(true);
      try {
        const resp = await fetch(
          `${API_BASE}/busca/combinada?q=${encodeURIComponent(query)}&top_n=5`
        );
        if (resp.ok) {
          const data = await resp.json();
          setResultados(data.resultados ?? []);
          setAberto(true);
        }
      } catch {
        // silencioso
      } finally {
        setCarregando(false);
      }
    }, 300);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query, resultadosMock]);

  return (
    <div data-testid="busca-semantica" className="relative w-full max-w-md">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar item ou serviço..."
          data-testid="busca-input"
          className="w-full rounded-lg border border-gray-300 px-4 py-2 pr-10 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {carregando && (
          <div data-testid="busca-loading" className="absolute right-3 top-2.5">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          </div>
        )}
      </div>

      {aberto && resultados.length > 0 && (
        <div
          data-testid="busca-resultados"
          className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg"
        >
          {resultados.map((item, i) => (
            <button
              key={item.id ?? i}
              onClick={() => {
                onSelecionar?.(item);
                setAberto(false);
                setQuery(item.descricao);
              }}
              className="flex w-full items-center justify-between px-4 py-2 text-left text-sm hover:bg-blue-50"
              data-testid={`busca-item-${i}`}
            >
              <div className="flex-1 truncate">
                <span className="font-medium text-gray-900">{item.descricao}</span>
                {item.categoria && (
                  <span className="ml-2 text-xs text-gray-400">{item.categoria}</span>
                )}
              </div>
              {item.score_combinado !== undefined && (
                <span className="ml-2 text-xs text-blue-500">
                  {(item.score_combinado * 100).toFixed(0)}%
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {aberto && resultados.length === 0 && query.length >= 3 && !carregando && (
        <div
          data-testid="busca-vazia"
          className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white p-3 text-center text-sm text-gray-400 shadow-lg"
        >
          Nenhum resultado encontrado
        </div>
      )}
    </div>
  );
};
