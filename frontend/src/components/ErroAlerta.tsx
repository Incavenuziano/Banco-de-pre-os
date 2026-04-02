/**
 * ErroAlerta — Componente de exibição de erros.
 */

import React from "react";

interface ErroAlertaProps {
  mensagem: string;
  onFechar?: () => void;
}

/**
 * Alerta de erro com botão de fechar opcional.
 */
export const ErroAlerta: React.FC<ErroAlertaProps> = ({ mensagem, onFechar }) => {
  return (
    <div
      className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
      data-testid="erro-alerta"
      role="alert"
    >
      <span aria-hidden="true">⚠️</span>
      <span className="flex-1">{mensagem}</span>
      {onFechar && (
        <button
          onClick={onFechar}
          className="ml-2 text-red-500 hover:text-red-700"
          aria-label="Fechar alerta"
        >
          ×
        </button>
      )}
    </div>
  );
};
