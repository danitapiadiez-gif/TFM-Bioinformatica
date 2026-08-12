"""
Punto de entrada de la interfaz web (Streamlit multipage).

Ejecutar desde la raiz del proyecto con:
    streamlit run agentes/paso12_web_chatbot.py

Este fichero es solo un router: configura la pagina, registra las dos vistas
del sitio (landing y dashboard) y las expone en / y en /framework. Todo el
contenido vive en paso12_landing.py y paso12_dashboard.py.

La navegacion lateral automatica de Streamlit se oculta (position="hidden"):
la landing invita a entrar al framework con un boton propio, y el dashboard
puede volver a la landing con st.page_link.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="data.lung · framework transcriptómico",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

landing = st.Page(
    "paso12_landing.py",
    title="Inicio",
    url_path="",
    default=True,
)
dashboard = st.Page(
    "paso12_dashboard.py",
    title="Framework",
    url_path="framework",
)

pg = st.navigation([landing, dashboard], position="hidden")
pg.run()
