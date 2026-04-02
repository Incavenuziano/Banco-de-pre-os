/**
 * FiltrosAvancados — Formulário de filtros para a listagem de preços.
 * Filtros: UF, categoria, data início/fim, faixa de preço.
 * Mobile-first com layout responsivo.
 */

import React, { useState } from "react";
import type { FiltrosPrecos } from "../api/analise";

interface FiltrosAvancadosProps {
  categorias: string[];
  ufs: string[];
  municipios?: string[];
  onFiltrar: (filtros: FiltrosPrecos) => void;
  carregando?: boolean;
}

/**
 * Componente de filtros avançados para o dashboard de preços.
 * Emite o callback onFiltrar quando o formulário é submetido.
 */
export const FiltrosAvancados: React.FC<FiltrosAvancadosProps> = ({
  categorias,
  ufs,
  municipios = [],
  onFiltrar,
  carregando = false,
}) => {
  const [filtros, setFiltros] = useState<FiltrosPrecos>({});

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFiltros((prev) => ({ ...prev, [name]: value || undefined }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFiltrar({ ...filtros, pagina: 1 });
  };

  const handleLimpar = () => {
    setFiltros({});
    onFiltrar({});
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      data-testid="filtros-avancados"
    >
      <h2 className="mb-4 text-base font-semibold text-gray-700">
        🔍 Filtros Avançados
      </h2>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {/* UF */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="uf">
            UF
          </label>
          <select
            id="uf"
            name="uf"
            value={filtros.uf ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Todas</option>
            {ufs.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
          </select>
        </div>

        {/* Município */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="municipio">
            Município
          </label>
          <input
            id="municipio"
            name="municipio"
            type="text"
            list="municipios-list"
            value={filtros.municipio ?? ""}
            onChange={handleChange}
            placeholder="Ex: Brasília"
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
          {municipios.length > 0 && (
            <datalist id="municipios-list">
              {municipios.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
          )}
        </div>

        {/* Categoria */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="categoria">
            Categoria
          </label>
          <select
            id="categoria"
            name="categoria"
            value={filtros.categoria ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Todas</option>
            {categorias.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Data início */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="data_inicio">
            Data Início
          </label>
          <input
            id="data_inicio"
            name="data_inicio"
            type="date"
            value={filtros.data_inicio ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Data fim */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="data_fim">
            Data Fim
          </label>
          <input
            id="data_fim"
            name="data_fim"
            type="date"
            value={filtros.data_fim ?? ""}
            onChange={handleChange}
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Preço mínimo */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="preco_min">
            Preço Mín. (R$)
          </label>
          <input
            id="preco_min"
            name="preco_min"
            type="number"
            min={0}
            step="0.01"
            value={filtros.preco_min ?? ""}
            onChange={handleChange}
            placeholder="0,00"
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Preço máximo */}
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600" htmlFor="preco_max">
            Preço Máx. (R$)
          </label>
          <input
            id="preco_max"
            name="preco_max"
            type="number"
            min={0}
            step="0.01"
            value={filtros.preco_max ?? ""}
            onChange={handleChange}
            placeholder="9999,99"
            className="w-full rounded border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Botões */}
      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={carregando}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {carregando ? "Buscando..." : "Filtrar"}
        </button>
        <button
          type="button"
          onClick={handleLimpar}
          className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
        >
          Limpar
        </button>
      </div>
    </form>
  );
};
