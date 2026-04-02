/**
 * KPICard — Card de indicador chave de desempenho.
 * Componente reutilizável para exibir métricas numéricas no dashboard.
 */

import React from "react";

interface KPICardProps {
  titulo: string;
  valor: string | number;
  subtitulo?: string;
  cor?: "azul" | "verde" | "amarelo" | "vermelho";
  icone?: string;
}

const COR_CLASSES: Record<string, string> = {
  azul: "border-l-blue-500 bg-blue-50",
  verde: "border-l-green-500 bg-green-50",
  amarelo: "border-l-yellow-500 bg-yellow-50",
  vermelho: "border-l-red-500 bg-red-50",
};

const TEXTO_COR: Record<string, string> = {
  azul: "text-blue-700",
  verde: "text-green-700",
  amarelo: "text-yellow-700",
  vermelho: "text-red-700",
};

/**
 * Exibe um KPI com título, valor principal e subtítulo opcional.
 * @param titulo - Label do indicador
 * @param valor - Valor a ser exibido em destaque
 * @param subtitulo - Texto secundário opcional
 * @param cor - Cor do card (azul, verde, amarelo, vermelho)
 * @param icone - Emoji ou ícone para o card
 */
export const KPICard: React.FC<KPICardProps> = ({
  titulo,
  valor,
  subtitulo,
  cor = "azul",
  icone,
}) => {
  return (
    <div
      className={`rounded-lg border-l-4 p-4 shadow-sm ${COR_CLASSES[cor]}`}
      data-testid="kpi-card"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{titulo}</p>
          <p className={`mt-1 text-2xl font-bold ${TEXTO_COR[cor]}`}>{valor}</p>
          {subtitulo && (
            <p className="mt-1 text-xs text-gray-500">{subtitulo}</p>
          )}
        </div>
        {icone && (
          <span className="ml-3 text-2xl" aria-hidden="true">
            {icone}
          </span>
        )}
      </div>
    </div>
  );
};
