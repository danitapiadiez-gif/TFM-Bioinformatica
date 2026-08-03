"""
Paso 13: Clasificacion de subtipo histologico (ADC vs Escamoso) con LODO estricto.

Cambio de pregunta respecto al pipeline original:
  - El objetivo ya NO es tumor-vs-sano (resoluble por H&E, y dominado por
    composicion tisular: perdida de endotelio alveolar + estroma desmoplasico).
  - El objetivo es adenocarcinoma vs carcinoma escamoso, que si tiene
    consecuencia terapeutica (pemetrexed / bevacizumab contraindicados en
    escamoso) y no es trivial morfologicamente.

Correcciones metodologicas frente a ml_meta_validacion.py:
  1. Se reporta baseline de clase mayoritaria y balanced accuracy, no solo accuracy.
  2. Se excluyen cohortes con una sola clase (no son evaluables).
  3. La estabilidad de la firma se mide entre cohortes INDEPENDIENTES, no entre
     folds LODO (que comparten 71-99% del entrenamiento y por tanto no son
     replicas independientes).
  4. Rutas relativas al repositorio, no hardcodeadas al escritorio.
"""

import os
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cohortes con histologia anotada y ambas clases presentes.
# Los codigos de histologia NO son consistentes entre estudios: en GSE30219
# "SCC" significa small cell carcinoma, mientras que en GSE19188 "SCC" significa
# squamous cell carcinoma. Se mapea explicitamente para evitar ese error.
COHORTES = {
    "GSE30219": {
        "columna": "characteristics_ch1_3_histology",
        "mapa": {"ADC": "ADC", "SQC": "SQC"},  # SCC aqui = small cell -> excluido
    },
    "GSE50081": {
        "columna": "characteristics_ch1_1_histology",
        "mapa": {
            "adenocarcinoma": "ADC",
            "squamous cell carcinoma": "SQC",
            "squamous cell carcinoma x2": "SQC",
        },
    },
    "GSE19188": {
        "columna": "characteristics_ch1_1_cell_type",
        "mapa": {"ADC": "ADC", "SCC": "SQC"},  # SCC aqui = squamous
    },
}

ETIQUETA = {"ADC": 0, "SQC": 1}


def cargar_cohorte(gse, config):
    """Carga matriz y etiquetas de subtipo de un estudio, descartando ambiguos."""
    carpeta = os.path.join(BASE_DIR, f"TFM_{gse}")
    X = pd.read_csv(os.path.join(carpeta, "matriz_normalizada.csv"), index_col=0).T
    meta = pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))

    # CRITICO: alinear SIEMPRE por geo_accession, nunca por posicion.
    # En GSE30219 las columnas de la matriz estan en orden distinto a las filas
    # del metadata (mismo conjunto, otro orden): asignar por posicion, como hacia
    # ml_meta_validacion.py con `meta.index = X.index`, adjudica a cada muestra la
    # etiqueta clinica de otro paciente y destruye la senal.
    meta = meta.set_index("geo_accession")
    comunes = X.index.intersection(meta.index)
    if len(comunes) < len(X):
        print(f"  {gse}: aviso, {len(X) - len(comunes)} muestras sin metadata")
    X = X.loc[comunes]
    meta = meta.loc[comunes]

    crudo = meta[config["columna"]].astype(str).str.strip()
    subtipo = crudo.str.lower().map(
        {k.lower(): v for k, v in config["mapa"].items()}
    )

    mask = subtipo.notna().values
    descartados = dict(crudo[~mask].value_counts())
    print(f"  {gse}: {mask.sum()} usables | descartados: {descartados}")

    return X.loc[mask], subtipo[mask].map(ETIQUETA).values.astype(int)


def z_por_estudio(X, genes):
    """Estandariza dentro del estudio: unica correccion de batch aplicable
    cuando el estudio de test es enteramente held-out. Es ciega a las
    etiquetas, por lo que no hay fuga de informacion de clase."""
    return pd.DataFrame(
        StandardScaler().fit_transform(X[genes]), columns=genes
    )


def main():
    print("=" * 72)
    print("PASO 13: SUBTIPO HISTOLOGICO (ADC vs ESCAMOSO) - VALIDACION LODO")
    print("=" * 72)
    print("\n[1] Carga y armonizacion de histologia")

    datos, genes_comunes = {}, None
    for gse, cfg in COHORTES.items():
        X, y = cargar_cohorte(gse, cfg)
        if len(np.unique(y)) < 2:
            print(f"  {gse}: una sola clase -> excluido")
            continue
        datos[gse] = (X, y)
        genes_comunes = (
            set(X.columns) if genes_comunes is None
            else genes_comunes & set(X.columns)
        )

    genes = sorted(genes_comunes)
    print(f"\n  Genes comunes: {len(genes)}")
    total = sum(len(y) for _, y in datos.values())
    n_sqc = sum(int(y.sum()) for _, y in datos.values())
    print(f"  Total: {total} muestras | ADC={total - n_sqc} SQC={n_sqc}")

    print("\n[2] Validacion Leave-One-Dataset-Out")
    filas, coef_por_cohorte = [], {}
    ids = list(datos)

    for test_id in ids:
        X_te_raw, y_te = datos[test_id]
        train_ids = [g for g in ids if g != test_id]

        X_tr = pd.concat(
            [z_por_estudio(datos[g][0], genes) for g in train_ids],
            ignore_index=True,
        )
        y_tr = np.concatenate([datos[g][1] for g in train_ids])
        X_te = z_por_estudio(X_te_raw, genes)

        modelo = LogisticRegression(
            solver="liblinear", l1_ratio=1, C=0.1, max_iter=5000,
            class_weight="balanced",
        )
        modelo.fit(X_tr, y_tr)

        pred = modelo.predict(X_te)
        prob = modelo.predict_proba(X_te)[:, 1]

        # Baseline honesto: predecir siempre la clase mayoritaria del test.
        baseline = max(np.mean(y_te == 0), np.mean(y_te == 1))
        tn, fp, fn, tp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()

        filas.append({
            "Cohorte_Test": test_id,
            "n_test": len(y_te),
            "n_ADC": int((y_te == 0).sum()),
            "n_SQC": int((y_te == 1).sum()),
            "n_train": len(y_tr),
            "Baseline_Mayoritaria": round(baseline, 4),
            "Accuracy": round(accuracy_score(y_te, pred), 4),
            "Balanced_Accuracy": round(balanced_accuracy_score(y_te, pred), 4),
            "AUC": round(roc_auc_score(y_te, prob), 4),
            "Sensibilidad_SQC": round(tp / (tp + fn), 4) if (tp + fn) else np.nan,
            "Especificidad_ADC": round(tn / (tn + fp), 4) if (tn + fp) else np.nan,
            "Ganancia_vs_Baseline": round(accuracy_score(y_te, pred) - baseline, 4),
            "Genes_Seleccionados": int((modelo.coef_[0] != 0).sum()),
        })
        print(f"  Test={test_id:<10} n={len(y_te):<4} "
              f"bal.acc={balanced_accuracy_score(y_te, pred):.3f} "
              f"AUC={roc_auc_score(y_te, prob):.3f} "
              f"(baseline {baseline:.3f})")

    res = pd.DataFrame(filas)

    print("\n[3] Firma: replicacion de tamano de efecto entre cohortes")
    # Intersecar los soportes de LASSO es una mala definicion de firma: con genes
    # correlacionados L1 elige uno arbitrariamente y la interseccion se vacia por
    # motivos algoritmicos, no biologicos. Se usa la d de Cohen calculada de forma
    # independiente en cada cohorte y se exige mismo signo y magnitud en las tres.
    UMBRAL_D = 0.8  # efecto grande (convencion de Cohen)

    for gse, (X, y) in datos.items():
        Xg = X[genes]
        adc, sqc = Xg[y == 0], Xg[y == 1]
        n0, n1 = len(adc), len(sqc)
        s_pool = np.sqrt(
            ((n0 - 1) * adc.var(ddof=1) + (n1 - 1) * sqc.var(ddof=1)) / (n0 + n1 - 2)
        )
        coef_por_cohorte[gse] = (sqc.mean() - adc.mean()) / s_pool.replace(0, np.nan)

    D = pd.DataFrame(coef_por_cohorte)
    cols = list(datos)
    mismo_signo = (D[cols] > 0).all(axis=1) | (D[cols] < 0).all(axis=1)
    magnitud = (D[cols].abs() > UMBRAL_D).all(axis=1)

    D["d_Media"] = D[cols].mean(axis=1)
    D["d_Minima_Abs"] = D[cols].abs().min(axis=1)
    D["Replicado_3_Cohortes"] = mismo_signo & magnitud

    firma = D[D["Replicado_3_Cohortes"]].copy()
    firma["Direccion"] = np.where(firma["d_Media"] > 0, "Escamoso", "Adenocarcinoma")
    # Se ordena por el efecto MINIMO entre cohortes, no por la media: penaliza a los
    # genes que dependen de una sola cohorte para parecer fuertes.
    firma = firma.sort_values("d_Minima_Abs", ascending=False)

    print(f"  Umbral: |d| > {UMBRAL_D} y mismo signo en las {len(cols)} cohortes")
    print(f"  Genes replicados: {len(firma)} de {len(genes)}")
    n_sq = int((firma["Direccion"] == "Escamoso").sum())
    print(f"    hacia Escamoso: {n_sq} | hacia Adenocarcinoma: {len(firma) - n_sq}")

    # Control positivo: marcadores usados en inmunohistoquimica clinica.
    canonicos = {
        "Escamoso": ["KRT5", "KRT6A", "TP63", "DSG3", "SOX2", "PKP1", "KRT14"],
        "Adenocarcinoma": ["NAPSA", "NKX2-1", "SFTPB", "SLC34A2", "MUC1"],
    }
    print("\n  Control positivo (marcadores de IHC clinica):")
    for direccion, lista in canonicos.items():
        hallados = [g for g in lista if g in firma.index
                    and firma.loc[g, "Direccion"] == direccion]
        print(f"    {direccion:<16} {len(hallados)}/{len(lista)} recuperados: {hallados}")

    print("\n[4] Resultados")
    print(res.to_string(index=False))
    print(f"\n  TOP 15 de la firma replicada:")
    print(firma[["d_Media", "d_Minima_Abs", "Direccion"]]
          .head(15).to_string())

    res.to_csv(os.path.join(BASE_DIR, "SUBTIPO_LODO_RESULTADOS.csv"), index=False)
    firma.to_csv(os.path.join(BASE_DIR, "SUBTIPO_FIRMA_REPLICADA.csv"))

    resumen = {
        "tarea": "ADC vs Escamoso (subtipo histologico)",
        "cohortes": list(datos),
        "n_total": int(total),
        "balanced_accuracy_media": float(res["Balanced_Accuracy"].mean()),
        "auc_media": float(res["AUC"].mean()),
        "ganancia_media_vs_baseline": float(res["Ganancia_vs_Baseline"].mean()),
        "n_genes_firma_replicada": int(len(firma)),
    }
    with open(os.path.join(BASE_DIR, "SUBTIPO_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    print("\n" + "=" * 72)
    print(f"Balanced accuracy media : {resumen['balanced_accuracy_media']:.3f}")
    print(f"AUC media               : {resumen['auc_media']:.3f}")
    print(f"Ganancia vs baseline    : {resumen['ganancia_media_vs_baseline']:+.3f}")
    print("=" * 72)


if __name__ == "__main__":
    main()
