"""
Paso 12: interfaz web de consulta de resultados (Streamlit).

Ejecutar con:  streamlit run agentes/paso12_web_chatbot.py

Reescrito respecto a la version anterior, que presentaba cuatro problemas:

  - Leia los resultados de ~/Desktop, no los encontraba, e inyectaba un contexto
    vacio bajo el encabezado "RESULTADOS REALES"; el modelo respondia entonces
    desde su conocimiento general presentandolo como resultados del trabajo.
  - Mostraba en la barra lateral "Precision Media: 84.7%", cifra escrita a mano
    que corresponde a la media de accuracy incluyendo las tres cohortes de una
    sola clase, es decir, al valor inflado.
  - Afirmaba en el prompt de sistema que LODO "garantiza robustez universal",
    exactamente lo que los analisis posteriores mostraron que no ocurre.
  - Se presentaba como "soporte a la decision clinica" e invitaba a introducir
    consultas medicas.

Todas las metricas mostradas se leen ahora de los CSV de resultados.
"""

import os
import sys

import pandas as pd
import streamlit as st
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

st.set_page_config(page_title="Consulta de resultados - TFM", page_icon="🔬",
                   layout="centered")

st.title("Consulta de resultados del TFM")
st.caption("Auditoría de reproducibilidad de firmas transcriptómicas en cáncer "
           "de pulmón. Herramienta de consulta de resultados de investigación.")


# --- Carga de contexto: falla de forma explicita si no hay datos -----------
@st.cache_data(show_spinner="Cargando resultados del proyecto...")
def cargar_sistema():
    return prompt_sistema()


@st.cache_data
def cargar_metricas():
    """Lee las metricas de cabecera de los CSV. Ninguna esta escrita a mano."""
    m = {}
    lodo = os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv")
    if os.path.exists(lodo):
        d = pd.read_csv(lodo)
        ev = d[d["Evaluable"]]
        m["n_cohortes"] = len(d)
        m["n_evaluables"] = len(ev)
        m["bal_acc"] = ev["Balanced_Accuracy"].mean()
        m["auc"] = ev["AUC"].mean()
        m["especificidad"] = ev["Especificidad"].mean()
        m["no_superan"] = int((~ev["Supera_Baseline"]).sum())
    aud = os.path.join(BASE_DIR, "AUDITORIA_COHORTES.csv")
    if os.path.exists(aud):
        a = pd.read_csv(aud)
        m["n_muestras"] = int(a["N_Total"].sum())
        m["sin_clasificar"] = int(a["N_Sin_Clasificar"].sum())
        m["desalineadas"] = int(a["N_Muestras_Desalineadas"].fillna(0).sum())
    sub = os.path.join(BASE_DIR, "SUBTIPO_LODO_RESULTADOS.csv")
    if os.path.exists(sub):
        m["auc_subtipo"] = pd.read_csv(sub)["AUC"].mean()
    return m


try:
    sistema = cargar_sistema()
except FaltanResultados as e:
    st.error("**No se puede iniciar el asistente: faltan los resultados.**")
    st.code(str(e))
    st.info("El asistente no arranca sin datos de forma deliberada: responder "
            "sin ellos produciría respuestas inventadas presentadas como "
            "resultados del trabajo.")
    st.stop()

# Ruta explicita: find_dotenv() depende del directorio de invocacion.
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
clave = os.getenv("GROQ_API_KEY")
if clave:
    clave = clave.strip().strip('"').strip("'")
if not clave or not clave.startswith("gsk_"):
    st.error("No se encontró una `GROQ_API_KEY` válida en el archivo `.env` "
             "del proyecto.")
    st.stop()
cliente = Groq(api_key=clave)


# --- Barra lateral: metricas leidas de los resultados ----------------------
met = cargar_metricas()
with st.sidebar:
    st.header("Resultados del proyecto")
    st.caption("Cifras leídas de los CSV de resultados.")

    if "bal_acc" in met:
        st.metric("Balanced accuracy (tumor vs. sano)",
                  f"{met['bal_acc']:.3f}".replace(".", ","),
                  help=f"Media sobre las {met['n_evaluables']} cohortes "
                       f"evaluables de {met['n_cohortes']}. Las 3 cohortes con "
                       f"una sola clase quedan excluidas: en ellas la accuracy "
                       f"es 1,000 por definición.")
        st.metric("AUC media", f"{met['auc']:.3f}".replace(".", ","),
                  help="La firma ordena bien las muestras entre cohortes, pero "
                       "el umbral de decisión no transfiere.")
        st.metric("Especificidad media",
                  f"{met['especificidad']:.3f}".replace(".", ","),
                  help="Frente a una sensibilidad media de 0,983: el modelo "
                       "clasifica como tumoral casi todo lo que recibe.")
        st.warning(f"{met['no_superan']} de {met['n_evaluables']} cohortes "
                   f"evaluables no superan su propio *baseline*.")

    if "auc_subtipo" in met:
        st.metric("AUC subtipo (control positivo)",
                  f"{met['auc_subtipo']:.3f}".replace(".", ","),
                  help="Adenocarcinoma vs. escamoso. Válido solo sobre tumores "
                       "ya confirmados como una de las dos clases.")

    if "n_muestras" in met:
        st.divider()
        st.caption("**Integridad de los datos**")
        st.caption(f"Muestras totales: {met['n_muestras']}")
        st.caption(f"Sin clasificar por el LLM: {met['sin_clasificar']} "
                   f"({100 * met['sin_clasificar'] / met['n_muestras']:.1f}\\%)")
        st.caption(f"Con etiqueta cruzada (corregido): {met['desalineadas']}")

    st.divider()
    inv = inventario()
    with st.expander(f"Ficheros cargados ({sum(inv.values())}/{len(inv)})"):
        for n, ok in inv.items():
            st.caption(f"{'✓' if ok else '✗'} `{n}`")

    if st.button("Limpiar conversación"):
        st.session_state.pop("mensajes", None)
        st.rerun()

st.info("Este asistente responde únicamente con lo que figura en los resultados "
        "del trabajo. **No proporciona consejo médico ni diagnóstico**, y la "
        "firma estudiada no está validada para uso clínico.", icon="ℹ️")

# --- Conversacion ---------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [{
        "role": "assistant",
        "content": (
            "Puedo consultar los resultados de los pasos 13 a 18 de este "
            "trabajo. Algunas preguntas por las que empezar:\n\n"
            "- ¿Qué rendimiento real tiene el clasificador tumor frente a sano?\n"
            "- ¿Qué pasó con SLC6A4 y los demás genes de la firma original?\n"
            "- ¿Por qué tres cohortes no son evaluables?\n"
            "- ¿Qué hipótesis no se confirmaron?\n"
            "- ¿Qué mide realmente la firma de consenso?"
        ),
    }]

for m in st.session_state.mensajes:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if pregunta := st.chat_input("Consulta sobre los resultados del trabajo..."):
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando los resultados..."):
            try:
                resp = cliente.chat.completions.create(
                    messages=([{"role": "system", "content": sistema}]
                              + st.session_state.mensajes[-12:]),
                    model=MODELO,
                    temperature=0.0,
                    max_tokens=900,
                )
                texto = resp.choices[0].message.content
                st.markdown(texto)
                st.session_state.mensajes.append(
                    {"role": "assistant", "content": texto})
            except Exception as e:
                st.error(f"Error al consultar el modelo: {e}")
                st.session_state.mensajes.pop()
