"""
Tests de regresion del alineamiento muestra-etiqueta.

Este fichero existe por el fallo mas grave que encontro el trabajo: en GSE30219
las 307 columnas de la matriz de expresion estan en orden distinto a las filas
del metadata, aunque contengan las mismas muestras. Asignar las etiquetas por
posicion adjudicaba a cada muestra los datos clinicos de otro paciente, y el
efecto era indistinguible de una ausencia de senal: AUC 0,56 con el bug frente a
0,99 corregido, con los mismos datos y el mismo modelo.

El bug no lanzaba ninguna excepcion. Solo podia detectarse comparando con
marcadores biologicos conocidos. De ahi que se fije aqui como test.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfm import cohortes  # noqa: E402

COHORTE_DESALINEADA = "GSE30219"

# Marcadores de escamoso y de adenocarcinoma usados en inmunohistoquimica
# clinica. Con las etiquetas bien alineadas, la diferencia entre subtipos tiene
# que ser grande y del signo esperado. Es el control que revelo el bug.
MARCADORES_ESCAMOSO = ["KRT5", "DSG3", "TP63"]
MARCADORES_ADENO = ["NAPSA", "NKX2-1"]


def _hay_datos(gse):
    return gse in cohortes.disponibles()


def test_la_cohorte_conocida_sigue_desalineada_en_disco():
    """Documenta el estado real del dato: si esto cambia, el resto no aplica."""
    if not _hay_datos(COHORTE_DESALINEADA):
        pytest.skip(f"{COHORTE_DESALINEADA} no esta procesada")
    d = cohortes.diagnostico_alineamiento(COHORTE_DESALINEADA)
    assert d["estado"] == "DESALINEADO"
    assert d["n_desalineadas"] == d["n_matriz"], (
        "se esperaba que TODAS las muestras estuvieran fuera de posicion")


def test_cargar_alinea_por_identificador_no_por_posicion():
    """La carga del framework debe reordenar, no confiar en el orden del fichero."""
    if not _hay_datos(COHORTE_DESALINEADA):
        pytest.skip(f"{COHORTE_DESALINEADA} no esta procesada")

    X, meta = cohortes.cargar(COHORTE_DESALINEADA, devolver_meta=True)
    # El indice de la matriz y el del metadata han de coincidir elemento a
    # elemento, no solo como conjunto.
    assert list(X.index) == list(meta.index)


def test_asignar_por_posicion_destruye_la_senal_biologica():
    """Reproduce el bug y comprueba que el alineamiento correcto la recupera.

    Es el test que da sentido a los demas: mide la consecuencia, no la forma.
    """
    if not _hay_datos(COHORTE_DESALINEADA):
        pytest.skip(f"{COHORTE_DESALINEADA} no esta procesada")

    carpeta = cohortes.carpeta(COHORTE_DESALINEADA)
    Xt = pd.read_csv(os.path.join(carpeta, "matriz_normalizada.csv"),
                     index_col=0).T
    meta = pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))
    col = "characteristics_ch1_3_histology"
    if col not in meta.columns:
        pytest.skip("la cohorte no trae histologia anotada")

    # (a) Como lo hacia el pipeline original: por posicion.
    meta_pos = meta.copy()
    meta_pos.index = Xt.index
    hist_pos = meta_pos[col].astype(str).str.strip()

    # (b) Como lo hace el framework: por identificador.
    X_ok, meta_ok = cohortes.cargar(COHORTE_DESALINEADA, devolver_meta=True)
    hist_ok = meta_ok[col].astype(str).str.strip()

    def separacion(X, hist, gen):
        """Diferencia de medias entre escamoso y adenocarcinoma."""
        if gen not in X.columns:
            return None
        adc = X.loc[hist == "ADC", gen].astype(float)
        sqc = X.loc[hist == "SQC", gen].astype(float)
        if len(adc) < 5 or len(sqc) < 5:
            return None
        return float(sqc.mean() - adc.mean())

    comprobados = 0
    for gen in MARCADORES_ESCAMOSO:
        d_pos = separacion(Xt, hist_pos, gen)
        d_ok = separacion(X_ok, hist_ok, gen)
        if d_pos is None or d_ok is None:
            continue
        comprobados += 1
        # Con las etiquetas correctas, un marcador de escamoso separa mas.
        assert d_ok > d_pos, (
            f"{gen}: la asignacion por posicion no deberia separar mas "
            f"({d_pos:+.2f}) que la correcta ({d_ok:+.2f})")

    assert comprobados > 0, "ningun marcador estaba en la matriz"


def test_todas_las_cohortes_quedan_alineadas_tras_cargar():
    """Invariante del framework: ninguna carga devuelve datos desalineados."""
    disponibles = cohortes.disponibles()
    if not disponibles:
        pytest.skip(
            "No hay TFM_GSE*/ locales (los datos brutos no se versionan). "
            "El test se ejecuta en local; en CI se salta por diseno.")
    for gse in disponibles:
        X, meta = cohortes.cargar(gse, devolver_meta=True)
        assert list(X.index) == list(meta.index), f"{gse} quedo desalineada"


def test_las_etiquetas_corresponden_a_sus_muestras():
    """Con mapa de etiquetas, cada valor debe venir de la fila de su muestra."""
    for gse in cohortes.disponibles()[:4]:
        X, y, meta = cohortes.cargar(
            gse, "grupo_analisis", {"sano": 0, "enfermo": 1}, devolver_meta=True)
        if X is None:
            continue
        assert len(X) == len(y) == len(meta)
        esperado = (meta["grupo_analisis"].astype(str).str.strip().str.lower()
                    .map({"sano": 0, "enfermo": 1}).values)
        assert np.array_equal(y, esperado), (
            f"{gse}: las etiquetas no corresponden a sus propias filas")
