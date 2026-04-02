/**
 * Documentacao — Página de documentação interativa do Banco de Preços.
 */

import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

interface ChangelogEntry {
  versao: string;
  data: string;
  descricao: string;
  itens: string[];
}

interface ComplianceInfo {
  normas: string[];
  fontes_aceitas: string[];
}

export const Documentacao: React.FC = () => {
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([]);
  const [metodologia, setMetodologia] = useState<string>("");
  const [compliance, setCompliance] = useState<ComplianceInfo | null>(null);
  const [abaAtiva, setAbaAtiva] = useState<"changelog" | "metodologia" | "compliance">("changelog");
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      setCarregando(true);
      try {
        const [clRes, metRes, compRes] = await Promise.all([
          fetch(`${API_BASE}/docs/changelog`).then((r) => r.json()),
          fetch(`${API_BASE}/docs/metodologia`).then((r) => r.json()),
          fetch(`${API_BASE}/docs/compliance`).then((r) => r.json()),
        ]);
        setChangelog(clRes.versoes ?? []);
        setMetodologia(metRes.conteudo ?? metRes.metodologia ?? "");
        setCompliance(compRes);
      } catch {
        // silencioso
      } finally {
        setCarregando(false);
      }
    };
    carregar();
  }, []);

  const abas = [
    { id: "changelog" as const, label: "Changelog" },
    { id: "metodologia" as const, label: "Metodologia" },
    { id: "compliance" as const, label: "Compliance" },
  ];

  return (
    <div className="min-h-screen bg-gray-50" data-testid="pagina-documentacao">
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-4xl px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">Documentação</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Metodologia, compliance e changelog do Banco de Preços
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-6">
        {/* Abas */}
        <div className="mb-6 flex gap-2" data-testid="doc-abas">
          {abas.map((aba) => (
            <button
              key={aba.id}
              onClick={() => setAbaAtiva(aba.id)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                abaAtiva === aba.id
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-100"
              }`}
              data-testid={`aba-${aba.id}`}
            >
              {aba.label}
            </button>
          ))}
        </div>

        {carregando ? (
          <div data-testid="doc-carregando" className="text-center py-12 text-gray-400">
            Carregando documentação...
          </div>
        ) : (
          <>
            {/* Changelog */}
            {abaAtiva === "changelog" && (
              <div data-testid="doc-changelog" className="space-y-4">
                {changelog.map((entry, i) => (
                  <div key={i} className="rounded-lg border bg-white p-4">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="rounded-full bg-blue-100 px-3 py-0.5 text-xs font-bold text-blue-700">
                        v{entry.versao}
                      </span>
                      <span className="text-xs text-gray-400">{entry.data}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 mb-1">{entry.descricao}</p>
                    <ul className="list-disc pl-5 text-xs text-gray-600 space-y-0.5">
                      {entry.itens.map((item, j) => (
                        <li key={j}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}

            {/* Metodologia */}
            {abaAtiva === "metodologia" && (
              <div
                data-testid="doc-metodologia"
                className="rounded-lg border bg-white p-6 prose prose-sm max-w-none"
              >
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                  {metodologia}
                </pre>
              </div>
            )}

            {/* Compliance */}
            {abaAtiva === "compliance" && compliance && (
              <div data-testid="doc-compliance" className="rounded-lg border bg-white p-6 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Normas Aplicáveis</h3>
                  <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                    {compliance.normas?.map((n, i) => <li key={i}>{n}</li>)}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Fontes Aceitas</h3>
                  <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                    {compliance.fontes_aceitas?.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
};
