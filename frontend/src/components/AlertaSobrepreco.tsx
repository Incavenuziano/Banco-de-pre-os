/**
 * AlertaSobrepreco — Badge colorido indicando status de sobrepreço.
 */

import React from "react";

export type StatusAlerta = "NORMAL" | "ATENCAO" | "CRITICO" | "SEM_REFERENCIA";

interface AlertaSobreprecoProps {
  status: StatusAlerta;
  desvio?: number;
  /** Mostra desvio percentual inline. */
  mostrarDesvio?: boolean;
}

const STATUS_CONFIG: Record<StatusAlerta, { cor: string; label: string; icone: string }> = {
  NORMAL: { cor: "bg-green-100 text-green-800", label: "Normal", icone: "" },
  ATENCAO: { cor: "bg-yellow-100 text-yellow-800", label: "Atenção", icone: "" },
  CRITICO: { cor: "bg-red-100 text-red-800", label: "Crítico", icone: "" },
  SEM_REFERENCIA: { cor: "bg-gray-100 text-gray-500", label: "S/ ref.", icone: "" },
};

export const AlertaSobrepreco: React.FC<AlertaSobreprecoProps> = ({
  status,
  desvio,
  mostrarDesvio = false,
}) => {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.SEM_REFERENCIA;

  return (
    <span
      data-testid="alerta-badge"
      data-status={status}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${config.cor}`}
    >
      {config.label}
      {mostrarDesvio && desvio !== undefined && (
        <span data-testid="alerta-desvio" className="ml-0.5 opacity-75">
          ({desvio > 0 ? "+" : ""}{desvio.toFixed(1)}%)
        </span>
      )}
    </span>
  );
};
