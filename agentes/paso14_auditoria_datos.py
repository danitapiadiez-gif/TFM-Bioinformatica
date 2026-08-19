"""
Paso 14: Auditoria de integridad de las cohortes.

Analisis puramente descriptivo: no contrasta ninguna hipotesis, documenta el
estado real de los datos sobre los que se construyeron los resultados previos.

Comprueba cuatro cosas por cohorte:
  1. Alineamiento muestra-etiqueta (matriz vs metadata).
  2. Tasa de exito de la curacion clinica automatizada por LLM.
  3. Composicion de clases, marcando las cohortes de una sola clase, que no son
     evaluables como conjunto de test aunque produzcan accuracy alta.
  4. Cobertura: cohortes declaradas en datasets.txt frente a las procesadas.
"""

import os

import numpy as np
import pandas as pd

from utils_cohortes import (
    BASE_DIR,
    datasets_declarados,
    diagnosticar_alineamiento,
    listar_cohortes,
)


def auditar():
    print("=" * 78)
    print("PASO 14: AUDITORIA DE INTEGRIDAD DE LAS COHORTES")
    print("=" * 78)

    declarados = datasets_declarados()
    procesados = listar_cohortes()

    filas = []
    for gse in procesados:
        carpeta = os.path.join(BASE_DIR, f"TFM_{gse}")
        meta = pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))
        alin = diagnosticar_alineamiento(gse)

        grupos = (
            meta["grupo_analisis"].astype(str).str.strip().str.lower()
            if "grupo_analisis" in meta.columns
            else pd.Series(dtype=str)
        )
        n_total = len(meta)
        n_sano = int((grupos == "sano").sum())
        n_enf = int((grupos == "enfermo").sum())
        n_desc = n_total - n_sano - n_enf
        n_etiq = n_sano + n_enf

        filas.append({
            "Cohorte": gse,
            "Declarada_en_datasets_txt": gse in declarados,
            "Plataforma": meta["platform_id"].iloc[0] if "platform_id" in meta else "?",
            "N_Total": n_total,
            "N_Sano": n_sano,
            "N_Enfermo": n_enf,
            "N_Sin_Clasificar": n_desc,
            "Tasa_Exito_Curacion": round(n_etiq / n_total, 4) if n_total else np.nan,
            "Alineamiento": alin["estado"],
            "N_Muestras_Desalineadas": alin["n_desalineadas"],
            "Clases_Presentes": int(n_sano > 0) + int(n_enf > 0),
            "Evaluable_Como_Test": (n_sano > 0 and n_enf > 0),
            "Baseline_Si_Test": (
                round(max(n_sano, n_enf) / n_etiq, 4) if n_etiq else np.nan
            ),
        })

    aud = pd.DataFrame(filas)

    print("\n[1] Cobertura del pipeline")
    print(f"  Declaradas en datasets.txt : {len(declarados)}")
    print(f"  Con datos procesados       : {len(procesados)}")
    perdidas = [g for g in declarados if g not in procesados]
    extra = [g for g in procesados if g not in declarados]
    print(f"  Declaradas SIN procesar    : {len(perdidas)} -> {perdidas}")
    print(f"  Procesadas NO declaradas   : {len(extra)} -> {extra}")

    print("\n[2] Alineamiento muestra-etiqueta")
    mal = aud[aud["Alineamiento"] != "OK"]
    if mal.empty:
        print("  Todas las cohortes alineadas correctamente.")
    for _, r in mal.iterrows():
        print(f"  {r['Cohorte']}: {r['Alineamiento']} "
              f"({int(r['N_Muestras_Desalineadas'])}/{r['N_Total']} muestras "
              f"con la etiqueta de otro paciente)")

    print("\n[3] Curacion clinica automatizada (LLM)")
    for _, r in aud.sort_values("Tasa_Exito_Curacion").iterrows():
        marca = "  <-- FALLO" if r["Tasa_Exito_Curacion"] < 0.5 else ""
        print(f"  {r['Cohorte']:<12} {r['Tasa_Exito_Curacion']:>6.1%} "
              f"({r['N_Sin_Clasificar']:>3} de {r['N_Total']:>3} sin clasificar)"
              f"{marca}")
    tot = aud["N_Total"].sum()
    sin = aud["N_Sin_Clasificar"].sum()
    print(f"  GLOBAL: {(tot - sin) / tot:.1%} "
          f"({sin} de {tot} muestras sin clasificar)")

    print("\n[4] Evaluabilidad como cohorte de test")
    mono = aud[~aud["Evaluable_Como_Test"]]
    print(f"  Evaluables (dos clases) : {int(aud['Evaluable_Como_Test'].sum())}")
    print(f"  NO evaluables (monoclase o sin etiquetas): {len(mono)}")
    for _, r in mono.iterrows():
        n_et = r["N_Sano"] + r["N_Enfermo"]
        print(f"    {r['Cohorte']:<12} sano={r['N_Sano']:>3} enfermo={r['N_Enfermo']:>3}"
              f" -> accuracy maxima trivial = "
              f"{'1.000 (predecir siempre la unica clase)' if n_et else 'sin etiquetas'}")

    print("\n[5] Tabla completa")
    print(aud.to_string(index=False))

    ruta = os.path.join(BASE_DIR, "resultados/auditoria/AUDITORIA_COHORTES.csv")
    aud.to_csv(ruta, index=False)
    print(f"\n  Guardado: {os.path.basename(ruta)}")

    print("\n" + "=" * 78)
    print("RESUMEN DE MODOS DE FALLO DETECTADOS")
    print("=" * 78)
    print(f"  1. Cohortes declaradas que nunca se procesaron : {len(perdidas)}")
    print(f"  2. Cohortes con desalineamiento muestra-etiqueta: {len(mal)} "
          f"({int(aud['N_Muestras_Desalineadas'].fillna(0).sum())} muestras)")
    print(f"  3. Muestras perdidas en la curacion por LLM     : {sin} de {tot} "
          f"({sin / tot:.1%})")
    print(f"  4. Cohortes no evaluables usadas como test      : {len(mono)}")
    print("=" * 78)
    return aud


if __name__ == "__main__":
    auditar()
