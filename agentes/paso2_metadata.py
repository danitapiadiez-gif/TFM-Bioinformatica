import pandas as pd
import numpy as np
import os


def procesar_metadata(gse_id, gse, df_raw, ruta_analisis):
    """
    PASO 2 (versión árbol de decisión):
    - Normaliza matriz de expresión según tipo de análisis (ruta_analisis).
    - Procesa metadata y define 'grupo_analisis' cuando sea posible.
    
    Devuelve:
      df_norm  -> matriz normalizada
      meta     -> metadata con columna 'grupo_analisis'
    """
    print(f"\n PASO 2: Procesando metadata y normalizando ({gse_id}) [{ruta_analisis}]...")
    base_path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    os.makedirs(base_path, exist_ok=True)
    
    # 1. Copiar metadata y limpiar nombres de columnas
    meta = gse.phenotype_data.copy()
    meta.columns = [c.replace(".", "_").replace(" ", "_") for c in meta.columns]
    print(f" Columnas metadata: {list(meta.columns)}")
    
    # 2. NORMALIZACIÓN BASE (log2 + quantile)
    df = df_raw.copy()
    
    max_val = df.max().max()
    min_val = df.min().min()
    print(f" Rango de expresión bruto: min={min_val:.3f}, max={max_val:.3f}")
    
    # Log2 si parece que son intensidades grandes o counts
    if max_val > 50:
        print("Aplicando transformación log2(x+1)...")
        df = np.log2(df + 1)
    
    # Normalización tipo quantile (simplificada, neutra respecto a ruta)
    print("Normalización tipo quantile (simplificada)...")
    ranks = df.rank(method='average', axis=0)
    df_mean = df.stack().groupby(ranks.stack().astype(int)).mean()
    df_norm = ranks.stack().astype(int).map(df_mean).unstack()
    
    # Guardar matriz normalizada (antes de normalización específica de microarray/bulk)
    df_norm.to_csv(os.path.join(base_path, "matriz_normalizada.csv"))
    print(f" Matriz normalizada guardada: {df_norm.shape}")
    
    # 3. DEFINIR GRUPOS DE ANÁLISIS
    meta['grupo_analisis'] = asignar_grupos(gse_id, meta)
    print(f" Grupos detectados: {meta['grupo_analisis'].value_counts().to_dict()}")
    
    # Guardar metadata procesada
    meta.to_csv(os.path.join(base_path, "metadata_procesada.csv"))
    
    return df_norm, meta


from groq import Groq
import json
import re
from dotenv import load_dotenv

# Cargar configuración
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def asignar_grupos(gse_id, meta):
    """
    PASO 2: Clasificación Inteligente con IA (Llama 3 vía Groq)
    Analiza la metadata y mapea a 'Sano' o 'Enfermo'.
    """
    print(f" -> Iniciando Clasificación Inteligente con IA para {gse_id}...")
    
    # 1. Preparar una muestra de la metadata y lista de valores únicos
    # Tomamos las columnas y los valores únicos de las columnas más prometedoras
    candidatos = [c for c in meta.columns if any(k in c.lower() for k in ['tissue', 'histology', 'type', 'source', 'characteristics'])]
    valores_ejemplo = {c: meta[c].unique()[:15].tolist() for c in candidatos}
    
    prompt = f"""
Eres un experto en bioinformática y oncología clínica.
Analiza los metadatos de un estudio de expresión génica (GEO ID: {gse_id}).

VALORES ÚNICOS POR COLUMNA (Muestra):
{valores_ejemplo}

TU MISIÓN:
1. Identifica qué columna es la mejor para distinguir entre pacientes 'Sanos' (controles, tejido normal, adyacente sano) y 'Enfermos' (tumores, casos, cáncer, metástasis).
2. Crea un mapeo EXHAUSTIVO para TODOS los valores que ves en esa columna.

REGLAS DE CLASIFICACIÓN:
- 'Sano': Tissue normal, Healthy, Control, Adjacent normal, NTL, Baseline.
- 'Enfermo': Tumor, Cancer, Adenocarcinoma, SQC, NSCLC, Case, Malignant.

RESPONDE ÚNICAMENTE CON UN OBJETO JSON:
{{
  "columna_seleccionada": "nombre_de_la_columna",
  "mapeo": {{
     "valor_exacto_1": "Sano",
     "valor_exacto_2": "Enfermo",
     "valor_exacto_3": "Sano"
  }}
}}
"""

    if GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0, 
                response_format={"type": "json_object"}
            )
            
            respuesta_ia = json.loads(completion.choices[0].message.content)
            col_ia = respuesta_ia.get("columna_seleccionada")
            mapeo_ia = respuesta_ia.get("mapeo")
            
            if col_ia in meta.columns and mapeo_ia:
                print(f"  IA seleccionó columna: '{col_ia}'")
                
                # Mapeo insensible a mayúsculas/espacios
                mapeo_clean = {str(k).strip().lower(): v for k, v in mapeo_ia.items()}
                
                def aplicar_mapeo(x):
                    val = str(x).strip().lower()
                    return mapeo_clean.get(val, "Desconocido")

                grupos = meta[col_ia].apply(aplicar_mapeo)
                return grupos
                
        except Exception as e:
            print(f"  Error en IA (Paso 2): {e}. Usando sistema heurístico de respaldo...")
    
    # --- SISTEMA DE RESPALDO (Heurística) si la IA falla ---
    return asignar_grupos_heuristico(meta)

def asignar_grupos_heuristico(meta):
    """Sistema de respaldo basado en reglas si la IA no está disponible."""
    columnas = meta.columns
    prioridad_bio = ['tissue', 'histology', 'diagnosis', 'disease', 'cell_type', 'treatment', 'genotype']
    scores = {}
    for col in columnas:
        c_low = col.lower()
        score = 0
        if any(key in c_low for key in prioridad_bio): score += 10
        if any(key in c_low for key in ['group', 'condition', 'class', 'phenotype', 'response']): score += 5
        if any(key in c_low for key in ['status', 'date', 'version', 'submission']): score -= 15
        if 'characteristics' in c_low: score += 3
        num_valores = len(meta[col].unique())
        if num_valores <= 1: score = -100
        elif num_valores > 8: score -= 5
        scores[col] = score

    mejores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if mejores and mejores[0][1] > 0:
        col_elegida = mejores[0][0]
        return meta[col_elegida].astype(str).apply(lambda x: x.split(':')[-1].strip() if ':' in x else x)
    
    return pd.Series('Exploratorio', index=meta.index)
