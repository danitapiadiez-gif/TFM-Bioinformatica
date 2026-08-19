"""
Paso 20: recalibracion de umbral (isotonica y Platt) para tumor-vs-sano.

Ataca la debilidad tecnica visible del clasificador: AUC 0,925 pero balanced
accuracy 0,772, brecha causada por umbral 0,5 fijo sobre un train desbalanceado
(938 tumores frente a 219 controles). El propio trabajo lo declaraba en
Discusion como problema corregible; aqui se corrige.

Para cada fold LODO: reentrena la regresion logistica L1 envuelta en
CalibratedClassifierCV (5-fold interno sobre el train) usando isotonica y Platt
(sigmoid). Reevalua las metricas en el test-cohort y compara con el modelo sin
calibrar.

Salidas:
  LODO_RECALIBRADO_RESULTADOS.csv  metricas por cohorte antes / despues, para
                                   isotonica y para Platt
  LODO_RECALIBRADO_RESUMEN.json    medias LODO y ganancias

Ejecutar:  python agentes/paso20_recalibracion.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, confusion_matrix, roc_auc_score,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfm import tareas, validacion  # noqa: E402
from tfm.cohortes import RAIZ  # noqa: E402


def _metricas(y, pred, prob):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y, pred),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "auc": roc_auc_score(y, prob),
        "sensibilidad": tp / (tp + fn) if (tp + fn) else np.nan,
        "especificidad": tn / (tn + fp) if (tn + fp) else np.nan,
    }


def _entrenar_calibrado(X_tr, y_tr, metodo):
    base = LogisticRegression(
        solver="liblinear", C=0.5, max_iter=2000, random_state=0,
    )
    # cv=5 hace la calibracion en cross-validation interno sobre el train:
    # no filtra informacion del test-cohort.
    cal = CalibratedClassifierCV(base, method=metodo, cv=5)
    cal.fit(X_tr, y_tr)
    return cal


def main():
    print("=" * 78)
    print("PASO 20: recalibracion isotonica y Platt sobre tumor-vs-sano")
    print("=" * 78)

    t = tareas.obtener("tumor_vs_sano")
    datos, descartadas = t.cargar(verbose=False)
    genes = t.genes(datos)
    print(f"  Cohortes cargadas: {len(datos)}  ·  genes comunes: {len(genes)}")

    # 1) LODO sin calibrar (referencia)
    print("\n[A] LODO sin calibrar (referencia)")
    ref = validacion.lodo(datos, genes, modelo=t.modelo)
    ref_por_cohorte = {r.cohorte: r for r in ref}

    # 2) LODO con recalibracion
    filas = []
    for metodo in ["isotonic", "sigmoid"]:  # sigmoid == Platt scaling
        etiqueta = "isotonica" if metodo == "isotonic" else "platt"
        print(f"\n[B] LODO con calibracion {etiqueta}")

        for test_id in datos:
            X_te_raw, y_te = datos[test_id]
            train_ids = [g for g in datos if g != test_id]
            X_tr = pd.concat(
                [validacion.escalar_por_estudio(datos[g][0], genes)
                 for g in train_ids],
                ignore_index=True,
            )
            y_tr = np.concatenate([datos[g][1] for g in train_ids])
            X_te = validacion.escalar_por_estudio(X_te_raw, genes)

            n0, n1 = int((y_te == 0).sum()), int((y_te == 1).sum())
            if not (n0 and n1):
                continue

            cal = _entrenar_calibrado(X_tr, y_tr, metodo)
            prob_cal = cal.predict_proba(X_te)[:, 1]
            pred_cal = (prob_cal >= 0.5).astype(int)

            m_cal = _metricas(y_te, pred_cal, prob_cal)

            r_ref = ref_por_cohorte[test_id]
            filas.append({
                "Cohorte_Test": test_id,
                "n_test": len(y_te),
                "Metodo": etiqueta,
                "AUC_ref": round(r_ref.auc, 4),
                "BalAcc_ref": round(r_ref.balanced_accuracy, 4),
                "Sens_ref": round(r_ref.sensibilidad, 4),
                "Espec_ref": round(r_ref.especificidad, 4),
                "AUC_cal": round(m_cal["auc"], 4),
                "BalAcc_cal": round(m_cal["balanced_accuracy"], 4),
                "Sens_cal": round(m_cal["sensibilidad"], 4),
                "Espec_cal": round(m_cal["especificidad"], 4),
                "Delta_BalAcc": round(
                    m_cal["balanced_accuracy"] - r_ref.balanced_accuracy, 4),
            })
            print(f"  {test_id:>12}  BalAcc {r_ref.balanced_accuracy:.3f} "
                  f"-> {m_cal['balanced_accuracy']:.3f}  "
                  f"(Δ {m_cal['balanced_accuracy']-r_ref.balanced_accuracy:+.3f})")

    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(RAIZ, "LODO_RECALIBRADO_RESULTADOS.csv"), index=False)

    # 3) Resumen
    resumen = {}
    for metodo in ["isotonica", "platt"]:
        sub = df[df["Metodo"] == metodo]
        resumen[metodo] = {
            "auc_ref_media":    float(sub["AUC_ref"].mean()),
            "auc_cal_media":    float(sub["AUC_cal"].mean()),
            "balacc_ref_media": float(sub["BalAcc_ref"].mean()),
            "balacc_cal_media": float(sub["BalAcc_cal"].mean()),
            "sens_cal_media":   float(sub["Sens_cal"].mean()),
            "espec_cal_media":  float(sub["Espec_cal"].mean()),
            "ganancia_balacc":  float(sub["Delta_BalAcc"].mean()),
            "n_cohortes":       int(len(sub)),
        }

    with open(os.path.join(RAIZ, "LODO_RECALIBRADO_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    print("\n" + "=" * 78)
    print("RESUMEN DE LA RECALIBRACION")
    print("=" * 78)
    for metodo, r in resumen.items():
        print(f"\n{metodo.upper()}:")
        print(f"  BalAcc referencia -> calibrada: "
              f"{r['balacc_ref_media']:.3f} -> {r['balacc_cal_media']:.3f} "
              f"(Δ {r['ganancia_balacc']:+.3f})")
        print(f"  Sensibilidad / Especificidad: "
              f"{r['sens_cal_media']:.3f} / {r['espec_cal_media']:.3f}")
        print(f"  AUC (no debe cambiar): "
              f"{r['auc_ref_media']:.3f} -> {r['auc_cal_media']:.3f}")

    print("\nGuardado:")
    print("  LODO_RECALIBRADO_RESULTADOS.csv")
    print("  LODO_RECALIBRADO_RESUMEN.json")


if __name__ == "__main__":
    main()
