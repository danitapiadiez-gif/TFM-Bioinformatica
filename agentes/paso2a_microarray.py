import pandas as pd
import numpy as np
import os

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def normalizar_microarray(df_norm, meta, gse_id):
    """Pipeline específico microarray.
    
    En esta versión asumimos que df_norm ya viene:
      - Log2-transformado (si hacía falta)
      - Normalizado por quantile en procesar_metadata
    Así evitamos aplicar log2 dos veces.
    """
    path = os.path.join(_RAIZ, f"TFM_{gse_id}")
    

    
    df_norm.to_csv(os.path.join(path, "microarray_normalizada.csv"))
    return df_norm