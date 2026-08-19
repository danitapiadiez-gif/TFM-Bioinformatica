"""
Paso 23: validacion externa del panel minimo de 20 genes en TCGA-LUAD y
TCGA-LUSC (RNA-Seq), platforma completamente distinta a la de entrenamiento
(microarray Affymetrix GPL570).

Responde a la limitacion mas visible del trabajo: transferibilidad a RNA-Seq.
Descarga solo la expresion de los 20 genes del panel via API publica de
cBioPortal (~pocos MB, no requiere autenticacion) y aplica un score simple:
todos los genes del panel escamoso puntuan en la misma direccion (up en
escamoso), asi que la suma normalizada (z-score) de sus expresiones separa
directamente LUAD (ADC) de LUSC (SQC).

Metrica principal: AUC del score frente a subtipo verdadero, con IC 95 %
bootstrap.

Ejecutar:  python agentes/paso23_validacion_tcga.py

Requiere conexion a Internet. La API de cBioPortal no exige credenciales.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfm import tareas, validacion  # noqa: E402
from tfm.cohortes import RAIZ  # noqa: E402

API = "https://www.cbioportal.org/api"
PANEL = [
    "DSG3", "KRT5", "CALML3", "KRT6B", "PKP1",
    "FAT2", "DAPL1", "TRIM29", "CLCA2", "DSC3",
    "S1PR5", "KRT6A", "KRT13", "SERPINB5", "TP63",
    "GJB5", "KRT16", "BNC1", "CERS3", "TMEM40",
]
STUDIES = {
    "LUAD": ("luad_tcga_pub", "luad_tcga_pub_rna_seq_v2_mrna"),
    "LUSC": ("lusc_tcga_pub", "lusc_tcga_pub_rna_seq_mrna"),
}
RNG = np.random.default_rng(0)


def _get(url, **params):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def _post(url, json_body, **params):
    r = requests.post(url, params=params, json=json_body, timeout=120)
    r.raise_for_status()
    return r.json()


def resolver_entrez_ids(genes):
    print(f"Resolviendo Entrez IDs de {len(genes)} simbolos HUGO...")
    ids = {}
    for hugo in genes:
        try:
            r = _get(f"{API}/genes/{hugo}")
            ids[hugo] = r["entrezGeneId"]
        except Exception as e:
            print(f"  ! No se encontro {hugo}: {e}")
    print(f"  OK {len(ids)}/{len(genes)}")
    return ids


def descargar_expresion(study_id, mrna_profile, entrez_ids):
    """Devuelve DataFrame samples x genes (log2 RSEM+1)."""
    print(f"  Descargando expresion de {study_id}...")
    data = _post(
        f"{API}/molecular-profiles/{mrna_profile}/molecular-data/fetch",
        json_body={
            "entrezGeneIds": list(entrez_ids.values()),
            "sampleListId": f"{study_id}_all",
        },
    )
    df = pd.DataFrame(data)
    # Estructura: sampleId, entrezGeneId, value
    hugo_by_id = {v: k for k, v in entrez_ids.items()}
    df["gene"] = df["entrezGeneId"].map(hugo_by_id)
    mat = df.pivot_table(index="sampleId", columns="gene", values="value",
                         aggfunc="first")
    # log2(x+1) — RSEM viene en counts normalizados, no en log
    mat = np.log2(mat.astype(float).clip(lower=0) + 1)
    print(f"    {mat.shape[0]} muestras x {mat.shape[1]} genes")
    return mat


def bootstrap_auc(y, scores, n=1000):
    aucs = []
    for _ in range(n):
        idx = RNG.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) < 2:
            continue
        aucs.append(roc_auc_score(y[idx], scores[idx]))
    return np.percentile(aucs, 2.5), np.percentile(aucs, 97.5)


def main():
    print("=" * 78)
    print("PASO 23: validacion del panel minimo (20 genes) en TCGA RNA-Seq")
    print("=" * 78)

    entrez = resolver_entrez_ids(PANEL)
    if len(entrez) < len(PANEL) * 0.8:
        print("Demasiados genes sin Entrez ID, abortando.")
        return

    # Descargar expresion de LUAD y LUSC
    matrices = {}
    for label, (study, profile) in STUDIES.items():
        matrices[label] = descargar_expresion(study, profile, entrez)

    # Unir con etiqueta (0 = ADC, 1 = SQC, coherente con la firma del panel:
    # todos los genes del panel puntuan alto en escamoso).
    luad = matrices["LUAD"].copy()
    luad["subtipo"] = 0
    lusc = matrices["LUSC"].copy()
    lusc["subtipo"] = 1
    X = pd.concat([luad, lusc])

    # Restringir a genes disponibles en ambas
    genes_ok = [g for g in PANEL if g in X.columns and X[g].notna().mean() > 0.9]
    print(f"\nGenes utilizables: {len(genes_ok)}/{len(PANEL)}")
    y = X["subtipo"].values

    # --- Score simple: suma de z-scores (no usa pesos aprendidos)
    Xg = X[genes_ok].fillna(X[genes_ok].mean())
    Xz = StandardScaler().fit_transform(Xg.values)
    score_simple = Xz.sum(axis=1)
    auc_simple = roc_auc_score(y, score_simple)
    lo_s, hi_s = bootstrap_auc(y, score_simple)

    # --- Score con pesos aprendidos: entrenar LASSO L1 sobre las 3 cohortes
    # de subtipo microarray usando solo los 20 genes del panel, y transferir
    # los coeficientes a las expresiones TCGA (z-score dentro de cada
    # plataforma para hacerlas comparables).
    print("\nEntrenando LASSO L1 sobre microarray subtipo (panel de 20 genes)...")
    t = tareas.obtener("subtipo_histologico")
    datos, _ = t.cargar(verbose=False)
    genes_train = [g for g in genes_ok
                   if all(g in datos[k][0].columns for k in datos)]
    X_tr = pd.concat(
        [validacion.escalar_por_estudio(datos[k][0], genes_train)
         for k in datos],
        ignore_index=True,
    )
    y_tr = np.concatenate([datos[k][1] for k in datos])
    modelo = LogisticRegression(
        penalty="l1", solver="liblinear", C=0.5, max_iter=2000, random_state=0
    ).fit(X_tr, y_tr)
    print(f"  Entrenado con {len(y_tr)} muestras y {len(genes_train)} genes.")

    # Aplicar a TCGA: mismo pre-procesado (z-score sobre las TCGA agregadas)
    Xtc = X[genes_train].fillna(X[genes_train].mean())
    Xtc_z = StandardScaler().fit_transform(Xtc.values)
    score_lasso = modelo.decision_function(Xtc_z)
    auc_lasso = roc_auc_score(y, score_lasso)
    lo_l, hi_l = bootstrap_auc(y, score_lasso)

    print(f"\nAUC panel (LUAD vs LUSC) en TCGA RNA-Seq:")
    print(f"  Score simple (suma z):     {auc_simple:.4f}  IC 95 %: [{lo_s:.4f}, {hi_s:.4f}]")
    print(f"  Score LASSO (transferido): {auc_lasso:.4f}  IC 95 %: [{lo_l:.4f}, {hi_l:.4f}]")
    print(f"  n_LUAD = {(y == 0).sum()}   n_LUSC = {(y == 1).sum()}")

    # Guardar
    resumen = {
        "plataforma_train":      "microarray Affymetrix GPL570 (3 cohortes)",
        "plataforma_test":       "TCGA RNA-Seq (RSEM normalized)",
        "n_luad":                int((y == 0).sum()),
        "n_lusc":                int((y == 1).sum()),
        "n_muestras_train":      int(len(y_tr)),
        "n_genes_panel":         len(PANEL),
        "n_genes_disponibles":   len(genes_ok),
        "n_genes_usados_lasso":  len(genes_train),
        "auc_score_simple":      float(auc_simple),
        "auc_score_simple_ic95": [float(lo_s), float(hi_s)],
        "auc_lasso_transferido": float(auc_lasso),
        "auc_lasso_ic95":        [float(lo_l), float(hi_l)],
        "panel_genes":           genes_ok,
    }
    with open(os.path.join(RAIZ, "VALIDACION_TCGA_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    # Detalle por muestra
    out = X.reset_index()[["sampleId", "subtipo"]].copy()
    out["subtipo_txt"]  = out["subtipo"].map({0: "LUAD", 1: "LUSC"})
    out["score_simple"] = score_simple
    out["score_lasso"]  = score_lasso
    out.to_csv(os.path.join(RAIZ, "VALIDACION_TCGA_MUESTRAS.csv"), index=False)

    print("\nGuardado:")
    print("  VALIDACION_TCGA_RESUMEN.json")
    print("  VALIDACION_TCGA_MUESTRAS.csv")


if __name__ == "__main__":
    main()
