/**
 * SeletorCategoria — Seletor de categoria para gráficos de análise.
 * Componente reutilizável utilizado em tendências e comparativos.
 */

import React from "react";

interface SeletorCategoriaProps {
  categorias: string[];
  categoriaSelecionada: string;
  onChange: (categoria: string) => void;
  label?: string;
}

/**
 * Seletor de categoria com label e callback onChange.
 * @param categorias - Lista de categorias disponíveis
 * @param categoriaSelecionada - Categoria atualmente selecionada
 * @param onChange - Callback ao mudar de categoria
 * @param label - Label do seletor
 */
export const SeletorCategoria: React.FC<SeletorCategoriaProps> = ({
  categorias,
  categoriaSelecionada,
  onChange,
  label = "Categoria",
}) => {
  return (
    <div className="flex items-center gap-2" data-testid="seletor-categoria">
      <label className="text-sm font-medium text-gray-600">{label}:</label>
      <select
        value={categoriaSelecionada}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
      >
        {categorias.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>
    </div>
  );
};
