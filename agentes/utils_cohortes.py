"""
Utilidades compartidas para la carga de cohortes GEO.

Existe por un motivo concreto: el bug de alineamiento muestra-etiqueta detectado
en GSE30219. Centralizar la carga evita que cada script vuelva a asignar
etiquetas por posicion. Cualquier analisis nuevo debe usar cargar_cohorte().
"""

import glob
import os

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ETIQUETA_BINARIA = {"sano": 0, "enfermo": 1}

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


def listar_cohortes():
    """Devuelve los IDs GSE con datos procesados en disco."""
    salida = []
    for carpeta in sorted(glob.glob(os.path.join(BASE_DIR, "TFM_GSE*"))):
        gse = os.path.basename(carpeta).replace("TFM_", "")
        tiene = all(
            os.path.exists(os.path.join(carpeta, f))
            for f in ("matriz_normalizada.csv", "metadata_procesada.csv")
        )
        if tiene:
            salida.append(gse)
    return salida


def datasets_declarados():
    """Lee datasets.txt, ignorando comentarios y lineas vacias."""
    ruta = os.path.join(BASE_DIR, "datasets.txt")
    if not os.path.exists(ruta):
        return []
    with open(ruta) as fh:
        return [
            ln.strip() for ln in fh
            if ln.strip() and not ln.strip().startswith("#")
        ]


def diagnosticar_alineamiento(gse):
    """Compara el orden de las columnas de la matriz con las filas del metadata.

    Devuelve un dict con el veredicto. Es la comprobacion que faltaba en el
    pipeline original: `meta.index = X.index` asume orden identico y adjudica a
    cada muestra la etiqueta clinica de otro paciente cuando no lo es.
    """
    carpeta = os.path.join(BASE_DIR, f"TFM_{gse}")
    cols = list(
        pd.read_csv(os.path.join(carpeta, "matriz_normalizada.csv"),
                    index_col=0, nrows=1).columns
    )
    acc = list(
        pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))["geo_accession"]
    )

    if set(cols) != set(acc):
        return {
            "estado": "CONJUNTOS_DISTINTOS",
            "n_matriz": len(cols),
            "n_metadata": len(acc),
            "n_desalineadas": np.nan,
        }

    desalineadas = sum(1 for a, b in zip(cols, acc) if a != b)
    return {
        "estado": "OK" if desalineadas == 0 else "DESALINEADO",
        "n_matriz": len(cols),
        "n_metadata": len(acc),
        "n_desalineadas": desalineadas,
    }


def cargar_cohorte(gse, columna_etiqueta="grupo_analisis", mapa=None,
                   devolver_meta=False):
    """Carga (X, y) de una cohorte alineando SIEMPRE por geo_accession.

    X: DataFrame muestras x genes (float32).
    y: array de enteros segun `mapa`; las muestras no mapeables se descartan.
    """
    if mapa is None:
        mapa = ETIQUETA_BINARIA

    carpeta = os.path.join(BASE_DIR, f"TFM_{gse}")
    X = pd.read_csv(
        os.path.join(carpeta, "matriz_normalizada.csv"), index_col=0
    ).T.astype(np.float32)
    meta = pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))

    # Alineamiento explicito por identificador de muestra, nunca por posicion.
    meta = meta.set_index("geo_accession")
    comunes = X.index.intersection(meta.index)
    X, meta = X.loc[comunes], meta.loc[comunes]

    if columna_etiqueta not in meta.columns:
        return (None, None, meta) if devolver_meta else (None, None)

    crudo = meta[columna_etiqueta].astype(str).str.strip().str.lower()
    y_ser = crudo.map({k.lower(): v for k, v in mapa.items()})
    mask = y_ser.notna().values

    X_f = X.loc[mask]
    y_f = y_ser[mask].values.astype(int)
    if devolver_meta:
        return X_f, y_f, meta.loc[mask]
    return X_f, y_f


def genes_comunes(matrices):
    """Interseccion ordenada de genes entre varias matrices muestras x genes."""
    comun = None
    for X in matrices:
        s = set(X.columns)
        comun = s if comun is None else comun & s
    return sorted(comun) if comun else []


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
