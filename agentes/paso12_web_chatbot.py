import streamlit as st
import os
import pandas as pd
import glob
from groq import Groq
from dotenv import load_dotenv

# Configuración de la página
st.set_page_config(page_title="Genomic Intelligence AI", page_icon="🧬", layout="centered")

# Estilo personalizado (CSS)
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    .stChatInput { border-top: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# Cargar configuración
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ No se encontró la API Key en el archivo .env")
    st.stop()

client = Groq(api_key=api_key)

def generar_contexto_tfm():
    """Recopila toda la información de los agentes y resultados."""
    desktop = os.path.expanduser("~/Desktop")
    contexto = """DEFINICIÓN OFICIAL DEL TFM:
Este Trabajo de Fin de Máster consiste en el desarrollo de un 'Framework Transcriptómico de Inteligencia Genómica'. 
Sus características clave son:
1. CURACIÓN CON IA: Uso de LLMs (Llama 3) para clasificar automáticamente metadatos clínicos de NCBI GEO.
2. META-ANÁLISIS: Síntesis estadística de múltiples estudios independientes para buscar consistencia direccional.
3. VALIDACIÓN LODO (Leave-One-Dataset-Out): Estrategia de validación cruzada donde se entrena con n-1 estudios y se valida en un ESTUDIO COMPLETO independiente (no solo una muestra). Esto garantiza robustez universal.
4. REGULARIZACIÓN LASSO: Selección de los genes más predictivos eliminando el ruido.
5. OBJETIVO: Identificar una firma molecular de consenso capaz de diagnosticar cáncer de pulmón en cualquier cohorte independiente.

"""
    contexto += "SISTEMA DE CONOCIMIENTO - RESULTADOS REALES\n\n"
    
    ruta_firma = os.path.join(desktop, "FIRMA_CONSENSO_FINAL_TFM.csv")
    if os.path.exists(ruta_firma):
        df_firma = pd.read_csv(ruta_firma).head(30)
        contexto += "TOP 30 BIOMARCADORES:\n" + df_firma.to_string(index=False) + "\n\n"
    
    carpetas = glob.glob(os.path.join(desktop, "TFM_GSE*"))
    contexto += f"DATOS: Analizados {len(carpetas)} estudios de cáncer de pulmón.\n"
    contexto += "MÉTODO: Validación LODO y regularización Lasso.\n"
    return contexto

# Interfaz de usuario
st.title("🧬 Genomic Intelligence Assistant")
st.caption("Soporte a la decisión clínica basado en el TFM de Cáncer de Pulmón")

if "messages" not in st.session_state:
    contexto = generar_contexto_tfm()
    st.session_state.messages = [
        {"role": "system", "content": f"Eres un asistente científico de un TFM. Responde SOLO sobre Cáncer de Pulmón basándote en esto: {contexto}. Si preguntan otra cosa, di 'ERROR DE ÁMBITO'."},
        {"role": "assistant", "content": "Hola. Soy tu asistente genómico. ¿En qué puedo ayudarte hoy respecto a la firma molecular de pulmón?"}
    ]

# Mostrar historial
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Entrada de usuario
if prompt := st.chat_input("Escribe tu consulta médica..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizando firmas genómicas..."):
            try:
                completion = client.chat.completions.create(
                    messages=st.session_state.messages,
                    model="llama-3.1-8b-instant",  # Modelo más rápido y con mayores límites
                    temperature=0.0
                )
                response = completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")

# Sidebar con estadísticas
with st.sidebar:
    st.header("📊 Estadísticas del Proyecto")
    st.info("Estudios: 11")
    st.success("Precisión Media: 84.7%")
    st.warning("Biomarcadores: 20")
    if st.button("Limpiar Chat"):
        st.session_state.messages = []
        st.rerun()
