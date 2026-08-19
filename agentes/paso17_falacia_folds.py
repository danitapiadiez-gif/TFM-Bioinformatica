"""
Paso 17: la consistencia de signo sobre folds LODO no es evidencia de replicacion.

El analisis original (ml_meta_validacion.py, memoria §4.4.8 y §5.3.3) mide la
estabilidad de un gen sumando el signo de su coeficiente a lo largo de los folds
LODO, y presenta "11/11" como prueba de robustez biologica.

El problema es estructural: cada fold LODO entrena con todas las cohortes menos
una, de modo que dos folds cualesquiera comparten la gran mayoria de sus
muestras de entrenamiento. No son replicas independientes, sino casi el mismo
modelo ajustado varias veces. El acuerdo de signo esta garantizado por el diseno.

Contraste: se mide el acuerdo de signo de dos formas sobre el MISMO conjunto de
genes y las MISMAS cohortes:
  (a) entre folds LODO        -> entrenamientos solapados (metodo original)
  (b) entre modelos por cohorte -> entrenamientos disjuntos (replicacion real)

Hipotesis pre-registrada: (a) produce muchos mas genes con acuerdo perfecto que
(b). Si ambos numeros se parecen, la metrica original era valida.
"""

import os
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from utils_cohortes import BASE_DIR, cargar_cohorte, genes_comunes, listar_cohortes

MODELO = dict(solver="liblinear", l1_ratio=1, C=0.5, max_iter=2000,
              random_state=0)


def main():
    print("=" * 78)
    print("PASO 17: CONSISTENCIA DE SIGNO - FOLDS SOLAPADOS vs COHORTES INDEPENDIENTES")
    print("=" * 78)

    datos = {}
    for gse in listar_cohortes():
        X, y = cargar_cohorte(gse)
        if X is not None and len(X) and (y == 0).any() and (y == 1).any():
            datos[gse] = (X, y)
    ids = list(datos)
    genes = genes_comunes([X for X, _ in datos.values()])
    n_por_cohorte = {g: len(y) for g, (_, y) in datos.items()}
    total = sum(n_por_cohorte.values())
    print(f"\n  Cohortes con ambas clases: {len(ids)} | genes: {len(genes)} "
          f"| muestras: {total}")

    print("\n[1] Cuanto se solapan los entrenamientos LODO")
    solapes = []
    for a, b in combinations(ids, 2):
        n_a = total - n_por_cohorte[a]   # tamano del train del fold a
        n_b = total - n_por_cohorte[b]
        compartidas = total - n_por_cohorte[a] - n_por_cohorte[b]
        solapes.append(compartidas / min(n_a, n_b))
    solapes = np.array(solapes)
    print(f"  Fraccion de muestras de entrenamiento compartidas entre dos folds:")
    print(f"    minimo {solapes.min():.1%} | mediana {np.median(solapes):.1%} "
          f"| maximo {solapes.max():.1%}")
    print(f"  En cambio, los modelos por cohorte comparten 0% de sus muestras.")

    print("\n[2] (a) Coeficientes por fold LODO (entrenamientos solapados)")
    coef_lodo = {}
    for test_id in ids:
        train_ids = [g for g in ids if g != test_id]
        X_tr = pd.concat(
            [pd.DataFrame(StandardScaler().fit_transform(datos[g][0][genes]))
             for g in train_ids],
            ignore_index=True,
        )
        y_tr = np.concatenate([datos[g][1] for g in train_ids])
        m = LogisticRegression(**MODELO).fit(X_tr, y_tr)
        coef_lodo[test_id] = pd.Series(m.coef_[0], index=genes)
        print(f"  fold sin {test_id:<12} train={len(y_tr):>4} muestras, "
              f"{int((m.coef_[0] != 0).sum())} genes no nulos")

    print("\n[3] (b) Coeficientes por cohorte independiente (entrenamientos disjuntos)")
    coef_indep = {}
    for gse in ids:
        X, y = datos[gse]
        m = LogisticRegression(**MODELO).fit(
            StandardScaler().fit_transform(X[genes]), y
        )
        coef_indep[gse] = pd.Series(m.coef_[0], index=genes)
        print(f"  solo {gse:<12} train={len(y):>4} muestras, "
              f"{int((m.coef_[0] != 0).sum())} genes no nulos")

    L = pd.DataFrame(coef_lodo)
    I = pd.DataFrame(coef_indep)
    k = len(ids)

    def resumen(M, etiqueta):
        signos = np.sign(M)
        no_nulo = (M != 0)
        n_no_nulo = no_nulo.sum(axis=1)
        # Acuerdo perfecto: seleccionado en TODAS y con el mismo signo en todas.
        perfecto = (n_no_nulo == k) & (signos.sum(axis=1).abs() == k)
        # Genes seleccionados al menos una vez.
        alguna = n_no_nulo > 0
        return {
            "metodo": etiqueta,
            "genes_seleccionados_alguna_vez": int(alguna.sum()),
            "genes_seleccionados_en_todas": int((n_no_nulo == k).sum()),
            "genes_acuerdo_signo_perfecto": int(perfecto.sum()),
            "pct_de_los_seleccionados": (
                round(100 * perfecto.sum() / max(alguna.sum(), 1), 2)),
        }

    r_lodo = resumen(L, f"(a) folds LODO solapados (k={k})")
    r_indep = resumen(I, f"(b) cohortes independientes (k={k})")
    comp = pd.DataFrame([r_lodo, r_indep])

    print("\n[4] Resultados")
    print(comp.to_string(index=False))

    a = r_lodo["genes_acuerdo_signo_perfecto"]
    b = r_indep["genes_acuerdo_signo_perfecto"]
    print("\n[5] Veredicto")
    print(f"  Genes con acuerdo de signo perfecto entre folds LODO      : {a}")
    print(f"  Genes con acuerdo de signo perfecto entre cohortes indep. : {b}")
    if b > 0:
        print(f"  Factor de inflacion: {a / b:.1f}x")
    else:
        print(f"  Factor de inflacion: no calculable (ningun gen replica de forma"
              f" independiente)")

    print()
    if a > b:
        print(f"  >>> HIPOTESIS CONFIRMADA. El metodo original produce {a} genes")
        print(f"      'estables' frente a {b} que replican realmente entre")
        print(f"      cohortes disjuntas. La consistencia de signo sobre folds")
        print(f"      solapados ({np.median(solapes):.0%} de muestras compartidas)")
        print(f"      mide reproducibilidad del ajuste, no del fenomeno biologico.")
    else:
        print(f"  >>> HIPOTESIS REFUTADA. El acuerdo entre folds no supera al de")
        print(f"      cohortes independientes ({a} vs {b}); la metrica original")
        print(f"      no estaba inflada por el solapamiento.")

    # Los genes que SI replican de forma independiente: firma defendible.
    signos_i = np.sign(I)
    replican = I[((I != 0).sum(axis=1) == k)
                 & (signos_i.sum(axis=1).abs() == k)].copy()
    if not replican.empty:
        replican["Coef_Medio"] = replican[ids].mean(axis=1)
        replican = replican.reindex(
            replican["Coef_Medio"].abs().sort_values(ascending=False).index)
        print(f"\n  Genes que replican en las {k} cohortes independientes "
              f"(firma defendible):")
        print(replican[["Coef_Medio"]].head(20).to_string())
        replican.to_csv(os.path.join(BASE_DIR, "resultados/firma_consenso/FIRMA_REPLICADA_INDEPENDIENTE.csv"))

    # Contraste directo con los genes estrella de la memoria (§5.3.2, Tabla 7).
    estrella = ["SLC6A4", "S100A10", "KANK3", "SH3GL3", "HIST1H2BM", "ZNF702P", "TOX3"]
    print(f"\n  Genes destacados en la memoria (Tabla 7, p.64):")
    print(f"  {'Gen':<12} {'signo folds LODO':>17} {'signo cohortes indep':>22} "
          f"{'replica':>9}")
    for g in estrella:
        if g not in L.index:
            print(f"  {g:<12} {'ausente de la matriz comun':>17}")
            continue
        s_l = int(np.sign(L.loc[g]).sum())
        s_i = int(np.sign(I.loc[g]).sum())
        nn_i = int((I.loc[g] != 0).sum())
        rep = "SI" if (nn_i == k and abs(s_i) == k) else "no"
        print(f"  {g:<12} {f'{s_l:+d}/{k}':>17} {f'{s_i:+d}/{k} ({nn_i} no nulos)':>22} "
              f"{rep:>9}")

    # -----------------------------------------------------------------------
    # Control necesario: la comparacion (a) vs (b) esta confundida por el tamano
    # de muestra. Los modelos por cohorte entrenan con 10-246 muestras y los
    # folds LODO con 416-652; con L1, menos muestras seleccionan menos genes, de
    # modo que exigir interseccion en las k puede dar 0 por esparsidad y no por
    # falta de replicacion.
    #
    # El control aisla el solapamiento midiendo la concordancia de signo entre
    # PAREJAS de modelos con tamano de entrenamiento comparable:
    #   - pareja de folds LODO      -> ~98% de muestras compartidas, n~600
    #   - pareja de mitades disjuntas -> 0% compartidas, n~331
    # Si la concordancia cae al pasar de la primera a la segunda, la diferencia
    # es atribuible al solapamiento y no a la esparsidad.
    # -----------------------------------------------------------------------
    print("\n[6] Control del confundido por tamano de muestra")
    print("    (concordancia de signo entre PAREJAS, entrenamientos comparables)")

    def concordancia(c1, c2):
        """% de acuerdo de signo entre los genes seleccionados por AMBOS."""
        ambos = (c1 != 0) & (c2 != 0)
        if ambos.sum() == 0:
            return np.nan, 0
        return float((np.sign(c1[ambos]) == np.sign(c2[ambos])).mean()), int(ambos.sum())

    conc_lodo = [concordancia(L[a], L[b]) for a, b in combinations(ids, 2)]
    v_lodo = [c for c, n in conc_lodo if not np.isnan(c)]
    print(f"  Parejas de folds LODO (~{np.median(solapes):.0%} compartido): "
          f"concordancia media {np.mean(v_lodo):.1%} "
          f"(n={len(v_lodo)} parejas)")

    # Mitades disjuntas del conjunto agrupado, estratificadas por cohorte.
    rng = np.random.RandomState(0)
    X_all = pd.concat(
        [pd.DataFrame(StandardScaler().fit_transform(datos[g][0][genes]),
                      columns=genes) for g in ids],
        ignore_index=True,
    )
    y_all = np.concatenate([datos[g][1] for g in ids])
    coh_all = np.concatenate([[g] * len(datos[g][1]) for g in ids])

    conc_disj, tam_disj = [], []
    for rep in range(10):
        mitad = np.zeros(len(y_all), dtype=bool)
        for g in ids:  # estratificar por cohorte y clase
            for clase in (0, 1):
                idx = np.where((coh_all == g) & (y_all == clase))[0]
                if len(idx) < 2:
                    continue
                elegidos = rng.RandomState if False else rng.permutation(idx)
                mitad[elegidos[: len(idx) // 2]] = True
        ma, mb = mitad, ~mitad
        if len(np.unique(y_all[ma])) < 2 or len(np.unique(y_all[mb])) < 2:
            continue
        m1 = LogisticRegression(**MODELO).fit(X_all[ma], y_all[ma])
        m2 = LogisticRegression(**MODELO).fit(X_all[mb], y_all[mb])
        c, n = concordancia(pd.Series(m1.coef_[0], index=genes),
                            pd.Series(m2.coef_[0], index=genes))
        if not np.isnan(c):
            conc_disj.append(c)
            tam_disj.append((int(ma.sum()), int(mb.sum()), n))
    print(f"  Parejas de mitades DISJUNTAS (0% compartido, "
          f"n~{tam_disj[0][0] if tam_disj else 0} cada una): "
          f"concordancia media {np.mean(conc_disj):.1%} "
          f"({len(conc_disj)} repeticiones)")

    caida = np.mean(v_lodo) - np.mean(conc_disj)
    print(f"\n  Caida de concordancia al eliminar el solapamiento: "
          f"{caida:+.1%}")
    if caida > 0.05:
        print(f"  >>> El control CONFIRMA el efecto: con tamanos de entrenamiento")
        print(f"      comparables, quitar el solapamiento reduce la concordancia")
        print(f"      de signo {np.mean(v_lodo):.1%} -> {np.mean(conc_disj):.1%}.")
        print(f"      La inflacion no es un artefacto de esparsidad del LASSO.")
    else:
        print(f"  >>> El control NO respalda el efecto: la concordancia apenas")
        print(f"      cambia al eliminar el solapamiento, por lo que la diferencia")
        print(f"      observada en [4] se debe al tamano de muestra y no al diseno")
        print(f"      de los folds. La critica a la metrica original queda")
        print(f"      debilitada y debe reformularse.")

    comp["concordancia_pareja_media"] = [np.mean(v_lodo), np.mean(conc_disj)]
    comp.to_csv(os.path.join(BASE_DIR, "resultados/auditoria/FALACIA_FOLDS_COMPARACION.csv"), index=False)
    print("\n  Guardado: FALACIA_FOLDS_COMPARACION.csv, "
          "resultados/firma_consenso/FIRMA_REPLICADA_INDEPENDIENTE.csv")
    print("=" * 78)


if __name__ == "__main__":
    main()
