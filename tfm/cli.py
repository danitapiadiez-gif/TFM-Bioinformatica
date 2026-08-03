"""
Punto de entrada del framework.

    python -m tfm listar
    python -m tfm comprobar
    python -m tfm ejecutar subtipo_histologico
    python -m tfm ejecutar tumor_vs_sano

Ejecutar una tarea nueva no requiere codigo nuevo: basta declararla en
configuracion/tareas.yaml.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

from tfm import cohortes, comprobaciones, firma, tareas, validacion

TAMANOS_PANEL = [3, 5, 8, 10, 15, 20, 30, 50, 100, 250, 500, 1000]


def _dec(v, n=4):
    return f"{v:.{n}f}".replace(".", ",")


def cmd_listar(_):
    defs = tareas.cargar_definiciones()
    print("Tareas declaradas en configuracion/tareas.yaml:\n")
    for n, t in defs.items():
        print(f"  {n}")
        print(f"    {t.descripcion.strip()}")
        print(f"    clases: {t.clases[0]} / {t.clases[1]}  |  "
              f"cohortes declaradas: {len(t.fuentes)}")
        if t.relevancia_clinica:
            print(f"    relevancia: {t.relevancia_clinica.strip()}")
        print()
    return 0


def cmd_comprobar(_):
    print("=" * 74)
    print("COMPROBACIONES PREVIAS SOBRE LOS DATOS")
    print("=" * 74)
    avisos = comprobaciones.ejecutar()
    criticos = [a for a in avisos if a.gravedad == "critico"]
    print(f"\n  {len(criticos)} avisos criticos de {len(avisos)}.")
    print("  Ninguno de estos fallos interrumpe un pipeline que no los compruebe.")
    return 0


def cmd_ejecutar(args):
    t = tareas.obtener(args.tarea)
    print("=" * 74)
    print(f"TAREA: {t.nombre}")
    print("=" * 74)
    print(f"  {t.descripcion.strip()}\n")

    print("[1] Carga de cohortes (alineadas por geo_accession)")
    datos, descartadas = t.cargar(verbose=True)
    for g, motivo in descartadas.items():
        print(f"    {g:<12} aviso: {motivo}")
    genes = t.genes(datos)
    print(f"\n    {len(datos)} cohortes | {len(genes)} genes comunes")

    print("\n[2] Comprobaciones previas")
    comprobaciones.ejecutar(datos, t.clases)

    print("\n[3] Validacion externa LODO")
    resultados = validacion.lodo(datos, genes, t.modelo)
    tabla = validacion.tabla(resultados)
    res = validacion.resumen(resultados)
    print(tabla.to_string(index=False))
    print(f"\n    balanced accuracy media : {_dec(res['balanced_accuracy_media'])}"
          f"  (sobre {res['n_evaluables']} de {res['n_cohortes']} evaluables)")
    print(f"    AUC media               : {_dec(res['auc_media'])}")
    print(f"    especificidad media     : {_dec(res['especificidad_media'])}")
    print(f"    no superan su baseline  : {res['n_no_superan_baseline']}"
          f" de {res['n_evaluables']}")
    print(f"    accuracy media ingenua  : {_dec(res['accuracy_media_ingenua'])}"
          f"  (sobre las {res['n_cohortes']}, sin contenido)")

    print("\n[4] Firma: replicacion entre cohortes ajustadas por separado")
    D = firma.d_de_cohen(datos, genes)
    sel = firma.replicados(D, t.clases)
    print(f"    genes validados: {len(sel)} de {len(genes)} "
          f"({100 * len(sel) / len(genes):.2f} %)")
    if len(sel):
        print(sel[["d_Media", "d_Minima_Abs", "Direccion"]].head(10).to_string())

    salida = {"tarea": t.nombre, **res,
              "n_genes_evaluados": len(genes),
              "n_genes_validados": int(len(sel))}

    print("\n[5] Panel minimo")
    if len(sel) >= 3:
        k, curva = firma.panel_minimo(datos, list(sel.index), TAMANOS_PANEL,
                                      t.modelo)
        print(curva.to_string(index=False))
        print(f"\n    panel minimo: {k} genes")
        salida["panel_minimo"] = k
        salida["panel_minimo_genes"] = list(sel.index[:k])
        curva.to_csv(os.path.join(cohortes.RAIZ,
                                  f"{t.nombre}_PANEL_CURVA.csv"), index=False)
    else:
        print("    no procede: menos de 3 genes superan la validacion")

    tabla.to_csv(os.path.join(cohortes.RAIZ, f"{t.nombre}_LODO.csv"), index=False)
    sel.to_csv(os.path.join(cohortes.RAIZ, f"{t.nombre}_FIRMA.csv"))
    with open(os.path.join(cohortes.RAIZ, f"{t.nombre}_RESUMEN.json"), "w") as fh:
        json.dump(salida, fh, indent=2, ensure_ascii=False)

    print(f"\n  Guardado: {t.nombre}_LODO.csv, {t.nombre}_FIRMA.csv, "
          f"{t.nombre}_RESUMEN.json")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="tfm",
        description="Framework transcriptomico: identificacion y validacion "
                    "de biomarcadores.")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("listar", help="tareas declaradas").set_defaults(
        func=cmd_listar)
    sub.add_parser("comprobar", help="comprobaciones previas").set_defaults(
        func=cmd_comprobar)
    e = sub.add_parser("ejecutar", help="ejecuta una tarea de principio a fin")
    e.add_argument("tarea", choices=tareas.listar())
    e.set_defaults(func=cmd_ejecutar)

    args = p.parse_args(argv)
    return args.func(args)
