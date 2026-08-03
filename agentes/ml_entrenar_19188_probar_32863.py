import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rutas base (las mismas que en ml_entrenamiento_un_dataset.py)
BASE_DESKTOP = _RAIZ

def rutas_gse(gse_id):
    if gse_id == "GSE19188":
        base_dir = os.path.join(BASE_DESKTOP, "TFM_GSE19188")
    elif gse_id == "GSE32863":
        base_dir = os.path.join(BASE_DESKTOP, "TFM_GSE32863")
    else:
        raise ValueError(f"No hay rutas definidas aún para {gse_id}")

    ruta_matriz = os.path.join(base_dir, "matriz_normalizada.csv")
    ruta_meta   = os.path.join(base_dir, "metadata_procesada.csv")
    return ruta_matriz, ruta_meta

def crear_label_binaria(meta, gse_id):
    if gse_id == "GSE19188":
        if "grupo_analisis" not in meta.columns:
            raise ValueError("No se encuentra 'grupo_analisis' en metadata_procesada.csv de GSE19188")
        meta["label_binaria"] = (
            meta["grupo_analisis"].astype(str).str.strip().str.lower() != "normal"
        ).astype(int)

    elif gse_id == "GSE32863":
        col = "characteristics_ch1_9_tissue"
        if col not in meta.columns:
            raise ValueError(f"No se encuentra '{col}' en metadata_procesada.csv de GSE32863")
        col_values = meta[col].astype(str).str.strip().str.lower()
        meta["label_binaria"] = col_values.apply(lambda v: 1 if "tumor" in v else 0)

    else:
        raise ValueError(f"No hay regla de label_binaria para {gse_id}")

    return meta

def cargar_X_y(gse_id):
    ruta_matriz, ruta_meta = rutas_gse(gse_id)

    # Matriz: genes x muestras → transponer
    expr = pd.read_csv(ruta_matriz, index_col=0)
    X = expr.T  # muestras x genes

    meta = pd.read_csv(ruta_meta)
    meta = crear_label_binaria(meta, gse_id)

    # Alineamos por posición (asumimos mismo orden que columnas original)
    if len(meta) != len(X):
        raise ValueError(
            f"{gse_id}: metadata ({len(meta)}) y matriz ({len(X)}) no tienen el mismo número de muestras"
        )
    meta = meta.copy()
    meta.index = X.index

    y = meta["label_binaria"].values

    return X, y

def main():
    # 1. Cargar datos de ambos GSE
    X_train, y_train = cargar_X_y("GSE19188")
    X_test,  y_test  = cargar_X_y("GSE32863")

    print(f"GSE19188: {X_train.shape[0]} muestras, {X_train.shape[1]} genes")
    print(f"GSE32863: {X_test.shape[0]} muestras, {X_test.shape[1]} genes")

    # 2. Intersección de genes (columnas comunes)
    genes_comunes = X_train.columns.intersection(X_test.columns)
    print(f"Nº de genes comunes: {len(genes_comunes)}")

    if len(genes_comunes) == 0:
        raise ValueError("No hay genes comunes entre GSE19188 y GSE32863")

    X_train_common = X_train[genes_comunes]
    X_test_common  = X_test[genes_comunes]

    # 3. Escalado usando solo el train (GSE19188)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_common)
    X_test_scaled  = scaler.transform(X_test_common)

    # 4. Entrenar modelo en GSE19188 (regresión logística)
    clf = LogisticRegression(max_iter=2000)
    clf.fit(X_train_scaled, y_train)

    # 5. Evaluar en GSE32863 (validación externa)
    y_pred = clf.predict(X_test_scaled)
    y_proba = clf.predict_proba(X_test_scaled)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm  = confusion_matrix(y_test, y_pred)
    rep = classification_report(y_test, y_pred, digits=3)

    print("\n===== Validación externa: entreno en GSE19188, pruebo en GSE32863 =====")
    print(f"Accuracy (externo): {acc:.3f}")
    print(f"AUC (externo):      {auc:.3f}")
    print("Matriz de confusión (GSE32863):")
    print(cm)
    print("Classification report (GSE32863):")
    print(rep)

if __name__ == "__main__":
    main()