"""
Comprobaciones previas: los cuatro modos de fallo, como control automatico.

Los cuatro problemas que este trabajo documento comparten el rasgo que los hace
peligrosos: ninguno interrumpe la ejecucion. El pipeline termina, escribe sus
ficheros y produce tablas de aspecto correcto.

De ahi este modulo: cada fallo encontrado se convierte en una comprobacion que
toda tarea ejecuta ANTES de analizar. El framework incorpora sus propias
lecciones en lugar de dejarlas en la memoria.

  1. Cobertura     cohortes declaradas que no llegaron a procesarse
  2. Alineamiento  muestras con la etiqueta clinica de otro paciente
  3. Curacion      tasa de exito del etiquetado automatico, por cohorte
  4. Evaluabilidad cohortes de una sola clase usadas como conjunto de test

`ejecutar()` devuelve una lista de Aviso. Los de gravedad "critico" son los que
invalidan un resultado si se ignoran.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tfm import cohortes


@dataclass
class Aviso:
    comprobacion: str
    gravedad: str          # critico | atencion | informativo
    cohorte: str
    mensaje: str

    def __str__(self):
        marca = {"critico": "[!!]", "atencion": "[! ]", "informativo": "[  ]"}
        return (f"{marca.get(self.gravedad, '[  ]')} {self.comprobacion:<14} "
                f"{self.cohorte:<12} {self.mensaje}")


def cobertura() -> list[Aviso]:
    """Cohortes declaradas frente a cohortes con datos."""
    dec, disp = cohortes.declaradas(), cohortes.disponibles()
    avisos = []
    for g in dec:
        if g not in disp:
            avisos.append(Aviso(
                "cobertura", "critico", g,
                "declarada en datasets.txt pero nunca procesada: el pipeline "
                "continuo sin emitir ningun error"))
    for g in disp:
        if g not in dec:
            avisos.append(Aviso(
                "cobertura", "atencion", g,
                "presente en los resultados pero no declarada: la cohorte "
                "analizada no coincide con la declarada"))
    return avisos


def alineamiento(gses: list[str] | None = None) -> list[Aviso]:
    """Orden de las columnas de la matriz frente a las filas del metadata."""
    avisos = []
    for g in (gses or cohortes.disponibles()):
        d = cohortes.diagnostico_alineamiento(g)
        if d["estado"] == "DESALINEADO":
            avisos.append(Aviso(
                "alineamiento", "critico", g,
                f"{int(d['n_desalineadas'])} de {d['n_matriz']} muestras "
                f"recibirian la etiqueta de otro paciente si se asignase por "
                f"posicion"))
        elif d["estado"] == "CONJUNTOS_DISTINTOS":
            avisos.append(Aviso(
                "alineamiento", "critico", g,
                f"matriz y metadata contienen muestras distintas "
                f"({d['n_matriz']} frente a {d['n_metadata']})"))
    return avisos


def curacion(gses: list[str] | None = None,
             columna: str = "grupo_analisis",
             umbral: float = 0.5) -> list[Aviso]:
    """Tasa de exito del etiquetado automatico, cohorte a cohorte."""
    import os
    avisos = []
    for g in (gses or cohortes.disponibles()):
        ruta = os.path.join(cohortes.carpeta(g), "metadata_procesada.csv")
        meta = pd.read_csv(ruta)
        if columna not in meta.columns:
            continue
        v = meta[columna].astype(str).str.strip().str.lower()
        n_ok = int(v.isin(["sano", "enfermo"]).sum())
        tasa = n_ok / len(meta) if len(meta) else 0
        if tasa < umbral:
            avisos.append(Aviso(
                "curacion", "critico", g,
                f"solo el {100 * tasa:.1f} % de las muestras recibio etiqueta "
                f"({len(meta) - n_ok} de {len(meta)} sin clasificar): la "
                f"fraccion superviviente no representa al estudio"))
        elif tasa < 1:
            avisos.append(Aviso(
                "curacion", "atencion", g,
                f"{len(meta) - n_ok} de {len(meta)} muestras sin clasificar "
                f"({100 * tasa:.1f} % de exito)"))
    return avisos


def evaluabilidad(datos, clases: dict[int, str]) -> list[Aviso]:
    """Cohortes que no pueden funcionar como conjunto de test."""
    avisos = []
    for g, (_, y) in datos.items():
        n0, n1 = int((y == 0).sum()), int((y == 1).sum())
        if not (n0 and n1):
            presente = clases[1] if n1 else clases[0]
            avisos.append(Aviso(
                "evaluabilidad", "critico", g,
                f"una sola clase ({presente}, n={max(n0, n1)}): predecir siempre "
                f"esa clase alcanza accuracy 1,000 por definicion, de modo que "
                f"no es evaluable como test"))
        elif min(n0, n1) / (n0 + n1) < 0.1:
            avisos.append(Aviso(
                "evaluabilidad", "atencion", g,
                f"desbalance acusado ({n0}/{n1}): el baseline de clase "
                f"mayoritaria es {max(n0, n1) / (n0 + n1):.3f}"))
    return avisos


def ejecutar(datos=None, clases=None, verbose: bool = True) -> list[Aviso]:
    """Las cuatro comprobaciones. Se ejecuta antes de cualquier analisis."""
    avisos = cobertura() + alineamiento() + curacion()
    if datos is not None and clases is not None:
        avisos += evaluabilidad(datos, clases)

    if verbose:
        criticos = [a for a in avisos if a.gravedad == "critico"]
        print(f"  Comprobaciones previas: {len(avisos)} avisos "
              f"({len(criticos)} criticos)")
        for a in avisos:
            print(f"    {a}")
        if not avisos:
            print("    sin incidencias")
    return avisos
