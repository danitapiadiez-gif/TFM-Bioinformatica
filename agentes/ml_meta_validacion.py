import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
import glob

# Configuración de rutas
BASE_DIR = "/Users/danieltapiadiez/Desktop"

def detectar_datasets():
    """Detecta carpetas de datasets que tienen los archivos necesarios."""
    folders = glob.glob(os.path.join(BASE_DIR, "TFM_GSE*"))
    validos = []
    for f in folders:
        if os.path.exists(os.path.join(f, "matriz_normalizada.csv")) and \
           os.path.exists(os.path.join(f, "metadata_procesada.csv")):
            validos.append(f)
    return validos

def cargar_y_limpiar(ruta_folder):
    """Carga matriz y metadatos, filtrando solo Sano y Enfermo."""
    gse_id = os.path.basename(ruta_folder).replace("TFM_", "")
    X = pd.read_csv(os.path.join(ruta_folder, "matriz_normalizada.csv"), index_col=0).T
    meta = pd.read_csv(os.path.join(ruta_folder, "metadata_procesada.csv"))
    
    if len(meta) == len(X):
        meta.index = X.index
    else:
        if 'geo_accession' in meta.columns:
            meta.set_index('geo_accession', inplace=True)
            X = X.loc[X.index.intersection(meta.index)]
            meta = meta.loc[X.index]

    def mapear(val):
        v = str(val).strip().lower()
        if v == 'enfermo': return 1
        if v == 'sano': return 0
        return -1

    if 'grupo_analisis' not in meta.columns:
        return gse_id, None, None

    meta["label"] = meta["grupo_analisis"].apply(mapear)
    mask = meta["label"] != -1
    X_filtered = X.loc[mask]
    y_filtered = meta.loc[mask, "label"].values
    
    return gse_id, X_filtered, y_filtered

def ejecutar_lodo_con_biomarcadores():
    """Ejecuta LODO y extrae la importancia de los genes (Biomarcadores de Oro)."""
    folders = detectar_datasets()
    if len(folders) < 2:
        print(f"Error: Se detectaron {len(folders)} datasets.")
        return

    print(f"--- Iniciando Meta-Validación y Búsqueda de Biomarcadores de Oro ---")
    
    datasets_data = {}
    genes_comunes = None

    for f in folders:
        gse_id, X, y = cargar_y_limpiar(f)
        if X is not None and len(X) > 0:
            datasets_data[gse_id] = (X, y)
            if genes_comunes is None:
                genes_comunes = set(X.columns)
            else:
                genes_comunes = genes_comunes.intersection(set(X.columns))

    if not genes_comunes:
        print("Error: No se encontraron genes comunes.")
        return

    genes_comunes = sorted(list(genes_comunes))
    print(f"Genes analizados en consenso: {len(genes_comunes)}")

    resultados = []
    # Diccionario para acumular coeficientes (importancia)
    importancias_acumuladas = pd.DataFrame(index=genes_comunes)

    ids = list(datasets_data.keys())
    for i in range(len(ids)):
        test_id = ids[i]
        train_ids = [ids[j] for j in range(len(ids)) if i != j]
        
        print(f"Iteración {i+1}/{len(ids)}: Test={test_id}")
        
        X_train_list = []
        y_train_list = []
        for tid in train_ids:
            X_tmp, y_tmp = datasets_data[tid]
            X_tmp = X_tmp[genes_comunes]
            scaler = StandardScaler()
            X_train_list.append(pd.DataFrame(scaler.fit_transform(X_tmp), columns=genes_comunes))
            y_train_list.append(y_tmp)
            
        X_train = pd.concat(X_train_list, ignore_index=True)
        y_train = np.concatenate(y_train_list)
        
        X_test_raw, y_test = datasets_data[test_id]
        X_test_raw = X_test_raw[genes_comunes]
        scaler_test = StandardScaler()
        X_test = scaler_test.fit_transform(X_test_raw)

        # Usamos penalización L1 (Lasso) para forzar a que solo los genes más importantes tengan peso
        model = LogisticRegression(max_iter=2000, penalty='l1', solver='liblinear', C=0.5)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        
        resultados.append({"Dataset": test_id, "Accuracy": acc})
        
        # Guardar coeficientes de esta iteración
        importancias_acumuladas[f"Fold_{test_id}"] = model.coef_[0]

    # Calcular importancia media (valor absoluto)
    importancias_acumuladas["Importancia_Media"] = importancias_acumuladas.abs().mean(axis=1)
    importancias_acumuladas["Consistencia_Signo"] = importancias_acumuladas.drop("Importancia_Media", axis=1).apply(lambda x: np.sign(x).sum(), axis=1)
    
    # Ordenar por importancia y guardar
    biomarcadores = importancias_acumuladas.sort_values("Importancia_Media", ascending=False)
    
    ruta_biomarcadores = os.path.join(BASE_DIR, "BIOMARCADORES_DE_ORO_CONSENSO.csv")
    biomarcadores.to_csv(ruta_biomarcadores)
    
    print("\n" + "="*40)
    print(f"PROCESO COMPLETADO")
    print(f"Top 10 Biomarcadores Identificados:")
    print(biomarcadores[["Importancia_Media", "Consistencia_Signo"]].head(10))
    print(f"\nLista completa guardada en: {ruta_biomarcadores}")
    print("="*40)

if __name__ == "__main__":
    ejecutar_lodo_con_biomarcadores()
