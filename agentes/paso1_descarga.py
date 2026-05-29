import GEOparse
import pandas as pd
import os

def descargar_datos(gse_id):
    """Verifica si ya existe el archivo o lo descarga, mapeando probes → símbolos."""
    print(f"\n PASO 1: Cargando/Descargando {gse_id}...")
    base_path = os.path.join(os.path.expanduser("~"), "Desktop", f"TFM_{gse_id}")
    os.makedirs(base_path, exist_ok=True)
    
    local_file = os.path.join(base_path, f"{gse_id}_family.soft.gz")
    try:
        if os.path.exists(local_file):
            print(f" -> Usando archivo local encontrado en {base_path}")
            gse = GEOparse.get_GEO(filepath=local_file, silent=True)
        else:
            gse = GEOparse.get_GEO(geo=gse_id, destdir=base_path, silent=True)
        
        # Matriz de expresión a partir de VALUE (Series Matrix)
        df = gse.pivot_samples('VALUE')
        print(f" Matriz cruda (probes): {df.shape[0]} features x {df.shape[1]} muestras")
        
        # Intentar mapear probes → símbolos
        df_mapeada = mapear_probes_a_genes(gse, df)
        
        # Guardar matriz mapeada (o probes si no se pudo mapear)
        df_mapeada.to_csv(os.path.join(base_path, "matriz_raw.csv"))
        print(f" Matriz final guardada (filas = genes o probes): {df_mapeada.shape}")
        
        return gse, df_mapeada
    
    except Exception as e:
        print(f" Error en descarga/matriz: {e}")
        return None, None


def mapear_probes_a_genes(gse, df):
    """
    Intenta mapear probes a símbolos génicos usando la tabla GPL.
    Especialmente pensado para Affymetrix (ej. GPL570, HG-U133_Plus_2).
    Si no se puede, devuelve df tal cual.
    """
    gpls = list(gse.gpls.values())
    if not gpls:
        print(" No hay plataformas (GPL) asociadas. No se mapea.")
        return df
    
    gpl = gpls[0]
    if not hasattr(gpl, "table") or gpl.table is None or gpl.table.empty:
        print(" Tabla GPL vacía o no disponible. No se mapea.")
        return df
    
    tabla = gpl.table.copy()
    print(f" GPL ID: {gpl.name}, primeras columnas: {list(tabla.columns)[:10]} ...")
    
    # Normalizar nombres de columnas para buscar símbolos
    columnas_lower = {c.lower(): c for c in tabla.columns}
    
    posibles_nombres = [
        "gene symbol", "genesymbol", "symbol", "gene_symbol",
        "gene.symbol", "gene sym", "hgnc symbol"
    ]
    
    col_symbol = None
    for nombre in posibles_nombres:
        if nombre in columnas_lower:
            col_symbol = columnas_lower[nombre]
            break
    
    if col_symbol is None:
        print(" No se encontró columna de símbolos génicos en GPL. Se mantienen probes.")
        return df
    
    if "ID" not in tabla.columns:
        print(" La tabla GPL no tiene columna 'ID'. No se puede mapear probes → genes.")
        return df
    
    print(f"Columna de símbolos usada: {col_symbol}")
    
    # Construir diccionario probe → símbolo
    try:
        mapping_df = tabla[["ID", col_symbol]].dropna()
        mapping_df = mapping_df[mapping_df[col_symbol] != ""]
        
        # Quitar múltiple anotación (ej. "TP53 /// TP53P1"), nos quedamos con el primer símbolo
        mapping_df[col_symbol] = mapping_df[col_symbol].astype(str).str.split(" /// ").str[0]
        
        # Diccionario probes → símbolos
        mapping = dict(zip(mapping_df["ID"], mapping_df[col_symbol]))
        
        # Aplicar al índice de df
        df_genes = df.copy()
        df_genes.index = df_genes.index.map(lambda x: mapping.get(x, None))
        
        # Quitar filas sin símbolo
        antes = df_genes.shape[0]
        df_genes = df_genes[~df_genes.index.isna()]
        df_genes = df_genes[df_genes.index != ""]
        despues = df_genes.shape[0]
        print(f" Probes con símbolo: {despues}/{antes}")
        
        if df_genes.empty:
            print("Después de mapear, no queda ninguna fila. Se mantienen probes.")
            return df
        
        # Agrupar por símbolo y promediar probes replicados
        df_genes = df_genes.groupby(df_genes.index).mean()
        
        print(f" Mapeo completado: {df_genes.shape[0]} genes únicos.")
        return df_genes
    
    except Exception as e:
        print(f" Error mapeando probes a genes: {e}")
        print("Se devuelve la matriz original (probes).")
        return df