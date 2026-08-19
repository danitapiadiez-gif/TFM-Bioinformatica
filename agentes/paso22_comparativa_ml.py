"""
Paso 22: comparativa LODO de tres clasificadores para tumor-vs-sano.

Cierra el OE2 con datos: evalua LASSO L1, Random Forest y SVM lineal bajo el
mismo bucle LODO (mismas cohortes, misma normalizacion por estudio, misma
semilla), y compara AUC / balanced accuracy / sensibilidad / especificidad.

Justifica de forma explicita la eleccion de LASSO por interpretabilidad, ahora
con la referencia numerica de los otros dos modelos en el mismo protocolo de
validacion externa, no por decision de diseno.

Ejecutar:  python agentes/paso22_comparativa_ml.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, confusion_matrix, roc_auc_score,
)
from sklearn.svm import SVC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfm import tareas, validacion  # noqa: E402
from tfm.cohortes import RAIZ  # noqa: E402


MODELOS = {
    "LASSO_L1": lambda: LogisticRegression(
        penalty="l1", solver="liblinear", C=0.5, max_iter=2000, random_state=0),
    "Random_Forest": lambda: RandomForestClassifier(
        n_estimators=300, max_features="sqrt", random_state=0, n_jobs=-1),
    "SVM_lineal": lambda: SVC(
        kernel="linear", C=1.0, probability=True, random_state=0),
}


def _metricas(y, pred, prob):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y, pred),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "auc": roc_auc_score(y, prob),
        "sensibilidad": tp / (tp + fn) if (tp + fn) else np.nan,
        "especificidad": tn / (tn + fp) if (tn + fp) else np.nan,
    }


def main():
    print("=" * 78)
    print("PASO 22: comparativa LODO de LASSO L1 vs Random Forest vs SVM lineal")
    print("=" * 78)

    t = tareas.obtener("tumor_vs_sano")
    datos, _ = t.cargar(verbose=False)
    genes = t.genes(datos)
    print(f"\nCohortes: {len(datos)}   Genes comunes: {len(genes)}")

    filas = []
    resumen = {}
    for nombre, factory in MODELOS.items():
        print(f"\n[{nombre}]")
        aucs, bals, sens, espec = [], [], [], []
        for test_id in datos:
            X_te_raw, y_te = datos[test_id]
            n0, n1 = int((y_te == 0).sum()), int((y_te == 1).sum())
            if not (n0 and n1):
                continue
            train_ids = [g for g in datos if g != test_id]
            X_tr = pd.concat(
                [validacion.escalar_por_estudio(datos[g][0], genes)
                 for g in train_ids],
                ignore_index=True,
            )
            y_tr = np.concatenate([datos[g][1] for g in train_ids])
            X_te = validacion.escalar_por_estudio(X_te_raw, genes)

            m = factory().fit(X_tr, y_tr)
            pred = m.predict(X_te)
            prob = m.predict_proba(X_te)[:, 1]
            met = _metricas(y_te, pred, prob)

            filas.append({
                "Modelo": nombre, "Cohorte_Test": test_id, "n_test": len(y_te),
                "AUC":              round(met["auc"], 4),
                "Balanced_Accuracy":round(met["balanced_accuracy"], 4),
                "Sensibilidad":     round(met["sensibilidad"], 4),
                "Especificidad":    round(met["especificidad"], 4),
            })
            aucs.append(met["auc"])
            bals.append(met["balanced_accuracy"])
            sens.append(met["sensibilidad"])
            espec.append(met["especificidad"])
            print(f"  {test_id:>12}  AUC {met['auc']:.3f}  "
                  f"BalAcc {met['balanced_accuracy']:.3f}")

        resumen[nombre] = {
            "n_cohortes_evaluables":  len(aucs),
            "auc_media":              float(np.mean(aucs)),
            "auc_desv":               float(np.std(aucs, ddof=1)),
            "balanced_accuracy_media":float(np.mean(bals)),
            "sensibilidad_media":     float(np.mean(sens)),
            "especificidad_media":    float(np.mean(espec)),
        }

    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(RAIZ, "resultados/comparativa_ml/COMPARATIVA_ML_LODO.csv"), index=False)

    with open(os.path.join(RAIZ, "resultados/comparativa_ml/COMPARATIVA_ML_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2)

    print("\n" + "=" * 78)
    print("RESUMEN COMPARATIVO (LODO, medias sobre cohortes evaluables)")
    print("=" * 78)
    print(f"{'Modelo':<16} {'AUC':>10} {'BalAcc':>10} {'Sens.':>10} {'Espec.':>10}")
    for nombre, r in resumen.items():
        print(f"{nombre:<16} "
              f"{r['auc_media']:>10.3f} "
              f"{r['balanced_accuracy_media']:>10.3f} "
              f"{r['sensibilidad_media']:>10.3f} "
              f"{r['especificidad_media']:>10.3f}")

    print("\nGuardado:")
    print("  COMPARATIVA_ML_LODO.csv")
    print("  COMPARATIVA_ML_RESUMEN.json")


if __name__ == "__main__":
    main()
