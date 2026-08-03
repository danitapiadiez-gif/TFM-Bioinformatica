"""
Paso 15: Re-evaluacion honesta del LODO tumor-vs-sano.

Reproduce la validacion original (misma tarea, mismo modelo: LASSO C=0.5) y
cambia UNICAMENTE dos cosas, para que la diferencia observada sea atribuible al
reporte y no a un cambio de metodo:

  1. Alineamiento muestra-etiqueta por geo_accession (corrige las 307 muestras
     de GSE30219 que recibian la etiqueta de otro paciente).
  2. Metricas: se anade baseline de clase mayoritaria, balanced accuracy,
     sensibilidad y especificidad, y se marca como NO EVALUABLE toda cohorte de
     test con una sola clase.

Hipotesis pre-registrada: la media baja respecto al 0.811 reportado, y GSE31210
y GSE40791 quedan por debajo de su baseline. Si sale lo contrario, se reporta.
"""

import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from utils_cohortes import BASE_DIR, cargar_cohorte, genes_comunes, listar_cohortes

# Especificacion del modelo original (ml_meta_validacion.py), conservada a
# proposito: L1, C=0.5, sin ponderacion de clases.
MODELO = dict(solver="liblinear", l1_ratio=1, C=0.5, max_iter=2000)


def main():
    print("=" * 78)
    print("PASO 15: LODO TUMOR-vs-SANO CON METRICAS HONESTAS")
    print("=" * 78)

    print("\n[1] Carga (alineada por geo_accession)")
    datos = {}
    for gse in listar_cohortes():
        X, y = cargar_cohorte(gse)
        if X is None or len(X) == 0:
            print(f"  {gse}: sin etiquetas utilizables -> excluida")
            continue
        datos[gse] = (X, y)
        n0, n1 = int((y == 0).sum()), int((y == 1).sum())
        ev = "evaluable" if (n0 and n1) else "MONOCLASE (no evaluable como test)"
        print(f"  {gse:<12} n={len(y):>4}  sano={n0:>3} enfermo={n1:>3}  {ev}")

    genes = genes_comunes([X for X, _ in datos.values()])
    print(f"\n  Genes comunes a las {len(datos)} cohortes: {len(genes)}")

    print("\n[2] Validacion LODO")
    filas = []
    for test_id in datos:
        X_te_raw, y_te = datos[test_id]
        train_ids = [g for g in datos if g != test_id]

        # z-score dentro de cada estudio (unica homogeneizacion aplicable con el
        # estudio de test completamente held-out); ciega a las etiquetas.
        X_tr = pd.concat(
            [pd.DataFrame(StandardScaler().fit_transform(datos[g][0][genes]))
             for g in train_ids],
            ignore_index=True,
        )
        y_tr = np.concatenate([datos[g][1] for g in train_ids])
        X_te = StandardScaler().fit_transform(X_te_raw[genes])

        modelo = LogisticRegression(**MODELO).fit(X_tr, y_tr)
        pred = modelo.predict(X_te)
        prob = modelo.predict_proba(X_te)[:, 1]

        n0, n1 = int((y_te == 0).sum()), int((y_te == 1).sum())
        evaluable = bool(n0 and n1)
        baseline = max(n0, n1) / len(y_te)
        acc = accuracy_score(y_te, pred)

        if evaluable:
            tn, fp, fn, tp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()
            bal = balanced_accuracy_score(y_te, pred)
            auc = roc_auc_score(y_te, prob)
            sens, espec = tp / (tp + fn), tn / (tn + fp)
        else:
            bal = auc = sens = espec = np.nan

        filas.append({
            "Cohorte_Test": test_id,
            "n_test": len(y_te),
            "n_Sano": n0,
            "n_Enfermo": n1,
            "n_train": len(y_tr),
            "Evaluable": evaluable,
            "Baseline_Mayoritaria": round(baseline, 4),
            "Accuracy": round(acc, 4),
            "Balanced_Accuracy": round(bal, 4) if evaluable else np.nan,
            "AUC": round(auc, 4) if evaluable else np.nan,
            "Sensibilidad": round(sens, 4) if evaluable else np.nan,
            "Especificidad": round(espec, 4) if evaluable else np.nan,
            "Ganancia_vs_Baseline": round(acc - baseline, 4),
            "Supera_Baseline": bool(acc > baseline),
            "Genes_Seleccionados": int((modelo.coef_[0] != 0).sum()),
        })

        etq = "" if evaluable else "  [NO EVALUABLE: una sola clase]"
        print(f"  Test={test_id:<12} acc={acc:.3f} baseline={baseline:.3f} "
              f"bal.acc={'  n/a' if not evaluable else f'{bal:.3f}'}{etq}")

    res = pd.DataFrame(filas)
    ev = res[res["Evaluable"]]

    print("\n[3] Resultados")
    print(res.to_string(index=False))

    print("\n[4] Medias: ingenua frente a honesta")
    print(f"  Accuracy media sobre las {len(res)} cohortes (como en la memoria)"
          f" : {res['Accuracy'].mean():.4f}")
    print(f"  Accuracy media sobre las {len(ev)} EVALUABLES"
          f"                     : {ev['Accuracy'].mean():.4f}")
    print(f"  Balanced accuracy media sobre las evaluables"
          f"              : {ev['Balanced_Accuracy'].mean():.4f}")
    print(f"  AUC media sobre las evaluables"
          f"                            : {ev['AUC'].mean():.4f}")
    print(f"  Baseline medio de las evaluables"
          f"                          : {ev['Baseline_Mayoritaria'].mean():.4f}")
    print(f"  Ganancia media sobre baseline (evaluables)"
          f"                 : {ev['Ganancia_vs_Baseline'].mean():+.4f}")

    peores = ev[~ev["Supera_Baseline"]]
    print(f"\n  Cohortes evaluables que NO superan su baseline: "
          f"{len(peores)} de {len(ev)}")
    for _, r in peores.iterrows():
        print(f"    {r['Cohorte_Test']:<12} acc={r['Accuracy']:.3f} "
              f"vs baseline={r['Baseline_Mayoritaria']:.3f} "
              f"({r['Ganancia_vs_Baseline']:+.3f})")

    res.to_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"), index=False)

    print("\n" + "=" * 78)
    print("CONTRASTE CON LO REPORTADO EN LA MEMORIA")
    print("=" * 78)
    print(f"  Memoria (p.60): accuracy media 0.811 sobre 11 folds, "
          f"3 de ellos monoclase")
    print(f"  Honesto       : balanced accuracy media "
          f"{ev['Balanced_Accuracy'].mean():.3f} sobre {len(ev)} folds evaluables")
    print(f"  Ganancia real media sobre azar informado: "
          f"{ev['Ganancia_vs_Baseline'].mean():+.3f}")
    print("=" * 78)
    return res


if __name__ == "__main__":
    main()
