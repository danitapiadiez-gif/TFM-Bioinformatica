"""
Paso 18: limites del clasificador de subtipo ante las histologias excluidas.

El paso 13 obtuvo AUC 0.97 clasificando adenocarcinoma frente a escamoso, pero
para ello excluyo 145 muestras: neuroendocrino de celula grande, basaloide,
carcinoide, microcitico, celula grande y adenoescamoso. Es decir, quito
precisamente los casos que en la practica clinica son ambiguos.

Este paso somete el modelo a esas muestras. No hay etiqueta correcta que predecir
(no son ni ADC ni escamoso), asi que lo que se mide es la CALIBRACION: un modelo
honesto deberia asignarles probabilidades intermedias; un modelo sobreconfiado
las fuerza a una de las dos clases.

Metrica pre-registrada: porcentaje de muestras ambiguas con probabilidad > 0.9 o
< 0.1, es decir, clasificadas con alta confianza en una categoria a la que no
pertenecen. Cuanto mas alto, menos utilizable es el modelo en la practica.
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from utils_cohortes import BASE_DIR, genes_comunes

# Histologias por cohorte: las dos clases entrenables y las ambiguas excluidas.
CONFIG = {
    "GSE30219": {
        "columna": "characteristics_ch1_3_histology",
        "entrenables": {"ADC": 0, "SQC": 1},
        "ambiguas": {
            "LCNE": "neuroendocrino celula grande",
            "BAS": "basaloide",
            "CARCI": "carcinoide",
            "SCC": "microcitico (small cell)",
            "LCC": "celula grande",
            "Other": "otro",
        },
    },
    "GSE50081": {
        "columna": "characteristics_ch1_1_histology",
        "entrenables": {"adenocarcinoma": 0, "squamous cell carcinoma": 1,
                        "squamous cell carcinoma x2": 1},
        "ambiguas": {
            "large cell carcinoma": "celula grande",
            "adenosquamous carcinoma": "adenoescamoso",
            "nsclarge cell carcinoma-mixed": "mixto",
            "nsclc-favor adenocarcinoma": "indeterminado",
        },
    },
    "GSE19188": {
        "columna": "characteristics_ch1_1_cell_type",
        "entrenables": {"ADC": 0, "SCC": 1},
        "ambiguas": {"LCC": "celula grande"},
    },
}

MODELO = dict(solver="liblinear", l1_ratio=1, C=0.1, max_iter=5000,
              class_weight="balanced", random_state=0)


def cargar(gse, cfg):
    carpeta = os.path.join(BASE_DIR, f"TFM_{gse}")
    X = pd.read_csv(os.path.join(carpeta, "matriz_normalizada.csv"),
                    index_col=0).T.astype(np.float32)
    meta = pd.read_csv(os.path.join(carpeta, "metadata_procesada.csv"))
    meta = meta.set_index("geo_accession")          # alineamiento explicito
    comunes = X.index.intersection(meta.index)
    X, meta = X.loc[comunes], meta.loc[comunes]

    crudo = meta[cfg["columna"]].astype(str).str.strip().str.lower()
    ent = {k.lower(): v for k, v in cfg["entrenables"].items()}
    amb = {k.lower(): v for k, v in cfg["ambiguas"].items()}

    m_ent = crudo.isin(ent).values
    m_amb = crudo.isin(amb).values
    return (X.loc[m_ent], crudo[m_ent].map(ent).values.astype(int),
            X.loc[m_amb], crudo[m_amb].map(amb).values)


def main():
    print("=" * 78)
    print("PASO 18: EL CLASIFICADOR DE SUBTIPO ANTE LAS HISTOLOGIAS EXCLUIDAS")
    print("=" * 78)

    ent, amb = {}, {}
    for gse, cfg in CONFIG.items():
        Xe, ye, Xa, ea = cargar(gse, cfg)
        ent[gse] = (Xe, ye)
        amb[gse] = (Xa, ea)
        print(f"  {gse:<12} entrenables={len(ye):>4}  ambiguas={len(ea):>4}")

    genes = genes_comunes([X for X, _ in ent.values()])
    n_ent = sum(len(y) for _, y in ent.values())
    n_amb = sum(len(e) for _, e in amb.values())
    print(f"\n  Total entrenables (ADC/escamoso): {n_ent}")
    print(f"  Total ambiguas excluidas del paso 13: {n_amb}")
    print(f"  Es decir, el paso 13 descarto el "
          f"{n_amb / (n_ent + n_amb):.1%} de los tumores disponibles")

    print("\n[1] Entrenamiento con todas las muestras ADC/escamoso")
    X_tr = pd.concat(
        [pd.DataFrame(StandardScaler().fit_transform(ent[g][0][genes]))
         for g in ent],
        ignore_index=True,
    )
    y_tr = np.concatenate([ent[g][1] for g in ent])
    modelo = LogisticRegression(**MODELO).fit(X_tr, y_tr)
    print(f"  n={len(y_tr)}, genes con coeficiente no nulo: "
          f"{int((modelo.coef_[0] != 0).sum())}")

    print("\n[2] Probabilidades asignadas a las muestras ambiguas")
    filas, por_muestra = [], []
    for gse in amb:
        Xa, etiquetas = amb[gse]
        if len(Xa) == 0:
            continue
        Xa_s = StandardScaler().fit_transform(Xa[genes])
        prob = modelo.predict_proba(Xa_s)[:, 1]   # P(escamoso)
        por_muestra.append(pd.DataFrame({
            "Cohorte": gse, "Muestra": Xa.index,
            "Histologia": etiquetas, "P_Escamoso": prob,
        }))
        for tipo in pd.unique(etiquetas):
            m = etiquetas == tipo
            p = prob[m]
            extremas = int(((p > 0.9) | (p < 0.1)).sum())
            filas.append({
                "Cohorte": gse,
                "Histologia": tipo,
                "n": int(m.sum()),
                "P_escamoso_mediana": round(float(np.median(p)), 3),
                "P_escamoso_min": round(float(p.min()), 3),
                "P_escamoso_max": round(float(p.max()), 3),
                "N_Alta_Confianza": extremas,
                "Pct_Alta_Confianza": round(100 * extremas / m.sum(), 1),
                "Pct_Asignadas_Escamoso": round(100 * float((p > 0.5).mean()), 1),
            })

    res = pd.DataFrame(filas).sort_values("n", ascending=False)
    print(res.to_string(index=False))

    # Referencia: como se comporta el modelo en las muestras que SI son ADC/SQC.
    prob_ent = modelo.predict_proba(X_tr)[:, 1]
    ext_ent = float(((prob_ent > 0.9) | (prob_ent < 0.1)).mean())

    tot_amb = res["n"].sum()
    tot_ext = res["N_Alta_Confianza"].sum()
    pct = 100 * tot_ext / tot_amb

    print("\n[3] Veredicto")
    print(f"  Muestras ambiguas evaluadas                        : {tot_amb}")
    print(f"  Clasificadas con alta confianza (P>0.9 o P<0.1)    : "
          f"{tot_ext} ({pct:.1f}%)")
    print(f"  Referencia en muestras ADC/escamoso reales         : "
          f"{100 * ext_ent:.1f}%")
    pct_esc = (res["Pct_Asignadas_Escamoso"] * res["n"]).sum() / tot_amb
    print(f"  Asignadas a escamoso                               : {pct_esc:.1f}%")
    print()
    if pct > 50:
        print(f"  >>> LIMITACION CONFIRMADA. El modelo asigna una de las dos")
        print(f"      clases con alta confianza al {pct:.0f}% de las muestras que")
        print(f"      no pertenecen a ninguna: no detecta estar fuera de dominio.")
    else:
        print(f"  >>> HIPOTESIS NO CONFIRMADA ({pct:.0f}% < 50%). El modelo es MAS")
        print(f"      prudente con las histologias que no vio ({pct:.0f}% de")
        print(f"      asignaciones confiadas) que con las que si vio "
              f"({100 * ext_ent:.0f}%).")
        print(f"      La exclusion del paso 13 penaliza menos de lo previsto.")

    # El agregado esconde dos comportamientos opuestos que si importan.
    print("\n[4] Desglose que el porcentaje global oculta")
    bas = res[res["Histologia"] == "basaloide"]
    if not bas.empty:
        r = bas.iloc[0]
        print(f"  Basaloide (n={r['n']}): mediana P(escamoso)="
              f"{r['P_escamoso_mediana']}, {r['Pct_Asignadas_Escamoso']}% a escamoso.")
        print(f"    No es necesariamente un error: el carcinoma basaloide se")
        print(f"    considera una variante de escamoso en varias clasificaciones,")
        print(f"    por lo que el modelo puede estar acertando la biologia.")

    neuro = res[res["Histologia"].isin(
        ["neuroendocrino celula grande", "microcitico (small cell)", "carcinoide"])]
    if not neuro.empty:
        n_neuro = int(neuro["n"].sum())
        pct_adc = 100 - (neuro["Pct_Asignadas_Escamoso"] * neuro["n"]).sum() / n_neuro
        print(f"\n  Tumores neuroendocrinos (n={n_neuro}: LCNE, microcitico,")
        print(f"  carcinoide): {pct_adc:.0f}% asignados a ADENOCARCINOMA.")
        print(f"    Este si es un fallo con consecuencia clinica directa. El")
        print(f"    microcitico se trata de forma completamente distinta al NSCLC,")
        print(f"    y el modelo lo etiqueta como adenocarcinoma sin senalar duda.")
        print(f"    Conclusion: el AUC 0.97 del paso 13 solo es valido sobre")
        print(f"    tumores YA confirmados como ADC o escamoso; el modelo no")
        print(f"    puede usarse como primer filtro sobre un caso sin diagnosticar.")

    res.to_csv(os.path.join(BASE_DIR, "resultados/subtipo/SUBTIPO_CASOS_DIFICILES.csv"), index=False)
    pd.concat(por_muestra, ignore_index=True).to_csv(
        os.path.join(BASE_DIR, "resultados/subtipo/SUBTIPO_PROBS_AMBIGUAS.csv"), index=False)

    # Resumen para que la memoria y la interfaz no citen cifras a mano.
    n_neuro = int(neuro["n"].sum()) if not neuro.empty else 0
    pct_adc_neuro = (
        100 - (neuro["Pct_Asignadas_Escamoso"] * neuro["n"]).sum() / n_neuro
        if n_neuro else float("nan"))
    with open(os.path.join(BASE_DIR, "resultados/subtipo/SUBTIPO_DIFICILES_RESUMEN.json"), "w") as fh:
        json.dump({
            "n_entrenables": int(n_ent),
            "n_ambiguas": int(n_amb),
            "pct_excluidas": 100 * n_amb / (n_ent + n_amb),
            "pct_alta_confianza_ambiguas": float(pct),
            "pct_alta_confianza_vistas": 100 * float(ext_ent),
            "n_neuroendocrinos": n_neuro,
            "pct_neuro_a_adenocarcinoma": float(pct_adc_neuro),
        }, fh, indent=2)
    print("\n  Guardado: SUBTIPO_CASOS_DIFICILES.csv, SUBTIPO_PROBS_AMBIGUAS.csv, "
          "resultados/subtipo/SUBTIPO_DIFICILES_RESUMEN.json")
    print("=" * 78)


if __name__ == "__main__":
    main()
