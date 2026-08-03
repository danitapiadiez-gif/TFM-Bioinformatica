"""
Tests de la capa de validacion.

Fijan las tres decisiones que el trabajo demostro que importan:

  1. Una cohorte de test con una sola clase NO es evaluable, aunque produzca
     accuracy alta. Antes del refactor esas cohortes entraban en la media.
  2. Los resultados son deterministas. Sin random_state, liblinear producia
     cifras distintas entre ejecuciones (paso 18: 29,9 % frente a 30,5 %).
  3. La media honesta se calcula sobre cohortes evaluables, y la ingenua se
     reporta aparte para contraste, nunca como resultado.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfm import validacion  # noqa: E402


def _sintetico(n_por_cohorte=(40, 40, 30), n_genes=60, semilla=7,
               monoclase=None):
    """Cohortes sinteticas con senal real y un desplazamiento por estudio.

    El desplazamiento imita el efecto lote: obliga a que la estandarizacion por
    estudio haga su trabajo.
    """
    rng = np.random.RandomState(semilla)
    datos = {}
    for i, n in enumerate(n_por_cohorte):
        nombre = f"GSEsint{i}"
        if monoclase is not None and i == monoclase:
            y = np.ones(n, dtype=int)
        else:
            y = np.array([0, 1] * (n // 2), dtype=int)[:n]
        X = rng.normal(loc=3.0 * i, scale=1.0, size=(n, n_genes))
        # Los diez primeros genes llevan la senal.
        X[:, :10] += y[:, None] * 2.0
        datos[nombre] = (
            pd.DataFrame(X, columns=[f"G{j}" for j in range(n_genes)],
                         index=[f"{nombre}_{k}" for k in range(n)]),
            y,
        )
    return datos, [f"G{j}" for j in range(n_genes)]


def test_detecta_senal_en_datos_sinteticos():
    datos, genes = _sintetico()
    rs = validacion.lodo(datos, genes)
    ev = [r for r in rs if r.evaluable]
    assert len(ev) == 3
    assert np.mean([r.auc for r in ev]) > 0.9


def test_cohorte_monoclase_no_es_evaluable():
    """El fallo que inflaba la media: accuracy alta sin contenido."""
    datos, genes = _sintetico(monoclase=1)
    rs = validacion.lodo(datos, genes)
    por_nombre = {r.cohorte: r for r in rs}

    mono = por_nombre["GSEsint1"]
    assert mono.evaluable is False
    assert mono.baseline == pytest.approx(1.0)
    # Las metricas que necesitan dos clases no existen.
    assert np.isnan(mono.auc)
    assert np.isnan(mono.balanced_accuracy)
    assert np.isnan(mono.especificidad)
    # La accuracy sigue calculandose, y ahi esta el peligro: cualquier valor que
    # tome carece de informacion, porque la estrategia trivial de predecir
    # siempre la unica clase presente alcanza 1,000. Por eso no basta con mirar
    # la accuracy: hay que comprobar el numero de clases.
    assert not np.isnan(mono.accuracy)
    assert mono.ganancia <= 0, (
        "sobre una cohorte monoclase ninguna accuracy puede superar el baseline")


def test_el_resumen_excluye_las_no_evaluables():
    datos, genes = _sintetico(monoclase=1)
    rs = validacion.lodo(datos, genes)
    r = validacion.resumen(rs)
    assert r["n_cohortes"] == 3
    assert r["n_evaluables"] == 2
    # La media ingenua se reporta, pero aparte y etiquetada como tal.
    assert "accuracy_media_ingenua" in r
    assert not np.isnan(r["balanced_accuracy_media"])


def test_es_determinista():
    """Sin random_state fijado, liblinear daba resultados distintos por ejecucion."""
    datos, genes = _sintetico()
    a = validacion.tabla(validacion.lodo(datos, genes))
    b = validacion.tabla(validacion.lodo(datos, genes))
    pd.testing.assert_frame_equal(a, b)


def test_el_baseline_es_la_clase_mayoritaria():
    datos, genes = _sintetico(n_por_cohorte=(40, 40, 40))
    # Se desbalancea la tercera cohorte a mano.
    X, y = datos["GSEsint2"]
    y = y.copy()
    y[:36] = 1
    datos["GSEsint2"] = (X, y)

    rs = {r.cohorte: r for r in validacion.lodo(datos, genes)}
    r = rs["GSEsint2"]
    assert r.baseline == pytest.approx(max((y == 0).sum(), (y == 1).sum()) / len(y))
    assert r.supera_baseline == (r.accuracy > r.baseline)


def test_modelos_por_cohorte_son_entrenamientos_disjuntos():
    """La replicacion se mide entre ajustes disjuntos, no entre folds solapados."""
    datos, genes = _sintetico()
    coef = validacion.modelos_por_cohorte(datos, genes)
    assert list(coef.columns) == list(datos)
    assert coef.shape[0] == len(genes)


def test_la_tabla_trae_las_metricas_honestas():
    datos, genes = _sintetico(monoclase=1)
    t = validacion.tabla(validacion.lodo(datos, genes))
    for col in ("Baseline_Mayoritaria", "Balanced_Accuracy", "AUC",
                "Sensibilidad", "Especificidad", "Evaluable",
                "Ganancia_vs_Baseline"):
        assert col in t.columns, f"falta la columna {col}"
    assert t.loc[t["Cohorte_Test"] == "GSEsint1", "Evaluable"].iloc[0] is np.False_ \
        or not t.loc[t["Cohorte_Test"] == "GSEsint1", "Evaluable"].iloc[0]
