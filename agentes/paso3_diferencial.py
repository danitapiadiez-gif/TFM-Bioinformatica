import pandas as pd
import numpy as np
from scipy import stats
import os
from statsmodels.stats.multitest import multipletests

def ejecutar_diferencial(gse_id, df_norm, meta):
    """
    PASO 3: Análisis diferencial comparando Sano vs Enfermo.
    """
    print(f"\n PASO 3: Análisis estadístico diferencial ({gse_id})...")
    path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    os.makedirs(path, exist_ok=True)
    
    # 1. Definir el dataframe de resultados vacío por si acaso
    resultados_vacio = pd.DataFrame(columns=['GENE_SYMBOL', 'LogFC', 'pvalue', 'adj_pvalue'])
    
    if 'grupo_analisis' not in meta.columns:
        print(" No existe columna 'grupo_analisis'.")
        resultados_vacio.to_csv(os.path.join(path, "resultados_completos.csv"), index=False)
        return resultados_vacio

    # 2. Filtrar solo Sano y Enfermo
    meta_filt = meta[meta['grupo_analisis'].isin(['Sano', 'Enfermo'])]
    grupos = meta_filt['grupo_analisis'].value_counts()
    print(f" Distribución para diferencial: {grupos.to_dict()}")

    if 'Sano' not in grupos or 'Enfermo' not in grupos or grupos['Sano'] < 2 or grupos['Enfermo'] < 2:
        print(" No hay suficientes muestras en ambos grupos (Sano/Enfermo) para el test.")
        resultados_vacio.to_csv(os.path.join(path, "resultados_completos.csv"), index=False)
        return resultados_vacio

    # 3. Preparar muestras
    muestras_sano = meta_filt[meta_filt['grupo_analisis'] == 'Sano'].index.intersection(df_norm.columns)
    muestras_enfermo = meta_filt[meta_filt['grupo_analisis'] == 'Enfermo'].index.intersection(df_norm.columns)
    
    print(f" Comparando Enfermo (n={len(muestras_enfermo)}) vs Sano (n={len(muestras_sano)})")
    
    # 4. Cálculo de LogFC y T-Test
    mean_sano = df_norm[muestras_sano].mean(axis=1)
    mean_enfermo = df_norm[muestras_enfermo].mean(axis=1)
    log2fc = mean_enfermo - mean_sano
    
    pvals = []
    for idx in df_norm.index:
        stat, pval = stats.ttest_ind(
            df_norm.loc[idx, muestras_enfermo],
            df_norm.loc[idx, muestras_sano],
            equal_var=False, nan_policy='omit'
        )
        pvals.append(pval)
    
    pvals = np.array(pvals)
    _, pvals_adj, _, _ = multipletests(pvals, alpha=0.05, method='fdr_bh')
    
    resultados = pd.DataFrame({
        'GENE_SYMBOL': df_norm.index,
        'LogFC': log2fc.values,
        'pvalue': pvals,
        'adj_pvalue': pvals_adj
    })
    
    resultados.to_csv(os.path.join(path, "resultados_completos.csv"), index=False)
    sig = resultados[resultados['adj_pvalue'] < 0.05]
    print(f" ✅ Genes significativos encontrados: {len(sig)}")
    
    return sig