"""
Compatibilidad: reexporta la carga de cohortes del paquete `tfm`.

Este modulo tenia su propia implementacion del alineamiento muestra-etiqueta y de
la interseccion de genes, duplicando lo que ahora vive en `tfm/cohortes.py`. Dos
implementaciones del mismo alineamiento son dos sitios donde puede reaparecer el
fallo de GSE30219, de modo que aqui solo quedan los paneles de marcadores y el
calculo de score, que son especificos del paso 16.

Los scripts nuevos deben importar de `tfm.cohortes` directamente.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfm.cohortes import (  # noqa: F401,E402
    RAIZ as BASE_DIR,
    cargar as _cargar,
    diagnostico_alineamiento as diagnosticar_alineamiento,
    disponibles as listar_cohortes,
    declaradas as datasets_declarados,
    genes_comunes,
)

ETIQUETA_BINARIA = {"sano": 0, "enfermo": 1}


def cargar_cohorte(gse, columna_etiqueta="grupo_analisis", mapa=None,
                   devolver_meta=False):
    """Delega en tfm.cohortes.cargar: una sola implementacion del alineamiento."""
    return _cargar(gse, columna_etiqueta, mapa or ETIQUETA_BINARIA,
                   devolver_meta=devolver_meta)


# Marcadores de tejido pulmonar NORMAL, por compartimento celular. Se usan como
# panel de referencia para estimar contenido de pulmon sano en una muestra.
MARCADORES_PULMON_NORMAL = {
    "epitelio_alveolar_AT1": ["AGER", "CAV1", "CLDN18", "PDPN"],
    "epitelio_alveolar_AT2": ["SFTPC", "SFTPB", "SFTPA1", "NAPSA", "SLC34A2"],
    "endotelio": ["PECAM1", "EMCN", "CLDN5", "CDH5", "VWF"],
    "otros_estroma_normal": ["FABP4", "TCF21", "WIF1", "FHL1"],
}

# Marcadores de proliferacion y estroma tumoral (esperados al alza en tumor).
MARCADORES_TUMOR_GENERICO = {
    "proliferacion": ["MKI67", "TOP2A", "CCNB1", "BIRC5", "AURKA"],
    "estroma_desmoplasico": ["COL10A1", "COL11A1", "COL1A1", "SPP1", "MMP11"],
}


def score_panel(X, panel, genes_disponibles=None):
    """Score de un panel de marcadores: media de la expresion z-escalada.

    Se z-escala DENTRO de la cohorte, de modo que el score es comparable entre
    muestras del mismo estudio (no entre estudios distintos).
    """
    if genes_disponibles is None:
        genes_disponibles = set(X.columns)
    presentes = [g for g in panel if g in genes_disponibles]
    if not presentes:
        return None, []
    sub = X[presentes].astype(float)
    z = (sub - sub.mean()) / sub.std(ddof=0).replace(0, np.nan)
    return z.mean(axis=1), presentes
