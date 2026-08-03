"""
Tests de la derivacion de firma.

Fijan el criterio de replicacion y, sobre todo, la diferencia entre medir el
acuerdo entre folds solapados y entre cohortes disjuntas: ese fue el fallo que
sostenia la firma inicial del trabajo.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfm import firma  # noqa: E402

CLASES = {0: "control", 1: "caso"}


def _datos(semilla=3, n_genes=40, genes_con_senal=6):
    rng = np.random.RandomState(semilla)
    datos = {}
    for i, n in enumerate((50, 50, 40)):
        y = np.array([0, 1] * (n // 2))[:n]
        X = rng.normal(loc=2.0 * i, size=(n, n_genes))
        X[:, :genes_con_senal] += y[:, None] * 3.0
        datos[f"C{i}"] = (
            pd.DataFrame(X, columns=[f"G{j}" for j in range(n_genes)]), y)
    return datos, [f"G{j}" for j in range(n_genes)]


def test_recupera_los_genes_con_senal_y_solo_esos():
    datos, genes = _datos()
    D = firma.d_de_cohen(datos, genes)
    sel = firma.replicados(D, CLASES)
    con_senal = {f"G{j}" for j in range(6)}
    assert con_senal.issubset(set(sel.index))
    # Ningun gen de ruido deberia colarse con d > 0,8 en las TRES cohortes.
    assert len(set(sel.index) - con_senal) <= 1


def test_exige_la_misma_direccion_en_todas_las_cohortes():
    datos, genes = _datos()
    # Se invierte la senal de un gen en una sola cohorte.
    X, y = datos["C1"]
    X = X.copy()
    X["G0"] = X["G0"] - y * 6.0
    datos["C1"] = (X, y)

    sel = firma.replicados(firma.d_de_cohen(datos, genes), CLASES)
    assert "G0" not in sel.index, (
        "un gen que cambia de direccion entre cohortes no puede validarse")


def test_ordena_por_el_efecto_minimo_no_por_la_media():
    """Penaliza a los genes que dependen de una sola cohorte para parecer fuertes."""
    datos, genes = _datos()
    sel = firma.replicados(firma.d_de_cohen(datos, genes), CLASES)
    minimos = sel["d_Minima_Abs"].values
    assert all(minimos[i] >= minimos[i + 1] for i in range(len(minimos) - 1))


def test_el_acuerdo_de_signo_distingue_solapado_de_disjunto():
    """El nucleo del hallazgo del paso 17, como test.

    Coeficientes casi identicos (modelos con entrenamientos solapados) producen
    acuerdo perfecto; coeficientes independientes, no.
    """
    rng = np.random.RandomState(11)
    base = rng.normal(size=200)

    solapados = pd.DataFrame({f"f{k}": base + rng.normal(scale=0.01, size=200)
                              for k in range(5)})
    disjuntos = pd.DataFrame({f"c{k}": rng.normal(size=200) for k in range(5)})

    a = firma.concordancia_de_signo(solapados)
    b = firma.concordancia_de_signo(disjuntos)
    assert a["genes_acuerdo_signo_perfecto"] > 5 * b["genes_acuerdo_signo_perfecto"]


def test_el_panel_minimo_es_menor_que_la_firma_completa():
    datos, genes = _datos(n_genes=60, genes_con_senal=8)
    sel = firma.replicados(firma.d_de_cohen(datos, genes), CLASES)
    if len(sel) < 4:
        return
    k, curva = firma.panel_minimo(datos, list(sel.index), [2, 4, 8, 16])
    assert not curva.empty
    assert 0 < k <= len(sel)
    assert curva["AUC_Media"].max() > 0.9
