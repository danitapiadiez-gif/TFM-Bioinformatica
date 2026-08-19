"""
Lectura y agregacion de las cifras del framework para las paginas web.

Ambas paginas (landing y dashboard) leen de aqui, de modo que sus imports no
disparen efectos secundarios de Streamlit (todo el dashboard viejo estaba
escrito en el nivel top del modulo).
"""

import json
import os

import pandas as pd
import streamlit as st

from contexto_tfm import BASE_DIR


@st.cache_data
def tabla(nombre):
    """Devuelve un CSV del proyecto como DataFrame, o None si no existe."""
    ruta = os.path.join(BASE_DIR, nombre)
    return pd.read_csv(ruta) if os.path.exists(ruta) else None


@st.cache_data
def metricas():
    """Cifras de cabecera, leidas de los CSV de los pasos 13-18."""
    m = {}
    if (d := tabla("resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv")) is not None:
        ev = d[d["Evaluable"]]
        m |= {
            "n_cohortes": len(d), "n_ev": len(ev),
            "bal_acc": ev["Balanced_Accuracy"].mean(),
            "auc": ev["AUC"].mean(),
            "sens": ev["Sensibilidad"].mean(),
            "espec": ev["Especificidad"].mean(),
            "base": ev["Baseline_Mayoritaria"].mean(),
            "ganancia": ev["Ganancia_vs_Baseline"].mean(),
            "no_superan": int((~ev["Supera_Baseline"]).sum()),
            "acc_11": d["Accuracy"].mean(),
        }
    if (a := tabla("resultados/auditoria/AUDITORIA_COHORTES.csv")) is not None:
        # "Analizadas" = solo las que el LLM logro etiquetar (sano + enfermo).
        # "Total descargadas" (n_muestras) se mantiene por si algo lo usa.
        a = a.copy()
        a["N_Analizadas"] = a["N_Sano"] + a["N_Enfermo"]
        ev_aud = a[a["Evaluable_Como_Test"]]
        m |= {
            "n_muestras": int(a["N_Analizadas"].sum()),
            "n_descargadas": int(a["N_Total"].sum()),
            "n_muestras_ev": int(ev_aud["N_Analizadas"].sum()),
            "sin_clas": int(a["N_Sin_Clasificar"].sum()),
            "desal": int(a["N_Muestras_Desalineadas"].fillna(0).sum()),
            "n_mono": int((~a["Evaluable_Como_Test"]).sum()),
        }
    if (s := tabla("resultados/subtipo/SUBTIPO_LODO_RESULTADOS.csv")) is not None:
        m |= {"auc_sub": s["AUC"].mean(),
              "bal_sub": s["Balanced_Accuracy"].mean(),
              "n_sub": int(s["n_test"].sum())}
    if (c := tabla("resultados/firma_consenso/COMPOSICION_VS_BIOLOGIA.csv")) is not None:
        v = c["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
        m |= {"rho": v.mean(), "n_rho": len(v),
              "rho_max": v.min(), "n_rho_sup": int((v.abs() > 0.7).sum())}
    if (f := tabla("resultados/auditoria/FALACIA_FOLDS_COMPARACION.csv")) is not None:
        m |= {"conc_lodo": f.iloc[0]["concordancia_pareja_media"] * 100,
              "conc_disj": f.iloc[1]["concordancia_pareja_media"] * 100,
              "genes_folds": int(f.iloc[0]["genes_acuerdo_signo_perfecto"]),
              "genes_disj": int(f.iloc[1]["genes_acuerdo_signo_perfecto"])}
    if (h := tabla("resultados/subtipo/SUBTIPO_CASOS_DIFICILES.csv")) is not None:
        m |= {"pct_conf": 100 * h["N_Alta_Confianza"].sum() / h["n"].sum()}
    return m


@st.cache_data
def resumen_firma():
    """Resumen JSON del paso 19 (n genes validados, panel minimo, IHC, ...).

    Parche: en versiones antiguas del JSON, 'auc_firma_completa' guardaba
    por error el maximo de la curva del panel minimo (que se alcanza en un
    panel intermedio, ~50 genes) en vez de la AUC evaluada con TODA la
    firma. Si esta disponible PANEL_MINIMO_CURVA.csv, se sobreescribe con
    el valor correcto (fila N_Genes == n_genes_validados). Asi la UI
    muestra la cifra correcta sin necesidad de regenerar el JSON.
    """
    ruta = os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_RESUMEN.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta) as fh:
        rf = json.load(fh)
    curva = tabla("resultados/firma_consenso/PANEL_MINIMO_CURVA.csv")
    if curva is not None and "auc_curva_maxima" not in rf:
        n_val = rf.get("n_genes_validados")
        fila = curva[curva["N_Genes"] == n_val]
        if not fila.empty:
            rf["auc_curva_maxima"] = rf.get("auc_firma_completa")
            rf["auc_firma_completa"] = float(fila["AUC_Media"].iloc[0])
    return rf


def dec(v, n=3):
    """Numero con coma decimal, sin importar la locale del sistema.
    Devuelve '—' si el valor es None o NaN, para evitar '0,000' fantasma."""
    if v is None:
        return "—"
    try:
        if v != v:  # NaN
            return "—"
    except TypeError:
        return "—"
    return f"{v:.{n}f}".replace(".", ",")
