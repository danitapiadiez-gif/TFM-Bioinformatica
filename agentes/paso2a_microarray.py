import pandas as pd
import numpy as np
import os


def normalizar_microarray(df_norm, meta, gse_id):
    """Pipeline específico microarray.
    
    En esta versión asumimos que df_norm ya viene:
      - Log2-transformado (si hacía falta)
      - Normalizado por quantile en procesar_metadata
    Así evitamos aplicar log2 dos veces.
    """
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    

    
    df_norm.to_csv(os.path.join(path, "microarray_normalizada.csv"))
    return df_norm