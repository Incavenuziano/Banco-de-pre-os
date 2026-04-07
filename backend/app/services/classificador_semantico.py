"""Classificador semântico de itens por categoria.

Estratégia em duas camadas:
1. Tenta usar llama-cpp-python com modelo GGUF local (EmbeddingGemma ou similar).
   O caminho do modelo é configurado via variável de ambiente LLAMA_MODEL_PATH.
2. Fallback: TF-IDF com vocabulário expandido por categoria (zero dependências externas).

O classificador semântico é usado como fallback do ClassificadorRegex no
ClassificadorHibrido — itens que o regex não consegue classificar passam por aqui.
"""

from __future__ import annotations

import logging
import math
import os
import unicodedata
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Vocabulário expandido por categoria
# Cada entrada mapeia o nome canônico da categoria para uma string de sinônimos
# e termos técnicos frequentes em descrições de licitação. Quanto mais rica a
# descrição, melhor a cobertura semântica.
# ──────────────────────────────────────────────────────────────────────────────
VOCABULARIO_CATEGORIAS: dict[str, str] = {
    "Papel A4": (
        "papel sulfite resma impressora folha cópia xerox reprografia branco "
        "a4 ofício 75g 90g 210x297 500 folhas papelaria impresso"
    ),
    "Material de Limpeza Geral": (
        "detergente limpador multiuso limpa vidro sabão sabonete esponja pano "
        "chão vassoura rodo balde desengordurante desentupidor limpeza "
        "higienizante higienizacao saneante germicida produto limpeza esfregão flanela"
    ),
    "Sabonete / Álcool em Gel": (
        "sabonete álcool gel 70% higienizante antisséptico bactericida mãos "
        "alcool sanitizante dispensador álcool glicerinado"
    ),
    "Combustível (Gasolina / Etanol / Diesel)": (
        "gasolina etanol diesel combustível álcool hidratado s10 s500 "
        "aditivado gnv arla biodiesel litro abastecimento posto combustível"
    ),
    "Cartucho / Toner": (
        "toner cartucho tinta impressora hp epson canon brother lexmark "
        "compatível original ribbon refil xerox laser jato inkjet"
    ),
    "Gêneros Alimentícios (Merenda Escolar)": (
        "arroz feijão açúcar sal óleo soja leite fubá macarrão farinha "
        "merenda escolar alimento alimentação gênero alimentício "
        "margarina manteiga café biscoito bolacha tempero vinagre massa"
    ),
    "Serviço de Limpeza e Conservação": (
        "serviço limpeza conservação predial terceirização asseio "
        "zeladoria limpeza contratação limpeza prestação serviço "
        "funcionário limpeza mão obra limpeza mensal limpeza"
    ),
    "Pneu / Câmara de Ar": (
        "pneu câmara ar borracha aro veículo carro ônibus caminhão "
        "moto radial diagonal recauchutado reforma pneu remold"
    ),
    "EPI (Equipamento de Proteção Individual)": (
        "epi capacete bota segurança luva proteção óculos proteção "
        "colete sinalizador botina cinto segurança protetor auricular "
        "respirador máscara equipamento proteção individual nr"
    ),
    "Uniforme Funcional": (
        "uniforme camisa camiseta calça jaleco avental farda "
        "vestuário roupa profissional bordado funcional camiseta polo "
        "bermuda servidores municipais"
    ),
    "Mesa / Cadeira de Escritório": (
        "cadeira escritório mesa escritório mobiliário reunião "
        "giratória ergonômica estação trabalho bancada poltrona "
        "secretária executiva"
    ),
    "Armário / Arquivo": (
        "armário aço arquivo estante metálica gaveteiro fichário "
        "porta objetos roupeiro prateleira metal gaveta"
    ),
    "Computador Desktop": (
        "computador desktop pc processador intel amd core i3 i5 i7 "
        "workstation all-in-one cpu teclado mouse kit estação trabalho"
    ),
    "Notebook / Laptop": (
        "notebook laptop computador portátil ultrabook i3 i5 i7 "
        "intel amd ryzen tela ssd ram memória portátil"
    ),
    "Nobreak / UPS": (
        "nobreak ups estabilizador tensão bateria ininterrupta "
        "proteção elétrica va volt ampere"
    ),
    "Switch / Roteador": (
        "switch roteador rede portas ethernet gigabit wireless "
        "wi-fi access point hub lan firewall"
    ),
    "Impressora": (
        "impressora laser jato tinta multifuncional copiadora "
        "scanner plotter térmica impressora"
    ),
    "Projetor Multimídia": (
        "projetor multimídia datashow tela projeção lúmens hdmi "
        "apresentação retroprojetor"
    ),
    "Material de Expediente Geral": (
        "caneta lápis borracha grampeador clipe pasta fichário "
        "bloco rascunho envelope formulário expediente cola tesoura "
        "régua corretivo marcador pincel atômico"
    ),
    "Papel Higiênico": (
        "papel higiênico folha dupla rolo banheiro sanitário "
        "toalha papel toalha interfolha"
    ),
    "Saco de Lixo": (
        "saco lixo sacola descartável litros preto azul verde "
        "reciclável coleta rolo"
    ),
    "Material Elétrico": (
        "fio cabo elétrico tomada interruptor disjuntor fita "
        "isolante lâmpada led fluorescente condulite eletroduto "
        "quadro elétrico chave fusível"
    ),
    "Material Hidráulico": (
        "cano tubo pvc joelho cotovelo registro torneira "
        "válvula conexão hidráulica encanamento caixa água"
    ),
    "Tintas e Vernizes": (
        "tinta acrílica látex verniz esmalte massa corrida "
        "fundo primer rolo pincel solvente aguarrás lata tinta"
    ),
    "Cimento / Areia / Brita": (
        "cimento areia brita concreto argamassa reboco cal "
        "tijolo bloco material construção saco cimento"
    ),
    "Medicamentos Básicos (OTC)": (
        "medicamento remédio comprimido cápsula solução injetável "
        "analgésico dipirona paracetamol ibuprofeno antibiótico "
        "farmácia droga"
    ),
    "Material Hospitalar / Descartáveis Médicos": (
        "seringa agulha atadura curativo luva descartável "
        "máscara cirúrgica esparadrapo algodão gaze hospital "
        "material hospitalar descartável médico"
    ),
    "Gás de Cozinha (GLP)": (
        "gás cozinha glp botijão 13kg p13 p45 granel "
        "gás liquefeito petróleo recarga"
    ),
    "Água Mineral": (
        "água mineral galão 20 litros garrafa potável "
        "bebedouro refil purificador copo descartável"
    ),
    "Serviço de Vigilância / Portaria": (
        "vigilância portaria segurança armada desarmada "
        "vigia monitoramento ronda patrimonial posto vigilância"
    ),
    "Serviço de Transporte Escolar": (
        "transporte escolar van micro-ônibus ônibus aluno "
        "estudante rota transporte escolar fretamento"
    ),
    "Serviço de Manutenção Predial": (
        "manutenção predial elétrica hidráulica civil "
        "reforma pequenos reparos pintura instalação prédio"
    ),
    "Serviço de Dedetização / Controle de Pragas": (
        "dedetização controle pragas fumigação "
        "extermínio insetos roedores pulverização desinsetização"
    ),
    "Serviço de TI / Suporte": (
        "suporte técnico ti tecnologia informação rede "
        "helpdesk manutenção computador sistema assistência"
    ),
    "Software / Sistema de Informação": (
        "software sistema licença aplicativo erp "
        "gestão contabilidade nota fiscal sistema informação"
    ),
    "Serviço de Telefonia / Internet": (
        "telefonia internet banda larga link dados "
        "telefone celular corporativo plano serviço"
    ),
    "Serviço de Impressão / Reprografia": (
        "impressão cópia reprografia outsourcing "
        "impressora locação contrato cópias"
    ),
    "Mobiliário Escolar": (
        "carteira escolar cadeira aluno mesa escolar "
        "lousa quadro negro branco mobiliário escolar"
    ),
    "Câmera de Segurança (CFTV)": (
        "câmera segurança cftv dvr nvr monitoramento "
        "circuito fechado televisão ip vigilância câmera"
    ),
    "Peças e Acessórios para Veículos": (
        "peça veículo acessório auto manutenção veicular "
        "filtro óleo freio amortecedor correia bateria carro"
    ),
    "Mobiliário Escolar": (
        "carteira escolar mesa aluno cadeira escola lousa "
        "quadro negro verde giz mobiliário pedagógico"
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Protocolo de backend de embedding (dependency injection)
# ──────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class EmbeddingBackend(Protocol):
    """Interface que qualquer backend de embedding deve satisfazer."""

    def embed(self, texto: str) -> list[float]:
        """Gera vetor denso para um texto."""
        ...

    @property
    def dimensao(self) -> int:
        """Dimensão dos vetores gerados."""
        ...

    @property
    def nome(self) -> str:
        """Identificador do backend usado (para metodo no resultado)."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Backend 1: llama-cpp-python (modelo GGUF local)
# ──────────────────────────────────────────────────────────────────────────────

class LlamaCppBackend:
    """Backend de embedding usando llama-cpp-python com modelo GGUF local."""

    def __init__(self, model_path: str) -> None:
        from llama_cpp import Llama  # type: ignore[import]

        self._model = Llama(
            model_path=model_path,
            embedding=True,
            n_ctx=512,
            n_threads=os.cpu_count() or 4,
            verbose=False,
        )
        # Detecta dimensão gerando um embedding de teste
        teste = self._model.embed("teste")
        self._dim = len(teste) if isinstance(teste[0], float) else len(teste[0])
        logger.info("LlamaCppBackend carregado: %s (dim=%d)", model_path, self._dim)

    def embed(self, texto: str) -> list[float]:
        resultado = self._model.embed(texto)
        # llama-cpp pode retornar list[float] ou list[list[float]]
        if resultado and isinstance(resultado[0], list):
            return resultado[0]
        return resultado  # type: ignore[return-value]

    @property
    def dimensao(self) -> int:
        return self._dim

    @property
    def nome(self) -> str:
        return "semantico_llama"


# ──────────────────────────────────────────────────────────────────────────────
# Backend 2: TF-IDF com vocabulário expandido (fallback zero-dependência)
# ──────────────────────────────────────────────────────────────────────────────

STOPWORDS_PT: frozenset[str] = frozenset({
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "a", "o", "os", "as", "e", "é", "um", "uma", "uns", "umas",
    "para", "por", "com", "que", "se", "ao", "à", "ou", "mas",
    "tipo", "cor", "com", "sem", "sob", "sobre",
})


def _normalizar_texto(texto: str) -> str:
    """Lowercase + remove acentos."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _tokenizar(texto: str) -> list[str]:
    """Tokeniza texto removendo stopwords e tokens muito curtos."""
    import re
    texto_norm = _normalizar_texto(texto)
    tokens = re.split(r"[\s\W]+", texto_norm)
    return [t for t in tokens if t and len(t) >= 2 and t not in STOPWORDS_PT]


class TFIDFBackend:
    """Embedding TF-IDF com vocabulário derivado das descrições de categoria.

    Constrói um vocabulário global a partir do VOCABULARIO_CATEGORIAS e
    representa cada texto como um vetor TF-IDF normalizado (L2).
    É um fallback determinístico sem dependências externas.
    """

    def __init__(self, corpus: list[str]) -> None:
        """
        Args:
            corpus: Lista de textos que formam o vocabulário de referência.
        """
        self._vocabulario, self._idf = self._construir_vocabulario(corpus)
        self._dim = len(self._vocabulario)
        logger.info("TFIDFBackend inicializado: vocabulário=%d termos", self._dim)

    def _construir_vocabulario(
        self, corpus: list[str]
    ) -> tuple[list[str], dict[str, float]]:
        n = len(corpus)
        doc_freq: dict[str, int] = {}
        for texto in corpus:
            for token in set(_tokenizar(texto)):
                doc_freq[token] = doc_freq.get(token, 0) + 1

        idf = {
            termo: math.log(n / (1 + df)) + 1.0
            for termo, df in doc_freq.items()
        }
        vocabulario = sorted(idf.keys())
        return vocabulario, idf

    def embed(self, texto: str) -> list[float]:
        tokens = _tokenizar(texto)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        vetor = [tf.get(t, 0) * self._idf.get(t, 0.0) for t in self._vocabulario]

        # Normalização L2
        norma = math.sqrt(sum(v * v for v in vetor))
        if norma > 0:
            vetor = [v / norma for v in vetor]
        return vetor

    @property
    def dimensao(self) -> int:
        return self._dim

    @property
    def nome(self) -> str:
        return "semantico_tfidf"


# ──────────────────────────────────────────────────────────────────────────────
# Funções utilitárias
# ──────────────────────────────────────────────────────────────────────────────

def _similaridade_cosseno(v1: list[float], v2: list[float]) -> float:
    """Calcula similaridade de cosseno entre dois vetores."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norma1 = math.sqrt(sum(a * a for a in v1))
    norma2 = math.sqrt(sum(b * b for b in v2))
    if norma1 == 0 or norma2 == 0:
        return 0.0
    return round(min(dot / (norma1 * norma2), 1.0), 6)


# ──────────────────────────────────────────────────────────────────────────────
# Classificador Semântico principal
# ──────────────────────────────────────────────────────────────────────────────

class ClassificadorSemantico:
    """Classifica descrições de itens por similaridade semântica com categorias.

    Fluxo de inicialização:
    1. Tenta carregar llama-cpp-python com o modelo em LLAMA_MODEL_PATH.
    2. Se não disponível, usa TFIDFBackend como fallback automático.

    Os embeddings das categorias são pré-computados uma vez no __init__ e
    reutilizados em todas as classificações (operação O(1) por lookup).
    """

    # Score mínimo para aceitar uma classificação semântica
    SCORE_MINIMO: float = 0.15

    def __init__(
        self,
        categorias: list[dict[str, Any]] | None = None,
        model_path: str | None = None,
    ) -> None:
        """
        Args:
            categorias: Lista de dicts com 'id' e 'nome' das categorias do banco.
                        Se None, usa apenas VOCABULARIO_CATEGORIAS.
            model_path: Caminho para arquivo .gguf. Se None, lê LLAMA_MODEL_PATH.
        """
        self._cat_map: dict[str, int] = {}
        if categorias:
            for cat in categorias:
                self._cat_map[cat["nome"]] = cat["id"]

        # Inicializa o backend de embedding
        self._backend = self._inicializar_backend(model_path)

        # Pré-computa embeddings de todas as categorias
        self._embeddings_categorias: dict[str, list[float]] = {}
        for nome_cat, descricao in VOCABULARIO_CATEGORIAS.items():
            self._embeddings_categorias[nome_cat] = self._backend.embed(descricao)

        logger.info(
            "ClassificadorSemantico pronto: backend=%s, categorias=%d",
            self._backend.nome,
            len(self._embeddings_categorias),
        )

    def _inicializar_backend(self, model_path: str | None) -> EmbeddingBackend:
        """Tenta llama-cpp-python, cai para TF-IDF se não disponível."""
        caminho = model_path or os.environ.get("LLAMA_MODEL_PATH", "")
        if caminho and os.path.isfile(caminho):
            try:
                backend = LlamaCppBackend(caminho)
                logger.info("Usando backend llama-cpp-python: %s", caminho)
                return backend
            except Exception as exc:
                logger.warning(
                    "Falha ao carregar llama-cpp-python (%s), usando TF-IDF: %s",
                    caminho,
                    exc,
                )

        # Fallback: constrói corpus a partir dos vocabulários das categorias
        corpus = list(VOCABULARIO_CATEGORIAS.values())
        return TFIDFBackend(corpus)

    def classificar(self, descricao: str) -> dict[str, Any] | None:
        """Classifica uma descrição por similaridade semântica.

        Args:
            descricao: Texto da descrição do item.

        Returns:
            Dict com categoria_id, categoria_nome, score e metodo,
            ou None se nenhuma categoria atingir o score mínimo.
        """
        if not descricao or not descricao.strip():
            return None

        vetor_item = self._backend.embed(descricao)
        if not vetor_item:
            return None

        melhor_nome: str | None = None
        melhor_score: float = 0.0

        for nome_cat, vetor_cat in self._embeddings_categorias.items():
            score = _similaridade_cosseno(vetor_item, vetor_cat)
            if score > melhor_score:
                melhor_score = score
                melhor_nome = nome_cat

        if melhor_nome is None or melhor_score < self.SCORE_MINIMO:
            return None

        return {
            "categoria_id": self._cat_map.get(melhor_nome),
            "categoria_nome": melhor_nome,
            "score": round(melhor_score, 4),
            "metodo": self._backend.nome,
        }

    def classificar_lote(
        self, descricoes: list[str]
    ) -> list[dict[str, Any] | None]:
        """Classifica uma lista de descrições em lote.

        Args:
            descricoes: Lista de descrições de itens.

        Returns:
            Lista de resultados (None para itens não classificados).
        """
        return [self.classificar(d) for d in descricoes]

    @property
    def backend_nome(self) -> str:
        """Nome do backend em uso (para diagnóstico)."""
        return self._backend.nome


# ──────────────────────────────────────────────────────────────────────────────
# Classificador Híbrido (regex → semântico)
# ──────────────────────────────────────────────────────────────────────────────

class ClassificadorHibrido:
    """Combina ClassificadorRegex (rápido, preciso) com ClassificadorSemantico (abrangente).

    Fluxo:
    1. Tenta regex → retorna se score >= 0.8.
    2. Se regex falhar ou score < 0.8, tenta semântico.
    3. Retorna o melhor resultado entre os dois, ou None se nenhum classificar.

    Essa estratégia garante que os casos óbvios (capturados por regex) não
    sofram overhead de embedding, enquanto os casos difíceis são cobertos
    pelo classificador semântico.
    """

    def __init__(
        self,
        categorias: list[dict[str, Any]] | None = None,
        model_path: str | None = None,
    ) -> None:
        from app.services.classificador_regex import ClassificadorRegex

        self._regex = ClassificadorRegex(categorias=categorias)
        self._semantico = ClassificadorSemantico(
            categorias=categorias, model_path=model_path
        )

    def classificar(self, descricao: str) -> dict[str, Any] | None:
        """Classifica usando regex primeiro, semântico como fallback.

        Args:
            descricao: Texto da descrição do item.

        Returns:
            Melhor resultado disponível ou None.
        """
        resultado_regex = self._regex.classificar(descricao)

        # Regex com alta confiança → retorna direto
        if resultado_regex and resultado_regex["score"] >= 0.8:
            return resultado_regex

        # Tenta semântico
        resultado_semantico = self._semantico.classificar(descricao)

        # Escolhe o melhor entre os dois
        candidatos = [r for r in [resultado_regex, resultado_semantico] if r]
        if not candidatos:
            return None

        return max(candidatos, key=lambda r: r["score"])

    def classificar_lote(
        self, descricoes: list[str]
    ) -> list[dict[str, Any] | None]:
        """Classifica uma lista de descrições."""
        return [self.classificar(d) for d in descricoes]
