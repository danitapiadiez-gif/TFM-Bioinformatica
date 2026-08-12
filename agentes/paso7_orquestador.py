import time
from paso0_clasificador import clasificar_dataset
from paso1_descarga import descargar_datos, mapear_probes_a_genes
from paso2_metadata import procesar_metadata
from paso2a_microarray import normalizar_microarray
from paso2b_bulk import normalizar_bulk
from paso3_diferencial import ejecutar_diferencial
from paso4_informe import generar_informe
from paso5_graficos import generar_graficos
from paso6_dashboard import generar_dashboard

from paso5b_ml_entrenamiento import entrenar_modelos_ml


def lanzar_analisis_completo(gse_id):
    """Pipeline maestro con árbol de decisión."""
    print(f"\n{'='*80}")
    print(f" FRAMEWORK TRANSCRIPTÓMICO v3.0 - {gse_id}")
    print(f"{'='*80}")
    
    # PASO 0: CLASIFICACIÓN CRÍTICA
    gse, df_raw, ruta, plataformas = clasificar_dataset(gse_id)
    if gse is None:
        print(" Fallo en clasificación")
        return
    
    print(f" Ruta seleccionada: {ruta.upper()}")
    print(f" Plataformas: {', '.join(plataformas[:2])}...")
    
    # PASO 1: DESCARGA / MAPEADO
    if df_raw is None or df_raw.empty:
        print(f" Descargando datos para {gse_id}...")
        gse, df_raw = descargar_datos(gse_id)
    
    if gse is None or df_raw is None or df_raw.empty:
        print(f" Fallo en descarga o matriz vacía para {gse_id}")
        return
    
    # PASO 1.5: TRADUCCIÓN GENÓMICA (Probes -> Symbols)
    print(f"\n --- PASO 1.5: TRADUCCIÓN GENÓMICA ({gse_id}) ---")
    df_raw = mapear_probes_a_genes(gse, df_raw)
    
    # PASO 2: METADATA + NORMALIZACIÓN BASE
    df_norm, meta = procesar_metadata(gse_id, gse, df_raw, ruta)
    if df_norm is None or meta is None:
        print(" Fallo en procesamiento de metadata/normalización")
        return

    # === FILTRO DE ESTUDIO COMPARATIVO (Mejora solicitada) ===
    if 'grupo_analisis' in meta.columns:
        conteo = meta['grupo_analisis'].value_counts().to_dict()
        print(f" -> Resumen de clasificación: {conteo}")
        
        if 'Sano' not in conteo or 'Enfermo' not in conteo:
            print(f"\n ⏭ SALTANDO ESTUDIO: {gse_id} no es un estudio comparativo (falta grupo Sano o Enfermo).")
            print(" Solo procesamos estudios con casos y controles para el TFM.")
            return
        
        if conteo['Sano'] < 2 or conteo['Enfermo'] < 2:
            print(f"\n ⏭ SALTANDO ESTUDIO: {gse_id} tiene muestras insuficientes en algún grupo (<2).")
            return
    
    # PASO 2A/2B: Normalización específica según ruta
    if ruta == 'microarray':
        df_final = normalizar_microarray(df_norm, meta, gse_id)
    elif ruta == 'bulk_rnaseq':
        df_final = normalizar_bulk(df_norm, meta, gse_id)
    else:
        df_final = df_norm
    
    # PASO 3: DIFERENCIAL
    genes_sig = ejecutar_diferencial(gse_id, df_final, meta)
    
    # PASO 4: INFORME SIEMPRE (aunque no haya genes significativos)
    if genes_sig is not None and not genes_sig.empty:
        print(f" Hay {len(genes_sig)} genes significativos. Informe diferencial.")
        generar_informe(gse_id, genes_sig, gse)
    else:
        print(" Sin genes significativos o diseño no válido. Informe exploratorio.")
        generar_informe(gse_id, genes_sig, gse)
    
    # PASO 5: GRÁFICOS
    generar_graficos(gse_id)

    # PASO 5B: MACHINE LEARNING
    try:
        print("\n Ejecutando módulo de Machine Learning...")
        entrenar_modelos_ml(gse_id)
        print(" ML completado y resultados_ml.csv generado.")
    except Exception as e:
        print(f" Error en módulo ML: {e}")
        print("   Continuamos sin resultados de ML para el dashboard.")
    
    # PASO 6: DASHBOARD (al final, para incluir ML si existe)
    generar_dashboard(gse_id)
    
    if genes_sig is not None and not genes_sig.empty:
        print(f"\n ÉXITO COMPLETO ")
        print(f" ~/Desktop/TFM_{gse_id}/")
        print(f" Ruta: {ruta} | Genes sig: {len(genes_sig)}")
    else:
        print("\n Análisis completado en modo EXPLORATORIO (sin diferencial significativo).")
        print(f" ~/Desktop/TFM_{gse_id}/")


if __name__ == "__main__":
    import os
    
    archivo_datasets = "datasets.txt"
    if not os.path.exists(archivo_datasets):
        # Crear uno por defecto si no existe
        with open(archivo_datasets, "w") as f:
            f.write("GSE19188\n")
        print(f" Se ha creado {archivo_datasets}. Añade ahí los IDs de GEO.")
        gse_list = ["GSE19188"]
    else:
        with open(archivo_datasets, "r") as f:
            gse_list = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"\n Se han encontrado {len(gse_list)} datasets para procesar.")
    
    for gse in gse_list:
        print(f"\n{'#'*60}")
        print(f" INICIANDO PROCESAMIENTO DE: {gse}")
        print(f"{'#'*60}")
        
        try:
            lanzar_analisis_completo(gse)
            print(f"\n FINALIZADO CON ÉXITO: {gse}")
        except Exception as e:
            print(f"\n [!] ERROR CRÍTICO procesando {gse}: {e}")
            print(" Saltando al siguiente dataset...")
        
        time.sleep(5)  # Breve pausa para no saturar
    
    print(f"\n{'='*60}")
    print(" PIPELINE FINALIZADO PARA TODA LA LISTA")
    print(f"{'='*60}")