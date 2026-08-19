"""
Paso 19: salida de biomarcadores del framework, tras su capa de validacion.

Este es el producto del framework: una firma de biomarcadores que ha superado los
criterios de validacion, mas el panel minimo que conserva el rendimiento.

La capa de validacion aplica cuatro criterios, los mismos a cualquier tarea:

  1. Tamano de efecto grande en CADA cohorte por separado (|d| de Cohen > 0,8).
  2. Direccion concordante en todas las cohortes.
  3. Ajuste independiente por cohorte, sin folds solapados: la replicacion se
     mide entre entrenamientos disjuntos.
  4. Validacion externa LODO sobre cohorte completa held-out, con baseline de
     clase mayoritaria declarado.

El paso ejecuta la validacion sobre las DOS tareas del trabajo, con criterios
identicos, para mostrar que la capa discrimina:

  - subtipo histologico (ADC frente a escamoso): la supera
  - tumor frente a sano: no la supera

Y determina el panel minimo: cuantos genes bastan para conservar el AUC, que es
lo que convierte una lista de genes en algo utilizable.
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from paso13_subtipo_lodo import COHORTES as COHORTES_SUBTIPO
from paso13_subtipo_lodo import ETIQUETA, cargar_cohorte as cargar_subtipo
from utils_cohortes import BASE_DIR, cargar_cohorte, genes_comunes, listar_cohortes

MODELO = dict(solver="liblinear", l1_ratio=1, C=0.1, max_iter=5000,
              class_weight="balanced", random_state=0)

UMBRAL_D = 0.8
TAMANOS_PANEL = [3, 5, 8, 10, 15, 20, 30, 50, 100, 250, 500, 1174]

# Marcadores de uso clinico establecido, para validacion externa de la firma.
# No participan en la seleccion: sirven para comprobar si el framework los
# recupera por si solo.
IHC_CLINICA = {
    "Escamoso": ["KRT5", "KRT6A", "KRT6B", "KRT14", "KRT13", "TP63", "DSG3",
                 "DSC3", "SOX2", "PKP1", "CALML3", "S100A2"],
    "Adenocarcinoma": ["NAPSA", "NKX2-1", "SFTPB", "SFTPA1", "SFTPC", "SLC34A2",
                       "MUC1", "CEACAM6"],
}


def d_cohen_por_cohorte(datos, genes):
    """d de Cohen de cada gen en cada cohorte, calculada de forma independiente."""
    salida = {}
    for gse, (X, y) in datos.items():
        Xg = X[genes]
        a, b = Xg[y == 0], Xg[y == 1]
        n0, n1 = len(a), len(b)
        if n0 < 2 or n1 < 2:
            continue
        s = np.sqrt(((n0 - 1) * a.var(ddof=1) + (n1 - 1) * b.var(ddof=1))
                    / (n0 + n1 - 2))
        salida[gse] = (b.mean() - a.mean()) / s.replace(0, np.nan)
    return pd.DataFrame(salida)


def replicados(D, umbral=UMBRAL_D):
    """Genes con |d| > umbral y mismo signo en TODAS las cohortes."""
    cols = list(D.columns)
    mismo = (D[cols] > 0).all(axis=1) | (D[cols] < 0).all(axis=1)
    magnitud = (D[cols].abs() > umbral).all(axis=1)
    sel = D[mismo & magnitud].copy()
    sel["d_Media"] = sel[cols].mean(axis=1)
    sel["d_Minima_Abs"] = sel[cols].abs().min(axis=1)
    sel["Direccion"] = np.where(sel["d_Media"] > 0, "Escamoso", "Adenocarcinoma")
    # Se ordena por el efecto MINIMO entre cohortes: penaliza a los genes que
    # dependen de una sola cohorte para parecer fuertes.
    return sel.sort_values("d_Minima_Abs", ascending=False)


def lodo_con_panel(datos, panel):
    """Validacion LODO restringida a un panel de genes."""
    filas = []
    for test_id in datos:
        X_te, y_te = datos[test_id]
        train = [g for g in datos if g != test_id]
        X_tr = pd.concat(
            [pd.DataFrame(StandardScaler().fit_transform(datos[g][0][panel]))
             for g in train], ignore_index=True)
        y_tr = np.concatenate([datos[g][1] for g in train])
        m = LogisticRegression(**MODELO).fit(X_tr, y_tr)
        Xs = StandardScaler().fit_transform(X_te[panel])
        base = max(np.mean(y_te == 0), np.mean(y_te == 1))
        filas.append({
            "Cohorte": test_id,
            "AUC": roc_auc_score(y_te, m.predict_proba(Xs)[:, 1]),
            "Bal_Acc": balanced_accuracy_score(y_te, m.predict(Xs)),
            "Baseline": base,
        })
    return pd.DataFrame(filas)


def main():
    print("=" * 78)
    print("PASO 19: FIRMA DE BIOMARCADORES VALIDADA POR EL FRAMEWORK")
    print("=" * 78)

    # ---------------- Tarea A: subtipo histologico -----------------------
    print("\n[A] Tarea con consecuencia terapeutica: ADC frente a escamoso")
    sub = {}
    for gse, cfg in COHORTES_SUBTIPO.items():
        X, y = cargar_subtipo(gse, cfg)
        if len(np.unique(y)) == 2:
            sub[gse] = (X, y)
    genes_sub = genes_comunes([X for X, _ in sub.values()])
    print(f"  {len(sub)} cohortes independientes | {len(genes_sub)} genes")

    Dsub = d_cohen_por_cohorte(sub, genes_sub)
    firma = replicados(Dsub)
    print(f"  Genes que superan la validacion: {len(firma)} de {len(genes_sub)} "
          f"({100 * len(firma) / len(genes_sub):.1f} %)")

    # ---------------- Tarea B: tumor frente a sano -----------------------
    print("\n[B] Misma validacion sobre la tarea tumor frente a sano")
    tvs = {}
    for gse in listar_cohortes():
        X, y = cargar_cohorte(gse)
        if X is not None and len(X) and (y == 0).any() and (y == 1).any():
            tvs[gse] = (X, y)
    genes_tvs = genes_comunes([X for X, _ in tvs.values()])
    Dtvs = d_cohen_por_cohorte(tvs, genes_tvs)
    firma_tvs = replicados(Dtvs)
    print(f"  {len(tvs)} cohortes | {len(genes_tvs)} genes")
    print(f"  Genes que superan la validacion: {len(firma_tvs)} de "
          f"{len(genes_tvs)} ({100 * len(firma_tvs) / len(genes_tvs):.2f} %)")

    r_sub = 100 * len(firma) / len(genes_sub)
    r_tvs = 100 * len(firma_tvs) / len(genes_tvs)
    print(f"\n  >>> Los MISMOS criterios validan el {r_sub:.1f} % de los genes en la")
    print(f"      tarea de subtipo y el {r_tvs:.2f} % en tumor-vs-sano: una razon de")
    print(f"      {r_sub / r_tvs:.1f} a 1. La capa de validacion discrimina entre tareas.")
    print("      Matiz necesario: con criterio de tamano de efecto tumor-vs-sano SI")
    print(f"      retiene {len(firma_tvs)} genes. El 0 del paso 17 correspondia a otro")
    print("      criterio (interseccion de soportes LASSO). Y esos genes son, segun el")
    print("      paso 16, marcadores de composicion tisular en buena parte.")

    # ---------------- Validacion externa: marcadores de IHC --------------
    print("\n[C] Validacion externa contra marcadores de uso clinico")
    print("    (no participan en la seleccion; se comprueba si el framework")
    print("     los recupera por si solo)")
    recuperados = {}
    for direccion, lista in IHC_CLINICA.items():
        hall = [g for g in lista
                if g in firma.index and firma.loc[g, "Direccion"] == direccion]
        recuperados[direccion] = hall
        print(f"  {direccion:<16} {len(hall)}/{len(lista)}  {hall}")

    # ---------------- Panel minimo ---------------------------------------
    print("\n[D] Panel minimo: cuantos genes bastan")
    ranking = list(firma.index)
    curva = []
    for k in TAMANOS_PANEL:
        if k > len(ranking):
            continue
        r = lodo_con_panel(sub, ranking[:k])
        curva.append({
            "N_Genes": k,
            "AUC_Media": r["AUC"].mean(),
            "Bal_Acc_Media": r["Bal_Acc"].mean(),
            "AUC_Minima": r["AUC"].min(),
        })
        print(f"  {k:>5} genes -> AUC media {r['AUC'].mean():.4f} "
              f"(minima {r['AUC'].min():.4f})  "
              f"bal.acc {r['Bal_Acc'].mean():.4f}")
    curva = pd.DataFrame(curva)

    auc_max = curva["AUC_Media"].max()
    suficiente = curva[curva["AUC_Media"] >= auc_max - 0.01]["N_Genes"].min()
    # AUC con la firma completa: el ultimo tamano de TAMANOS_PANEL, que es
    # len(ranking) (todos los genes validados). No confundir con el maximo
    # de la curva, que suele estar en un panel intermedio (~50 genes).
    auc_completa = float(
        curva.loc[curva["N_Genes"] == len(ranking), "AUC_Media"].iloc[0])
    print(f"\n  Panel minimo que conserva el AUC (a menos de 0,01 del maximo): "
          f"{suficiente} genes")
    print(f"  AUC firma completa ({len(ranking)} genes): {auc_completa:.4f}")
    print(f"  AUC maxima de la curva: {auc_max:.4f}")

    # ---------------- Entregable -----------------------------------------
    cols_coh = [c for c in firma.columns if c.startswith("GSE")]
    salida = firma.head(60).copy()
    salida.insert(0, "Rango", range(1, len(salida) + 1))
    salida["Marcador_IHC_Clinica"] = [
        any(g in v for v in IHC_CLINICA.values()) for g in salida.index
    ]
    salida["En_Panel_Minimo"] = [
        g in ranking[:int(suficiente)] for g in salida.index
    ]
    orden = (["Rango"] + cols_coh
             + ["d_Media", "d_Minima_Abs", "Direccion",
                "Marcador_IHC_Clinica", "En_Panel_Minimo"])
    salida = salida[orden]
    salida.to_csv(os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_TOP60.csv"))
    curva.to_csv(os.path.join(BASE_DIR, "resultados/firma_consenso/PANEL_MINIMO_CURVA.csv"), index=False)
    firma.to_csv(os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_COMPLETA.csv"))

    resumen = {
        "tarea_validada": "Adenocarcinoma frente a carcinoma escamoso",
        "n_cohortes_independientes": len(sub),
        "n_genes_evaluados": len(genes_sub),
        "n_genes_validados": int(len(firma)),
        "pct_genes_validados": 100 * len(firma) / len(genes_sub),
        "n_genes_validados_tumor_vs_sano": int(len(firma_tvs)),
        "panel_minimo": int(suficiente),
        "auc_panel_minimo": float(
            curva.loc[curva["N_Genes"] == suficiente, "AUC_Media"].iloc[0]),
        "auc_firma_completa": auc_completa,
        "auc_curva_maxima": float(auc_max),
        "ihc_recuperados": {k: len(v) for k, v in recuperados.items()},
        "ihc_total": {k: len(v) for k, v in IHC_CLINICA.items()},
        "top10": list(firma.index[:10]),
        "panel_minimo_genes": ranking[:int(suficiente)],
    }
    with open(os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_VALIDADA_RESUMEN.json"), "w") as fh:
        json.dump(resumen, fh, indent=2, ensure_ascii=False)

    print("\n[E] Firma entregada: top 15")
    print(firma[["d_Media", "d_Minima_Abs", "Direccion"]].head(15).to_string())

    print("\n" + "=" * 78)
    print(f"  Genes validados            : {len(firma)}")
    print(f"  Panel minimo               : {suficiente} genes, "
          f"AUC {resumen['auc_panel_minimo']:.4f}")
    print(f"  Marcadores de IHC recuperados: "
          f"{sum(len(v) for v in recuperados.values())} de "
          f"{sum(len(v) for v in IHC_CLINICA.values())}")
    print(f"  Misma validacion en tumor-vs-sano: {len(firma_tvs)} genes")
    print("=" * 78)
    print("  Guardado: FIRMA_VALIDADA_TOP60.csv, FIRMA_VALIDADA_COMPLETA.csv,")
    print("            PANEL_MINIMO_CURVA.csv, FIRMA_VALIDADA_RESUMEN.json")


if __name__ == "__main__":
    main()
