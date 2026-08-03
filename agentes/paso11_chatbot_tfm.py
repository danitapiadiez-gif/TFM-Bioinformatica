"""
Paso 11: interfaz conversacional de consulta de resultados (terminal).

Reescrito respecto a la version anterior, que presentaba tres defectos:

  - Leia los resultados de ~/Desktop en lugar del directorio del proyecto, no
    encontraba ningun fichero y construia un contexto vacio bajo el encabezado
    "SISTEMA DE CONOCIMIENTO". El modelo respondia entonces desde su
    conocimiento parametrico, presentandolo como resultados del trabajo.
  - Inyectaba la cadena fija "Rendimiento ML Local: Alta Precision reportada."
    sin leer ninguna metrica.
  - Imprimia parte de la clave de API por pantalla.

El contexto se construye ahora en contexto_tfm.py a partir de los CSV de
resultados, y el programa no arranca si faltan.
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contexto_tfm import (  # noqa: E402
    BASE_DIR,
    FaltanResultados,
    inventario,
    prompt_sistema,
)

MODELO = "llama-3.3-70b-versatile"
TEMPERATURA = 0.0          # consulta de datos: sin creatividad
MAX_HISTORIAL = 12         # turnos conservados


def obtener_cliente():
    """Devuelve un cliente de Groq, o None si no hay credencial utilizable."""
    # Ruta explicita: find_dotenv() depende del directorio de invocacion.
    load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
    clave = os.getenv("GROQ_API_KEY")
    if clave:
        clave = clave.strip().strip('"').strip("'")

    if not clave:
        print("No se encontro GROQ_API_KEY en el archivo .env.")
        print("Anade la linea  GROQ_API_KEY=...  al fichero .env del proyecto.")
        return None
    if not clave.startswith("gsk_"):
        print("La clave encontrada no tiene el formato de Groq (debe empezar por gsk_).")
        return None

    # No se imprime la clave, ni parcialmente.
    print("Credencial de Groq cargada correctamente.")
    return Groq(api_key=clave)


def main():
    print("=" * 74)
    print(" ASISTENTE DE CONSULTA DE RESULTADOS - TFM AUDITORIA DE REPRODUCIBILIDAD")
    print("=" * 74)

    try:
        sistema = prompt_sistema()
    except FaltanResultados as e:
        print(f"\nNo se puede iniciar el asistente.\n\n{e}")
        return 1

    inv = inventario()
    cargados = [n for n, ok in inv.items() if ok]
    ausentes = [n for n, ok in inv.items() if not ok]
    print(f"\nResultados cargados ({len(cargados)}):")
    for n in cargados:
        print(f"  - {n}")
    if ausentes:
        print(f"\nNo disponibles ({len(ausentes)}); el asistente lo indicara si se "
              f"le pregunta por ellos:")
        for n in ausentes:
            print(f"  - {n}")

    cliente = obtener_cliente()
    if cliente is None:
        return 1

    print("\nEl asistente responde solo con lo que figura en esos resultados.")
    print("No da consejo medico ni diagnostico.")
    print("Escribe 'salir' para terminar.\n")
    print("Ejemplos de consulta:")
    print("  - ¿Que rendimiento real tiene el clasificador tumor frente a sano?")
    print("  - ¿Que paso con SLC6A4?")
    print("  - ¿Por que tres cohortes no son evaluables?")
    print("  - ¿Que hipotesis no se confirmaron?\n")

    historial = []
    while True:
        try:
            pregunta = input("[Consulta]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            break

        historial.append({"role": "user", "content": pregunta})
        mensajes = [{"role": "system", "content": sistema}] + historial[-MAX_HISTORIAL:]

        try:
            resp = cliente.chat.completions.create(
                messages=mensajes, model=MODELO, temperature=TEMPERATURA,
                max_tokens=900,
            )
            texto = resp.choices[0].message.content
            print(f"\n[Asistente]: {texto}\n")
            historial.append({"role": "assistant", "content": texto})
        except Exception as e:
            print(f"\nError al consultar el modelo: {e}\n")
            historial.pop()

    print("Sesion finalizada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
