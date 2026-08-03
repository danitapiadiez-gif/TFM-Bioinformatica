"""
Paso 16: la firma tumor-vs-sano, ¿mide biologia tumoral o composicion tisular?

Hipotesis: la firma de consenso no captura biologia especifica del cancer, sino
la proporcion de tejido pulmonar normal presente en la muestra (perdida de
epitelio alveolar y endotelio capilar, ganancia de estroma desmoplasico).

Contraste decisivo: correlacionar el score del clasificador con un score de
contenido de pulmon normal SOLO ENTRE MUESTRAS TUMORALES. Restringirlo a
tumores es lo que hace la prueba informativa: sobre todas las muestras la
correlacion es alta por construccion (los controles son pulmon normal), lo cual
no distingue ambas hipotesis.

  - |rho| alto entre tumores  -> el clasificador lee tejido normal residual
                                 (pureza tumoral), no biologia del cancer.
  - |rho| bajo entre tumores  -> la hipotesis de composicion es FALSA y la firma
                                 mide algo distinto. Se reporta como refutacion.

Umbral pre-registrado: |rho| > 0.7 se considera confirmacion.
"""

import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from utils_cohortes import (
    BASE_DIR,
    MARCADORES_PULMON_NORMAL,
    MARCADORES_TUMOR_GENERICO,
    cargar_cohorte,
    genes_comunes,
    listar_cohortes,
    score_panel,
)

MODELO = dict(solver="liblinear", l1_ratio=1, C=0.5, max_iter=2000)
UMBRAL_RHO = 0.7


def main():
    print("=" * 78)
    print("PASO 16: COMPOSICION TISULAR frente a BIOLOGIA TUMORAL")
    print("=" * 78)

    datos = {}
    for gse in listar_cohortes():
        X, y = cargar_cohorte(gse)
        if X is not None and len(X) and (y == 0).any() and (y == 1).any():
            datos[gse] = (X, y)
    genes = genes_comunes([X for X, _ in datos.values()])
    print(f"\n  Cohortes con ambas clases: {len(datos)} | genes comunes: {len(genes)}")

    panel_normal = [g for grp in MARCADORES_PULMON_NORMAL.values() for g in grp]
    panel_tumor = [g for grp in MARCADORES_TUMOR_GENERICO.values() for g in grp]

    print("\n[1] Composicion de la firma de consenso original")
    ruta_firma = os.path.join(BASE_DIR, "FIRMA_CONSENSO_FINAL_TFM.csv")
    if os.path.exists(ruta_firma):
        firma = pd.read_csv(ruta_firma).head(50)
        top = set(firma["GENE_SYMBOL"])
        solapan = sorted(top & set(panel_normal))
        print(f"  Top 50 de FIRMA_CONSENSO_FINAL_TFM.csv")
        print(f"  Marcadores de pulmon normal presentes en el top 50: "
              f"{len(solapan)} -> {solapan}")
        # Direccion: los marcadores de tejido normal deben tener LogFC negativo.
        sub = firma[firma["GENE_SYMBOL"].isin(panel_normal)]
        if not sub.empty:
            print(f"  LogFC de esos marcadores (negativo = reprimido en tumor):")
            for _, r in sub.iterrows():
                print(f"    {r['GENE_SYMBOL']:<10} LogFC={r['LogFC_Medio']:+.2f}")

    print("\n[2] Contraste por cohorte (LODO, score sobre la cohorte held-out)")
    filas = []
    for test_id in datos:
        X_te_raw, y_te = datos[test_id]
        train_ids = [g for g in datos if g != test_id]

        X_tr = pd.concat(
            [pd.DataFrame(StandardScaler().fit_transform(datos[g][0][genes]))
             for g in train_ids],
            ignore_index=True,
        )
        y_tr = np.concatenate([datos[g][1] for g in train_ids])
        modelo = LogisticRegression(**MODELO).fit(X_tr, y_tr)

        X_te = StandardScaler().fit_transform(X_te_raw[genes])
        score_tumor = modelo.decision_function(X_te)  # mayor = mas "enfermo"

        s_norm, usados_n = score_panel(X_te_raw, panel_normal)
        s_prol, usados_t = score_panel(X_te_raw, panel_tumor)
        if s_norm is None:
            continue

        es_tumor = y_te == 1
        n_tum = int(es_tumor.sum())

        # Correlacion sobre TODAS las muestras: alta por construccion, no informativa.
        rho_todas, p_todas = spearmanr(score_tumor, s_norm.values)
        # Correlacion SOLO entre tumores: la prueba decisiva.
        if n_tum >= 8:
            rho_tum, p_tum = spearmanr(score_tumor[es_tumor],
                                       s_norm.values[es_tumor])
        else:
            rho_tum, p_tum = np.nan, np.nan

        rho_prol = (
            spearmanr(score_tumor[es_tumor], s_prol.values[es_tumor])[0]
            if s_prol is not None and n_tum >= 8 else np.nan
        )

        filas.append({
            "Cohorte": test_id,
            "n_tumores": n_tum,
            "n_sanos": int((~es_tumor).sum()),
            "Rho_TODAS_vs_PulmonNormal": round(rho_todas, 4),
            "p_TODAS": f"{p_todas:.2e}",
            "Rho_SOLO_TUMORES_vs_PulmonNormal": (
                round(rho_tum, 4) if not np.isnan(rho_tum) else np.nan),
            "p_SOLO_TUMORES": f"{p_tum:.2e}" if not np.isnan(rho_tum) else "n/a",
            "Rho_SOLO_TUMORES_vs_Proliferacion": (
                round(rho_prol, 4) if not np.isnan(rho_prol) else np.nan),
            "Marcadores_Normal_Usados": len(usados_n),
        })
        print(f"  {test_id:<12} n_tum={n_tum:>3}  "
              f"rho(todas)={rho_todas:+.3f}   "
              f"rho(solo tumores)="
              f"{f'{rho_tum:+.3f}' if not np.isnan(rho_tum) else '  n/a':>7}")

    res = pd.DataFrame(filas)
    print("\n[3] Resultados")
    print(res.to_string(index=False))

    val = res["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
    print("\n[4] Veredicto")
    print(f"  Marcadores de pulmon normal empleados: {len(panel_normal)} "
          f"({', '.join(panel_normal[:8])}...)")
    print(f"  rho medio sobre TODAS las muestras       : "
          f"{res['Rho_TODAS_vs_PulmonNormal'].mean():+.4f}  "
          f"(alto por construccion, no informativo)")
    print(f"  rho medio SOLO ENTRE TUMORES             : {val.mean():+.4f}")
    print(f"  cohortes con |rho| > {UMBRAL_RHO} entre tumores      : "
          f"{int((val.abs() > UMBRAL_RHO).sum())} de {len(val)}")

    confirmada = abs(val.mean()) > UMBRAL_RHO
    print()
    if confirmada:
        print(f"  >>> HIPOTESIS CONFIRMADA: |rho| medio = {abs(val.mean()):.3f} "
              f"> {UMBRAL_RHO}")
        print("      Entre muestras tumorales, el score del clasificador sigue")
        print("      la cantidad de tejido pulmonar normal residual. La firma")
        print("      mide composicion tisular / pureza tumoral, no biologia del")
        print("      cancer.")
    else:
        print(f"  >>> HIPOTESIS REFUTADA: |rho| medio = {abs(val.mean()):.3f} "
              f"<= {UMBRAL_RHO}")
        print("      La composicion tisular NO explica por si sola el score del")
        print("      clasificador entre tumores. La interpretacion de la firma")
        print("      como artefacto de composicion no se sostiene con este dato")
        print("      y debe revisarse.")

    res.to_csv(os.path.join(BASE_DIR, "COMPOSICION_VS_BIOLOGIA.csv"), index=False)
    print("\n  Guardado: COMPOSICION_VS_BIOLOGIA.csv")
    print("=" * 78)
    return res


if __name__ == "__main__":
    main()
