"""
Definicion de tareas biologicas, desde configuracion y no desde codigo.

Esta es la pieza que convierte el conjunto de scripts en un framework: plantear
una pregunta nueva —pronostico, estado de gen conductor, estadio— es anadir una
entrada a `configuracion/tareas.yaml`, no escribir otro script con otra copia del
bucle LODO.

Una tarea declara de que cohortes se sirve, de que columna clinica salen las
etiquetas y como se mapean sus valores, que valores se descartan por ambiguos, y
opcionalmente su especificacion de modelo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import yaml

from tfm import cohortes

RAIZ = cohortes.RAIZ
CONFIG = os.path.join(RAIZ, "configuracion")


@dataclass
class FuenteCohorte:
    """De donde saca una tarea las etiquetas en una cohorte concreta."""

    gse: str
    columna: str
    mapa: dict[str, int]
    descartar: list[str] = field(default_factory=list)


@dataclass
class Tarea:
    nombre: str
    descripcion: str
    clases: dict[int, str]
    fuentes: list[FuenteCohorte]
    modelo: dict | None = None
    relevancia_clinica: str = ""

    def cargar(self, verbose: bool = False):
        """Carga las cohortes de la tarea. Descarta las que no tengan dos clases."""
        datos, descartadas = {}, {}
        for f in self.fuentes:
            if f.gse not in cohortes.disponibles():
                descartadas[f.gse] = "sin datos procesados"
                continue
            X, y = cohortes.cargar(f.gse, f.columna, f.mapa)
            if X is None or len(X) == 0:
                descartadas[f.gse] = f"columna «{f.columna}» ausente o vacia"
                continue
            if len(np.unique(y)) < 2:
                # Sigue siendo entrenamiento valido; quien decide es la validacion.
                descartadas[f.gse] = "una sola clase"
            datos[f.gse] = (X, y)
            if verbose:
                n0, n1 = int((y == 0).sum()), int((y == 1).sum())
                marca = "" if (n0 and n1) else "   [MONOCLASE]"
                print(f"    {f.gse:<12} n={len(y):>4}  "
                      f"{self.clases[0]}={n0:>3} {self.clases[1]}={n1:>3}{marca}")
        return datos, descartadas

    def genes(self, datos) -> list[str]:
        return cohortes.genes_comunes([X for X, _ in datos.values()])


def _fuente(d: dict) -> FuenteCohorte:
    return FuenteCohorte(gse=d["gse"], columna=d["columna"],
                         mapa={str(k): int(v) for k, v in d["mapa"].items()},
                         descartar=[str(x) for x in d.get("descartar", [])])


def cargar_definiciones(ruta: str | None = None) -> dict[str, Tarea]:
    """Lee todas las tareas declaradas en configuracion/tareas.yaml."""
    ruta = ruta or os.path.join(CONFIG, "tareas.yaml")
    with open(ruta, encoding="utf-8") as fh:
        bruto = yaml.safe_load(fh)
    salida = {}
    for nombre, d in bruto["tareas"].items():
        salida[nombre] = Tarea(
            nombre=nombre,
            descripcion=d["descripcion"],
            clases={int(k): str(v) for k, v in d["clases"].items()},
            fuentes=[_fuente(f) for f in d["cohortes"]],
            modelo=d.get("modelo"),
            relevancia_clinica=d.get("relevancia_clinica", ""),
        )
    return salida


def obtener(nombre: str) -> Tarea:
    defs = cargar_definiciones()
    if nombre not in defs:
        disponibles = ", ".join(defs)
        raise KeyError(
            f"Tarea «{nombre}» no declarada. Disponibles: {disponibles}. "
            f"Para anadir una nueva, edita configuracion/tareas.yaml.")
    return defs[nombre]


def listar() -> list[str]:
    return list(cargar_definiciones())
