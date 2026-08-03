import GEOparse
import pandas as pd
import os
import re

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clasificar_dataset(gse_id):
    """Detecta tipo de dataset y ruta de análisis óptima."""
    print(f"\n PASO 0: CLASIFICANDO {gse_id}...")
    path = os.path.join(_RAIZ, f"TFM_{gse_id}")
    os.makedirs(path, exist_ok=True)
    
    # Intentar cargar localmente primero
    local_file = os.path.join(path, f"{gse_id}_family.soft.gz")
    try:
        if os.path.exists(local_file):
            print(f" -> Usando archivo local: {local_file}")
            gse = GEOparse.get_GEO(filepath=local_file, silent=True)
        else:
            gse = GEOparse.get_GEO(geo=gse_id, destdir=path, silent=True)
        
        # 1. ANÁLISIS DE PLATAFORMA  CORREGIDO
        gpls = list(gse.gpls.values())
        plataformas = []
        for gpl in gpls:
            try:
                plataformas.append(gpl.metadata.get('title', ['N/A'])[0])
            except:
                plataformas.append('N/A')
        
        print(f" Plataformas encontradas: {len(plataformas)}")
        
        # Patrones para clasificación
        patron_microarray = re.compile(r'(Affymetrix|Illumina.*Bead|Agilent|GPL\d+|microarray)', re.I)
        patron_rnaseq = re.compile(r'(RNA-Seq|RNAseq|count|reads|HTSeq)', re.I)
        patron_scrna = re.compile(r'(single-cell|scRNA|10X|Drop-seq)', re.I)
        
        # 2. SCORES DE CLASIFICACIÓN  CORREGIDO
        texto_platforms = ' '.join(plataformas)
        texto_meta = ' '.join(gse.phenotype_data.astype(str).values.flatten()[:1000])  # Limitar tamaño
        
        scores = {
            'microarray': len(patron_microarray.findall(texto_platforms)),
            'bulk_rnaseq': len(patron_rnaseq.findall(texto_meta)),
            'scrna': len(patron_scrna.findall(texto_meta))
        }
        
        # 3. ANÁLISIS DE MATRIZ
        try:
            df = gse.pivot_samples('VALUE')
            tipo_matriz = clasificar_matriz(df)
        except:
            tipo_matriz = 'desconocido'
        
        # DECISIÓN FINAL
        if scores['microarray'] > 0 or tipo_matriz == 'microarray':
            ruta = 'microarray'
        elif scores['bulk_rnaseq'] > 0 or tipo_matriz == 'rnaseq_count':
            ruta = 'bulk_rnaseq'
        elif scores['scrna'] > 0:
            ruta = 'scrna'
        else:
            ruta = 'exploratorio'
        
        print(f" TIPO: {ruta.upper()} | scores: {scores} | matriz: {tipo_matriz}")
        return gse, df if 'df' in locals() else None, ruta, plataformas
        
    except Exception as e:
        print(f" Error clasificación: {e}")
        return None, None, 'exploratorio', ['N/A']

def clasificar_matriz(df):
    """Clasifica matriz por estadísticas."""
    if df.empty or df.isna().all().all():
        return 'desconocido'
    
    try:
        max_val = df.max().max()
        min_val = df.min().min()
        
        if max_val < 1000 and min_val >= 0:
            return 'rnaseq_count'
        elif max_val > 10 and min_val > 0:
            return 'microarray'
        elif max_val > 10000:
            return 'rnaseq_raw'
        else:
            return 'normalizado'
    except:
        return 'desconocido'