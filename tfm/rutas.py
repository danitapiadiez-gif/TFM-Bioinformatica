"""Rutas centralizadas y helper para asegurar carpetas de resultados.

Los pasos del pipeline escriben CSV/JSON bajo `resultados/<categoria>/`.
Este modulo garantiza que las carpetas existan antes de escribir, sin
tener que llamar a `os.makedirs` en cada script.

Uso:
    from tfm.rutas import RESULTADOS, asegurar_carpetas
    asegurar_carpetas()
    fichero = RESULTADOS / "subtipo" / "SUBTIPO_LODO_RESULTADOS.csv"
"""
from pathlib import Path

# Raiz del proyecto (dos niveles por encima de este fichero: tfm/rutas.py)
RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"

# Subcarpetas por tarea biologica / analisis
CARPETAS = {
    "auditoria":     RESULTADOS / "auditoria",
    "subtipo":       RESULTADOS / "subtipo",
    "tumor_vs_sano": RESULTADOS / "tumor_vs_sano",
    "firma_consenso": RESULTADOS / "firma_consenso",
    "recalibracion": RESULTADOS / "recalibracion",
    "comparativa_ml": RESULTADOS / "comparativa_ml",
    "tcga":          RESULTADOS / "tcga",
}


def asegurar_carpetas() -> None:
    """Crea todas las carpetas de resultados si no existen.

    Idempotente: se puede llamar cuantas veces se quiera. Debe ser lo
    primero que haga un paso del pipeline antes de escribir salidas.
    """
    for carpeta in CARPETAS.values():
        carpeta.mkdir(parents=True, exist_ok=True)


# Ejecuta la creacion al importar el modulo, para que cualquier import
# de tfm.rutas garantice que las carpetas estan disponibles.
asegurar_carpetas()
