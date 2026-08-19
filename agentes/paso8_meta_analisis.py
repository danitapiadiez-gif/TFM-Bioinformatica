import pandas as pd
import os
import glob
import numpy as np

def ejecutar_meta_analisis():
    """
    PASO 8: Meta-análisis determinista de biomarcadores.
    Calcula matriz de LogFC y consistencia direccional.
    """
    print(f"\n{'='*80}")
    print(f" PASO 8: INICIANDO META-ANÁLISIS ESTADÍSTICO")
    print(f"{'='*80}")
    
    base_path = os.path.expanduser("~/Desktop")
    carpetas = glob.glob(os.path.join(base_path, "TFM_GSE*"))
    
    data_consolidada = [] # Lista de diccionarios con info de cada gen
    
    # 1. Recolectar todos los resultados significativos
    for carpeta in carpetas:
        gse_id = os.path.basename(carpeta).replace("TFM_", "")
        ruta_res = os.path.join(carpeta, "resultados_completos.csv")
        
        if os.path.exists(ruta_res):
            df_gse = pd.read_csv(ruta_res)
            if not df_gse.empty and 'adj_pvalue' in df_gse.columns:
                # Solo genes significativos
                sig = df_gse[df_gse['adj_pvalue'] < 0.05].copy()
                sig['GSE'] = gse_id
                data_consolidada.append(sig[['GENE_SYMBOL', 'LogFC', 'GSE']])

    if not data_consolidada:
        print(" No hay datos suficientes.")
        return

    full_df = pd.concat(data_consolidada)
    
    # 2. Crear Matriz Pivotada (Genes x Estudios)
    matriz_logfc = full_df.pivot_table(index='GENE_SYMBOL', columns='GSE', values='LogFC')
    
    # 3. Calcular Métricas de Consenso
    resumen = pd.DataFrame(index=matriz_logfc.index)
    resumen['Num_Estudios'] = matriz_logfc.notna().sum(axis=1)
    resumen['LogFC_Medio'] = matriz_logfc.mean(axis=1)
    
    # Consistencia direccional: ¿Todos los estudios van en el mismo sentido?
    def calcular_consistencia(row):
        vals = row.dropna()
        if len(vals) <= 1: return 1.0
        # Si el signo del min es igual al del max, todos tienen el mismo sentido
        return 1.0 if (np.sign(vals.min()) == np.sign(vals.max())) else 0.0

    resumen['Consistencia_Direccional'] = matriz_logfc.apply(calcular_consistencia, axis=1)
    
    # Filtrar solo los que tengan consistencia total
    ganadores = resumen[resumen['Consistencia_Direccional'] == 1.0].sort_values('Num_Estudios', ascending=False)
    
    # Unir con la matriz de LogFC para el CSV final
    resultado_final = ganadores.join(matriz_logfc)
    
    ruta_final = os.path.join(base_path, "resultados/firma_consenso/BIOMARCADORES_UNIVERSALES_CANCER_PULMON.csv")
    resultado_final.to_csv(ruta_final)
    
    print(f" Meta-análisis completado. Ganadores: {len(ganadores)} genes consistentes.")
    print(resultado_final[['Num_Estudios', 'LogFC_Medio']].head(15))
    return resultado_final

if __name__ == "__main__":
    ejecutar_meta_analisis()
