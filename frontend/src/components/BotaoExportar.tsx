/**
 * BotaoExportar — Botão de exportação de dados em CSV.
 * Dispara download direto do endpoint /exportar/csv.
 */

import React from "react";
import { analiseAPI } from "../api/analise";
import type { FiltrosPrecos } from "../api/analise";

interface BotaoExportarProps {
  filtros?: FiltrosPrecos;
  label?: string;
  disabled?: boolean;
}

/**
 * Botão que aciona download de CSV com os filtros ativos.
 * @param filtros - Filtros para aplicar na exportação
 * @param label - Texto do botão
 * @param disabled - Desabilitar o botão
 */
export const BotaoExportar: React.FC<BotaoExportarProps> = ({
  filtros,
  label = "Exportar CSV",
  disabled = false,
}) => {
  const handleExportar = () => {
    const url = analiseAPI.urlExportarCSV(filtros);
    const link = document.createElement("a");
    link.href = url;
    link.download = "";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <button
      onClick={handleExportar}
      disabled={disabled}
      data-testid="botao-exportar"
      className="flex items-center gap-1.5 rounded border border-green-600 bg-white px-3 py-1.5 text-sm font-medium text-green-700 hover:bg-green-50 disabled:opacity-40"
    >
      <span aria-hidden="true">⬇</span>
      {label}
    </button>
  );
};
