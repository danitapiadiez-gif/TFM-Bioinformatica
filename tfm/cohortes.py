"""
Carga de cohortes GEO, con alineamiento muestra-etiqueta explicito.

Este modulo existe por un fallo concreto: en GSE30219 las columnas de la matriz
de expresion estan en orden distinto a las filas del metadata, aunque contengan
las mismas muestras. Asignar las etiquetas por posicion adjudicaba a cada muestra
los datos clinicos de otro paciente, y no producia ningun error.

Toda carga pasa por aqui y alinea por `geo_accession`. No hay via alternativa.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carpeta(gse: str) -> str:
    return os.path.join(RAIZ, f"TFM_{gse}")


def disponibles() -> list[str]:
    """Cohortes con matriz y metadata procesados en disco."""
    salida = []
    for c in sorted(glob.glob(os.path.join(RAIZ, "TFM_GSE*"))):
        if all(os.path.exists(os.path.join(c, f)) for f in
               ("matriz_normalizada.csv", "metadata_procesada.csv")):
            salida.append(os.path.basename(c).replace("TFM_", ""))
    return salida


def declaradas(fichero: str = "datasets.txt") -> list[str]:
    """Cohortes declaradas en el fichero de configuracion del pipeline."""
    ruta = os.path.join(RAIZ, fichero)
    if not os.path.exists(ruta):
        return []
    with open(ruta) as fh:
        return [l.strip() for l in fh
                if l.strip() and not l.strip().startswith("#")]


def diagnostico_alineamiento(gse: str) -> dict:
    """Compara el orden de las columnas de la matriz con las filas del metadata."""
    cols = list(pd.read_csv(os.path.join(carpeta(gse), "matriz_normalizada.csv"),
                            index_col=0, nrows=1).columns)
    acc = list(pd.read_csv(os.path.join(carpeta(gse),
                                        "metadata_procesada.csv"))["geo_accession"])
    if set(cols) != set(acc):
        return {"estado": "CONJUNTOS_DISTINTOS", "n_matriz": len(cols),
                "n_metadata": len(acc), "n_desalineadas": np.nan}
    mal = sum(1 for a, b in zip(cols, acc) if a != b)
    return {"estado": "OK" if mal == 0 else "DESALINEADO",
            "n_matriz": len(cols), "n_metadata": len(acc), "n_desalineadas": mal}


def cargar(gse: str, columna: str | None = None,
           mapa: dict[str, int] | None = None,
           devolver_meta: bool = False):
    """Carga (X muestras x genes, y) alineando SIEMPRE por geo_accession.

    Sin `columna` devuelve solo la matriz y el metadata alineados. Con `columna` y
    `mapa` devuelve las etiquetas, descartando las muestras no mapeables.
    """
    c = carpeta(gse)
    X = pd.read_csv(os.path.join(c, "matriz_normalizada.csv"),
                    index_col=0).T.astype(np.float32)
    meta = pd.read_csv(os.path.join(c, "metadata_procesada.csv"))

    # Alineamiento por identificador, nunca por posicion.
    meta = meta.set_index("geo_accession")
    comunes = X.index.intersection(meta.index)
    X, meta = X.loc[comunes], meta.loc[comunes]

    if columna is None:
        return (X, meta) if devolver_meta else X
    if columna not in meta.columns:
        return (None, None, meta) if devolver_meta else (None, None)

    crudo = meta[columna].astype(str).str.strip().str.lower()
    y = crudo.map({k.lower(): v for k, v in (mapa or {}).items()})
    mask = y.notna().values
    Xf, yf = X.loc[mask], y[mask].values.astype(int)
    return (Xf, yf, meta.loc[mask]) if devolver_meta else (Xf, yf)


def genes_comunes(matrices) -> list[str]:
    """Interseccion ordenada de genes entre varias matrices."""
    comun = None
    for X in matrices:
        s = set(X.columns)
        comun = s if comun is None else comun & s
    return sorted(comun) if comun else []
