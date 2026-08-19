"""
Paso 21: intervalos de confianza al 95 % por bootstrap sobre las predicciones LODO.

Responde a la duda estadistica evidente al ver dos cohortes evaluables con
n<=15 y una AUC individual de 0,44. Reporta:
  - IC por cohorte para AUC y balanced accuracy (bootstrap sobre las muestras
    del propio test-cohort).
  - IC pooled sobre todas las predicciones concatenadas (bootstrap sobre las
    muestras totales).

No reentrena nada: solo remuestrea las predicciones existentes.

Ejecutar:  python agentes/paso21_bootstrap_ic.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfm import tareas, validacion  # noqa: E402
from tfm.cohortes import RAIZ  # noqa: E402

N_BOOT = 1000
RNG = np.random.default_rng(0)


def bootstrap_auc_balacc(y, prob, pred, n=N_BOOT):
    n_obs = len(y)
    aucs, bals = [], []
    if len(np.unique(y)) < 2:
        return np.nan, np.nan, np.nan, np.nan
    for _ in range(n):
        idx = RNG.integers(0, n_obs, n_obs)
        y_b, p_b, pr_b = y[idx], prob[idx], pred[idx]
        if len(np.unique(y_b)) < 2:
            continue  # remuestreo degenerado en cohorte pequeña; se salta
        aucs.append(roc_auc_score(y_b, p_b))
        bals.append(balanced_accuracy_score(y_b, pr_b))
    if not aucs:
        return np.nan, np.nan, np.nan, np.nan
    return (np.percentile(aucs, 2.5), np.percentile(aucs, 97.5),
            np.percentile(bals, 2.5), np.percentile(bals, 97.5))


def main():
    print("=" * 78)
    print("PASO 21: IC 95 % por bootstrap sobre predicciones LODO tumor-vs-sano")
    print("=" * 78)

    t = tareas.obtener("tumor_vs_sano")
    datos, _ = t.cargar(verbose=False)
    genes = t.genes(datos)
    resultados = validacion.lodo(datos, genes, t.modelo)

    filas = []
    y_pool, prob_pool, pred_pool = [], [], []
    for r in resultados:
        if not r.evaluable:
            continue
        y_pool.append(r.y_verdadero)
        prob_pool.append(r.probabilidad)
        pred_pool.append(r.prediccion)

        auc_lo, auc_hi, bal_lo, bal_hi = bootstrap_auc_balacc(
            r.y_verdadero, r.probabilidad, r.prediccion)
        filas.append({
            "Cohorte_Test": r.cohorte,
            "n_test": r.n_test,
            "AUC": round(r.auc, 4),
            "AUC_IC95_lo": round(auc_lo, 4) if not np.isnan(auc_lo) else np.nan,
            "AUC_IC95_hi": round(auc_hi, 4) if not np.isnan(auc_hi) else np.nan,
            "BalAcc": round(r.balanced_accuracy, 4),
            "BalAcc_IC95_lo": round(bal_lo, 4) if not np.isnan(bal_lo) else np.nan,
            "BalAcc_IC95_hi": round(bal_hi, 4) if not np.isnan(bal_hi) else np.nan,
        })
        print(f"  {r.cohorte:>12} (n={r.n_test:>3})   "
              f"AUC {r.auc:.3f} [{auc_lo:.3f}, {auc_hi:.3f}]   "
              f"BalAcc {r.balanced_accuracy:.3f} [{bal_lo:.3f}, {bal_hi:.3f}]")

    # Pooled
    y_all    = np.concatenate(y_pool)
    prob_all = np.concatenate(prob_pool)
    pred_all = np.concatenate(pred_pool)
    auc_lo, auc_hi, bal_lo, bal_hi = bootstrap_auc_balacc(y_all, prob_all, pred_all)
    auc_pool = roc_auc_score(y_all, prob_all)
    bal_pool = balanced_accuracy_score(y_all, pred_all)
    filas.append({
        "Cohorte_Test": "POOLED",
        "n_test": int(len(y_all)),
        "AUC": round(auc_pool, 4),
        "AUC_IC95_lo": round(auc_lo, 4),
        "AUC_IC95_hi": round(auc_hi, 4),
        "BalAcc": round(bal_pool, 4),
        "BalAcc_IC95_lo": round(bal_lo, 4),
        "BalAcc_IC95_hi": round(bal_hi, 4),
    })
    print(f"\n  {'POOLED':>12} (n={len(y_all):>3})   "
          f"AUC {auc_pool:.3f} [{auc_lo:.3f}, {auc_hi:.3f}]   "
          f"BalAcc {bal_pool:.3f} [{bal_lo:.3f}, {bal_hi:.3f}]")

    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(RAIZ, "LODO_IC_BOOTSTRAP.csv"), index=False)

    resumen = {
        "n_bootstrap": N_BOOT,
        "auc_pooled":         float(auc_pool),
        "auc_pooled_ic95":    [float(auc_lo), float(auc_hi)],
        "balacc_pooled":      float(bal_pool),
        "balacc_pooled_ic95": [float(bal_lo), float(bal_hi)],
    }
    with open(os.path.join(RAIZ, "LODO_IC_BOOTSTRAP_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2)

    print("\nGuardado:")
    print("  LODO_IC_BOOTSTRAP.csv")
    print("  LODO_IC_BOOTSTRAP_RESUMEN.json")


if __name__ == "__main__":
    main()
