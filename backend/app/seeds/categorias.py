"""Seeds de 50 categorias prioritárias para compras municipais."""

CATEGORIAS: list[dict[str, str]] = [
    # TIC
    {"nome": "Computador Desktop", "familia": "TIC", "descricao": "Computadores de mesa e workstations"},
    {"nome": "Notebook", "familia": "TIC", "descricao": "Computadores portáteis"},
    {"nome": "Monitor", "familia": "TIC", "descricao": "Monitores e telas para computador"},
    {"nome": "Impressora", "familia": "TIC", "descricao": "Impressoras laser e jato de tinta"},
    {"nome": "Câmera de Segurança", "familia": "TIC", "descricao": "Câmeras de videomonitoramento e CFTV"},
    {"nome": "Drone", "familia": "TIC", "descricao": "Veículos aéreos não tripulados"},
    {"nome": "Switch de Rede", "familia": "TIC", "descricao": "Switches e equipamentos de rede"},
    {"nome": "Software e Licenças", "familia": "TIC", "descricao": "Licenciamento de software e sistemas"},
    {"nome": "Nobreak/UPS", "familia": "TIC", "descricao": "Nobreaks e estabilizadores"},
    {"nome": "Projetor Multimídia", "familia": "TIC", "descricao": "Projetores para apresentações"},

    # Material de escritório
    {"nome": "Papel A4", "familia": "Material de Escritório", "descricao": "Papel sulfite A4 75g/m²"},
    {"nome": "Caneta Esferográfica", "familia": "Material de Escritório", "descricao": "Canetas esferográficas diversas"},
    {"nome": "Toner para Impressora", "familia": "Material de Escritório", "descricao": "Toners e cartuchos de tinta"},
    {"nome": "Cartucho de Tinta", "familia": "Material de Escritório", "descricao": "Cartuchos para impressoras jato de tinta"},
    {"nome": "Envelope", "familia": "Material de Escritório", "descricao": "Envelopes diversos tamanhos"},

    # Limpeza e higiene
    {"nome": "Detergente", "familia": "Limpeza e Higiene", "descricao": "Detergente líquido e em pó"},
    {"nome": "Álcool Gel", "familia": "Limpeza e Higiene", "descricao": "Álcool gel 70% para higienização"},
    {"nome": "Papel Higiênico", "familia": "Limpeza e Higiene", "descricao": "Papel higiênico folha simples e dupla"},
    {"nome": "Desinfetante", "familia": "Limpeza e Higiene", "descricao": "Desinfetantes e sanitizantes"},
    {"nome": "Saco de Lixo", "familia": "Limpeza e Higiene", "descricao": "Sacos de lixo diversos tamanhos"},

    # Alimentação / merenda escolar
    {"nome": "Arroz", "familia": "Alimentação", "descricao": "Arroz tipo 1 e parboilizado"},
    {"nome": "Feijão", "familia": "Alimentação", "descricao": "Feijão carioca e preto"},
    {"nome": "Leite", "familia": "Alimentação", "descricao": "Leite integral e desnatado UHT"},
    {"nome": "Óleo de Soja", "familia": "Alimentação", "descricao": "Óleo de soja refinado"},
    {"nome": "Açúcar", "familia": "Alimentação", "descricao": "Açúcar cristal e refinado"},

    # Mobiliário
    {"nome": "Cadeira de Escritório", "familia": "Mobiliário", "descricao": "Cadeiras giratórias e fixas para escritório"},
    {"nome": "Mesa de Escritório", "familia": "Mobiliário", "descricao": "Mesas e estações de trabalho"},
    {"nome": "Armário de Aço", "familia": "Mobiliário", "descricao": "Armários e arquivos de aço"},
    {"nome": "Estante Metálica", "familia": "Mobiliário", "descricao": "Estantes e prateleiras metálicas"},
    {"nome": "Carteira Escolar", "familia": "Mobiliário", "descricao": "Carteiras e conjuntos para sala de aula"},

    # Combustíveis
    {"nome": "Gasolina Comum", "familia": "Combustíveis", "descricao": "Gasolina comum automotiva"},
    {"nome": "Diesel S10", "familia": "Combustíveis", "descricao": "Óleo diesel S10"},
    {"nome": "Etanol", "familia": "Combustíveis", "descricao": "Etanol hidratado automotivo"},

    # Saúde
    {"nome": "Luva de Procedimento", "familia": "Saúde", "descricao": "Luvas descartáveis para procedimentos"},
    {"nome": "Seringa Descartável", "familia": "Saúde", "descricao": "Seringas descartáveis diversos volumes"},
    {"nome": "Medicamento Genérico", "familia": "Saúde", "descricao": "Medicamentos genéricos diversos"},
    {"nome": "Máscara Cirúrgica", "familia": "Saúde", "descricao": "Máscaras cirúrgicas descartáveis"},
    {"nome": "Material Odontológico", "familia": "Saúde", "descricao": "Insumos e materiais odontológicos"},

    # Construção / manutenção predial
    {"nome": "Cimento Portland", "familia": "Construção", "descricao": "Cimento Portland CP-II e CP-IV"},
    {"nome": "Tinta Acrílica", "familia": "Construção", "descricao": "Tintas acrílicas para parede"},
    {"nome": "Tubo PVC", "familia": "Construção", "descricao": "Tubos e conexões PVC"},
    {"nome": "Fio Elétrico", "familia": "Construção", "descricao": "Fios e cabos elétricos"},
    {"nome": "Lâmpada LED", "familia": "Construção", "descricao": "Lâmpadas LED diversas potências"},

    # Serviços
    {"nome": "Serviço de Limpeza", "familia": "Serviços", "descricao": "Prestação de serviço de limpeza e conservação"},
    {"nome": "Serviço de Vigilância", "familia": "Serviços", "descricao": "Prestação de serviço de vigilância patrimonial"},
    {"nome": "Serviço de TI", "familia": "Serviços", "descricao": "Suporte técnico e manutenção de TI"},
    {"nome": "Serviço de Manutenção Predial", "familia": "Serviços", "descricao": "Manutenção preventiva e corretiva predial"},
    {"nome": "Serviço de Transporte", "familia": "Serviços", "descricao": "Locação de veículos e transporte"},

    # Uniformes / EPIs
    {"nome": "Uniforme Escolar", "familia": "Uniformes e EPIs", "descricao": "Camisetas e conjuntos para uniformes escolares"},
    {"nome": "Bota de Segurança", "familia": "Uniformes e EPIs", "descricao": "Botas e calçados de segurança"},
    {"nome": "Capacete de Segurança", "familia": "Uniformes e EPIs", "descricao": "Capacetes de proteção individual"},
]


def get_categorias() -> list[dict[str, str]]:
    """Retorna a lista de categorias prioritárias para seed."""
    return CATEGORIAS
