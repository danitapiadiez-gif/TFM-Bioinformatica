import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generar_consenso_tfm():
    """
    Script de síntesis final para el TFM.
    Une los resultados de Estadística (Paso 8) y ML (LODO).
    """
    print("Iniciando análisis de consenso final...")
    
    # Rutas de archivos
    desktop = _RAIZ
    ruta_est = os.path.join(desktop, "resultados/firma_consenso/BIOMARCADORES_UNIVERSALES_CANCER_PULMON.csv")
    ruta_ml = os.path.join(desktop, "resultados/firma_consenso/BIOMARCADORES_DE_ORO_CONSENSO.csv")
    ruta_salida = os.path.join(desktop, "resultados/firma_consenso/FIRMA_CONSENSO_FINAL_TFM.csv")
    
    if not os.path.exists(ruta_est) or not os.path.exists(ruta_ml):
        print("Error: No se encuentran los archivos CSV en el escritorio.")
        return

    # 1. Cargar datos
    df_est = pd.read_csv(ruta_est)
    df_ml = pd.read_csv(ruta_ml)
    
    # Renombrar la primera columna del ML si es necesario (a veces pandas la lee como 'Unnamed: 0')
    if 'GENE_SYMBOL' not in df_ml.columns:
        df_ml.rename(columns={df_ml.columns[0]: 'GENE_SYMBOL'}, inplace=True)

    # 2. Mezclar (Inner Join) para encontrar genes en ambos
    # Solo nos quedamos con los que aparecen en ambas listas para asegurar máxima robustez
    df_final = pd.merge(df_est, df_ml, on='GENE_SYMBOL')
    
    # 3. Crear Puntuación de Consenso
    # Normalizamos ambas métricas entre 0 y 1 para que pesen lo mismo
    df_final['abs_logfc'] = df_final['LogFC_Medio'].abs()
    
    # Min-Max Scaling simple para combinar
    df_final['score_est'] = (df_final['abs_logfc'] - df_final['abs_logfc'].min()) / (df_final['abs_logfc'].max() - df_final['abs_logfc'].min())
    df_final['score_ml'] = (df_final['Importancia_Media'] - df_final['Importancia_Media'].min()) / (df_final['Importancia_Media'].max() - df_final['Importancia_Media'].min())
    
    # Puntuación final: 50% Estadística + 50% Machine Learning
    df_final['Puntuacion_Consenso'] = (df_final['score_est'] + df_final['score_ml']) / 2
    
    # 4. Ordenar y Seleccionar columnas clave para la memoria
    columnas_clave = [
        'GENE_SYMBOL', 'Puntuacion_Consenso', 'LogFC_Medio', 
        'Importancia_Media', 'Consistencia_Signo', 'Num_Estudios'
    ]
    
    df_ranking = df_final[columnas_clave].sort_values('Puntuacion_Consenso', ascending=False)
    
    # 5. Guardar resultados
    df_ranking.to_csv(ruta_salida, index=False)
    print(f"Ranking de consenso guardado en: {ruta_salida}")
    
    # 6. Gráfico de Dispersión (Visualización para la memoria)
    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=df_ranking.head(50), x='LogFC_Medio', y='Importancia_Media', 
                    size='Puntuacion_Consenso', hue='Puntuacion_Consenso', palette='viridis', sizes=(20, 200))
    
    # Anotar los top 10 genes
    for i in range(10):
        row = df_ranking.iloc[i]
        plt.text(row['LogFC_Medio'], row['Importancia_Media'], row['GENE_SYMBOL'], fontsize=9, fontweight='bold')
        
    plt.title('Top 50 Biomarcadores: Estadística (LogFC) vs Machine Learning (Importancia)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(desktop, "GRAFICO_CONSENSO_FINAL.png"), dpi=300)
    print("Gráfico de consenso generado: GRAFICO_CONSENSO_FINAL.png")

    print("\nTOP 15 BIOMARCADORES DE LA FIRMA FINAL:")
    print(df_ranking.head(15).to_string(index=False))

if __name__ == "__main__":
    generar_consenso_tfm()
