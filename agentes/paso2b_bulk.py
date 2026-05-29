import pandas as pd
import numpy as np
import os

def normalizar_bulk(df_norm, meta, gse_id):
    """Pipeline específico bulk RNA-seq."""
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    
    # Verificar si son counts
    if df_norm.min().min() >= 0 and df_norm.max().max() < 10000:
        # DESeq2-style normalization simulada
        size_factors = np.median(df_norm, axis=0)
        df_norm = df_norm.div(size_factors, axis=1)
        df_norm = np.log2(df_norm + 1)
    
    df_norm.to_csv(os.path.join(path, "bulk_normalizada.csv"))
    return df_norm