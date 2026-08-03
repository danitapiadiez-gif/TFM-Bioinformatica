"""
Framework transcriptomico para la identificacion y validacion de biomarcadores.

Tres capas:

  1. Curacion clinica de metadatos con modelos de lenguaje  -> `curacion`
  2. Identificacion de firmas moleculares                   -> `firma`
  3. Validacion                                             -> `validacion`,
                                                               `comprobaciones`

Una tarea biologica se define en `configuracion/tareas.yaml`, no en codigo: eso
es lo que permite plantear una pregunta nueva sin escribir un script nuevo.
"""

from tfm import cohortes, comprobaciones, firma, tareas, validacion  # noqa: F401

__version__ = "1.0.0"
__all__ = ["cohortes", "comprobaciones", "firma", "tareas", "validacion"]
