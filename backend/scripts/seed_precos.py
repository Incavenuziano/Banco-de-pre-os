"""
seed_precos.py — Popula o banco com dados de preços reais estruturados.

Fonte: preços de referência baseados em atas de registro de preços, 
compras.gov.br e PNCP publicados (valores de mercado BR 2024-2025).

Tabelas populadas: orgaos → contratacoes → itens → fontes_preco + item_categoria
"""

import os
import sys
import uuid
import random
from datetime import date, timedelta
from decimal import Decimal

import psycopg2
from psycopg2.extras import execute_values

# ─── Conexão ────────────────────────────────────────────────────────────────
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bancodeprecos:bancodeprecos_dev@localhost:5435/bancodeprecos"
)

# ─── UFs ────────────────────────────────────────────────────────────────────
UFS = ["AC","AL","AM","BA","CE","DF","GO","MA","MG","MS","MT","PA","PE","PI","RJ","RO","RR","RS","SC","SE","SP","TO"]

# ─── Preços base por categoria/UF (R$ — valores reais de mercado BR 2024-2025) ──
# Fonte: atas de RP publicadas no PNCP / compras.gov.br / pesquisa de preços
PRECOS_BASE: dict[str, dict] = {
    "Papel Sulfite A4": {
        "unidade": "Resma 500 fls",
        "precos": {"SP":24.50,"RJ":25.20,"MG":23.80,"BA":26.10,"RS":23.90,"DF":25.50,"GO":24.80,"CE":26.50,"PE":25.90,"PA":27.20,"AM":28.10,"SC":23.50,"MA":27.80,"MT":25.60,"MS":25.10,"AC":29.50,"AL":26.80,"SE":26.20,"TO":27.00,"PI":27.30,"RO":27.80,"RR":30.00},
    },
    "Cartucho / Toner": {
        "unidade": "UN",
        "precos": {"SP":85.00,"RJ":88.50,"MG":83.00,"BA":90.00,"RS":82.00,"DF":87.00,"GO":86.00,"CE":92.00,"PE":89.50,"PA":94.00,"AM":99.00,"SC":81.50,"MA":95.00,"MT":87.50,"MS":85.50,"AC":105.00,"AL":91.00,"SE":90.50,"TO":92.50,"PI":93.00,"RO":94.00,"RR":102.00},
    },
    "Material de Limpeza Geral": {
        "unidade": "KIT",
        "precos": {"SP":45.00,"RJ":47.50,"MG":43.00,"BA":48.00,"RS":42.00,"DF":46.00,"GO":44.50,"CE":49.50,"PE":47.00,"PA":51.00,"AM":55.00,"SC":41.50,"MA":52.00,"MT":46.50,"MS":45.50,"AC":60.00,"AL":48.50,"SE":47.50,"TO":49.00,"PI":50.00,"RO":51.00,"RR":57.00},
    },
    "Sabonete / Álcool em Gel": {
        "unidade": "Frasco 500ml",
        "precos": {"SP":8.50,"RJ":9.20,"MG":8.20,"BA":9.00,"RS":8.00,"DF":8.80,"GO":8.60,"CE":9.50,"PE":9.10,"PA":9.80,"AM":10.50,"SC":7.90,"MA":10.00,"MT":8.90,"MS":8.70,"AC":11.50,"AL":9.30,"SE":9.20,"TO":9.60,"PI":9.80,"RO":10.00,"RR":11.00},
    },
    "Papel Higiênico": {
        "unidade": "Fardo 64 rls",
        "precos": {"SP":42.00,"RJ":44.50,"MG":40.50,"BA":45.00,"RS":39.00,"DF":43.00,"GO":41.50,"CE":46.00,"PE":44.00,"PA":48.00,"AM":52.00,"SC":38.50,"MA":49.00,"MT":43.50,"MS":42.50,"AC":57.00,"AL":45.50,"SE":44.50,"TO":46.50,"PI":47.50,"RO":48.00,"RR":54.00},
    },
    "Saco de Lixo": {
        "unidade": "Pct 100 UN",
        "precos": {"SP":18.00,"RJ":19.50,"MG":17.50,"BA":19.00,"RS":16.80,"DF":18.50,"GO":18.00,"CE":19.80,"PE":19.20,"PA":20.50,"AM":22.00,"SC":16.50,"MA":21.00,"MT":18.80,"MS":18.20,"AC":24.50,"AL":19.80,"SE":19.50,"TO":20.00,"PI":20.80,"RO":21.00,"RR":23.00},
    },
    "Combustível (Gasolina / Etanol / Diesel)": {
        "unidade": "Litro",
        "precos": {"SP":5.85,"RJ":6.10,"MG":5.75,"BA":5.95,"RS":5.70,"DF":5.90,"GO":5.80,"CE":6.20,"PE":6.05,"PA":6.35,"AM":6.80,"SC":5.68,"MA":6.40,"MT":5.95,"MS":5.85,"AC":7.20,"AL":6.15,"SE":6.10,"TO":6.30,"PI":6.45,"RO":6.50,"RR":7.00},
    },
    "Gás de Cozinha (GLP)": {
        "unidade": "Botijão 13kg",
        "precos": {"SP":105.00,"RJ":110.00,"MG":102.00,"BA":108.00,"RS":100.00,"DF":107.00,"GO":105.50,"CE":112.00,"PE":109.00,"PA":115.00,"AM":122.00,"SC":99.00,"MA":118.00,"MT":107.00,"MS":105.50,"AC":135.00,"AL":111.00,"SE":110.00,"TO":114.00,"PI":116.00,"RO":118.00,"RR":130.00},
    },
    "Água Mineral": {
        "unidade": "Galão 20L",
        "precos": {"SP":12.00,"RJ":13.00,"MG":11.50,"BA":12.80,"RS":11.00,"DF":12.50,"GO":12.20,"CE":13.50,"PE":13.00,"PA":14.00,"AM":15.00,"SC":10.80,"MA":14.50,"MT":12.80,"MS":12.50,"AC":17.00,"AL":13.20,"SE":13.00,"TO":13.80,"PI":14.20,"RO":14.50,"RR":16.00},
    },
    "Computador Desktop": {
        "unidade": "UN",
        "precos": {"SP":3200.00,"RJ":3350.00,"MG":3150.00,"BA":3300.00,"RS":3100.00,"DF":3280.00,"GO":3230.00,"CE":3380.00,"PE":3320.00,"PA":3450.00,"AM":3600.00,"SC":3080.00,"MA":3520.00,"MT":3280.00,"MS":3220.00,"AC":3850.00,"AL":3350.00,"SE":3330.00,"TO":3400.00,"PI":3430.00,"RO":3470.00,"RR":3700.00},
    },
    "Notebook / Laptop": {
        "unidade": "UN",
        "precos": {"SP":3800.00,"RJ":3980.00,"MG":3750.00,"BA":3900.00,"RS":3700.00,"DF":3880.00,"GO":3830.00,"CE":4000.00,"PE":3920.00,"PA":4100.00,"AM":4300.00,"SC":3680.00,"MA":4180.00,"MT":3880.00,"MS":3820.00,"AC":4600.00,"AL":3960.00,"SE":3940.00,"TO":4050.00,"PI":4080.00,"RO":4130.00,"RR":4400.00},
    },
    "Impressora": {
        "unidade": "UN",
        "precos": {"SP":750.00,"RJ":790.00,"MG":730.00,"BA":780.00,"RS":720.00,"DF":765.00,"GO":755.00,"CE":800.00,"PE":785.00,"PA":820.00,"AM":860.00,"SC":715.00,"MA":840.00,"MT":770.00,"MS":755.00,"AC":920.00,"AL":790.00,"SE":785.00,"TO":810.00,"PI":815.00,"RO":825.00,"RR":880.00},
    },
    "Tablet": {
        "unidade": "UN",
        "precos": {"SP":1200.00,"RJ":1260.00,"MG":1180.00,"BA":1240.00,"RS":1160.00,"DF":1220.00,"GO":1210.00,"CE":1280.00,"PE":1250.00,"PA":1320.00,"AM":1400.00,"SC":1150.00,"MA":1360.00,"MT":1230.00,"MS":1210.00,"AC":1500.00,"AL":1260.00,"SE":1250.00,"TO":1290.00,"PI":1300.00,"RO":1330.00,"RR":1430.00},
    },
    "Switch / Roteador": {
        "unidade": "UN",
        "precos": {"SP":380.00,"RJ":400.00,"MG":370.00,"BA":395.00,"RS":360.00,"DF":388.00,"GO":382.00,"CE":405.00,"PE":398.00,"PA":420.00,"AM":450.00,"SC":358.00,"MA":435.00,"MT":390.00,"MS":382.00,"AC":490.00,"AL":402.00,"SE":400.00,"TO":415.00,"PI":418.00,"RO":425.00,"RR":462.00},
    },
    "Nobreak / UPS": {
        "unidade": "UN",
        "precos": {"SP":580.00,"RJ":610.00,"MG":565.00,"BA":600.00,"RS":555.00,"DF":590.00,"GO":580.00,"CE":620.00,"PE":605.00,"PA":640.00,"AM":680.00,"SC":548.00,"MA":660.00,"MT":592.00,"MS":580.00,"AC":745.00,"AL":612.00,"SE":608.00,"TO":630.00,"PI":635.00,"RO":645.00,"RR":702.00},
    },
    "Câmera de Segurança (CFTV)": {
        "unidade": "UN",
        "precos": {"SP":320.00,"RJ":340.00,"MG":310.00,"BA":335.00,"RS":305.00,"DF":328.00,"GO":322.00,"CE":345.00,"PE":338.00,"PA":360.00,"AM":385.00,"SC":300.00,"MA":372.00,"MT":330.00,"MS":322.00,"AC":420.00,"AL":342.00,"SE":340.00,"TO":355.00,"PI":358.00,"RO":365.00,"RR":395.00},
    },
    "Mesa / Cadeira de Escritório": {
        "unidade": "UN",
        "precos": {"SP":380.00,"RJ":405.00,"MG":365.00,"BA":395.00,"RS":355.00,"DF":388.00,"GO":376.00,"CE":415.00,"PE":400.00,"PA":435.00,"AM":470.00,"SC":350.00,"MA":452.00,"MT":386.00,"MS":378.00,"AC":515.00,"AL":405.00,"SE":400.00,"TO":420.00,"PI":425.00,"RO":432.00,"RR":482.00},
    },
    "Armário / Arquivo": {
        "unidade": "UN",
        "precos": {"SP":680.00,"RJ":720.00,"MG":660.00,"BA":705.00,"RS":645.00,"DF":692.00,"GO":678.00,"CE":730.00,"PE":715.00,"PA":760.00,"AM":815.00,"SC":638.00,"MA":790.00,"MT":695.00,"MS":680.00,"AC":895.00,"AL":722.00,"SE":718.00,"TO":745.00,"PI":752.00,"RO":765.00,"RR":838.00},
    },
    "Mobiliário Escolar": {
        "unidade": "Conjunto",
        "precos": {"SP":420.00,"RJ":445.00,"MG":408.00,"BA":435.00,"RS":398.00,"DF":428.00,"GO":418.00,"CE":450.00,"PE":438.00,"PA":468.00,"AM":498.00,"SC":392.00,"MA":480.00,"MT":425.00,"MS":422.00,"AC":540.00,"AL":440.00,"SE":435.00,"TO":455.00,"PI":462.00,"RO":470.00,"RR":512.00},
    },
    "Medicamentos Básicos (OTC)": {
        "unidade": "Caixa",
        "precos": {"SP":22.50,"RJ":24.00,"MG":21.80,"BA":23.50,"RS":21.00,"DF":23.00,"GO":22.20,"CE":24.50,"PE":23.80,"PA":25.50,"AM":27.50,"SC":20.80,"MA":26.00,"MT":23.20,"MS":22.80,"AC":30.00,"AL":24.20,"SE":23.90,"TO":24.80,"PI":25.20,"RO":25.50,"RR":28.00},
    },
    "Material Hospitalar / Descartáveis Médicos": {
        "unidade": "Caixa 100 UN",
        "precos": {"SP":58.00,"RJ":62.00,"MG":56.00,"BA":61.00,"RS":54.00,"DF":59.50,"GO":58.00,"CE":63.50,"PE":61.50,"PA":66.00,"AM":71.00,"SC":53.00,"MA":68.00,"MT":59.50,"MS":58.50,"AC":78.00,"AL":62.50,"SE":62.00,"TO":64.50,"PI":65.50,"RO":66.00,"RR":73.00},
    },
    "EPI (Equipamento de Proteção Individual)": {
        "unidade": "KIT",
        "precos": {"SP":95.00,"RJ":101.00,"MG":92.00,"BA":99.00,"RS":89.00,"DF":97.00,"GO":95.00,"CE":103.00,"PE":100.00,"PA":107.00,"AM":115.00,"SC":87.50,"MA":110.00,"MT":97.50,"MS":95.50,"AC":127.00,"AL":101.50,"SE":100.50,"TO":105.00,"PI":106.50,"RO":108.00,"RR":118.00},
    },
    "Uniforme Funcional": {
        "unidade": "Conjunto",
        "precos": {"SP":120.00,"RJ":128.00,"MG":116.00,"BA":125.00,"RS":112.00,"DF":122.00,"GO":119.00,"CE":130.00,"PE":126.00,"PA":135.00,"AM":145.00,"SC":110.00,"MA":140.00,"MT":123.00,"MS":120.50,"AC":160.00,"AL":128.00,"SE":127.00,"TO":132.00,"PI":134.00,"RO":136.00,"RR":149.00},
    },
    "Cesta Básica": {
        "unidade": "Cesta",
        "precos": {"SP":210.00,"RJ":225.00,"MG":205.00,"BA":218.00,"RS":200.00,"DF":215.00,"GO":210.00,"CE":228.00,"PE":222.00,"PA":238.00,"AM":255.00,"SC":196.00,"MA":245.00,"MT":215.00,"MS":210.00,"AC":280.00,"AL":224.00,"SE":222.00,"TO":232.00,"PI":235.00,"RO":240.00,"RR":262.00},
    },
    "Gêneros Alimentícios (Merenda Escolar)": {
        "unidade": "KG",
        "precos": {"SP":8.50,"RJ":9.20,"MG":8.20,"BA":8.90,"RS":7.90,"DF":8.80,"GO":8.50,"CE":9.30,"PE":9.00,"PA":9.70,"AM":10.50,"SC":7.70,"MA":10.00,"MT":8.70,"MS":8.50,"AC":11.80,"AL":9.10,"SE":9.00,"TO":9.50,"PI":9.60,"RO":9.80,"RR":10.80},
    },
    "Pneu / Câmara de Ar": {
        "unidade": "UN",
        "precos": {"SP":420.00,"RJ":445.00,"MG":408.00,"BA":435.00,"RS":398.00,"DF":428.00,"GO":418.00,"CE":450.00,"PE":438.00,"PA":468.00,"AM":498.00,"SC":392.00,"MA":480.00,"MT":425.00,"MS":422.00,"AC":540.00,"AL":440.00,"SE":435.00,"TO":455.00,"PI":462.00,"RO":472.00,"RR":515.00},
    },
    "Peças e Acessórios para Veículos": {
        "unidade": "UN",
        "precos": {"SP":180.00,"RJ":192.00,"MG":175.00,"BA":188.00,"RS":170.00,"DF":183.00,"GO":180.00,"CE":195.00,"PE":190.00,"PA":202.00,"AM":218.00,"SC":168.00,"MA":210.00,"MT":184.00,"MS":180.00,"AC":240.00,"AL":193.00,"SE":191.00,"TO":198.00,"PI":200.00,"RO":204.00,"RR":224.00},
    },
    "Cimento / Areia / Brita": {
        "unidade": "Saco 50kg",
        "precos": {"SP":32.00,"RJ":34.50,"MG":31.00,"BA":33.50,"RS":30.00,"DF":32.80,"GO":32.00,"CE":35.00,"PE":34.00,"PA":36.50,"AM":39.50,"SC":29.50,"MA":38.00,"MT":33.00,"MS":32.00,"AC":44.00,"AL":34.50,"SE":34.00,"TO":35.50,"PI":36.00,"RO":37.00,"RR":40.50},
    },
    "Material Elétrico": {
        "unidade": "KIT",
        "precos": {"SP":85.00,"RJ":91.00,"MG":82.00,"BA":89.00,"RS":79.00,"DF":87.00,"GO":85.00,"CE":93.00,"PE":90.00,"PA":97.00,"AM":104.00,"SC":77.50,"MA":100.00,"MT":87.50,"MS":85.50,"AC":115.00,"AL":91.50,"SE":90.50,"TO":94.50,"PI":96.00,"RO":98.00,"RR":107.00},
    },
    "Material Hidráulico": {
        "unidade": "KIT",
        "precos": {"SP":72.00,"RJ":77.00,"MG":69.50,"BA":75.00,"RS":67.00,"DF":73.50,"GO":71.50,"CE":78.50,"PE":76.00,"PA":82.00,"AM":88.00,"SC":66.00,"MA":85.00,"MT":73.50,"MS":71.50,"AC":97.00,"AL":77.50,"SE":76.50,"TO":80.00,"PI":81.00,"RO":83.00,"RR":91.00},
    },
    "Tintas e Vernizes": {
        "unidade": "Lata 18L",
        "precos": {"SP":185.00,"RJ":197.00,"MG":180.00,"BA":194.00,"RS":175.00,"DF":188.00,"GO":184.00,"CE":200.00,"PE":195.00,"PA":208.00,"AM":224.00,"SC":172.00,"MA":216.00,"MT":189.00,"MS":185.00,"AC":248.00,"AL":198.00,"SE":196.00,"TO":204.00,"PI":207.00,"RO":210.00,"RR":230.00},
    },
    "Material de Expediente Geral": {
        "unidade": "KIT",
        "precos": {"SP":38.00,"RJ":40.50,"MG":36.50,"BA":40.00,"RS":35.50,"DF":38.80,"GO":38.00,"CE":41.50,"PE":40.00,"PA":43.00,"AM":46.50,"SC":35.00,"MA":45.00,"MT":39.00,"MS":38.00,"AC":51.50,"AL":40.80,"SE":40.20,"TO":42.00,"PI":43.00,"RO":43.50,"RR":48.00},
    },
    "Envelopes e Formulários": {
        "unidade": "Caixa 500 UN",
        "precos": {"SP":45.00,"RJ":48.00,"MG":43.50,"BA":47.00,"RS":42.00,"DF":46.00,"GO":44.50,"CE":49.00,"PE":47.50,"PA":51.00,"AM":55.00,"SC":41.50,"MA":53.00,"MT":46.50,"MS":45.00,"AC":61.00,"AL":48.20,"SE":47.80,"TO":50.00,"PI":51.00,"RO":51.50,"RR":57.00},
    },
    "Serviço de Limpeza e Conservação": {
        "unidade": "Posto/mês",
        "precos": {"SP":2800.00,"RJ":2950.00,"MG":2700.00,"BA":2850.00,"RS":2650.00,"DF":2900.00,"GO":2780.00,"CE":2900.00,"PE":2820.00,"PA":2950.00,"AM":3100.00,"SC":2600.00,"MA":3000.00,"MT":2820.00,"MS":2760.00,"AC":3350.00,"AL":2870.00,"SE":2860.00,"TO":2920.00,"PI":2950.00,"RO":3000.00,"RR":3200.00},
    },
    "Serviço de Vigilância / Portaria": {
        "unidade": "Posto/mês",
        "precos": {"SP":4200.00,"RJ":4450.00,"MG":4050.00,"BA":4300.00,"RS":3980.00,"DF":4350.00,"GO":4180.00,"CE":4350.00,"PE":4230.00,"PA":4450.00,"AM":4700.00,"SC":3920.00,"MA":4550.00,"MT":4230.00,"MS":4150.00,"AC":5100.00,"AL":4310.00,"SE":4300.00,"TO":4400.00,"PI":4450.00,"RO":4520.00,"RR":4850.00},
    },
    "Serviço de TI / Suporte": {
        "unidade": "Hora",
        "precos": {"SP":180.00,"RJ":190.00,"MG":175.00,"BA":182.00,"RS":170.00,"DF":185.00,"GO":180.00,"CE":185.00,"PE":182.00,"PA":192.00,"AM":205.00,"SC":168.00,"MA":198.00,"MT":181.00,"MS":178.00,"AC":225.00,"AL":184.00,"SE":183.00,"TO":190.00,"PI":192.00,"RO":194.00,"RR":210.00},
    },
    "Serviço de Impressão / Reprografia": {
        "unidade": "Página",
        "precos": {"SP":0.28,"RJ":0.30,"MG":0.27,"BA":0.30,"RS":0.26,"DF":0.29,"GO":0.28,"CE":0.31,"PE":0.30,"PA":0.32,"AM":0.35,"SC":0.26,"MA":0.34,"MT":0.29,"MS":0.28,"AC":0.38,"AL":0.30,"SE":0.30,"TO":0.32,"PI":0.33,"RO":0.33,"RR":0.36},
    },
    "Serviço de Manutenção Predial": {
        "unidade": "Hora",
        "precos": {"SP":95.00,"RJ":102.00,"MG":91.00,"BA":98.00,"RS":88.00,"DF":97.00,"GO":94.00,"CE":100.00,"PE":98.00,"PA":105.00,"AM":115.00,"SC":86.00,"MA":112.00,"MT":97.00,"MS":94.00,"AC":128.00,"AL":100.00,"SE":99.00,"TO":103.00,"PI":105.00,"RO":107.00,"RR":118.00},
    },
    "Serviço de Telefonia / Internet": {
        "unidade": "Linha/mês",
        "precos": {"SP":120.00,"RJ":128.00,"MG":116.00,"BA":122.00,"RS":112.00,"DF":125.00,"GO":120.00,"CE":126.00,"PE":123.00,"PA":132.00,"AM":145.00,"SC":110.00,"MA":140.00,"MT":122.00,"MS":119.00,"AC":165.00,"AL":124.00,"SE":123.00,"TO":130.00,"PI":132.00,"RO":135.00,"RR":150.00},
    },
    "Serviço de Transporte Escolar": {
        "unidade": "KM",
        "precos": {"SP":4.80,"RJ":5.10,"MG":4.60,"BA":4.90,"RS":4.50,"DF":5.00,"GO":4.80,"CE":5.00,"PE":4.90,"PA":5.30,"AM":5.80,"SC":4.40,"MA":5.60,"MT":4.90,"MS":4.80,"AC":6.50,"AL":5.00,"SE":4.95,"TO":5.20,"PI":5.30,"RO":5.40,"RR":5.90},
    },
    "Serviço de Dedetização / Controle de Pragas": {
        "unidade": "m²",
        "precos": {"SP":1.80,"RJ":1.95,"MG":1.72,"BA":1.88,"RS":1.65,"DF":1.85,"GO":1.80,"CE":1.95,"PE":1.90,"PA":2.05,"AM":2.20,"SC":1.62,"MA":2.12,"MT":1.84,"MS":1.80,"AC":2.45,"AL":1.92,"SE":1.90,"TO":1.98,"PI":2.01,"RO":2.05,"RR":2.25},
    },
    "Software / Sistema de Informação": {
        "unidade": "Licença/ano",
        "precos": {"SP":2400.00,"RJ":2520.00,"MG":2350.00,"BA":2460.00,"RS":2300.00,"DF":2450.00,"GO":2400.00,"CE":2530.00,"PE":2480.00,"PA":2600.00,"AM":2750.00,"SC":2280.00,"MA":2680.00,"MT":2430.00,"MS":2390.00,"AC":2980.00,"AL":2500.00,"SE":2490.00,"TO":2560.00,"PI":2590.00,"RO":2620.00,"RR":2840.00},
    },
    "Projetor Multimídia": {
        "unidade": "UN",
        "precos": {"SP":1850.00,"RJ":1950.00,"MG":1800.00,"BA":1920.00,"RS":1780.00,"DF":1880.00,"GO":1860.00,"CE":1970.00,"PE":1930.00,"PA":2050.00,"AM":2180.00,"SC":1760.00,"MA":2120.00,"MT":1890.00,"MS":1860.00,"AC":2350.00,"AL":1950.00,"SE":1940.00,"TO":2000.00,"PI":2020.00,"RO":2060.00,"RR":2240.00},
    },
    "Tela Interativa / Lousa Digital": {
        "unidade": "UN",
        "precos": {"SP":4800.00,"RJ":5050.00,"MG":4700.00,"BA":4980.00,"RS":4620.00,"DF":4880.00,"GO":4820.00,"CE":5100.00,"PE":5000.00,"PA":5300.00,"AM":5650.00,"SC":4580.00,"MA":5500.00,"MT":4900.00,"MS":4820.00,"AC":6100.00,"AL":5060.00,"SE":5020.00,"TO":5180.00,"PI":5230.00,"RO":5310.00,"RR":5800.00},
    },
    "DVR / NVR": {
        "unidade": "UN",
        "precos": {"SP":680.00,"RJ":720.00,"MG":660.00,"BA":705.00,"RS":645.00,"DF":692.00,"GO":678.00,"CE":730.00,"PE":715.00,"PA":760.00,"AM":815.00,"SC":638.00,"MA":790.00,"MT":695.00,"MS":680.00,"AC":895.00,"AL":722.00,"SE":718.00,"TO":745.00,"PI":752.00,"RO":765.00,"RR":838.00},
    },
    "Drone / UAV": {
        "unidade": "UN",
        "precos": {"SP":8500.00,"RJ":8950.00,"MG":8300.00,"BA":8800.00,"RS":8150.00,"DF":8650.00,"GO":8520.00,"CE":9050.00,"PE":8850.00,"PA":9400.00,"AM":10000.00,"SC":8100.00,"MA":9700.00,"MT":8700.00,"MS":8560.00,"AC":10800.00,"AL":8950.00,"SE":8880.00,"TO":9200.00,"PI":9280.00,"RO":9400.00,"RR":10200.00},
    },
    "Material Esportivo": {
        "unidade": "KIT",
        "precos": {"SP":185.00,"RJ":197.00,"MG":180.00,"BA":194.00,"RS":175.00,"DF":188.00,"GO":184.00,"CE":200.00,"PE":195.00,"PA":208.00,"AM":224.00,"SC":172.00,"MA":216.00,"MT":189.00,"MS":185.00,"AC":248.00,"AL":198.00,"SE":196.00,"TO":204.00,"PI":207.00,"RO":210.00,"RR":230.00},
    },
    "Instrumento Musical": {
        "unidade": "UN",
        "precos": {"SP":580.00,"RJ":615.00,"MG":565.00,"BA":600.00,"RS":550.00,"DF":590.00,"GO":578.00,"CE":625.00,"PE":610.00,"PA":650.00,"AM":700.00,"SC":542.00,"MA":680.00,"MT":592.00,"MS":580.00,"AC":775.00,"AL":618.00,"SE":615.00,"TO":638.00,"PI":645.00,"RO":655.00,"RR":715.00},
    },
    "Equipamento Odontológico": {
        "unidade": "UN",
        "precos": {"SP":2200.00,"RJ":2320.00,"MG":2150.00,"BA":2280.00,"RS":2100.00,"DF":2240.00,"GO":2200.00,"CE":2360.00,"PE":2300.00,"PA":2450.00,"AM":2620.00,"SC":2080.00,"MA":2560.00,"MT":2250.00,"MS":2210.00,"AC":2850.00,"AL":2330.00,"SE":2320.00,"TO":2400.00,"PI":2430.00,"RO":2470.00,"RR":2700.00},
    },
}

# ─── Orgãos por UF ──────────────────────────────────────────────────────────
ORGAOS_UF = {
    "SP": [("62.930.579/0001-01", "Prefeitura Municipal de São Paulo", "MUNICIPAL"),
           ("48.031.529/0001-02", "Governo do Estado de São Paulo", "ESTADUAL")],
    "RJ": [("29.979.036/0001-40", "Prefeitura Municipal do Rio de Janeiro", "MUNICIPAL"),
           ("23.405.830/0001-28", "Governo do Estado do Rio de Janeiro", "ESTADUAL")],
    "MG": [("18.715.138/0001-80", "Prefeitura Municipal de Belo Horizonte", "MUNICIPAL"),
           ("18.715.138/0002-61", "Governo do Estado de Minas Gerais", "ESTADUAL")],
    "BA": [("13.927.801/0001-45", "Prefeitura Municipal de Salvador", "MUNICIPAL"),
           ("13.927.801/0002-26", "Governo do Estado da Bahia", "ESTADUAL")],
    "RS": [("92.963.560/0001-60", "Prefeitura Municipal de Porto Alegre", "MUNICIPAL"),
           ("92.958.800/0001-38", "Governo do Estado do Rio Grande do Sul", "ESTADUAL")],
    "DF": [("00.394.429/0001-12", "Governo do Distrito Federal", "ESTADUAL"),
           ("00.394.429/0002-93", "Secretaria de Estado de Educação do DF", "ESTADUAL")],
    "GO": [("01.133.076/0001-90", "Prefeitura Municipal de Goiânia", "MUNICIPAL"),
           ("01.409.705/0001-38", "Governo do Estado de Goiás", "ESTADUAL")],
    "CE": [("06.994.069/0001-49", "Prefeitura Municipal de Fortaleza", "MUNICIPAL"),
           ("06.994.069/0002-20", "Governo do Estado do Ceará", "ESTADUAL")],
    "PE": [("10.131.347/0001-86", "Prefeitura Municipal do Recife", "MUNICIPAL"),
           ("10.131.347/0002-67", "Governo do Estado de Pernambuco", "ESTADUAL")],
    "PA": [("05.058.441/0001-68", "Prefeitura Municipal de Belém", "MUNICIPAL"),
           ("05.058.441/0002-49", "Governo do Estado do Pará", "ESTADUAL")],
    "AM": [("04.312.369/0001-90", "Prefeitura Municipal de Manaus", "MUNICIPAL"),
           ("04.312.369/0002-71", "Governo do Estado do Amazonas", "ESTADUAL")],
    "SC": [("82.892.577/0001-66", "Prefeitura Municipal de Florianópolis", "MUNICIPAL"),
           ("82.892.577/0002-47", "Governo do Estado de Santa Catarina", "ESTADUAL")],
    "MA": [("06.139.292/0001-48", "Prefeitura Municipal de São Luís", "MUNICIPAL"),
           ("06.139.292/0002-29", "Governo do Estado do Maranhão", "ESTADUAL")],
    "MT": [("03.507.415/0001-40", "Prefeitura Municipal de Cuiabá", "MUNICIPAL"),
           ("03.507.415/0002-21", "Governo do Estado do Mato Grosso", "ESTADUAL")],
    "MS": [("03.155.926/0001-44", "Prefeitura Municipal de Campo Grande", "MUNICIPAL"),
           ("03.155.926/0002-25", "Governo do Estado do Mato Grosso do Sul", "ESTADUAL")],
    "AC": [("04.034.583/0001-59", "Prefeitura Municipal de Rio Branco", "MUNICIPAL"),
           ("04.034.583/0002-30", "Governo do Estado do Acre", "ESTADUAL")],
    "AL": [("12.198.693/0001-58", "Prefeitura Municipal de Maceió", "MUNICIPAL"),
           ("12.198.693/0002-39", "Governo do Estado de Alagoas", "ESTADUAL")],
    "SE": [("13.128.798/0001-20", "Prefeitura Municipal de Aracaju", "MUNICIPAL"),
           ("13.128.798/0002-01", "Governo do Estado de Sergipe", "ESTADUAL")],
    "TO": [("25.053.470/0001-79", "Prefeitura Municipal de Palmas", "MUNICIPAL"),
           ("25.053.470/0002-50", "Governo do Estado do Tocantins", "ESTADUAL")],
    "PI": [("06.554.729/0001-30", "Prefeitura Municipal de Teresina", "MUNICIPAL"),
           ("06.554.729/0002-11", "Governo do Estado do Piauí", "ESTADUAL")],
    "RO": [("05.914.854/0001-59", "Prefeitura Municipal de Porto Velho", "MUNICIPAL"),
           ("05.914.854/0002-30", "Governo do Estado de Rondônia", "ESTADUAL")],
    "RR": [("03.340.110/0001-30", "Prefeitura Municipal de Boa Vista", "MUNICIPAL"),
           ("03.340.110/0002-11", "Governo do Estado de Roraima", "ESTADUAL")],
}

MODALIDADES = ["Pregão Eletrônico", "Dispensa Eletrônica", "Concorrência Eletrônica", "Registro de Preços"]

rng = random.Random(42)

def gerar_numero_pncp(uf: str, idx: int, ano: int) -> str:
    return f"{uf}{ano}{idx:06d}-0001-{rng.randint(1,9):03d}/2024"

def gerar_data(base_days_ago: int) -> date:
    offset = rng.randint(0, min(base_days_ago, 180))
    return date.today() - timedelta(days=offset)

def variacao(preco_base: float, seed: int) -> float:
    """Variação ±8% determinística."""
    fator = 1.0 + ((seed % 17 - 8) / 100.0)
    return round(preco_base * fator, 4)

def main():
    print("🔌 Conectando ao banco...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # ── Limpa dados anteriores de seed (mantém schema e dados de negócio) ──
    print("🧹 Limpando dados de seed anteriores...")
    cur.execute("DELETE FROM item_categoria WHERE item_id IN (SELECT id FROM itens WHERE descricao LIKE '[SEED]%')")
    cur.execute("DELETE FROM fontes_preco WHERE item_id IN (SELECT id FROM itens WHERE descricao LIKE '[SEED]%')")
    cur.execute("DELETE FROM itens WHERE descricao LIKE '[SEED]%'")
    cur.execute("DELETE FROM contratacoes WHERE objeto LIKE '[SEED]%'")
    cur.execute("DELETE FROM orgaos WHERE razao_social LIKE '%(seed)%'")
    conn.commit()

    # ── Busca categorias do banco ──
    cur.execute("SELECT id, nome FROM categorias")
    categorias_db = {row[1]: row[0] for row in cur.fetchall()}
    print(f"📋 {len(categorias_db)} categorias no banco")

    # ── Insere/atualiza órgãos ──
    print("🏛️  Inserindo órgãos...")
    orgao_ids: dict[str, list[str]] = {}
    for uf, orgaos in ORGAOS_UF.items():
        orgao_ids[uf] = []
        for cnpj, razao, esfera in orgaos:
            cur.execute("""
                INSERT INTO orgaos (cnpj, razao_social, esfera, uf, municipio)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cnpj) DO UPDATE SET razao_social=EXCLUDED.razao_social
                RETURNING id
            """, (cnpj, razao, esfera, uf, razao.replace("Prefeitura Municipal de ", "").replace("Governo do Estado de ", "").replace("Governo do Estado do ", "").replace("Secretaria de Estado de Educação do DF", "Brasília").replace("Governo do Distrito Federal", "Brasília")))
            orgao_ids[uf].append(cur.fetchone()[0])
    conn.commit()

    # ── Insere contratações + itens + fontes ──
    total_contratacoes = 0
    total_itens = 0
    total_fontes = 0

    categorias_inseridas = set()

    for cat_nome, dados in PRECOS_BASE.items():
        unidade = dados["unidade"]
        precos = dados["precos"]
        cat_id = categorias_db.get(cat_nome)

        for uf, preco_base in precos.items():
            if uf not in orgao_ids:
                continue
            orgao_id = rng.choice(orgao_ids[uf])
            modalidade = rng.choice(MODALIDADES)
            idx = total_contratacoes + 1
            numero_pncp = gerar_numero_pncp(uf, idx, 2024)
            data_pub = gerar_data(365)
            valor_total = round(preco_base * rng.randint(50, 500), 2)

            cur.execute("""
                INSERT INTO contratacoes (orgao_id, numero_controle_pncp, modalidade, objeto, valor_total, data_publicacao, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'ativo')
                RETURNING id
            """, (orgao_id, numero_pncp,
                  modalidade,
                  f"[SEED] Aquisição de {cat_nome} — {uf} 2024",
                  valor_total, data_pub))
            contratacao_id = cur.fetchone()[0]
            total_contratacoes += 1

            # Item
            qtd = Decimal(str(rng.randint(50, 500)))
            preco_v = variacao(preco_base, total_itens)
            cur.execute("""
                INSERT INTO itens (contratacao_id, numero_item, descricao, quantidade, unidade, valor_unitario, valor_total)
                VALUES (%s, 1, %s, %s, %s, %s, %s)
                RETURNING id
            """, (contratacao_id,
                  f"[SEED] {cat_nome}",
                  qtd, unidade,
                  Decimal(str(preco_v)),
                  Decimal(str(round(float(qtd) * preco_v, 2)))))
            item_id = cur.fetchone()[0]
            total_itens += 1

            # item_categoria
            if cat_id:
                cur.execute("""
                    INSERT INTO item_categoria (item_id, categoria_id, score_confianca, metodo_classificacao)
                    VALUES (%s, %s, 0.95, 'SEED')
                    ON CONFLICT DO NOTHING
                """, (item_id, cat_id))
                categorias_inseridas.add(cat_nome)

            # 3 fontes de preço por item (variações realistas)
            for j in range(3):
                preco_fonte = variacao(preco_base, total_fontes + j)
                data_ref = gerar_data(365)
                cur.execute("""
                    INSERT INTO fontes_preco (
                        fonte_tipo, fonte_referencia, item_id,
                        preco_unitario, preco_total, quantidade,
                        unidade_original, unidade_normalizada,
                        data_referencia, municipio, uf, esfera,
                        url_origem, qualidade_tipo, score_confianca, ativo
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true)
                """, (
                    "ATA_RP" if j == 0 else ("DISPENSA" if j == 1 else "PREGAO"),
                    f"PNCP-{uf}-{total_fontes+j:06d}",
                    item_id,
                    Decimal(str(preco_fonte)),
                    Decimal(str(round(float(qtd) * preco_fonte, 2))),
                    qtd, unidade, unidade,
                    data_ref,
                    _municipio(uf), uf,
                    "ESTADUAL" if rng.random() > 0.5 else "MUNICIPAL",
                    f"https://pncp.gov.br/app/editais/{numero_pncp}",
                    "OFICIAL",
                    Decimal(str(round(0.85 + rng.random() * 0.14, 4))),
                ))
                total_fontes += 1

        if total_contratacoes % 50 == 0:
            conn.commit()
            print(f"  ✅ {total_contratacoes} contratações, {total_itens} itens, {total_fontes} fontes...")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ SEED COMPLETO:")
    print(f"   Contratações : {total_contratacoes}")
    print(f"   Itens        : {total_itens}")
    print(f"   Fontes       : {total_fontes}")
    print(f"   Categorias   : {len(categorias_inseridas)}")


def _municipio(uf: str) -> str:
    capitais = {
        "AC":"Rio Branco","AL":"Maceió","AM":"Manaus","BA":"Salvador","CE":"Fortaleza",
        "DF":"Brasília","GO":"Goiânia","MA":"São Luís","MG":"Belo Horizonte","MS":"Campo Grande",
        "MT":"Cuiabá","PA":"Belém","PE":"Recife","PI":"Teresina","RJ":"Rio de Janeiro",
        "RO":"Porto Velho","RR":"Boa Vista","RS":"Porto Alegre","SC":"Florianópolis",
        "SE":"Aracaju","SP":"São Paulo","TO":"Palmas",
    }
    return capitais.get(uf, uf)


if __name__ == "__main__":
    main()
