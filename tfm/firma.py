"""
Derivacion de la firma: criterios de replicacion y panel minimo.

La replicacion se mide entre cohortes ajustadas POR SEPARADO, nunca entre folds
LODO. El motivo es cuantitativo: dos folds LODO comparten una mediana del 97,6 %
de sus muestras de entrenamiento, y su acuerdo de signo resulto ser del 100,0 %
en las 28 parejas, frente al 77,33 % entre mitades disjuntas de tamano
comparable. Una metrica que no puede tomar valores bajos no aporta informacion.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tfm.validacion import lodo

UMBRAL_D = 0.8   # efecto grande, convencion de Cohen


def d_de_cohen(datos, genes) -> pd.DataFrame:
    """d de Cohen de cada gen en cada cohorte, calculada independientemente."""
    salida = {}
    for gse, (X, y) in datos.items():
        if len(np.unique(y)) < 2:
            continue
        Xg = X[genes]
        a, b = Xg[y == 0], Xg[y == 1]
        n0, n1 = len(a), len(b)
        if n0 < 2 or n1 < 2:
            continue
        s = np.sqrt(((n0 - 1) * a.var(ddof=1) + (n1 - 1) * b.var(ddof=1))
                    / (n0 + n1 - 2))
        salida[gse] = (b.mean() - a.mean()) / s.replace(0, np.nan)
    return pd.DataFrame(salida)


def replicados(D: pd.DataFrame, clases: dict[int, str],
               umbral: float = UMBRAL_D) -> pd.DataFrame:
    """Genes con |d| > umbral y misma direccion en TODAS las cohortes.

    Se ordena por el efecto MINIMO entre cohortes, no por la media: eso penaliza
    a los genes que dependen de una sola cohorte para parecer fuertes.
    """
    cols = list(D.columns)
    mismo = (D[cols] > 0).all(axis=1) | (D[cols] < 0).all(axis=1)
    magnitud = (D[cols].abs() > umbral).all(axis=1)
    sel = D[mismo & magnitud].copy()
    sel["d_Media"] = sel[cols].mean(axis=1)
    sel["d_Minima_Abs"] = sel[cols].abs().min(axis=1)
    sel["Direccion"] = np.where(sel["d_Media"] > 0, clases[1], clases[0])
    return sel.sort_values("d_Minima_Abs", ascending=False)


def concordancia_de_signo(coef: pd.DataFrame) -> dict:
    """Acuerdo direccional entre modelos, con el numero de genes en comun."""
    cols = list(coef.columns)
    k = len(cols)
    signos = np.sign(coef[cols])
    no_nulo = (coef[cols] != 0)
    n_no_nulo = no_nulo.sum(axis=1)
    perfecto = (n_no_nulo == k) & (signos.sum(axis=1).abs() == k)
    return {
        "k": k,
        "genes_seleccionados_alguna_vez": int((n_no_nulo > 0).sum()),
        "genes_seleccionados_en_todas": int((n_no_nulo == k).sum()),
        "genes_acuerdo_signo_perfecto": int(perfecto.sum()),
    }


def panel_minimo(datos, ranking: list[str], tamanos: list[int],
                 modelo: dict | None = None,
                 tolerancia: float = 0.01) -> tuple[int, pd.DataFrame]:
    """Panel mas pequeno que conserva el AUC dentro de `tolerancia` del maximo.

    Es lo que convierte una lista de mil genes en algo utilizable: sin este paso
    una firma no es un panel.
    """
    filas = []
    for k in tamanos:
        if k > len(ranking):
            continue
        rs = [r for r in lodo(datos, ranking[:k], modelo) if r.evaluable]
        if not rs:
            continue
        filas.append({
            "N_Genes": k,
            "AUC_Media": float(np.mean([r.auc for r in rs])),
            "Bal_Acc_Media": float(np.mean([r.balanced_accuracy for r in rs])),
            "AUC_Minima": float(np.min([r.auc for r in rs])),
        })
    curva = pd.DataFrame(filas)
    if curva.empty:
        return 0, curva
    techo = curva["AUC_Media"].max()
    minimo = int(curva[curva["AUC_Media"] >= techo - tolerancia]["N_Genes"].min())
    return minimo, curva
