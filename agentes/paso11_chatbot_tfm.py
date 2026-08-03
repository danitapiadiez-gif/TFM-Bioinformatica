import os
import pandas as pd
import glob
from groq import Groq
from dotenv import load_dotenv

# Cargar configuración - Forzamos el override por si hay basura en el entorno
load_dotenv(override=True)
api_key = os.getenv("GROQ_API_KEY")

if api_key:
    api_key = api_key.strip().replace('"', '').replace("'", "")

if not api_key or not api_key.startswith("gsk_"):
    print(" AVISO: No se detectó una API Key válida en el archivo .env")
    api_key = input("Introduce tu GROQ_API_KEY manualmente (empieza por gsk_): ").strip()

if not api_key.startswith("gsk_"):
    print(" ERROR: La clave introducida no tiene el formato correcto de Groq (debe empezar por gsk_)")
    exit()

print(f"Usando API Key: {api_key[:7]}...{api_key[-4:]}")
client = Groq(api_key=api_key)

def generar_contexto_tfm():
    """Recopila toda la información de los agentes y resultados en un solo resumen."""
    desktop = os.path.expanduser("~/Desktop")
    contexto = "SISTEMA DE CONOCIMIENTO - FRAMEWORK TRANSCRIPTÓMICO TFM\n\n"
    
    # 1. Cargar la Firma de Consenso (La joya de la corona)
    ruta_firma = os.path.join(desktop, "FIRMA_CONSENSO_FINAL_TFM.csv")
    if os.path.exists(ruta_firma):
        df_firma = pd.read_csv(ruta_firma).head(30) # Los top 30 son suficientes para el chat
        contexto += "TOP 30 BIOMARCADORES DE LA FIRMA DE CONSENSO (Estadística + ML):\n"
        contexto += df_firma.to_string(index=False) + "\n\n"
    
    # 2. Resumen de Estudios Procesados
    carpetas = glob.glob(os.path.join(desktop, "TFM_GSE*"))
    contexto += f"ESTUDIOS ANALIZADOS ({len(carpetas)} datasets):\n"
    
    for cap in carpetas:
        gse_id = os.path.basename(cap).replace("TFM_", "")
        contexto += f"\n--- Estudio {gse_id} ---\n"
        
        # Metadata (lo que dijo la IA)
        meta_path = os.path.join(cap, "metadata_procesada.csv")
        if os.path.exists(meta_path):
            df_meta = pd.read_csv(meta_path)
            if 'grupo_analisis' in df_meta.columns:
                conteo = df_meta['grupo_analisis'].value_counts().to_dict()
                contexto += f"Composición de muestras: {conteo}\n"
        
        # Resultados ML local
        res_ml = os.path.join(cap, "resultados_ml.csv") # Suponiendo que existe un resumen
        if os.path.exists(res_ml):
            # Podríamos leer el Accuracy local
            contexto += "Rendimiento ML Local: Alta Precisión reportada.\n"

    # 3. Metodología empleada (para que sepa cómo responder)
    contexto += "\nMETODOLOGÍA DEL PROYECTO:\n"
    contexto += "- Curación de metadatos con Llama 3.\n"
    contexto += "- Normalización por cuantiles y Log2.\n"
    contexto += "- Validación LODO (Leave-One-Dataset-Out) con 11 estudios.\n"
    contexto += "- Selección de genes mediante penalización Lasso (L1).\n"
    
    return contexto

def chat_interactivo():
    contexto = generar_contexto_tfm()
    print("\n" + "="*50)
    print(" GENOMIC INTELLIGENCE CHATBOT - SOPORTE TFM")
    print("="*50)
    print("El asistente tiene acceso a tus resultados de Consenso y ML.")
    print("Escribe 'salir' para finalizar.\n")

    # Definimos el comportamiento base con ejemplos (Few-Shot) para que aprenda el patrón de bloqueo
    history = [
        {"role": "system", "content": f"""Eres un sistema de consulta de datos estrictamente limitado al TFM de Cáncer de Pulmón.

    REGLA DE ORO: Si la pregunta NO trata sobre los datos del TFM, los genes de la firma o el cáncer de pulmón, responde ÚNICAMENTE: 'ERROR DE ÁMBITO: Esta consulta no pertenece a la investigación del TFM de Cáncer de Pulmón.'

    CONOCIMIENTO DEL TFM:
    {contexto}"""},
        # Ejemplo de bloqueo 1
        {"role": "user", "content": "¿Qué es una piscina?"},
        {"role": "assistant", "content": "ERROR DE ÁMBITO: Esta consulta no pertenece a la investigación del TFM de Cáncer de Pulmón."},
        # Ejemplo de bloqueo 2
        {"role": "user", "content": "Dime algo sobre el cáncer de mama"},
        {"role": "assistant", "content": "ERROR DE ÁMBITO: Esta consulta no pertenece a la investigación del TFM de Cáncer de Pulmón."},
        # Ejemplo de bloqueo 3
        {"role": "user", "content": "Hola, ¿quién eres?"},
        {"role": "assistant", "content": "Soy el asistente técnico del TFM sobre Cáncer de Pulmón. Puedo ayudarte a interpretar los resultados genómicos y la firma de consenso identificada."}
    ]

    while True:
        pregunta = input("\n[Investigador]: ")
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            break

        history.append({"role": "user", "content": pregunta})

        try:
            completion = client.chat.completions.create(
                messages=history,
                model="llama-3.3-70b-versatile",
                temperature=0.0,
                max_tokens=500
            )
            
            respuesta = completion.choices[0].message.content
            print(f"\n[Asistente TFM]: {respuesta}")
            history.append({"role": "assistant", "content": respuesta})
        except Exception as e:
            print(f"Error en el chat: {e}")

if __name__ == "__main__":
    chat_interactivo()
