/**
 * Dashboard — Página principal do Banco de Preços.
 *
 * Seções:
 * 1. KPIs gerais (total registros, UFs cobertas, categorias, cobertura %)
 * 2. Gráfico de tendências por categoria
 * 3. Gráfico comparativo entre UFs
 * 4. Tabela de preços com filtros avançados e exportação CSV
 */

import React, { useEffect, useState, useCallback } from "react";
import { analiseAPI } from "../api/analise";
import type {
  DashboardResponse,
  TendenciasResponse,
  ComparativoResponse,
  ListarPrecosResponse,
  FiltrosPrecos,
} from "../api/analise";

import { KPICard } from "../components/KPICard";
import { GraficoTendencias } from "../components/GraficoTendencias";
import { GraficoComparativo } from "../components/GraficoComparativo";
import { TabelaPrecos } from "../components/TabelaPrecos";
import { FiltrosAvancados } from "../components/FiltrosAvancados";
import { BotaoExportar } from "../components/BotaoExportar";
import { SeletorCategoria } from "../components/SeletorCategoria";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { ErroAlerta } from "../components/ErroAlerta";
import { IndicadorIPCA } from "../components/IndicadorIPCA";
import { BuscaSemantica } from "../components/BuscaSemantica";
import { BenchmarkRegional } from "../components/BenchmarkRegional";
import type { BenchmarkUFResponse } from "../api/analise";

const CATEGORIA_PADRAO = "Papel A4";

export const Dashboard: React.FC = () => {
  // Estados de dados
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [tendencias, setTendencias] = useState<TendenciasResponse | null>(null);
  const [comparativo, setComparativo] = useState<ComparativoResponse | null>(null);
  const [precos, setPrecos] = useState<ListarPrecosResponse | null>(null);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [ufs, setUFs] = useState<string[]>([]);
  const [municipios, setMunicipios] = useState<string[]>([]);

  // Estados de UI
  const [categoriaSelecionada, setCategoriaSelecionada] = useState(CATEGORIA_PADRAO);
  const [filtrosAtivos, setFiltrosAtivos] = useState<FiltrosPrecos>({});
  const [pagina, setPagina] = useState(1);
  const [ordenarPor, setOrdenarPor] = useState<"preco" | "data">("data");
  const [ordemAtual, setOrdemAtual] = useState<"asc" | "desc">("desc");

  // Estados de carregamento
  const [carregandoDash, setCarregandoDash] = useState(true);
  const [carregandoTendencias, setCarregandoTendencias] = useState(false);
  const [carregandoComparativo, setCarregandoComparativo] = useState(false);
  const [carregandoPrecos, setCarregandoPrecos] = useState(false);

  // Toggle correção monetária
  const [mostrarCorrigido, setMostrarCorrigido] = useState(false);

  // Benchmark regional
  const [benchmark, setBenchmark] = useState<BenchmarkUFResponse | null>(null);

  // Estados de erro
  const [erroDash, setErroDash] = useState<string | null>(null);
  const [erroPrecos, setErroPrecos] = useState<string | null>(null);

  // Carregar metadados e dashboard ao montar
  useEffect(() => {
    const carregar = async () => {
      try {
        setCarregandoDash(true);
        const [dashData, catsData, ufsData, munsData] = await Promise.all([
          analiseAPI.obterDashboard(),
          analiseAPI.listarCategorias(),
          analiseAPI.listarUFs(),
          analiseAPI.listarMunicipios(),
        ]);
        setDashboard(dashData);
        setCategorias(catsData.map((c) => c.nome));
        setUFs(ufsData.map((u) => u.uf));
        setMunicipios(munsData.map((m) => m.municipio));
      } catch (err) {
        setErroDash("Erro ao carregar dashboard. Verifique a conexão com o backend.");
      } finally {
        setCarregandoDash(false);
      }
    };
    carregar();
  }, []);

  // Carregar tendências ao mudar categoria
  useEffect(() => {
    if (!categoriaSelecionada) return;
    const carregar = async () => {
      setCarregandoTendencias(true);
      try {
        const data = await analiseAPI.obterTendencias(categoriaSelecionada, undefined, 6);
        setTendencias(data);
      } catch {
        // silencioso para gráfico
      } finally {
        setCarregandoTendencias(false);
      }
    };
    carregar();
  }, [categoriaSelecionada]);

  // Carregar comparativo ao mudar categoria
  useEffect(() => {
    if (!categoriaSelecionada) return;
    const carregar = async () => {
      setCarregandoComparativo(true);
      try {
        const data = await analiseAPI.obterComparativo(categoriaSelecionada);
        setComparativo(data);
      } catch {
        // silencioso para gráfico
      } finally {
        setCarregandoComparativo(false);
      }
    };
    carregar();
  }, [categoriaSelecionada]);

  // Carregar benchmark ao mudar categoria
  useEffect(() => {
    if (!categoriaSelecionada) return;
    const carregar = async () => {
      try {
        const data = await analiseAPI.obterBenchmarkUF(categoriaSelecionada);
        setBenchmark(data);
      } catch {
        // silencioso
      }
    };
    carregar();
  }, [categoriaSelecionada]);

  // Carregar preços com filtros
  const carregarPrecos = useCallback(
    async (filtros: FiltrosPrecos, pg: number, ordPor: string, ord: string) => {
      setCarregandoPrecos(true);
      setErroPrecos(null);
      try {
        const data = await analiseAPI.listarPrecos({
          ...filtros,
          pagina: pg,
          por_pagina: 20,
          ordenar_por: ordPor,
          ordem: ord,
        });
        setPrecos(data);
      } catch {
        setErroPrecos("Erro ao buscar preços. Tente novamente.");
      } finally {
        setCarregandoPrecos(false);
      }
    },
    []
  );

  // Carregar preços ao montar e ao mudar filtros/página/ordenação
  useEffect(() => {
    carregarPrecos(filtrosAtivos, pagina, ordenarPor, ordemAtual);
  }, [filtrosAtivos, pagina, ordenarPor, ordemAtual, carregarPrecos]);

  const handleOrdenar = (campo: "preco" | "data", direcao: "asc" | "desc") => {
    setOrdenarPor(campo);
    setOrdemAtual(direcao);
    setPagina(1);
  };

  const handleFiltrar = (filtros: FiltrosPrecos) => {
    setFiltrosAtivos(filtros);
    setPagina(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">
            📊 Banco de Preços — Dashboard de Análise
          </h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Análise de preços públicos por UF e categoria · 15 UFs validadas
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        {/* Erro global */}
        {erroDash && (
          <ErroAlerta mensagem={erroDash} onFechar={() => setErroDash(null)} />
        )}

        {/* KPIs */}
        {carregandoDash ? (
          <LoadingSpinner mensagem="Carregando dashboard..." />
        ) : dashboard ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <KPICard
              titulo="Total de Registros"
              valor={dashboard.kpis.total_registros.toLocaleString("pt-BR")}
              icone="📋"
              cor="azul"
            />
            <KPICard
              titulo="UFs Cobertas"
              valor={`${dashboard.kpis.total_ufs} / 27`}
              subtitulo={`${dashboard.kpis.cobertura_pct}% de cobertura`}
              icone="🗺️"
              cor="verde"
            />
            <KPICard
              titulo="Categorias"
              valor={dashboard.kpis.total_categorias}
              icone="📦"
              cor="amarelo"
            />
            <KPICard
              titulo="Última Atualização"
              valor={dashboard.kpis.ultima_atualizacao}
              icone="🕐"
              cor="azul"
            />
          </div>
        ) : null}

        {/* Indicador IPCA */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <IndicadorIPCA />
        </div>

        {/* Busca Semântica */}
        <div className="flex items-center gap-4">
          <BuscaSemantica />
        </div>

        {/* Seletor de Categoria para Gráficos */}
        <div className="flex items-center justify-between">
          <SeletorCategoria
            categorias={categorias}
            categoriaSelecionada={categoriaSelecionada}
            onChange={setCategoriaSelecionada}
            label="Categoria para análise"
          />
        </div>

        {/* Gráficos — lado a lado em desktop, empilhados em mobile */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <GraficoTendencias dados={tendencias} carregando={carregandoTendencias} />
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <GraficoComparativo dados={comparativo} carregando={carregandoComparativo} />
          </div>
        </div>

        {/* Benchmark Regional */}
        {benchmark && (
          <BenchmarkRegional
            categoria={benchmark.categoria}
            ranking={benchmark.ranking}
            estatisticas={benchmark.estatisticas}
          />
        )}

        {/* Filtros + Tabela */}
        <div className="space-y-3">
          <FiltrosAvancados
            categorias={categorias}
            ufs={ufs}
            municipios={municipios}
            onFiltrar={handleFiltrar}
            carregando={carregandoPrecos}
          />

          {/* Barra de ações */}
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">
              Listagem de Preços
            </h2>
            <BotaoExportar filtros={filtrosAtivos} />
          </div>

          {erroPrecos && (
            <ErroAlerta mensagem={erroPrecos} onFechar={() => setErroPrecos(null)} />
          )}

          <TabelaPrecos
            dados={precos}
            carregando={carregandoPrecos}
            onMudarPagina={setPagina}
            mostrarCorrigido={mostrarCorrigido}
            onToggleCorrigido={() => setMostrarCorrigido(!mostrarCorrigido)}
            ordenarPor={ordenarPor}
            ordemAtual={ordemAtual}
            onOrdenar={handleOrdenar}
          />
        </div>
      </main>

      <footer className="mt-8 border-t border-gray-200 bg-white py-4 text-center text-xs text-gray-400">
        Banco de Preços v0.9 · Semana 14 · Dados públicos — PNCP / ComprasGov
      </footer>
    </div>
  );
};
