import requests
import pandas as pd
import numpy as np
import os
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuración
BASE_DIR = _RAIZ
RUTA_BIOMARCADORES = os.path.join(BASE_DIR, "BIOMARCADORES_DE_ORO_CONSENSO.csv")
RUTA_PDF_RED = os.path.join(BASE_DIR, "RED_BIOLOGICA_FINAL.pdf")
STRING_API_URL = "https://string-db.org/api"

def obtener_interacciones_robustas(genes):
    print(f"Buscando interacciones para {len(genes)} genes en STRING-db...")
    
    # 1. Primero mapeamos los IDs para asegurar que STRING los reconoce
    map_url = f"{STRING_API_URL}/json/get_string_ids"
    map_params = {
        "identifiers": "\r".join(genes),
        "species": 9606,
        "limit": 1,
        "caller_identity": "tfm_genomic_intelligence"
    }
    map_res = requests.post(map_url, data=map_params)
    if map_res.status_code != 200:
        return []
    
    string_ids = [item["stringId"] for item in map_res.json()]
    print(f"Mapeados {len(string_ids)} genes correctamente.")

    # 2. Pedimos la red con un score más permisivo (0.2) para ver la "nube" de conexiones
    net_url = f"{STRING_API_URL}/json/network"
    net_params = {
        "identifiers": "\r".join(string_ids),
        "species": 9606,
        "required_score": 200, # 0.2 para asegurar que vemos la red
        "caller_identity": "tfm_genomic_intelligence"
    }
    
    res_net = requests.post(net_url, data=net_params)
    return res_net.json() if res_net.status_code == 200 else []

def generar_pdf_final(genes, interactions):
    print("Creando PDF con la red visual...")
    
    G = nx.Graph()
    for gene in genes:
        G.add_node(gene)
        
    for edge in interactions:
        G.add_edge(edge["preferredName_A"], edge["preferredName_B"], weight=edge["score"])

    plt.figure(figsize=(15, 15))
    
    # Usamos un layout más "orgánico"
    pos = nx.kamada_kawai_layout(G)
    
    # Dibujar bordes
    if interactions:
        edges = G.edges(data=True)
        weights = [e[2]['weight'] * 4 for e in edges]
        nx.draw_networkx_edges(G, pos, width=weights, edge_color='steelblue', alpha=0.3)
    
    # Dibujar nodos
    d = dict(G.degree)
    node_sizes = [v * 300 + 800 for v in d.values()]
    
    # Colorear por grado (conectividad)
    node_color = [v for v in d.values()]
    
    nodes = nx.draw_networkx_nodes(G, pos, 
                                   node_size=node_sizes, 
                                   node_color=node_color,
                                   cmap=plt.cm.YlOrRd, # De amarillo a rojo según importancia
                                   edgecolors='black',
                                   linewidths=1)
    
    # Etiquetas
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

    plt.title("RED DE INTERACCIÓN BIOLÓGICA (PPI)\nAnálisis de Consenso de Biomarcadores", fontsize=22, fontweight='bold')
    plt.axis('off')
    
    # Barra de color para importancia
    plt.colorbar(nodes, label='Grado de conectividad (Hub Score)', shrink=0.8)

    with PdfPages(RUTA_PDF_RED) as pdf:
        pdf.savefig(bbox_inches='tight')
        plt.close()

def main():
    if not os.path.exists(RUTA_BIOMARCADORES):
        print("Error: No hay datos de biomarcadores.")
        return
        
    df = pd.read_csv(RUTA_BIOMARCADORES)
    # Usamos el Top 50 para garantizar que haya conexiones
    genes_top = df.head(50).iloc[:, 0].tolist()
    
    interactions = obtener_interacciones_robustas(genes_top)
    
    if not interactions:
        print("AVISO: STRING no devolvió conexiones incluso a score bajo. Generando mapa de nodos aislados.")
    
    generar_pdf_final(genes_top, interactions)
    print(f"\n--- ÉXITO ---")
    print(f"Archivo generado: {RUTA_PDF_RED}")
    print(f"Por favor, abre 'RED_BIOLOGICA_FINAL.pdf' en tu Escritorio.")

if __name__ == "__main__":
    main()
