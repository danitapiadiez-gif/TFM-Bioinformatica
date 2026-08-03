import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de estilo científico
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16
})

# Directorio del TFM (directorio actual del script o del proyecto)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(BASE_DIR, "META_VALIDACION_ML_RESULTADOS.csv")):
    # Si no, asumimos el directorio de trabajo actual
    BASE_DIR = os.getcwd()

ruta_resultados = os.path.join(BASE_DIR, "META_VALIDACION_ML_RESULTADOS.csv")
ruta_biomarcadores = os.path.join(BASE_DIR, "BIOMARCADORES_DE_ORO_CONSENSO.csv")

def generar_grafica_rendimiento():
    """Genera un gráfico del rendimiento de cada cohorte en LODO."""
    df = pd.read_csv(ruta_resultados)
    df = df.sort_values(by="Accuracy", ascending=False)
    mean_acc = df["Accuracy"].mean()

    plt.figure(figsize=(10, 6))
    colors = ['#1a5f7a' if x >= 0.8 else '#f28e2b' if x >= 0.6 else '#e15759' for x in df['Accuracy']]
    
    bars = plt.bar(df['Dataset_Test'], df['Accuracy'], color=colors, edgecolor='black', alpha=0.85, width=0.6)
    
    # Línea de media
    plt.axhline(mean_acc, color='#e15759', linestyle='--', linewidth=2, 
                label=f'Precisión Media Global: {mean_acc:.1%}')
    
    # Etiquetas de valor en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + 0.02, 
                 f'{height:.1%}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.title("Rendimiento del Clasificador en Validación Externa (LODO)\nPrueba de Robustez sin Fuga de Datos (Data Leakage)", pad=20)
    plt.xlabel("Estudio de Prueba Independiente (Omitido en el Entrenamiento)")
    plt.ylabel("Precisión de Predicción (Accuracy)")
    plt.ylim(0, 1.15)
    plt.legend(loc='lower left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    salida = os.path.join(BASE_DIR, "grafica_1_lodo_performance.png")
    plt.savefig(salida, dpi=300)
    plt.close()
    print(f"Grafica 1 guardada en: {salida}")

def generar_heatmap_coeficientes():
    """Genera un mapa de calor de los coeficientes de Lasso (L1) para los top genes en cada Fold."""
    df_bio = pd.read_csv(ruta_biomarcadores)
    
    # Renombrar primera columna si es necesario
    if 'GENE_SYMBOL' not in df_bio.columns:
        df_bio.rename(columns={df_bio.columns[0]: 'GENE_SYMBOL'}, inplace=True)
        
    # Obtener el Top 15 de genes por importancia media
    top_15 = df_bio.sort_values(by="Importancia_Media", ascending=False).head(15)
    
    # Extraer columnas de los Folds
    columnas_fold = [col for col in df_bio.columns if col.startswith("Fold_")]
    
    # Crear matriz para el Heatmap
    heatmap_data = top_15.set_index("GENE_SYMBOL")[columnas_fold]
    
    # Limpiar nombres de columnas (quitar 'Fold_')
    heatmap_data.columns = [col.replace("Fold_", "") for col in heatmap_data.columns]
    
    plt.figure(figsize=(12, 8))
    
    # Usar mapa de color divergente (azul = subexpresado en tumor, rojo = sobreexpresado en tumor)
    sns.heatmap(heatmap_data, cmap="RdBu_r", center=0, annot=True, fmt=".2f",
                linewidths=.5, cbar_kws={'label': 'Coeficiente de Regresión Logística (Lasso L1)'})
    
    plt.title("Estabilidad de los Coeficientes LASSO en Validación Cruzada LODO\nConsistencia en la Dirección de Expresión por Estudio", pad=20)
    plt.xlabel("Cohorte de Prueba Excluida en el Entrenamiento (Fold)")
    plt.ylabel("Biomarcadores de Oro (Top 15)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    salida = os.path.join(BASE_DIR, "grafica_2_lasso_coefficients_heatmap.png")
    plt.savefig(salida, dpi=300)
    plt.close()
    print(f"Grafica 2 guardada en: {salida}")

def generar_grafica_consistencia_vs_peso():
    """Genera un gráfico de dispersión de consistencia direccional vs importancia media."""
    df_bio = pd.read_csv(ruta_biomarcadores)
    if 'GENE_SYMBOL' not in df_bio.columns:
        df_bio.rename(columns={df_bio.columns[0]: 'GENE_SYMBOL'}, inplace=True)
        
    plt.figure(figsize=(11, 7))
    
    # Graficar todos los genes
    scatter = plt.scatter(df_bio['Importancia_Media'], df_bio['Consistencia_Signo'], 
                          alpha=0.4, c=df_bio['Consistencia_Signo'].abs(), cmap='viridis', 
                          edgecolors='none', s=40)
    
    # Destacar y etiquetar el Top 15
    top_15 = df_bio.sort_values(by="Importancia_Media", ascending=False).head(15)
    
    # Añadir nombres de genes con flechas o texto para evitar solapamiento simple
    for _, row in top_15.iterrows():
        plt.annotate(row['GENE_SYMBOL'], 
                     xy=(row['Importancia_Media'], row['Consistencia_Signo']),
                     xytext=(row['Importancia_Media'] + 0.005, row['Consistencia_Signo'] + np.random.uniform(-0.15, 0.15)),
                     fontsize=9, fontweight='bold',
                     arrowprops=dict(arrowstyle="->", color='gray', lw=0.5, alpha=0.5))
                     
    plt.axhline(0, color='black', linestyle='-', linewidth=0.8)
    plt.axvline(df_bio['Importancia_Media'].mean(), color='red', linestyle=':', label='Importancia Media Global')
    
    plt.title("Consistencia Direccional vs. Importancia Predictiva (ML)\nIdentificación de Genes con Señal Biológica y Robustez Clínica", pad=20)
    plt.xlabel("Importancia Media en el Modelo (Magnitud del Coeficiente LASSO)")
    plt.ylabel("Consistencia del Signo (Nº Estudios con la misma dirección: -11 a +11)")
    plt.ylim(-12.5, 12.5)
    plt.colorbar(scatter, label='Fuerza del Consenso de Signo (Absoluto)')
    plt.legend()
    plt.tight_layout()
    
    salida = os.path.join(BASE_DIR, "grafica_3_sign_consistency.png")
    plt.savefig(salida, dpi=300)
    plt.close()
    print(f"Grafica 3 guardada en: {salida}")

if __name__ == "__main__":
    print("Iniciando la generación de visualizaciones avanzadas de ML...")
    generar_grafica_rendimiento()
    generar_heatmap_coeficientes()
    generar_grafica_consistencia_vs_peso()
    print("¡Proceso finalizado! Todas las gráficas científicas se han guardado con éxito.")
