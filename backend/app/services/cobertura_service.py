"""Serviço de cobertura — municípios prioritários e índice de cobertura por UF/município."""

from __future__ import annotations

from datetime import datetime
from typing import Any


MUNICIPIOS_PRIORITARIOS: dict[str, list[str]] = {
    "DF": [
        "Brasília", "Taguatinga", "Ceilândia", "Samambaia", "Planaltina",
        "Gama", "Sobradinho", "Recanto das Emas", "São Sebastião", "Santa Maria",
    ],
    "GO": [
        "Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Luziânia",
        "Águas Lindas de Goiás", "Valparaíso de Goiás", "Trindade", "Formosa", "Novo Gama",
    ],
    "SP": [
        "São Paulo", "Guarulhos", "Campinas", "São Bernardo do Campo", "Santo André",
        "Osasco", "São José dos Campos", "Ribeirão Preto", "Sorocaba", "Santos",
    ],
    "MG": [
        "Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim",
        "Montes Claros", "Ribeirão das Neves", "Uberaba", "Governador Valadares", "Ipatinga",
    ],
    "BA": [
        "Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna",
        "Lauro de Freitas", "Juazeiro", "Ilhéus", "Jequié", "Teixeira de Freitas",
    ],
    "RS": [
        "Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria",
        "Gravataí", "Viamão", "Novo Hamburgo", "São Leopoldo", "Rio Grande",
    ],
    "SC": [
        "Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó",
        "Criciúma", "Itajaí", "Jaraguá do Sul", "Lages", "Palhoça",
    ],
    "PR": [
        "Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel",
        "São José dos Pinhais", "Foz do Iguaçu", "Colombo", "Guarapuava", "Paranaguá",
    ],
    "CE": [
        "Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral",
        "Crato", "Itapipoca", "Maranguape", "Iguatu", "Quixadá",
    ],
    "PE": [
        "Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina",
        "Paulista", "Cabo de Santo Agostinho", "Camaragibe", "Garanhuns", "Vitória de Santo Antão",
    ],
}

# Lista expandida dos 50 principais municípios goianos por população/relevância
# para acompanhamento de cobertura de dados do PNCP.
MUNICIPIOS_GOIAS: list[str] = [
    # Top 10 por população
    "Goiânia",
    "Aparecida de Goiânia",
    "Anápolis",
    "Rio Verde",
    "Luziânia",
    "Águas Lindas de Goiás",
    "Valparaíso de Goiás",
    "Trindade",
    "Formosa",
    "Novo Gama",
    # Municípios médios com alta atividade licitatória
    "Caldas Novas",
    "Itumbiara",
    "Jataí",
    "Catalão",
    "Senador Canedo",
    "Goianésia",
    "Mineiros",
    "Inhumas",
    "Uruaçu",
    "Goiás",
    "Iporá",
    "Morrinhos",
    "Quirinópolis",
    "São Luís de Montes Belos",
    "Niquelândia",
    "Porangatu",
    "Ceres",
    "Rubiataba",
    "Goianira",
    # Municípios pequenos relevantes
    "Alexânia",
    "Anicuns",
    "Bela Vista de Goiás",
    "Cristalina",
    "Cumari",
    "Edéia",
    "Hidrolandia",
    "Ipameri",
    "Itaberaí",
    "Itapaci",
    "Itapirapuã",
    "Jaraguá",
    "Jussara",
    "Nerópolis",
    "Orizona",
    "Paraúna",
    "Pires do Rio",
    "Planaltina de Goiás",
    "Posse",
    "Santa Helena de Goiás",
    "Silvânia",
]

# Thresholds para classificação de cobertura por município
# Baseados em critérios práticos: municípios pequenos de GO têm em média
# 5-20 pregões/ano no PNCP, municípios grandes têm 50-200+.
_THRESHOLDS_COBERTURA = {
    "ALTA":         {"min_amostras": 50, "min_categorias": 5},
    "MEDIA":        {"min_amostras": 20, "min_categorias": 3},
    "BAIXA":        {"min_amostras": 5,  "min_categorias": 1},
    # Abaixo disso: INSUFICIENTE
}


class CoberturaService:
    """Consulta municípios prioritários e calcula índice de cobertura."""

    # ─────────────────────────────────────────────────────
    # Métodos originais (compatibilidade total)
    # ─────────────────────────────────────────────────────

    def obter_municipios_por_uf(self, uf: str) -> list[str]:
        """Retorna lista de municípios prioritários de uma UF.

        Args:
            uf: Sigla da UF (ex: 'GO').

        Returns:
            Lista de nomes de municípios.
        """
        return MUNICIPIOS_PRIORITARIOS.get(uf.upper(), [])

    def obter_ufs_cobertas(self) -> list[str]:
        """Retorna lista de UFs com municípios cadastrados.

        Returns:
            Lista de siglas de UFs cobertas.
        """
        return sorted(MUNICIPIOS_PRIORITARIOS.keys())

    def calcular_indice_cobertura(
        self, uf: str, n_amostras: int, n_categorias: int
    ) -> dict:
        """Calcula índice de cobertura de uma UF.

        Fórmula: min(n_amostras/1000, 1.0) * 0.6 + min(n_categorias/50, 1.0) * 0.4
        ALTO se indice > 0.7, MEDIO se > 0.4, BAIXO se <= 0.4.

        Args:
            uf: Sigla da UF.
            n_amostras: Número de amostras coletadas.
            n_categorias: Número de categorias cobertas.

        Returns:
            Dict com uf, indice, nivel, n_amostras e n_categorias.
        """
        indice = min(n_amostras / 1000, 1.0) * 0.6 + min(n_categorias / 50, 1.0) * 0.4
        indice = round(indice, 4)

        if indice > 0.7:
            nivel = "ALTO"
        elif indice > 0.4:
            nivel = "MEDIO"
        else:
            nivel = "BAIXO"

        return {
            "uf": uf.upper(),
            "indice": indice,
            "nivel": nivel,
            "n_amostras": n_amostras,
            "n_categorias": n_categorias,
        }

    # ─────────────────────────────────────────────────────
    # Métodos novos: cobertura por município goiano
    # ─────────────────────────────────────────────────────

    def obter_todos_municipios_go(self) -> list[str]:
        """Retorna lista completa dos 50 principais municípios goianos monitorados.

        Returns:
            Lista de nomes de municípios de Goiás.
        """
        return list(MUNICIPIOS_GOIAS)

    def calcular_cobertura_municipio(
        self,
        municipio: str,
        uf: str,
        n_amostras: int,
        n_categorias: int,
        ultima_atualizacao: datetime | None = None,
    ) -> dict[str, Any]:
        """Calcula o nível de cobertura de dados para um município específico.

        Níveis:
          ALTA        — ≥50 amostras e ≥5 categorias
          MEDIA       — ≥20 amostras e ≥3 categorias
          BAIXA       — ≥5 amostras e ≥1 categoria
          INSUFICIENTE — abaixo dos critérios de BAIXA

        Args:
            municipio: Nome do município.
            uf: Sigla da UF (ex: 'GO').
            n_amostras: Número de fontes de preço ativas para o município.
            n_categorias: Número de categorias distintas cobertas.
            ultima_atualizacao: Timestamp da última ingestão (opcional).

        Returns:
            Dict com municipio, uf, n_amostras, n_categorias, nivel e
            ultima_atualizacao (ISO string ou None).
        """
        nivel = "INSUFICIENTE"
        for nome_nivel, thr in _THRESHOLDS_COBERTURA.items():
            if n_amostras >= thr["min_amostras"] and n_categorias >= thr["min_categorias"]:
                nivel = nome_nivel
                break

        return {
            "municipio": municipio,
            "uf": uf.upper(),
            "n_amostras": n_amostras,
            "n_categorias": n_categorias,
            "nivel": nivel,
            "ultima_atualizacao": (
                ultima_atualizacao.isoformat() if ultima_atualizacao else None
            ),
        }

    def obter_mapa_cobertura_go(
        self,
        contagens: dict[str, dict[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        """Retorna o mapa de cobertura de todos os municípios goianos monitorados.

        Args:
            contagens: Dict {municipio: {n_amostras: int, n_categorias: int}}.
                       Se None, todos os municípios terão nível INSUFICIENTE
                       (útil para inicialização ou quando o banco não está disponível).

        Returns:
            Lista de dicts com cobertura por município, ordenada por nível
            (ALTA → MEDIA → BAIXA → INSUFICIENTE) e depois alfabeticamente.
        """
        contagens = contagens or {}
        resultado: list[dict[str, Any]] = []

        for municipio in MUNICIPIOS_GOIAS:
            dados = contagens.get(municipio, {"n_amostras": 0, "n_categorias": 0})
            status = self.calcular_cobertura_municipio(
                municipio=municipio,
                uf="GO",
                n_amostras=dados.get("n_amostras", 0),
                n_categorias=dados.get("n_categorias", 0),
            )
            resultado.append(status)

        # Ordena por nível (ALTA primeiro) depois por nome
        _ordem_nivel = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2, "INSUFICIENTE": 3}
        resultado.sort(key=lambda r: (_ordem_nivel.get(r["nivel"], 4), r["municipio"]))

        return resultado

    def resumo_cobertura_go(
        self, contagens: dict[str, dict[str, int]] | None = None
    ) -> dict[str, Any]:
        """Retorna resumo estatístico da cobertura em Goiás.

        Args:
            contagens: Dict {municipio: {n_amostras, n_categorias}}.

        Returns:
            Dict com totais por nível, total de municípios e percentual coberto.
        """
        mapa = self.obter_mapa_cobertura_go(contagens)

        contagem_niveis: dict[str, int] = {
            "ALTA": 0, "MEDIA": 0, "BAIXA": 0, "INSUFICIENTE": 0
        }
        for item in mapa:
            contagem_niveis[item["nivel"]] = contagem_niveis.get(item["nivel"], 0) + 1

        total = len(mapa)
        cobertos = contagem_niveis["ALTA"] + contagem_niveis["MEDIA"] + contagem_niveis["BAIXA"]

        return {
            "total_municipios": total,
            "municipios_cobertos": cobertos,
            "percentual_coberto": round(cobertos / total * 100, 1) if total else 0.0,
            "por_nivel": contagem_niveis,
        }
