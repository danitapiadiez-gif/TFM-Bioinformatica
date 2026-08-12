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
    if (d := tabla("LODO_HONESTO_RESULTADOS.csv")) is not None:
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
    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
        m |= {
            "n_muestras": int(a["N_Total"].sum()),
            "sin_clas": int(a["N_Sin_Clasificar"].sum()),
            "desal": int(a["N_Muestras_Desalineadas"].fillna(0).sum()),
            "n_mono": int((~a["Evaluable_Como_Test"]).sum()),
        }
    if (s := tabla("SUBTIPO_LODO_RESULTADOS.csv")) is not None:
        m |= {"auc_sub": s["AUC"].mean(),
              "bal_sub": s["Balanced_Accuracy"].mean(),
              "n_sub": int(s["n_test"].sum())}
    if (c := tabla("COMPOSICION_VS_BIOLOGIA.csv")) is not None:
        v = c["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
        m |= {"rho": v.mean(), "n_rho": len(v),
              "rho_max": v.min(), "n_rho_sup": int((v.abs() > 0.7).sum())}
    if (f := tabla("FALACIA_FOLDS_COMPARACION.csv")) is not None:
        m |= {"conc_lodo": f.iloc[0]["concordancia_pareja_media"] * 100,
              "conc_disj": f.iloc[1]["concordancia_pareja_media"] * 100,
              "genes_folds": int(f.iloc[0]["genes_acuerdo_signo_perfecto"]),
              "genes_disj": int(f.iloc[1]["genes_acuerdo_signo_perfecto"])}
    if (h := tabla("SUBTIPO_CASOS_DIFICILES.csv")) is not None:
        m |= {"pct_conf": 100 * h["N_Alta_Confianza"].sum() / h["n"].sum()}
    return m


@st.cache_data
def resumen_firma():
    """Resumen JSON del paso 19 (n genes validados, panel minimo, IHC, ...)."""
    ruta = os.path.join(BASE_DIR, "FIRMA_VALIDADA_RESUMEN.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta) as fh:
        return json.load(fh)


def dec(v, n=3):
    """Numero con coma decimal, sin importar la locale del sistema."""
    return f"{v:.{n}f}".replace(".", ",")
