"""
Paso 15: re-evaluacion honesta del LODO tumor-vs-sano.

Este fichero es ahora un envoltorio del framework. Antes contenia su propia copia
del bucle LODO: la misma que los pasos 13, 16, 17 y 19, cinco implementaciones
que podian divergir y de hecho divergian en el modelo, el escalado y las metricas.
La logica vive en tfm/validacion.py, y aqui solo queda lo propio de este paso:
el contraste con la cifra que se reportaba antes.

Equivalente a:  python -m tfm ejecutar tumor_vs_sano
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tfm import comprobaciones, tareas, validacion
from tfm.cohortes import RAIZ

# Lo que la memoria previa reportaba, para el contraste explicito.
ACCURACY_REPORTADA_ANTES = 0.811


def main():
    print("=" * 78)
    print("PASO 15: LODO TUMOR-vs-SANO CON METRICAS HONESTAS")
    print("=" * 78)

    t = tareas.obtener("tumor_vs_sano")
    print("\n[1] Carga (alineada por geo_accession)")
    datos, _ = t.cargar(verbose=True)
    genes = t.genes(datos)
    print(f"\n  Genes comunes a las {len(datos)} cohortes: {len(genes)}")

    print("\n[2] Comprobaciones previas")
    comprobaciones.ejecutar(datos, t.clases)

    print("\n[3] Validacion LODO")
    resultados = validacion.lodo(datos, genes, t.modelo)
    tabla = validacion.tabla(resultados)
    res = validacion.resumen(resultados)
    print(tabla.to_string(index=False))

    print("\n[4] Medias: ingenua frente a honesta")
    print(f"  Accuracy media sobre las {res['n_cohortes']} cohortes"
          f"        : {res['accuracy_media_ingenua']:.4f}")
    print(f"  Balanced accuracy media sobre las {res['n_evaluables']} evaluables"
          f": {res['balanced_accuracy_media']:.4f}")
    print(f"  AUC media sobre las evaluables"
          f"                    : {res['auc_media']:.4f}")
    print(f"  Baseline medio de las evaluables"
          f"                  : {res['baseline_medio']:.4f}")
    print(f"  Ganancia media sobre baseline"
          f"                     : {res['ganancia_media']:+.4f}")

    peores = tabla[tabla["Evaluable"] & ~tabla["Supera_Baseline"]]
    print(f"\n  Cohortes evaluables que NO superan su baseline: "
          f"{len(peores)} de {res['n_evaluables']}")
    for _, r in peores.iterrows():
        print(f"    {r['Cohorte_Test']:<12} acc={r['Accuracy']:.3f} "
              f"vs baseline={r['Baseline_Mayoritaria']:.3f} "
              f"({r['Ganancia_vs_Baseline']:+.3f})")

    tabla.to_csv(os.path.join(RAIZ, "resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv"), index=False)

    print("\n" + "=" * 78)
    print("CONTRASTE CON LO REPORTADO EN LA MEMORIA PREVIA")
    print("=" * 78)
    print(f"  Memoria (p.60): accuracy media {ACCURACY_REPORTADA_ANTES} sobre "
          f"{res['n_cohortes']} folds, 3 de ellos monoclase")
    print(f"  Honesto       : balanced accuracy media "
          f"{res['balanced_accuracy_media']:.3f} sobre {res['n_evaluables']} "
          f"folds evaluables")
    print(f"  Ganancia real media sobre azar informado: "
          f"{res['ganancia_media']:+.3f}")
    print("=" * 78)
    return tabla


if __name__ == "__main__":
    main()
