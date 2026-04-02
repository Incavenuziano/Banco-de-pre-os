"""Serviço de cobertura — municípios prioritários e índice de cobertura por UF."""

from __future__ import annotations


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


class CoberturaService:
    """Consulta municípios prioritários e calcula índice de cobertura."""

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
