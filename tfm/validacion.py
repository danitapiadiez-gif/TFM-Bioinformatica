"""
Validacion externa Leave-One-Dataset-Out: una sola implementacion.

Antes del refactor este bucle estaba reimplementado en cinco scripts (pasos 13,
15, 16, 17 y 19), y el bloque de estandarizacion por estudio, en cuatro. Cada
copia podia divergir: de hecho divergian en el modelo, en el escalado y en las
metricas reportadas.

Aqui hay una sola funcion, `lodo()`, que devuelve para cada fold todo lo que los
distintos analisis necesitan: metricas, predicciones, puntuaciones de decision y
coeficientes. Cada uso toma lo que le hace falta.

Decisiones que quedan fijadas en un unico lugar:

  - Estandarizacion DENTRO de cada estudio, ciega a las etiquetas. Es la unica
    homogeneizacion aplicable cuando el estudio de test esta completamente
    held-out, y no filtra informacion de clase.
  - random_state fijado: liblinear baraja coordenadas internamente y sin semilla
    los resultados varian entre ejecuciones.
  - Toda cohorte de test con una sola clase se marca `evaluable=False`. En ella
    la accuracy trivial es 1,000 por definicion, y las metricas que dependen de
    dos clases (AUC, balanced accuracy, especificidad) no existen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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

# Especificacion por defecto. Cada tarea puede sobreescribirla desde su
# configuracion; el random_state no se deja a criterio de la tarea.
MODELO_POR_DEFECTO = {
    "solver": "liblinear",
    "l1_ratio": 1,
    "C": 0.5,
    "max_iter": 2000,
}
SEMILLA = 0


@dataclass
class ResultadoFold:
    """Todo lo que produce un fold LODO, para que ningun uso tenga que repetirlo."""

    cohorte: str
    n_test: int
    n_clase_0: int
    n_clase_1: int
    n_train: int
    evaluable: bool
    baseline: float
    accuracy: float
    balanced_accuracy: float
    auc: float
    sensibilidad: float
    especificidad: float
    n_genes_seleccionados: int
    prediccion: np.ndarray = field(repr=False)
    probabilidad: np.ndarray = field(repr=False)
    score_decision: np.ndarray = field(repr=False)
    coeficientes: pd.Series = field(repr=False)
    muestras: pd.Index = field(repr=False)
    y_verdadero: np.ndarray = field(repr=False)

    @property
    def ganancia(self) -> float:
        return self.accuracy - self.baseline

    @property
    def supera_baseline(self) -> bool:
        return self.accuracy > self.baseline


def escalar_por_estudio(X: pd.DataFrame, genes: list[str]) -> pd.DataFrame:
    """Estandariza dentro del estudio. Ciega a las etiquetas."""
    return pd.DataFrame(
        StandardScaler().fit_transform(X[genes]), columns=genes
    )


def _construir_modelo(spec: dict[str, Any] | None) -> LogisticRegression:
    parametros = dict(MODELO_POR_DEFECTO)
    if spec:
        parametros.update(spec)
    parametros["random_state"] = SEMILLA
    return LogisticRegression(**parametros)


def lodo(
    datos: dict[str, tuple[pd.DataFrame, np.ndarray]],
    genes: list[str],
    modelo: dict[str, Any] | None = None,
    incluir_en_entrenamiento_no_evaluables: bool = True,
) -> list[ResultadoFold]:
    """Validacion externa dejando fuera una cohorte completa en cada iteracion.

    `datos` asocia cada cohorte a (X muestras x genes, y). Devuelve un
    ResultadoFold por cohorte, incluidas las no evaluables: se reportan marcadas,
    no se ocultan.

    Una cohorte de una sola clase sigue siendo entrenamiento valido, de modo que
    permanece en el conjunto de entrenamiento de los demas folds salvo que se
    indique lo contrario.
    """
    resultados = []
    for test_id in datos:
        X_te_raw, y_te = datos[test_id]
        train_ids = [
            g for g in datos
            if g != test_id
            and (incluir_en_entrenamiento_no_evaluables
                 or len(np.unique(datos[g][1])) == 2)
        ]
        if not train_ids:
            continue

        X_tr = pd.concat(
            [escalar_por_estudio(datos[g][0], genes) for g in train_ids],
            ignore_index=True,
        )
        y_tr = np.concatenate([datos[g][1] for g in train_ids])
        X_te = escalar_por_estudio(X_te_raw, genes)

        m = _construir_modelo(modelo).fit(X_tr, y_tr)
        pred = m.predict(X_te)
        prob = m.predict_proba(X_te)[:, 1]
        score = m.decision_function(X_te)

        n0 = int((y_te == 0).sum())
        n1 = int((y_te == 1).sum())
        evaluable = bool(n0 and n1)
        baseline = max(n0, n1) / len(y_te)

        if evaluable:
            tn, fp, fn, tp = confusion_matrix(y_te, pred, labels=[0, 1]).ravel()
            bal = balanced_accuracy_score(y_te, pred)
            auc = roc_auc_score(y_te, prob)
            sens = tp / (tp + fn) if (tp + fn) else np.nan
            espec = tn / (tn + fp) if (tn + fp) else np.nan
        else:
            bal = auc = sens = espec = np.nan

        resultados.append(ResultadoFold(
            cohorte=test_id,
            n_test=len(y_te),
            n_clase_0=n0,
            n_clase_1=n1,
            n_train=len(y_tr),
            evaluable=evaluable,
            baseline=baseline,
            accuracy=accuracy_score(y_te, pred),
            balanced_accuracy=bal,
            auc=auc,
            sensibilidad=sens,
            especificidad=espec,
            n_genes_seleccionados=int((m.coef_[0] != 0).sum()),
            prediccion=pred,
            probabilidad=prob,
            score_decision=score,
            coeficientes=pd.Series(m.coef_[0], index=genes),
            muestras=X_te_raw.index,
            y_verdadero=y_te,
        ))
    return resultados


def modelos_por_cohorte(
    datos: dict[str, tuple[pd.DataFrame, np.ndarray]],
    genes: list[str],
    modelo: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Un modelo ajustado en CADA cohorte por separado.

    Es la contraparte de `lodo()` para medir replicacion: los entrenamientos son
    disjuntos, de modo que el acuerdo entre ellos si es evidencia. Los folds LODO
    comparten la mayor parte de sus muestras y su acuerdo esta garantizado por el
    diseno.
    """
    coef = {}
    for gse, (X, y) in datos.items():
        if len(np.unique(y)) < 2:
            continue
        m = _construir_modelo(modelo).fit(escalar_por_estudio(X, genes), y)
        coef[gse] = pd.Series(m.coef_[0], index=genes)
    return pd.DataFrame(coef)


def tabla(resultados: list[ResultadoFold]) -> pd.DataFrame:
    """Resultados como tabla, con las metricas honestas y la marca de evaluable."""
    def r4(v):
        return round(v, 4) if v is not None and not pd.isna(v) else np.nan

    return pd.DataFrame([{
        "Cohorte_Test": r.cohorte,
        "n_test": r.n_test,
        "n_Sano": r.n_clase_0,
        "n_Enfermo": r.n_clase_1,
        "n_train": r.n_train,
        "Evaluable": r.evaluable,
        "Baseline_Mayoritaria": r4(r.baseline),
        "Accuracy": r4(r.accuracy),
        "Balanced_Accuracy": r4(r.balanced_accuracy),
        "AUC": r4(r.auc),
        "Sensibilidad": r4(r.sensibilidad),
        "Especificidad": r4(r.especificidad),
        "Ganancia_vs_Baseline": r4(r.ganancia),
        "Supera_Baseline": r.supera_baseline,
        "Genes_Seleccionados": r.n_genes_seleccionados,
    } for r in resultados])


def resumen(resultados: list[ResultadoFold]) -> dict[str, Any]:
    """Medias sobre las cohortes EVALUABLES, mas la media ingenua para contraste.

    La distincion es el nucleo del trabajo: promediar sobre las once cohortes,
    con las monoclase dentro, produce una cifra sin contenido.
    """
    ev = [r for r in resultados if r.evaluable]
    if not ev:
        return {"n_cohortes": len(resultados), "n_evaluables": 0}
    return {
        "n_cohortes": len(resultados),
        "n_evaluables": len(ev),
        "balanced_accuracy_media": float(np.mean([r.balanced_accuracy for r in ev])),
        "auc_media": float(np.mean([r.auc for r in ev])),
        "sensibilidad_media": float(np.mean([r.sensibilidad for r in ev])),
        "especificidad_media": float(np.mean([r.especificidad for r in ev])),
        "baseline_medio": float(np.mean([r.baseline for r in ev])),
        "ganancia_media": float(np.mean([r.ganancia for r in ev])),
        "n_no_superan_baseline": sum(1 for r in ev if not r.supera_baseline),
        # Solo para contraste con lo que se reportaba antes:
        "accuracy_media_ingenua": float(np.mean([r.accuracy for r in resultados])),
    }
