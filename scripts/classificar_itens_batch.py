"""Script de classificação batch de itens sem categoria.

Busca todos os itens sem categoria no banco e aplica o ClassificadorRegex.
Insere resultados em item_categoria.
"""
import sys
import os

# Adiciona o backend ao path para importar o classificador
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import psycopg2
from psycopg2.extras import execute_batch
import unicodedata
import re
from typing import Any

DSN = "postgresql://bancodeprecos:bancodeprecos_dev@localhost:5435/bancodeprecos"


def _strip_accents(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Regras de classificação inline (espelho do classificador_regex.py)
REGRAS = [
    # Papel A4
    (re.compile(r"\bPAPEL\s+(SULFITE\s+)?A4\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+(SULFITE\s+)?OFICIO\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+(PARA\s+)?COPIA\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+SULFITE\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+REPROGRAFIA\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+XEROX\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\s+IMPRESSAO\b", re.IGNORECASE), "Papel A4", True),
    (re.compile(r"\bPAPEL\b.*\b(75\s*G|75\s*GR|90\s*G|90\s*GR)\b", re.IGNORECASE), "Papel A4", False),
    # Limpeza
    (re.compile(r"\bDETERGENTE\b", re.IGNORECASE), "Material de Limpeza Geral", True),
    (re.compile(r"\bSABAO\b|\bSABONETE\b", re.IGNORECASE), "Material de Limpeza Geral", False),
    (re.compile(r"\bALCOOL\s*GEL\b|\bALCOOL\s*70\b", re.IGNORECASE), "Material de Limpeza Geral", True),
    (re.compile(r"\bDESINFETANTE\b|\bHIPOCLORITO\b|\bAGUA\s+SANITARIA\b", re.IGNORECASE), "Material de Limpeza Geral", True),
    (re.compile(r"\bVASSOURA\b|\bRODO\b|\bBALDE\b|\bESPONJA\b|\bPANO\s*(DE\s+)?CHAO\b", re.IGNORECASE), "Material de Limpeza Geral", False),
    (re.compile(r"\bLIMP(A|ADOR|EZA)\b", re.IGNORECASE), "Material de Limpeza Geral", False),
    (re.compile(r"\bPISCINA\b", re.IGNORECASE), "Material de Limpeza Geral", False),
    # Combustíveis
    (re.compile(r"\bGASOLINA\b", re.IGNORECASE), "Combustível (Gasolina / Etanol / Diesel)", True),
    (re.compile(r"\bETANOL\b|\bALCOOL\s+COMBUSTIVEL\b", re.IGNORECASE), "Combustível (Gasolina / Etanol / Diesel)", True),
    (re.compile(r"\bDIESEL\b|\bOLEO\s+DIESEL\b", re.IGNORECASE), "Combustível (Gasolina / Etanol / Diesel)", True),
    (re.compile(r"\bARLA\s*32\b", re.IGNORECASE), "Combustível (Gasolina / Etanol / Diesel)", False),
    # Toner/Cartucho
    (re.compile(r"\bTONER\b", re.IGNORECASE), "Cartucho / Toner", True),
    (re.compile(r"\bCARTUCHO\b", re.IGNORECASE), "Cartucho / Toner", True),
    (re.compile(r"\bRIBBON\b|\bREFIL\s*(DE\s+)?TINTA\b", re.IGNORECASE), "Cartucho / Toner", False),
    # Alimentos
    (re.compile(r"\bARROZ\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bFEIJAO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bACUCAR\b|\bAZUCAR\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bFARINHA\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bOLEO\s+(DE\s+)?SOJA\b|\bOLEO\s+VEGETAL\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bMASS[AÃ]\s*ALIMENTICIA\b|\bMACAR\b|\bMACARRAO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bSAL\s+(DE\s+)?COZINHA\b|\bSAL\s+REFINADO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bCAFE\s+(EM\s+)?PO\b|\bCAFE\s+TORRADO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bLEITE\s+(EM\s+)?PO\b|\bLEITE\s+(INTEGRAL|DESNATADO)\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bMERENDA\s+ESCOLAR\b|\bCESTA\s+BASICA\b|\bKIT\s+ALIMENT\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    # Água Mineral
    (re.compile(r"\bAGUA\s+MINERAL\b|\bAGUA\s+POTAVEL\b", re.IGNORECASE), "Água Mineral", True),
    (re.compile(r"\bGALAO\s+(DE\s+)?AGUA\b|\bGARRAFAO\b", re.IGNORECASE), "Água Mineral", False),
    # GLP
    (re.compile(r"\bGAS\s+(DE\s+)?COZINHA\b|\bGLP\b|\bGAS\s+LIQUEFEITO\b", re.IGNORECASE), "Gás de Cozinha (GLP)", True),
    (re.compile(r"\bBOTIJAO\s+(DE\s+)?GAS\b|\bBOTIJAO\s+GLP\b", re.IGNORECASE), "Gás de Cozinha (GLP)", True),
    # Material de escritório
    (re.compile(r"\bCANETA\b|\bLAPIS\b|\bBORRACHA\b|\bREGUA\b|\bCOMPASSO\b", re.IGNORECASE), "Material de Expediente Geral", True),
    (re.compile(r"\bCLIPE\b|\bGRAMPEADOR\b|\bGRAMPO\b|\bPERFURADOR\b", re.IGNORECASE), "Material de Expediente Geral", True),
    (re.compile(r"\bENVELOPE\b", re.IGNORECASE), "Envelopes e Formulários", True),
    (re.compile(r"\bETIQUETA\b", re.IGNORECASE), "Material de Expediente Geral", False),
    (re.compile(r"\bFITA\s+ADESIVA\b|\bDURATAPE\b|\bFITA\s+CREPE\b", re.IGNORECASE), "Material de Expediente Geral", False),
    # Informática
    (re.compile(r"\bCOMPUTADOR\b|\bDESKTOP\b|\bMICROCOMPUTADOR\b", re.IGNORECASE), "Computador Desktop", True),
    (re.compile(r"\bNOTEBOOK\b|\bLAPTOP\b", re.IGNORECASE), "Computador Desktop", True),
    (re.compile(r"\bIMPRESSORA\b", re.IGNORECASE), "Impressora", True),
    (re.compile(r"\bNOBREAK\b|\bUPS\b|\bFONTE\s+(DE\s+)?ENERGIA\b", re.IGNORECASE), "Nobreak / UPS", True),
    # Material elétrico
    (re.compile(r"\bFIO\s+ELETRICO\b|\bCABO\s+ELETRICO\b|\bFIO\s+COBRE\b", re.IGNORECASE), "Material Elétrico", True),
    (re.compile(r"\bDISJUNTOR\b|\bTOMBEAR\b|\bTOMADA\b|\bINTERRUPTOR\b", re.IGNORECASE), "Material Elétrico", True),
    (re.compile(r"\bLAMPADA\b|\bLED\s+\d+W\b|\bLAMPADA\s+LED\b", re.IGNORECASE), "Material Elétrico", True),
    (re.compile(r"\bELETRICO\b|\bELETRICAL\b", re.IGNORECASE), "Material Elétrico", False),
    # Material hidráulico
    (re.compile(r"\bCANO\s+PVC\b|\bTUBO\s+PVC\b|\bCOTOVELO\b|\bJOELHO\b|\bTEE\s+PVC\b", re.IGNORECASE), "Material Hidráulico", True),
    (re.compile(r"\bREGISTRO\s+(DE\s+)?AGUA\b|\bVALVULA\b|\bTORNEIRA\b", re.IGNORECASE), "Material Hidráulico", True),
    # Mobiliário
    (re.compile(r"\bMESA\s+(DE\s+)?(ESCRITORIO|REUNIAO|TRABALHO)\b", re.IGNORECASE), "Mesa / Cadeira de Escritório", True),
    (re.compile(r"\bCADEIRA\s+(DE\s+)?(ESCRITORIO|GIRATORIA|PLASTICA)\b", re.IGNORECASE), "Mesa / Cadeira de Escritório", True),
    (re.compile(r"\bARMARIO\b|\bARQUIVO\s+(DE\s+)?ACO\b", re.IGNORECASE), "Armário / Arquivo", True),
    (re.compile(r"\bMOBILIARIO\s+ESCOLAR\b|\bCARTEIRA\s+ESCOLAR\b|\bBELICHE\b", re.IGNORECASE), "Mobiliário Escolar", True),
    # EPI
    (re.compile(r"\bEPI\b|\bEQUIPAMENTO\s+(DE\s+)?PROTECAO\b|\bCAPA\s+DE\s+CHUVA\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", True),
    (re.compile(r"\bLUVA\s+(DE\s+)?NITRILA\b|\bLUVA\s+CIRURGICA\b|\bLUVA\s+LATEX\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", True),
    (re.compile(r"\bMASCARA\s+(CIRURGICA|N95|PFF2)\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", True),
    (re.compile(r"\bCAPACETE\b|\bBOTA\s+(DE\s+)?(BORRACHA|SEGURANCA)\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", True),
    # Medicamentos
    (re.compile(r"\bMEDICAMENTO\b|\bFARMACO\b|\bCOMPRIMIDO\b|\bCAPS[UÚ]LA\b", re.IGNORECASE), "Medicamentos Básicos (OTC)", True),
    (re.compile(r"\bFARMACIA\b|\bDROGARIA\b", re.IGNORECASE), "Medicamentos Básicos (OTC)", False),
    # Material hospitalar
    (re.compile(r"\bSERINGA\b|\bAGULHA\s+HIPOD\b|\bGAZE\b|\bATALHO\b|\bESTETOSCOPIO\b", re.IGNORECASE), "Material Hospitalar / Descartáveis Médicos", True),
    (re.compile(r"\bCATETER\b|\bSONDA\b|\bDRENO\b", re.IGNORECASE), "Material Hospitalar / Descartáveis Médicos", True),
    # Câmera / CFTV
    (re.compile(r"\bCAMERA\s+(DE\s+)?SEGURANCA\b|\bCFTV\b|\bDOME\s+CAMERA\b|\bBULLET\s+CAMERA\b", re.IGNORECASE), "Câmera de Segurança (CFTV)", True),
    (re.compile(r"\bDVR\b|\bNVR\b", re.IGNORECASE), "DVR / NVR", True),
    # Outros
    (re.compile(r"\bDRONE\b|\bVANT\b|\bUAV\b", re.IGNORECASE), "Drone / UAV", True),
    (re.compile(r"\bINSTRUMENTO\s+MUSICAL\b|\bVIOLAO\b|\bGUITARRA\b|\bTECLADO\s+MUSICAL\b", re.IGNORECASE), "Instrumento Musical", True),
    (re.compile(r"\bCIMENTO\b", re.IGNORECASE), "Cimento / Areia / Brita", True),
    (re.compile(r"\bARE(I|Ã)A\s+(GROSSA|FINA|MEDIA)\b|\bBRITA\b", re.IGNORECASE), "Cimento / Areia / Brita", True),
    (re.compile(r"\bKIT\s+(DE\s+)?PRIMEIROS?\s+SOCORROS\b|\bDEFIBRILADOR\b", re.IGNORECASE), "Kit de Primeiros Socorros", True),
    (re.compile(r"\bTRAJE\s+(DE\s+)?ESPORT\b|\bCHUTEIRA\b|\bBOLA\s+DE\b|\bCHUTEIRA\b|\bKIT\s+ESPORT\b", re.IGNORECASE), "Material Esportivo", True),
    # Cabo/Rede
    (re.compile(r"\bCABO\s+HDMI\b|\bCABO\s+VGA\b|\bCABO\s+USB\b|\bCABO\s+REDE\b", re.IGNORECASE), "Material Elétrico", False),
    (re.compile(r"\bRJ45\b|\bPATCH\s+CORD\b|\bCABO\s+UTP\b|\bCABO\s+CAT5\b|\bCABO\s+CAT6\b", re.IGNORECASE), "Material Elétrico", False),
    (re.compile(r"\bCABO\s+DE\s+FORCA\b|\bCABO\s+DE\s+REDE\b", re.IGNORECASE), "Material Elétrico", False),
    # Ferramentas
    (re.compile(r"\bPARAFUSADEIRA\b|\bFURADEIRA\b|\bSERRA\b|\bMARTELO\b|\bCHAVE\s+DE\b", re.IGNORECASE), "Material Elétrico", False),
    # Abraçadeiras / fixadores (hidráulico/elétrico)
    (re.compile(r"\bABRACAdEIRA\b|\bABRACADEIRA\b|\bARRUELA\b|\bPARAFUSO\b|\bPORC[AÃ]\b", re.IGNORECASE), "Material Hidráulico", False),
    (re.compile(r"\bCONECTOR\b|\bADAPTADOR\b", re.IGNORECASE), "Material Elétrico", False),
    # Alimentação (carne, frios, produtos alimentícios)
    (re.compile(r"\bCARNE\s+BOVINA\b|\bCARNE\s+SUINA\b|\bCARNE\s+DE\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bFRANGO\b|\bPEITO\s+DE\s+FRANGO\b|\bCOXA\b|\bFRANGO\s+INTEIRO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bBACON\b|\bAPRESUNTADO\b|\bLINGUICA\b|\bSALSICHA\b|\bPRESUNTO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bCOSTELA\b|\bPALETA\s+(BOVINA|SUINA|DESOSSADA)\b|\bPES\s+SUINOS\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bMARGARINA\b|\bMANTEIGA\b|\bEXTRATO\s+DE\s+TOMATE\b|\bSARDINHA\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bACHOCOLATADO\b|\bNESQUIK\b|\bLEITE\s+CONDENSADO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bBOLACHA\b|\bBISCOITO\b|\bMIPIPOCA\b|\bMILHO\s+DE\s+PIPOCA\b|\bPIPOCA\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    (re.compile(r"\bSAQUINHO\s+PARA\s+PIPOCA\b|\bPALITO\s+PARA\s+ALGODAO\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", False),
    (re.compile(r"\bCAFE\s+\d+\s*(G|GR|KG)\b|\bCAFE\s+PACOTE\b", re.IGNORECASE), "Gêneros Alimentícios (Merenda Escolar)", True),
    # Estabilizadores / nobreak
    (re.compile(r"\bESTABILIZADOR\s+DE\s+TENSAO\b|\bESTABILIZADOR\s+\d+\s*VA\b", re.IGNORECASE), "Nobreak / UPS", True),
    (re.compile(r"\bAUTOTRANSFORMADOR\b|\bTRANSFORMADOR\s+DE\s+VOLTAGEM\b", re.IGNORECASE), "Nobreak / UPS", False),
    (re.compile(r"\bFILTRO\s+DE\s+LINHA\b|\bFILTRO\s+ANTI\s*PICO\b", re.IGNORECASE), "Nobreak / UPS", False),
    # Informática / periféricos
    (re.compile(r"\bPEN\s+DRIVE\b|\bPENDRIVE\b|\bFLASH\s+USB\b", re.IGNORECASE), "Computador Desktop", False),
    (re.compile(r"\bADAPTADOR\s+WI.?FI\b|\bWI.?FI\s+USB\b|\bWI.?FI\s+NANO\b", re.IGNORECASE), "Computador Desktop", False),
    # Papelaria / escritório
    (re.compile(r"\bCARTAO\s+DE\s+VISITA\b|\bADESIVO\s+PARA\s+CAMPANHA\b|\bADESIVOS\b", re.IGNORECASE), "Material de Expediente Geral", False),
    (re.compile(r"\bALMOFADA\s+PARA\s+CARIMBO\b|\bCAMBO\b|\bREFORCO\s+AUTO\b|\bREFORCO\s+ADESIVO\b", re.IGNORECASE), "Material de Expediente Geral", False),
    (re.compile(r"\bESTILETE\b|\bTESOURA\b", re.IGNORECASE), "Material de Expediente Geral", False),
    # Roupas / uniformes
    (re.compile(r"\bCAMISETA\b|\bCAMISA\b|\bCONJUNTO\s+UNIFORME\b|\bUNIFORME\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", False),
    # Padrão trifásico / elétrico industrial
    (re.compile(r"\bPADRAO\s+TRIFASICO\b|\bPADRAO\s+MONOFASICO\b|\bBIFASICO\b", re.IGNORECASE), "Material Elétrico", False),
    (re.compile(r"\bCAPA\s+\d+\s*/\s*\d+SN\b|\bCAPA\s+[0-9½¾]+\b", re.IGNORECASE), "Material Hidráulico", False),
    # Serviços de engenharia/saúde do trabalho
    (re.compile(r"\bENGENHARIA\s+DE\s+SEGURANCA\b|\bMEDICINA\s+DO\s+TRABALHO\b|\bPPCMSO\b|\bPGR\b", re.IGNORECASE), "EPI (Equipamento de Proteção Individual)", False),
]


def classificar(descricao: str, cat_map: dict) -> dict | None:
    if not descricao:
        return None
    texto = _strip_accents(descricao.upper())
    for pattern, categoria_nome, exato in REGRAS:
        if pattern.search(texto):
            cat_id = cat_map.get(categoria_nome)
            if cat_id:
                return {
                    "categoria_id": cat_id,
                    "categoria_nome": categoria_nome,
                    "score": 1.0 if exato else 0.8,
                }
    return None


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    # Buscar mapa de categorias
    cur.execute("SELECT id, nome FROM categorias")
    cat_map = {nome: str(cid) for cid, nome in cur.fetchall()}
    print(f"Categorias carregadas: {len(cat_map)}")

    # Buscar itens sem categoria
    cur.execute("""
        SELECT i.id, i.descricao FROM itens i
        LEFT JOIN item_categoria ic ON ic.item_id = i.id
        WHERE ic.item_id IS NULL
        AND i.descricao IS NOT NULL
    """)
    itens = cur.fetchall()
    print(f"Itens sem categoria: {len(itens)}")

    inseridos = 0
    nao_classificados = 0
    batch = []

    for item_id, descricao in itens:
        resultado = classificar(descricao, cat_map)
        if resultado:
            batch.append((str(item_id), resultado["categoria_id"]))
            inseridos += 1
        else:
            nao_classificados += 1

        if len(batch) >= 100:
            execute_batch(cur, """
                INSERT INTO item_categoria (item_id, categoria_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, batch)
            conn.commit()
            print(f"  Batch inserido: {len(batch)} registros")
            batch = []

    if batch:
        execute_batch(cur, """
            INSERT INTO item_categoria (item_id, categoria_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, batch)
        conn.commit()
        print(f"  Batch final: {len(batch)} registros")

    print(f"\nResultado:")
    print(f"  Classificados: {inseridos}")
    print(f"  Sem correspondência: {nao_classificados}")

    # Verificar resultado final
    cur.execute("SELECT COUNT(*) FROM item_categoria")
    total = cur.fetchone()[0]
    print(f"  Total em item_categoria: {total}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
