/**
 * LoadingSpinner — Indicador de carregamento acessível.
 */

import React from "react";

interface LoadingSpinnerProps {
  tamanho?: "sm" | "md" | "lg";
  mensagem?: string;
}

const TAMANHO_CLASSES: Record<string, string> = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-2",
  lg: "h-12 w-12 border-4",
};

/**
 * Spinner animado com mensagem opcional.
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  tamanho = "md",
  mensagem,
}) => {
  return (
    <div
      className="flex flex-col items-center justify-center gap-2"
      data-testid="loading-spinner"
      role="status"
      aria-live="polite"
    >
      <div
        className={`animate-spin rounded-full border-blue-600 border-t-transparent ${TAMANHO_CLASSES[tamanho]}`}
        aria-hidden="true"
      />
      {mensagem && <p className="text-sm text-gray-500">{mensagem}</p>}
      <span className="sr-only">Carregando...</span>
    </div>
  );
};
