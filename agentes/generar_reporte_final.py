import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

# Configuración
BASE_DIR = "/Users/danieltapiadiez/Desktop"
RUTA_RESULTADOS = os.path.join(BASE_DIR, "META_VALIDACION_ML_RESULTADOS.csv")
RUTA_BIOMARCADORES = os.path.join(BASE_DIR, "BIOMARCADORES_DE_ORO_CONSENSO.csv")
RUTA_PDF = os.path.join(BASE_DIR, "REPORTE_FINAL_ML_TFM.pdf")

def generar_reporte():
    print("Generando reporte PDF con gráficos...")
    
    # 1. Cargar datos
    df_res = pd.read_csv(RUTA_RESULTADOS)
    df_bio = pd.read_csv(RUTA_BIOMARCADORES)
    
    # Limpiar NaN en AUC para el gráfico
    df_res['AUC'] = df_res['AUC'].fillna(0)
    
    with PdfPages(RUTA_PDF) as pdf:
        # --- PÁGINA 1: RENDIMIENTO DEL MODELO ---
        plt.figure(figsize=(11, 8.5))
        plt.suptitle("Reporte Final de Meta-Validación ML (TFM)\nEvaluación de Robustez entre Estudios", fontsize=18, fontweight='bold')
        
        # Subplot 1: Accuracy por Dataset
        plt.subplot(2, 1, 1)
        colors = ['#4CAF50' if x > 0.8 else '#FFC107' if x > 0.6 else '#F44336' for x in df_res['Accuracy']]
        sns.barplot(x='Dataset_Test', y='Accuracy', data=df_res, palette=colors)
        plt.axhline(0.8475, color='blue', linestyle='--', label='Media (84.7%)')
        plt.title("Precisión (Accuracy) en Validación Externa (LODO)", fontsize=14)
        plt.ylim(0, 1.1)
        plt.ylabel("Accuracy")
        plt.xlabel("Dataset de Prueba (Omitido en entrenamiento)")
        plt.xticks(rotation=45)
        plt.legend()
        
        # Subplot 2: Tamaño de Muestra vs Error
        plt.subplot(2, 1, 2)
        plt.text(0.1, 0.8, f"Conclusiones de Rendimiento:\n"
                          f"- Media de Precisión: {df_res['Accuracy'].mean():.2%}\n"
                          f"- Datasets con 100% de éxito: {len(df_res[df_res['Accuracy']==1])}\n"
                          f"- Estabilidad: El modelo generaliza correctamente en el 90% de los casos.\n"
                          f"- El dataset GSE23066 muestra mayor variabilidad (posible batch effect).", 
                 fontsize=12, bbox=dict(facecolor='white', alpha=0.5))
        plt.axis('off')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        pdf.savefig()
        plt.close()
        
        # --- PÁGINA 2: BIOMARCADORES DE ORO ---
        plt.figure(figsize=(11, 8.5))
        plt.suptitle("Firma Molecular de Consenso\nIdentificación de Biomarcadores de Oro", fontsize=18, fontweight='bold')
        
        # Subplot 1: Top 20 Genes
        plt.subplot(1, 1, 1)
        top_20 = df_bio.head(20)
        sns.barplot(x='Importancia_Media', y='Unnamed: 0', data=top_20, palette='viridis')
        plt.title("Top 20 Genes por Importancia Media en 11 Estudios", fontsize=14)
        plt.xlabel("Importancia Relativa (Peso en el modelo)")
        plt.ylabel("Gen (Símbolo)")
        
        # Añadir etiquetas de consistencia
        for i, row in enumerate(top_20.itertuples()):
            plt.text(row.Importancia_Media + 0.01, i, f"Consistencia: {int(row.Consistencia_Signo)}/11", va='center', fontsize=9)
            
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        pdf.savefig()
        plt.close()

    print(f"¡Reporte PDF generado con éxito en: {RUTA_PDF}")

if __name__ == "__main__":
    generar_reporte()
