import sys
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report

# Raiz del proyecto, derivada de la ubicacion de este fichero: el pipeline ya no
# depende de que los datos esten en el escritorio de una maquina concreta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DESKTOP = _RAIZ


def rutas_gse(gse_id):
    base_dir = os.path.join(BASE_DESKTOP, f"TFM_{gse_id}")
    ruta_matriz = os.path.join(base_dir, "matriz_normalizada.csv")
    ruta_meta   = os.path.join(base_dir, "metadata_procesada.csv")
    return base_dir, ruta_matriz, ruta_meta


def cargar_datos(gse_id):
    base_dir, ruta_matriz, ruta_meta = rutas_gse(gse_id)

    expr = pd.read_csv(ruta_matriz, index_col=0)  # genes x muestras
    X = expr.T                                   # muestras x genes

    meta = pd.read_csv(ruta_meta)
    return base_dir, X, meta


def crear_label_binaria(meta, gse_id):
    """
    Crea la etiqueta 0 (Sano) y 1 (Enfermo) basada en la columna 'grupo_analisis'.
    Universal para cualquier dataset procesado por el pipeline IA.
    """
    if "grupo_analisis" not in meta.columns:
        raise ValueError("No se encuentra la columna 'grupo_analisis' en metadata_procesada.csv")
    
    # Mapeo universal: Enfermo -> 1, Sano -> 0
    # Todo lo demás se ignora o se marca como -1 para filtrar
    def mapear(val):
        v = str(val).strip().lower()
        if v == 'enfermo': return 1
        if v == 'sano': return 0
        return -1

    meta["label_binaria"] = meta["grupo_analisis"].apply(mapear)
    
    # Filtrar muestras que no sean Sano ni Enfermo para el entrenamiento
    antes = len(meta)
    meta = meta[meta["label_binaria"] != -1]
    despues = len(meta)
    
    if despues < 4: # Mínimo para un split 80/20 con sentido
        raise ValueError(f"No hay suficientes muestras clasificadas como Sano/Enfermo para ML (solo {despues} de {antes})")
        
    print(f" -> ML: Usando {despues} muestras (Sano/Enfermo) de {antes} totales.")
    return meta


def preparar_X_y(X, meta):
    if len(meta) != len(X):
        raise ValueError(
            f"metadata_procesada ({len(meta)} filas) y matriz_normalizada ({len(X)} muestras) "
            "no tienen el mismo número de muestras."
        )

    meta = meta.copy()
    meta.index = X.index

    if "label_binaria" not in meta.columns:
        raise ValueError("No se ha encontrado la columna 'label_binaria' en metadata")

    y = meta["label_binaria"].values
    return X, y


def entrenar_y_evaluar_modelos(X, y, gse_id, base_dir):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    resultados = []
    importancias_genes = {}

    # 1. Regresión logística
    logreg = LogisticRegression(max_iter=2000)
    logreg.fit(X_train_scaled, y_train)
    y_pred = logreg.predict(X_test_scaled)
    y_proba = logreg.predict_proba(X_test_scaled)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm  = confusion_matrix(y_test, y_pred)
    rep = classification_report(y_test, y_pred, digits=3)

    resultados.append({
        "GSE": gse_id,
        "modelo": "LogisticRegression",
        "accuracy": acc,
        "auc": auc
    })

    genes = X.columns
    coef = logreg.coef_[0]
    df_imp_logreg = pd.DataFrame({
        "gen": genes,
        "coef_logreg": coef,
        "abs_coef_logreg": np.abs(coef)
    }).sort_values("abs_coef_logreg", ascending=False)
    importancias_genes["LogisticRegression"] = df_imp_logreg

    print(f"\n--- LogisticRegression ({gse_id}) ---")
    print(f"Accuracy: {acc:.3f}")
    print(f"AUC:      {auc:.3f}")
    print("Matriz de confusión:")
    print(cm)
    print("Classification report:")
    print(rep)

    # 2. Random Forest
    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        n_jobs=-1,
        random_state=42
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_proba_rf = rf.predict_proba(X_test)[:, 1]

    acc_rf = accuracy_score(y_test, y_pred_rf)
    auc_rf = roc_auc_score(y_test, y_proba_rf)
    cm_rf  = confusion_matrix(y_test, y_pred_rf)
    rep_rf = classification_report(y_test, y_pred_rf, digits=3)

    resultados.append({
        "GSE": gse_id,
        "modelo": "RandomForest",
        "accuracy": acc_rf,
        "auc": auc_rf
    })

    imp_rf = rf.feature_importances_
    df_imp_rf = pd.DataFrame({
        "gen": genes,
        "importancia_rf": imp_rf
    }).sort_values("importancia_rf", ascending=False)
    importancias_genes["RandomForest"] = df_imp_rf

    print(f"\n--- RandomForest ({gse_id}) ---")
    print(f"Accuracy: {acc_rf:.3f}")
    print(f"AUC:      {auc_rf:.3f}")
    print("Matriz de confusión:")
    print(cm_rf)
    print("Classification report:")
    print(rep_rf)

    # 3. SVM lineal
    svm = SVC(kernel="linear", probability=True, random_state=42)
    svm.fit(X_train_scaled, y_train)
    y_pred_svm = svm.predict(X_test_scaled)
    y_proba_svm = svm.predict_proba(X_test_scaled)[:, 1]

    acc_svm = accuracy_score(y_test, y_pred_svm)
    auc_svm = roc_auc_score(y_test, y_proba_svm)
    cm_svm  = confusion_matrix(y_test, y_pred_svm)
    rep_svm = classification_report(y_test, y_pred_svm, digits=3)

    resultados.append({
        "GSE": gse_id,
        "modelo": "SVM_linear",
        "accuracy": acc_svm,
        "auc": auc_svm
    })

    print(f"\n--- SVM_linear ({gse_id}) ---")
    print(f"Accuracy: {acc_svm:.3f}")
    print(f"AUC:      {auc_svm:.3f}")
    print("Matriz de confusión:")
    print(cm_svm)
    print("Classification report:")
    print(rep_svm)

    # Guardar métricas en CSV
    df_res = pd.DataFrame(resultados)
    ruta_res = os.path.join(base_dir, "resultados_ml.csv")
    df_res.to_csv(ruta_res, index=False)
    print(f"\n Métricas ML guardadas en: {ruta_res}")

    # Guardar importancias de genes y top20 para cualquier GSE
    if importancias_genes:
        df_comb = importancias_genes["LogisticRegression"].merge(
            importancias_genes["RandomForest"],
            on="gen",
            how="outer"
        )
        ruta_imp = os.path.join(base_dir, f"genes_importantes_ml_{gse_id}.csv")
        df_comb.to_csv(ruta_imp, index=False)
        print(f" Importancia de genes guardada en: {ruta_imp}")

        top20 = df_comb.sort_values("abs_coef_logreg", ascending=False).head(20)
        ruta_top20 = os.path.join(base_dir, f"top20_genes_ml_{gse_id}.csv")
        top20.to_csv(ruta_top20, index=False)
        print(f" Top 20 genes ML guardado en: {ruta_top20}")

    return df_res, importancias_genes


def entrenar_modelos_ml(gse_id):
    base_dir, X, meta = cargar_datos(gse_id)
    meta = crear_label_binaria(meta, gse_id)
    X, y = preparar_X_y(X, meta)
    return entrenar_y_evaluar_modelos(X, y, gse_id, base_dir)


def main():
    if len(sys.argv) < 2:
        print("Uso: python paso5b_ml_entrenamiento.py GSE19188")
        sys.exit(1)

    gse_id = sys.argv[1]
    entrenar_modelos_ml(gse_id)


if __name__ == "__main__":
    main()