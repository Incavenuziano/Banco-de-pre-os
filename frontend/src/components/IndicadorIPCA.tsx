/**
 * IndicadorIPCA — Card mostrando variação IPCA dos últimos 12 meses.
 */

import React, { useEffect, useState } from "react";
import type { DadoIPCA, SerieIPCAResponse } from "../api/correcao";
import { correcaoAPI } from "../api/correcao";

interface IndicadorIPCAProps {
  /** Dados mock para testes — se fornecido, não busca da API. */
  dadosMock?: SerieIPCAResponse | null;
}

export const IndicadorIPCA: React.FC<IndicadorIPCAProps> = ({ dadosMock }) => {
  const [dados, setDados] = useState<DadoIPCA[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (dadosMock !== undefined) {
      setDados(dadosMock?.dados?.slice(-12) ?? []);
      setCarregando(false);
      return;
    }

    const carregar = async () => {
      try {
        setCarregando(true);
        const resp = await correcaoAPI.serieIPCA(2025, 2026);
        setDados(resp.dados.slice(-12));
      } catch {
        setErro("Erro ao carregar dados IPCA");
      } finally {
        setCarregando(false);
      }
    };
    carregar();
  }, [dadosMock]);

  if (carregando) {
    return (
      <div data-testid="ipca-carregando" className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="animate-pulse space-y-2">
          <div className="h-4 w-32 rounded bg-gray-200" />
          <div className="h-6 w-20 rounded bg-gray-200" />
        </div>
      </div>
    );
  }

  if (erro) {
    return (
      <div data-testid="ipca-erro" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {erro}
      </div>
    );
  }

  const acumulado12m = dados.reduce(
    (acc, d) => acc * (1 + d.variacao_mensal / 100),
    1
  );
  const variacao12m = ((acumulado12m - 1) * 100).toFixed(2);
  const ultimoMes = dados.length > 0 ? dados[dados.length - 1] : null;

  return (
    <div data-testid="indicador-ipca" className="rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-blue-600">
            IPCA — Inflação
          </h3>
          <p className="mt-1 text-2xl font-bold text-gray-900" data-testid="ipca-acumulado">
            {variacao12m}%
          </p>
          <p className="text-xs text-gray-500">acumulado 12 meses</p>
        </div>
        {ultimoMes && (
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700" data-testid="ipca-ultimo-mes">
              {ultimoMes.variacao_mensal > 0 ? "+" : ""}
              {ultimoMes.variacao_mensal.toFixed(2)}%
            </p>
            <p className="text-xs text-gray-400">
              {ultimoMes.mes.toString().padStart(2, "0")}/{ultimoMes.ano}
            </p>
          </div>
        )}
      </div>

      {/* Mini barras de variação mensal */}
      {dados.length > 0 && (
        <div className="mt-3 flex items-end gap-0.5" data-testid="ipca-barras">
          {dados.map((d, i) => {
            const altura = Math.max(4, Math.abs(d.variacao_mensal) * 20);
            const cor = d.variacao_mensal >= 0 ? "bg-blue-400" : "bg-red-400";
            return (
              <div
                key={i}
                className={`w-full rounded-t ${cor}`}
                style={{ height: `${altura}px` }}
                title={`${d.mes.toString().padStart(2, "0")}/${d.ano}: ${d.variacao_mensal}%`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};
