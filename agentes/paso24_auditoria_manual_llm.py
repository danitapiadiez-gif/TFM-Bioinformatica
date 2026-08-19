"""
Paso 24: auditoria manual de la curacion LLM.

La 'tasa de exito' que se reporta ahora mide solo cuantas muestras NO se
etiquetaron como 'ambiguo'. Este paso responde a la pregunta obvia: de las
que si etiqueto, ¿lo hizo bien?

Fase A (muestreo, automatica):
  Si no existe AUDITORIA_MANUAL_LLM.csv, muestrea 40 muestras estratificadas
  por cohorte (aprox. 4-6 por cohorte evaluable) con:
    cohorte, geo_accession, texto_libre, etiqueta_llm, etiqueta_manual (vacio)
  El usuario rellena a mano etiqueta_manual (sano / enfermo / ambiguo).

Fase B (evaluacion, automatica):
  Si AUDITORIA_MANUAL_LLM.csv existe y tiene etiquetas manuales completadas,
  calcula precision del LLM (acuerdo etiqueta_llm vs etiqueta_manual) y una
  matriz de confusion.

Ejecutar dos veces:
  1) python agentes/paso24_auditoria_manual_llm.py   # genera plantilla
  2) rellenar manualmente la columna etiqueta_manual
  3) python agentes/paso24_auditoria_manual_llm.py   # calcula precision
"""

from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tfm.cohortes import RAIZ  # noqa: E402

CSV_PATH = os.path.join(RAIZ, "resultados/auditoria/AUDITORIA_MANUAL_LLM.csv")
N_MUESTRAS_TOTALES = 40
RNG = np.random.default_rng(0)


def _texto_libre_de_muestra(cohorte_dir, geo_accession):
    """Extrae el texto original de la muestra del SOFT o del CSV crudo."""
    # Primero intentar en el CSV curado
    meta = os.path.join(cohorte_dir, "metadata_procesada.csv")
    if os.path.exists(meta):
        m = pd.read_csv(meta)
        if "geo_accession" in m.columns and geo_accession in m["geo_accession"].values:
            row = m[m["geo_accession"] == geo_accession].iloc[0]
            campos = [c for c in row.index
                      if c not in ("grupo_analisis", "geo_accession")
                      and isinstance(row[c], str) and len(row[c]) > 3]
            return "  ·  ".join(f"{c}={row[c]}" for c in campos)
    return "(texto no disponible)"


def fase_A_generar_plantilla():
    print("=" * 78)
    print("PASO 24 FASE A: generacion de plantilla de auditoria manual")
    print("=" * 78)

    cohortes = sorted(glob.glob(os.path.join(RAIZ, "TFM_GSE*")))
    filas = []
    for cd in cohortes:
        gse = os.path.basename(cd).replace("TFM_", "")
        meta = os.path.join(cd, "metadata_procesada.csv")
        if not os.path.exists(meta):
            continue
        m = pd.read_csv(meta)
        if "grupo_analisis" not in m.columns:
            continue
        # Solo muestras con etiqueta LLM asignada (no NaN)
        m["grupo_lower"] = m["grupo_analisis"].astype(str).str.strip().str.lower()
        etiquetadas = m[m["grupo_lower"].isin(["sano", "enfermo"])]
        if len(etiquetadas) == 0:
            continue
        # Muestreo estratificado: hasta 2 sanas + 2 enfermas por cohorte
        n_por_clase = 2
        muestra = etiquetadas.groupby("grupo_lower", group_keys=False).apply(
            lambda g: g.sample(min(len(g), n_por_clase),
                               random_state=int(RNG.integers(0, 10000))))
        for _, r in muestra.iterrows():
            filas.append({
                "cohorte":           gse,
                "geo_accession":     r["geo_accession"],
                "texto_libre":       _texto_libre_de_muestra(cd, r["geo_accession"]),
                "etiqueta_llm":      str(r["grupo_analisis"]).strip().lower(),
                "etiqueta_manual":   "",
                "observaciones":     "",
            })

    df = pd.DataFrame(filas)
    if len(df) > N_MUESTRAS_TOTALES:
        df = df.sample(N_MUESTRAS_TOTALES, random_state=0).sort_values(
            ["cohorte", "etiqueta_llm"]).reset_index(drop=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"\nGenerada plantilla con {len(df)} muestras estratificadas por cohorte "
          f"({df['cohorte'].nunique()} cohortes).")
    print(f"Guardada en: {CSV_PATH}")
    print()
    print("SIGUIENTE PASO:")
    print("  1) Abre el fichero en Excel/Numbers.")
    print("  2) Para cada fila, lee 'texto_libre' y decide la etiqueta correcta:")
    print("       sano       -> tejido pulmonar no tumoral")
    print("       enfermo    -> tumor pulmonar")
    print("       ambiguo    -> no se puede decidir sin duda")
    print("  3) Rellena la columna 'etiqueta_manual' con esa etiqueta.")
    print("  4) Guarda el CSV.")
    print("  5) Vuelve a ejecutar este script para calcular la precision.")


def fase_B_evaluar():
    print("=" * 78)
    print("PASO 24 FASE B: evaluacion de la curacion LLM contra etiqueta manual")
    print("=" * 78)

    df = pd.read_csv(CSV_PATH)
    df["etiqueta_manual"] = df["etiqueta_manual"].astype(str).str.strip().str.lower()
    completadas = df[df["etiqueta_manual"].isin(["sano", "enfermo", "ambiguo"])]
    pendientes = len(df) - len(completadas)

    if pendientes:
        print(f"\nQuedan {pendientes} filas sin etiqueta_manual. Se calcula solo "
              f"sobre las {len(completadas)} completadas.")
    if len(completadas) < 20:
        print("Menos de 20 filas etiquetadas manualmente: precision poco fiable.")
        if len(completadas) == 0:
            return

    # Precision global
    acierto = (completadas["etiqueta_llm"] == completadas["etiqueta_manual"]).mean()
    print(f"\nPrecision global LLM vs manual: {acierto:.3f} "
          f"({int(acierto*len(completadas))}/{len(completadas)})")

    # Matriz de confusion
    labels = ["sano", "enfermo", "ambiguo"]
    conf = pd.crosstab(completadas["etiqueta_manual"], completadas["etiqueta_llm"],
                       margins=True, margins_name="Total")
    print("\nMatriz de confusion (filas = manual, columnas = LLM):")
    print(conf.to_string())

    # Precision por cohorte
    print("\nPrecision por cohorte:")
    por_cohorte = completadas.groupby("cohorte").apply(
        lambda g: pd.Series({
            "n": len(g),
            "aciertos": (g["etiqueta_llm"] == g["etiqueta_manual"]).sum(),
            "precision": (g["etiqueta_llm"] == g["etiqueta_manual"]).mean(),
        })
    )
    print(por_cohorte.to_string())

    # Guardar resumen
    resumen = {
        "n_auditadas":              int(len(completadas)),
        "n_pendientes":             int(pendientes),
        "precision_global":         float(acierto),
        "aciertos":                 int((completadas["etiqueta_llm"] == completadas["etiqueta_manual"]).sum()),
        "precision_por_cohorte":    {k: float(v) for k, v in por_cohorte["precision"].items()},
    }
    with open(os.path.join(RAIZ, "resultados/auditoria/AUDITORIA_MANUAL_LLM_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)
    print("\nGuardado AUDITORIA_MANUAL_LLM_RESUMEN.json")


def main():
    if not os.path.exists(CSV_PATH):
        fase_A_generar_plantilla()
    else:
        fase_B_evaluar()


if __name__ == "__main__":
    main()
