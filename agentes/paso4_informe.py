import os
import pandas as pd
from groq import Groq
from sklearn.decomposition import PCA
import numpy as np
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def generar_informe(gse_id, genes_sig, gse):
    """
    PASO 4: Genera un informe biológico usando IA (Groq) a partir de los genes significativos
    e incluye una interpretación básica de PCA, volcano y heatmap.
    """
    print(f"\n✍️ PASO 4: Generando informe biológico automático ({gse_id})...")
    base_path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    os.makedirs(base_path, exist_ok=True)
    
    # === 0. Cargar datos auxiliares para interpretar gráficos ===
    pca_texto, volcano_texto, heatmap_texto = interpretar_graficos(gse_id, base_path, genes_sig)
    
    if genes_sig is None or genes_sig.empty:
        print(" No hay genes significativos. Informe IA será más exploratorio.")
    
    # === 1. Seleccionar genes más relevantes (10 up, 10 down si existen) ===
    try:
        top_up = genes_sig.sort_values('LogFC', ascending=False).head(10)
        top_down = genes_sig.sort_values('LogFC', ascending=True).head(10)
        top_genes = pd.concat([top_up, top_down]).drop_duplicates()
    except Exception as e:
        print(f" Error seleccionando top genes: {e}")
        top_genes = genes_sig.copy() if genes_sig is not None else pd.DataFrame()
    
    # === 2. Tabla de genes para el prompt ===
    cols_disp = [c for c in ['GENE_SYMBOL', 'LogFC', 'pvalue', 'adj_pvalue'] if c in top_genes.columns]
    if cols_disp and not top_genes.empty:
        tabla_genes = top_genes[cols_disp].round(4).to_string(index=False)
    else:
        tabla_genes = "No se pudieron construir columnas estándar de genes."
    
    # === 3. Título del estudio ===
    try:
        titulo = gse.metadata.get('title', ['N/A'])[0]
    except Exception:
        titulo = "N/A"
    
    # === 4. Construcción del prompt, incluyendo los gráficos ===
    prompt = f"""
Eres un experto en biología molecular y transcriptómica.

Has analizado el estudio GEO {gse_id} con título:
"{titulo}"

Se han identificado genes diferencialmente expresados (LogFC > 0 y LogFC < 0) con corrección FDR (adj_pvalue),
y se han generado diferentes tipos de gráficos exploratorios:

INTERPRETACIÓN NUMÉRICA DE LOS GRÁFICOS (para que la uses como contexto):

- PCA:
{pca_texto}

- Volcano:
{volcano_texto}

- Heatmap:
{heatmap_texto}

A continuación tienes una tabla con algunos genes destacados (GENE_SYMBOL, LogFC, pvalue, adj_pvalue):

{tabla_genes}

Por favor, escribe un informe técnico en ESPAÑOL que incluya:

1. Un RESUMEN de qué procesos biológicos podrían estar alterados (inmunidad, proliferación, apoptosis, metabolismo, etc.), integrando la información de genes y de los gráficos (PCA, volcano, heatmap) de forma cualitativa.
2. Una SECCIÓN de GENES CLAVE: selecciona 3-5 genes de la lista, explica su función conocida y su posible rol en el contexto de la enfermedad o proceso biológico implícito.
3. Una SECCIÓN de INTERPRETACIÓN DE GRÁFICOS: comenta brevemente qué sugiere el PCA sobre la separación de muestras, qué indica el volcano sobre la magnitud y significancia de los cambios, y qué patrones generales se observan en el heatmap.
4. Una SECCIÓN de HIPÓTESIS: propone 2-3 hipótesis concretas que podrían validarse experimentalmente (por ejemplo mediante RT-qPCR, Western blot o ensayos funcionales).

No añadas introducciones genéricas sobre transcriptómica; céntrate en interpretar la lista de genes y los patrones globales de los gráficos.

Respuesta en formato texto, estilo académico, conciso pero claro.
"""
    
    informe_texto = ""
    
    # === 5. Llamada a Groq si hay API key ===
    if GROQ_API_KEY and GROQ_API_KEY != "gsk_TU_CLAVE_AQUI":
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3
            )
            informe_texto = completion.choices[0].message.content
            print(" Informe IA generado correctamente.")
        except Exception as e:
            print(f" Error al llamar a Groq (IA): {e}")
            informe_texto = (
                "No se pudo generar el informe con IA.\n"
                "Sin embargo, se dispone de una lista de genes significativos y de información básica sobre los gráficos.\n\n"
                "PCA:\n" + pca_texto + "\n\nVolcano:\n" + volcano_texto + "\n\nHeatmap:\n" + heatmap_texto +
                "\n\nTabla de genes:\n\n" + tabla_genes
            )
    else:
        print(" GROQ_API_KEY no configurada o placeholder. Informe IA no se generará.")
        informe_texto = (
            "La API de IA no está configurada. A continuación se muestra una descripción automática básica "
            "de los resultados y de los gráficos.\n\n"
            "PCA:\n" + pca_texto + "\n\nVolcano:\n" + volcano_texto + "\n\nHeatmap:\n" + heatmap_texto +
            "\n\nTabla de genes clave:\n\n" + tabla_genes
        )
    
    # === 6. Guardar informe en disco ===
    ruta_informe = os.path.join(base_path, "informe_biologico.txt")
    with open(ruta_informe, "w", encoding="utf-8") as f:
        f.write(f"INFORME AUTOMÁTICO DE INTERPRETACIÓN - DATASET {gse_id}\n")
        f.write("="*80 + "\n\n")
        f.write(informe_texto)
    
    print(f" Informe guardado en: {ruta_informe}")
    return informe_texto


def interpretar_graficos(gse_id, base_path, genes_sig):
    """
    Genera texto descriptivo básico sobre PCA, volcano y heatmap usando solo datos numéricos.
    No lee las imágenes; se basa en matriz_normalizada y resultados_completos.
    """
    # Valores por defecto
    pca_texto = "No se pudo calcular la varianza explicada del PCA (faltan datos)."
    volcano_texto = "No se pudo resumir el volcano (no hay resultados estadísticos disponibles)."
    heatmap_texto = "El heatmap se ha generado usando los genes con mayor variabilidad o significancia."
    
    # PCA
    try:
        df_norm = pd.read_csv(os.path.join(base_path, "matriz_normalizada.csv"), index_col=0)
        meta = pd.read_csv(os.path.join(base_path, "metadata_procesada.csv"), index_col=0)
        pca = PCA(n_components=2)
        comps = pca.fit_transform(df_norm.T.fillna(0))
        var_exp = pca.explained_variance_ratio_
        pca_texto = (
            f"El PCA sobre la matriz normalizada muestra que PC1 explica aproximadamente "
            f"{var_exp[0]*100:.1f}% de la varianza y PC2 alrededor de {var_exp[1]*100:.1f}%. "
        )
        if 'grupo_analisis' in meta.columns and meta['grupo_analisis'].nunique() == 2:
            grupos = meta['grupo_analisis'].value_counts().to_dict()
            pca_texto += (
                f"Se han considerado {len(meta)} muestras repartidas en {len(grupos)} grupos "
                f"({grupos}). Visualmente se espera cierta separación entre grupos en el plano PC1–PC2."
            )
        else:
            pca_texto += (
                "No se han identificado claramente dos grupos experimentales, por lo que la interpretación "
                "de la separación entre muestras es más exploratoria."
            )
    except Exception as e:
        pca_texto = f"No se pudo calcular el PCA por un error técnico ({e})."
    
    # Volcano
    try:
        resultados = pd.read_csv(os.path.join(base_path, "resultados_completos.csv"))
        if 'adj_pvalue' in resultados.columns and 'LogFC' in resultados.columns and not resultados.empty:
            n_total = resultados.shape[0]
            sig = resultados[resultados['adj_pvalue'] < 0.05]
            n_sig = sig.shape[0]
            n_up = sig[sig['LogFC'] > 0].shape[0]
            n_down = sig[sig['LogFC'] < 0].shape[0]
            volcano_texto = (
                f"El análisis diferencial ha evaluado aproximadamente {n_total} genes. "
                f"De ellos, {n_sig} presentan una FDR < 0.05, con {n_up} genes sobreexpresados "
                f"y {n_down} infraexpresados en el grupo de interés. "
                "El volcano plot refleja esta asimetría entre genes up- y down-regulados."
            )
        else:
            volcano_texto = (
                "No hay columna 'adj_pvalue' o 'LogFC' en los resultados, por lo que el volcano plot solo "
                "puede interpretarse de forma exploratoria (sin umbral de significación estadística)."
            )
    except Exception as e:
        volcano_texto = f"No se pudo resumir el volcano por un error al leer los resultados ({e})."
    
    # Heatmap
    try:
        if genes_sig is not None and not genes_sig.empty:
            n_heat = min(50, genes_sig.shape[0])
            heatmap_texto = (
                f"El heatmap se ha construido usando los {n_heat} genes más significativos "
                "según FDR, realizando una estandarización tipo Z-score por gen. "
                "Se espera observar patrones de coexpresión y posibles clústeres de muestras "
                "coherentes con los grupos experimentales."
            )
        else:
            heatmap_texto = (
                "El heatmap se ha generado seleccionando los genes con mayor variabilidad global, "
                "por lo que su interpretación es principalmente exploratoria (sin filtros de FDR)."
            )
    except Exception as e:
        heatmap_texto = f"No se pudo describir el heatmap por un error ({e})."
    
    return pca_texto, volcano_texto, heatmap_texto