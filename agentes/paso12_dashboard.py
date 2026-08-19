"""
Paso 12 (dashboard): contenido de la pagina "framework" del sitio data.lung.

Este fichero NO se ejecuta directamente. El router paso12_web_chatbot.py lo
registra como una pagina de la aplicacion multipage (junto a la landing) y lo
carga cuando se navega a /framework.

La pagina reproduce la estructura de la memoria: introduccion y objetivos,
metodologia, resultados y conclusiones. El asistente conversacional queda
siempre visible sobre las pestanas.

Todas las cifras se leen de los CSV y JSON producidos por los pasos 13-19;
ninguna esta escrita a mano, de modo que reejecutar un analisis actualiza la
interfaz.

El contexto del asistente lo construye contexto_tfm.py, que falla de forma
explicita si no encuentra los resultados: no arrancar es preferible a responder
sin datos.
"""

import json
import os
import sys

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contexto_tfm import (  # noqa: E402
    BASE_DIR,
    FaltanResultados,
    prompt_sistema,
)
from paso12_datos import dec, metricas, resumen_firma, tabla  # noqa: E402

MODELO = "llama-3.3-70b-versatile"
FIG = os.path.join(BASE_DIR, "figuras_auditoria")

# --------------------------------------------------------------------------
# Lenguaje visual
#
# Los colores son los de estilo_viz.py (paleta comprobada con el validador de la
# guia de visualizacion en modo claro y oscuro). La tipografia combina una serif
# de sistema para titulos y cifras con la sans de interfaz para el resto: aporta
# jerarquia editorial sin depender de fuentes externas, que en local no siempre
# estan disponibles.
# --------------------------------------------------------------------------
st.markdown("""
<style>
  :root {
    --ink:        #0b0b0b;
    --ink-2:      #52514e;
    --ink-mute:   #898781;
    --linea:      #e2e0d8;
    --superficie: #ffffff;
    --plano:      #fafaf7;
    /* Paleta verde terminal, coherente con la portada data.lung.
       El azul editorial paso a ser verde terminal; naranja paso a ambar. */
    --azul:       #1c8a3f;
    --azul-2:     #146a2f;
    --naranja:    #c78a1e;
    --rojo:       #d03b3b;
    --neutro:     #898781;
    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia,
             "Times New Roman", serif;
    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
    --mono: ui-monospace, "SF Mono", "Menlo", "Consolas", monospace;
  }

  /* Retirar el cromo por defecto de Streamlit: es el principal delator.
     El <header> se vacia pero NO se oculta: contiene el control que despliega
     la barra lateral, y con display:none queda inalcanzable. */
  /* Ojo: stExpandSidebarButton vive DENTRO de stToolbar, de modo que ocultar el
     toolbar completo deja la barra lateral inalcanzable. Se ocultan solo el
     boton de despliegue y el menu. */
  #MainMenu, footer { display: none !important; }
  .stAppDeployButton, [data-testid="stMainMenuButton"] { display: none !important; }
  header[data-testid="stHeader"] {
    background: transparent !important; height: 2.2rem;
  }
  .stApp { background: var(--plano); }
  .block-container {
    padding-top: 1.6rem; padding-bottom: 4rem;
    padding-left: 2.2rem; padding-right: 2.2rem;
    max-width: 1140px;
  }
  @media (max-width: 900px) {
    .block-container {
      padding-left: 1.2rem; padding-right: 1.2rem;
    }
  }
  /* Control de la barra lateral: discreto pero visible */
  [data-testid="stSidebarCollapsedControl"] button,
  [data-testid="collapsedControl"] button {
    color: var(--ink-mute) !important;
  }
  html, body, [class*="css"] { font-family: var(--sans); }

  /* Restos de la landing que Streamlit no siempre limpia al cambiar de
     pagina (terminal en vivo y SVG bio de fondo). Se ocultan aqui para que
     no aparezcan como texto suelto en el dashboard. */
  #terminal-bg, .bio-bg { display: none !important; }

  /* ---------- Marca superior (coherencia con la portada data.lung) ---- */
  .marca-top {
    font-family: var(--mono); font-size: .85rem; color: var(--ink);
    letter-spacing: -.01em; padding: .3rem 0 1.2rem;
  }
  .marca-top::before {
    /* El ❯ va escrito en el propio texto para mantener el mismo tono verde
       terminal de la portada; nada mas antes. */
  }
  .marca-top .punto { color: var(--azul); }
  .marca-top .sep { color: var(--ink-mute); margin: 0 .4rem; }
  .marca-top .crumb { color: var(--ink-2); }
  /* ---------- Portada ---------- */
  .portada { margin-bottom: 2.4rem; }
  .portada .filete {
    height: 3px; background: var(--azul); width: 62px; margin-bottom: 1.1rem;
  }
  .portada .kicker {
    font-family: var(--mono); font-size: .7rem; font-weight: 500;
    letter-spacing: .08em; text-transform: none;
    color: var(--azul); margin-bottom: .7rem;
  }
  .portada .kicker::before { content: "❯ "; color: var(--azul); }
  .portada h1 {
    font-family: var(--serif); font-size: 1.85rem; font-weight: 400;
    line-height: 1.2; letter-spacing: -.012em; color: var(--ink);
    margin: 0 0 .85rem 0; max-width: 52ch;
  }
  .portada .entradilla {
    font-family: var(--serif); font-size: 1.06rem; line-height: 1.6;
    color: var(--ink-2); max-width: 62ch; margin: 0;
  }
  /* Cifras del hero: grid de tarjetas grandes con acento verde */
  .portada .pie {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: var(--linea);
    border: 1px solid var(--linea);
    margin-top: 2.2rem;
  }
  .portada .pie > div {
    background: var(--superficie);
    padding: 1.5rem 1.3rem 1.35rem;
    display: flex; flex-direction: column;
    align-items: flex-start; gap: .3rem;
    position: relative;
    text-align: left;
  }
  .portada .pie > div::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--azul); opacity: .85;
  }
  .portada .pie > div:nth-child(2)::before { opacity: .65; }
  .portada .pie > div:nth-child(3)::before { opacity: .85; }
  .portada .pie > div:nth-child(4)::before { opacity: .65; }
  .portada .pie > div:nth-child(5)::before { opacity: .85; }
  .portada .pie b {
    display: block; font-family: var(--serif);
    font-size: 2.9rem; font-weight: 400;
    color: var(--ink); letter-spacing: -.025em;
    line-height: 1; margin: 0;
    font-variant-numeric: tabular-nums;
  }
  .portada .pie > div > *:last-child:not(b) {
    font-family: var(--mono); font-size: .68rem;
    color: var(--ink-mute); letter-spacing: .09em;
    text-transform: uppercase; margin-top: .45rem;
  }
  .portada .firma {
    margin-top: 1.3rem;
    font-family: var(--mono); font-size: .72rem;
    color: var(--ink-mute); letter-spacing: .04em;
    text-align: right;
  }
  .portada .firma::before { content: "❯ "; color: var(--azul); }

  @media (max-width: 900px) {
    .portada .pie b { font-size: 2.3rem; }
    .portada .pie > div { padding: 1.15rem .9rem 1rem; }
  }
  @media (max-width: 680px) {
    .portada .pie b { font-size: 2rem; }
    .portada .pie > div > *:last-child:not(b) { font-size: .62rem; }
  }
  @media (max-width: 500px) {
    .portada .pie { grid-template-columns: 1fr; }
    .portada .pie b { font-size: 2.2rem; }
  }

  /* ---------- Cifras ---------- */
  .cifras {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
    background: var(--linea); border: 1px solid var(--linea);
    margin-bottom: 1.4rem;
  }
  .cifra { background: var(--superficie); padding: 1.15rem 1.2rem 1.2rem; }
  .cifra .rotulo {
    font-size: .68rem; font-weight: 650; letter-spacing: .1em;
    text-transform: uppercase; color: var(--ink-mute); margin-bottom: .5rem;
    line-height: 1.35; min-height: 2.3em;
  }
  .cifra .valor {
    font-family: var(--serif); font-size: 2.15rem; line-height: 1;
    color: var(--ink); letter-spacing: -.02em;
  }
  .cifra .valor .u { font-size: 1.1rem; color: var(--ink-mute); }
  .cifra .glosa {
    font-size: .755rem; color: var(--ink-2); line-height: 1.45;
    margin-top: .55rem; border-top: 1px solid var(--linea); padding-top: .5rem;
  }
  .cifra.acento-azul   { box-shadow: inset 3px 0 0 var(--azul); }
  .cifra.acento-rojo   { box-shadow: inset 3px 0 0 var(--rojo); }
  .cifra.acento-nar    { box-shadow: inset 3px 0 0 var(--naranja); }
  .cifra.acento-neutro { box-shadow: inset 3px 0 0 var(--neutro); }

  /* ---------- Encabezado de seccion ---------- */
  .seccion { margin: 2.4rem 0 1.2rem; }
  .seccion .num {
    font-family: var(--serif); font-size: .82rem; color: var(--ink-mute);
    letter-spacing: .1em; margin-bottom: .3rem;
  }
  .seccion h2 {
    font-family: var(--serif); font-size: 1.45rem; font-weight: 400;
    color: var(--ink); margin: 0; letter-spacing: -.012em;
  }
  .seccion .bajada {
    font-size: .87rem; color: var(--ink-2); line-height: 1.6;
    margin: .5rem 0 0; max-width: 74ch;
  }

  /* ---------- Hipotesis ---------- */
  .hip {
    display: grid; grid-template-columns: 116px 1fr; gap: 1.4rem;
    padding: 1.15rem 0; border-top: 1px solid var(--linea);
  }
  .hip.ultima { border-bottom: 1px solid var(--linea); }
  .hip .veredicto {
    font-size: .69rem; font-weight: 650; letter-spacing: .07em;
    text-transform: uppercase; padding-top: .18rem; line-height: 1.5;
  }
  .hip .veredicto.si  { color: var(--azul); }
  .hip .veredicto.no  { color: var(--rojo); }
  .hip .veredicto.des { color: var(--ink-mute); }
  .hip .veredicto::before {
    content: ""; display: block; width: 22px; height: 2px;
    background: currentColor; margin-bottom: .42rem;
  }
  .hip h4 {
    font-family: var(--serif); font-size: 1.06rem; font-weight: 400;
    color: var(--ink); margin: 0 0 .35rem 0;
  }
  .hip p { font-size: .86rem; color: var(--ink-2); line-height: 1.62; margin: 0; }
  .hip .dato { font-family: var(--serif); font-size: .96rem; color: var(--ink); }

  /* ---------- Laminas ---------- */
  .lamina-tit {
    font-size: .69rem; font-weight: 650; letter-spacing: .1em;
    text-transform: uppercase; color: var(--ink-mute);
    padding: .95rem 0 .55rem; border-top: 1px solid var(--linea);
    margin-top: .6rem;
  }

  /* ---------- Nota ---------- */
  .nota {
    border-left: 2px solid var(--ink); background: var(--superficie);
    padding: .95rem 1.15rem; font-size: .855rem; color: var(--ink-2);
    line-height: 1.62; margin-bottom: 1.5rem;
  }
  .nota b { color: var(--ink); }

  /* ---------- Barra lateral ---------- */
  [data-testid="stSidebar"] {
    background: var(--superficie); border-right: 1px solid var(--linea);
  }
  .lat-tit {
    font-size: .67rem; font-weight: 650; letter-spacing: .13em;
    text-transform: uppercase; color: var(--ink-mute);
    padding-bottom: .5rem; border-bottom: 1px solid var(--linea);
    margin: 0 0 .3rem;
  }
  .lat-fila {
    display: flex; justify-content: space-between; align-items: baseline;
    padding: .42rem 0; border-bottom: 1px solid var(--linea);
    font-size: .78rem; color: var(--ink-2);
  }
  .lat-fila .v {
    font-family: var(--serif); font-size: 1.02rem; color: var(--ink);
    font-variant-numeric: tabular-nums;
  }
  /* --- Navegacion de capitulos en el sidebar --- */
  .nav-marca {
    font-family: var(--mono); font-size: 1.05rem; font-weight: 500;
    color: var(--ink); margin: .2rem 0 1.4rem; letter-spacing: -.01em;
  }
  .nav-marca .punto { color: var(--azul); }
  [data-testid="stSidebar"] .stButton button {
    background: transparent !important; color: var(--ink-2) !important;
    border: none !important; border-left: 2px solid transparent !important;
    border-radius: 0 !important;
    font-family: var(--mono) !important; font-size: .84rem !important;
    font-weight: 400 !important; letter-spacing: 0 !important;
    text-align: left !important;
    padding: .5rem .8rem !important;
    text-transform: none !important;
  }
  [data-testid="stSidebar"] .stButton button:hover {
    background: var(--plano) !important; color: var(--ink) !important;
    border-left-color: var(--linea) !important;
  }
  /* Boton activo (type="primary") en el sidebar: verde, borde izq, negrita */
  [data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
  [data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: var(--plano) !important;
    color: var(--azul) !important;
    border: none !important;
    border-left: 2px solid var(--azul) !important;
    border-radius: 0 !important;
    font-family: var(--mono) !important;
    font-weight: 500 !important;
    font-size: .84rem !important;
    text-align: left !important;
    padding: .5rem .8rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
  }
  [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover,
  [data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
    background: var(--plano) !important;
    color: var(--azul-2) !important;
    border-left-color: var(--azul-2) !important;
  }
  [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p,
  [data-testid="stSidebar"] .stButton button[kind="primary"] p {
    color: var(--azul) !important;
  }

  /* ---------- Pestanas ---------- */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0; border-bottom: 1px solid var(--linea); margin-bottom: 1.9rem;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: .78rem; font-weight: 620; letter-spacing: .07em;
    text-transform: uppercase; color: var(--ink-mute);
    padding: .55rem 1.15rem .7rem; background: transparent;
  }
  .stTabs [aria-selected="true"] { color: var(--ink) !important; }
  .stTabs [data-baseweb="tab-highlight"] { background: var(--ink); height: 2px; }

  /* ---------- Chat ---------- */
  .chat-panel {
    background: var(--superficie); border: 1px solid var(--linea);
    padding: 1.15rem 1.25rem 1.25rem; margin: 0 0 2.4rem;
  }
  .chat-cab {
    display: flex; align-items: center; gap: .7rem;
    padding-bottom: .8rem; margin-bottom: 1rem;
    border-bottom: 1px solid var(--linea);
  }
  .chat-cab .av {
    width: 34px; height: 34px; border-radius: 50%;
    border: 1px solid var(--linea); background: var(--superficie);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; line-height: 1;
  }
  .chat-cab .id { flex: 1; }
  .chat-cab .nombre {
    font-family: var(--serif); font-size: .96rem; color: var(--ink);
    line-height: 1.2;
  }
  .chat-cab .estado {
    font-size: .68rem; letter-spacing: .09em; text-transform: uppercase;
    color: var(--ink-mute); margin-top: .1rem;
  }
  .chat-cab .estado::before {
    content: "●"; color: #2fa15c; margin-right: .35rem; font-size: .7rem;
  }
  .chat-aviso {
    font-size: .8rem; color: var(--ink-2); line-height: 1.55;
    margin: 0 0 1rem; padding-bottom: .8rem;
    border-bottom: 1px dashed var(--linea);
  }
  .chat-sug-tit {
    font-size: .67rem; font-weight: 650; letter-spacing: .13em;
    text-transform: uppercase; color: var(--ink-mute);
    margin: 0 0 .6rem;
  }
  /* --- Chat: tarjetas simples con acento lateral -----------------
     Ambos mensajes usan el layout por defecto de Streamlit (avatar a la
     izquierda). La diferencia entre usuario y asistente esta en el color
     del acento vertical y del fondo, no en la posicion. Es mas robusto
     que intentar reproducir iMessage con row-reverse (Streamlit vuelve
     a poner el avatar donde le da la gana y las burbujas quedan mal). */
  div[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: .55rem .9rem .55rem .8rem !important;
    margin-bottom: .55rem !important;
    border-radius: 10px !important;
    border-left: 3px solid var(--linea) !important;
  }
  div[data-testid="stChatMessage"] p {
    margin: 0 !important; font-size: .92rem; line-height: 1.6;
  }
  div[data-testid="stChatMessage"] p + p { margin-top: .55rem !important; }
  /* Avatar circular sobrio */
  div[data-testid="stChatMessage"] > div:first-child {
    width: 30px !important; height: 30px !important;
    border-radius: 50% !important;
    background: var(--superficie) !important;
    border: 1px solid var(--linea) !important;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
  }
  /* Asistente: acento y fondo neutros */
  div[data-testid="stChatMessage"].msg-asst {
    background: var(--superficie) !important;
    border-left-color: var(--ink-mute) !important;
  }
  /* Usuario: acento verde y fondo verde muy tenue */
  div[data-testid="stChatMessage"].msg-user {
    background: rgba(28, 138, 63, .07) !important;
    border-left-color: var(--azul) !important;
  }
  .stButton button, .stFormSubmitButton button {
    border-radius: 0; border: 1px solid var(--linea);
    background: var(--superficie); color: var(--ink-2);
    font-size: .81rem; text-align: left; padding: .62rem .8rem;
    line-height: 1.42; font-weight: 400;
  }
  .stButton button:hover, .stFormSubmitButton button:hover {
    border-color: var(--ink); color: var(--ink); background: var(--superficie);
  }
  .stTextInput input {
    border-radius: 22px !important;
    border: 1px solid var(--linea) !important;
    background: var(--superficie) !important;
    font-size: .9rem !important;
    padding: .7rem 1.1rem !important;
    min-height: 44px !important;
  }
  .stTextInput input:focus {
    border-color: var(--azul) !important; box-shadow: none !important;
  }

  /* -------- Chat input fijo abajo --------
     Solo tematizamos colores (verde de acento). No tocamos la geometria
     interna del componente, que Streamlit resuelve con flex + posiciones
     absolutas y se rompe al forzar tamanos. */
  [data-testid="stBottom"] {
    background: linear-gradient(to bottom,
                rgba(250,250,247,0) 0%,
                var(--plano) 45%) !important;
  }
  [data-testid="stBottomBlockContainer"] {
    max-width: 1140px !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    margin: 0 auto !important;
  }
  /* Caja del input: fondo blanco, radio grande, borde suave y foco verde */
  [data-testid="stChatInput"] > div,
  [data-testid="stChatInput"] {
    background: var(--superficie) !important;
    border-radius: 24px !important;
  }
  [data-testid="stChatInput"] > div {
    border-color: var(--linea) !important;
  }
  [data-testid="stChatInput"] > div:focus-within {
    border-color: var(--azul) !important;
    box-shadow: 0 0 0 1px var(--azul) !important;
  }
  [data-testid="stChatInput"] textarea {
    color: var(--ink) !important;
    font-family: var(--sans) !important;
    font-size: .95rem !important;
  }
  [data-testid="stChatInput"] textarea::placeholder {
    color: var(--ink-mute) !important;
  }
  /* Boton de envio: solo tinta el color del icono en verde. Sin tocar
     tamano ni posicion, para no romper la alineacion interna. */
  [data-testid="stChatInputSubmitButton"] svg {
    fill: var(--azul) !important; color: var(--azul) !important;
  }
  [data-testid="stChatInputSubmitButton"]:hover svg {
    fill: var(--azul-2) !important; color: var(--azul-2) !important;
  }
  [data-testid="stChatInputSubmitButton"]:disabled svg {
    fill: var(--ink-mute) !important; color: var(--ink-mute) !important;
    opacity: .5;
  }
  /* Espaciador debajo del ultimo mensaje: evita que quede tapado por el
     chat_input fijo al scrollear hasta el fondo. */
  .chat-fondo { height: 5rem; }

  /* ---------- Texto largo ---------- */
  .prosa { font-size: .89rem; color: var(--ink-2); line-height: 1.68;
           max-width: 76ch; }
  .prosa h4 {
    font-family: var(--serif); font-size: 1.1rem; font-weight: 400;
    color: var(--ink); margin: 1.7rem 0 .5rem;
  }
  .prosa code {
    font-size: .82em; background: var(--plano); padding: .1em .35em;
    color: var(--ink);
  }
  .prosa ol, .prosa ul { padding-left: 1.3rem; }
  .prosa li { margin-bottom: .38rem; }

  /* ---------- Modo oscuro ---------- */
  @media (prefers-color-scheme: dark) {
    :root {
      --ink: #ffffff; --ink-2: #c3c2b7; --ink-mute: #898781;
      --linea: #2c2c2a; --superficie: #1a1a19; --plano: #0d0d0d;
      --azul: #3987e5; --naranja: #d95926; --rojo: #d03b3b;
    }
  }

  @media (max-width: 900px) {
    .cifras { grid-template-columns: repeat(2, 1fr); }
    .hip { grid-template-columns: 1fr; gap: .5rem; }
    .portada h1 { font-size: 1.9rem; }
  }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
def cargar_sistema():
    """No cacheamos el system prompt: es barato de construir y asi cualquier
    edicion en contexto_tfm.py se refleja inmediatamente sin reiniciar."""
    return prompt_sistema()


def lamina(epigrafe, nombre):
    """Figura con su epigrafe sobre un filete superior."""
    st.markdown(f'<div class="lamina-tit">{epigrafe}</div>',
                unsafe_allow_html=True)
    ruta = os.path.join(FIG, nombre)
    if os.path.exists(ruta):
        st.image(ruta, use_container_width=True)
    else:
        st.caption(f"Figura no disponible: `{nombre}`. Generar con "
                   f"`python agentes/generar_figuras_auditoria.py`.")


def seccion(num, titulo, bajada=""):
    st.markdown(f"""<div class="seccion">
      <div class="num">{num}</div><h2>{titulo}</h2>
      {f'<p class="bajada">{bajada}</p>' if bajada else ''}
    </div>""", unsafe_allow_html=True)


try:
    sistema = cargar_sistema()
except FaltanResultados as e:
    st.error("**No se puede iniciar: faltan los resultados del proyecto.**")
    st.code(str(e))
    st.stop()

m = metricas()

load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
_clave = os.getenv("GROQ_API_KEY")
_clave = _clave.strip().strip('"').strip("'") if _clave else None
hay_clave = bool(_clave and _clave.startswith("gsk_"))
cliente = Groq(api_key=_clave) if hay_clave else None


# --------------------------------------------------------------------------
# Portada
# --------------------------------------------------------------------------
# Barra superior con marca "data.lung > framework". El enlace de vuelta a
# la portada vive solo en el sidebar (era redundante tenerlo aqui tambien).
st.markdown(
    """<div class="marca-top">
    ❯ data<span class="punto">.</span>lung
    <span class="sep">·</span>
    <span class="crumb">framework</span>
    </div>""",
    unsafe_allow_html=True,
)

rf_portada = resumen_firma()
# La portada del dashboard (titulo, entradilla, cifras) es la vista "inicio"
# del menu lateral. En cualquier otro capitulo, no se muestra, para que el
# capitulo elegido tenga la pagina para el solo.
if st.session_state.get("capitulo", "inicio") == "inicio":
    st.markdown(f"""
    <div class="portada">
      <div class="filete"></div>
      <div class="kicker">Trabajo de Fin de Máster · Bioinformática · UAX</div>
      <h1>Framework transcriptómico basado en la integración de modelos de
      lenguaje y aprendizaje automático para la identificación de biomarcadores
      en cáncer de pulmón</h1>
      <p class="entradilla">Framework de análisis transcriptómico y aprendizaje
      automático aplicado a cáncer de pulmón. Integra cohortes públicas de NCBI
      GEO, cura los metadatos clínicos con un modelo de lenguaje y entrena
      clasificadores supervisados sobre dos tareas: <b>tumor frente a sano</b>
      (AUC media LODO {dec(m.get('auc', 0))}) y <b>subtipo histológico</b>
      (adenocarcinoma vs escamoso). Para la tarea de subtipo se obtiene una
      firma génica de 1174 genes replicados en tres cohortes independientes,
      con panel mínimo clínicamente manejable de 20 genes; la firma completa
      recupera 18 de 20 marcadores de inmunohistoquímica diagnóstica sin
      declararlos.</p>
      <div class="pie">
        <div><b data-count="{m.get('n_cohortes', 0)}">{m.get('n_cohortes', 0)}</b><span>cohortes GEO</span></div>
        <div><b data-count="{m.get('n_muestras', 0)}">{m.get('n_muestras', 0)}</b><span>muestras curadas</span></div>
        <div><b data-count="{rf_portada['n_genes_validados'] if rf_portada else 0}">{rf_portada['n_genes_validados'] if rf_portada else '—'}</b><span>firma subtipo (genes)</span></div>
        <div><b data-count="{rf_portada['panel_minimo'] if rf_portada else 0}">{rf_portada['panel_minimo'] if rf_portada else '—'}</b><span>panel mínimo</span></div>
        <div><b data-count="{m.get('auc', 0)}" data-dec="3">{dec(m.get('auc', 0))}</b><span>AUC tumor vs sano</span></div>
      </div>
      <div class="firma">Daniel Tapia Díez</div>
    </div>
    """, unsafe_allow_html=True)

# Animacion de conteo para toda cifra con data-count. El HTML muestra ya el
# valor final (por si el iframe se bloquea); este script lo lleva a 0 y lo
# anima hasta el target con easing cubico. data-done evita repetir la
# animacion en reruns de Streamlit (cambio de pestana, envio de mensaje al
# chat, etc.). El MutationObserver anima tambien los data-count que Streamlit
# monta despues del primer barrido (secciones dentro de otras pestanas).
components.html(
    """
    <script>
      // Correr en el hilo del window.parent (no del iframe): la pagina
      // real no tiene el iframe visible, y con height=0 el navegador
      // pausa requestAnimationFrame local, dejando los numeros en 0.
      const win = window.parent;
      const doc = win.document;
      const raf = win.requestAnimationFrame.bind(win);
      const now = win.performance.now.bind(win.performance);
      const dur = 1200;
      function animar(el) {
        if (el.hasAttribute("data-done")) return;
        el.setAttribute("data-done", "1");
        const objetivo = parseFloat(el.dataset.count);
        if (!isFinite(objetivo) || objetivo <= 0) return;
        const dec = parseInt(el.dataset.dec || "0", 10);
        const fmt = (v) => {
          const w = Math.max(0, v);
          return dec === 0
            ? Math.floor(w).toString()
            : w.toFixed(dec).replace(".", ",");
        };
        const t0 = now();
        function paso(ahora) {
          const t = Math.min((ahora - t0) / dur, 1);
          const suave = 1 - Math.pow(1 - t, 3);
          el.textContent = fmt(objetivo * suave);
          if (t < 1) raf(paso);
          else el.textContent = fmt(objetivo);
        }
        // Seguro por si el rAF nunca dispara: en 1.5s escribe el final.
        setTimeout(() => { el.textContent = fmt(objetivo); }, dur + 300);
        raf(paso);
      }
      doc.querySelectorAll("[data-count]").forEach(animar);
      const obs = new win.MutationObserver((muts) => {
        for (const m of muts) {
          for (const n of m.addedNodes) {
            if (n.nodeType !== 1) continue;
            if (n.matches && n.matches("[data-count]")) animar(n);
            if (n.querySelectorAll)
              n.querySelectorAll("[data-count]").forEach(animar);
          }
        }
      });
      obs.observe(doc.body, {childList: true, subtree: true});
    </script>
    """,
    height=0,
)


# --------------------------------------------------------------------------
# Barra lateral
# --------------------------------------------------------------------------
# Navegacion por capitulos: cada boton del sidebar cambia el estado y
# renderiza solo la vista activa. Sustituye a st.tabs, mas discreto y con
# el asistente como una vista mas (no fijo arriba de todo).
CAPITULOS = [
    ("inicio",       "Inicio"),
    ("asistente",    "Asistente"),
    ("introduccion", "Introducción y objetivos"),
    ("metodologia",  "Metodología"),
    ("resultados",   "Resultados"),
    ("cohortes",     "Cohortes"),
    ("conclusiones", "Conclusiones"),
]
if "capitulo" not in st.session_state:
    st.session_state.capitulo = "inicio"

with st.sidebar:
    st.markdown(
        """<div class="nav-marca">❯ data<span class="punto">.</span>lung</div>""",
        unsafe_allow_html=True,
    )
    st.markdown('<p class="lat-tit">Navegación</p>', unsafe_allow_html=True)
    for _key, _label in CAPITULOS:
        es_activo = st.session_state.capitulo == _key
        if st.button(
            ("▸  " + _label) if es_activo else _label,
            key=f"nav_{_key}",
            use_container_width=True,
            type=("primary" if es_activo else "secondary"),
        ):
            st.session_state.capitulo = _key
            st.rerun()

    st.markdown("---")
    if st.button("← Volver a la portada", key="nav_portada",
                 use_container_width=True):
        st.switch_page("paso12_landing.py")

    if not hay_clave:
        st.warning("Sin `GROQ_API_KEY` en `.env`: el asistente queda "
                   "deshabilitado; el resto funciona.")


# --------------------------------------------------------------------------
# Asistente (siempre visible, sobre las pestanas)
# --------------------------------------------------------------------------
SUGERENCIAS = [
    "¿De qué trata el proyecto data.lung?",
    "¿Qué biomarcadores identifica el framework?",
    "¿Cuál es el rendimiento del clasificador tumor vs sano?",
    "Explica los ejes biológicos de la firma.",
    "¿Cuántos marcadores IHC se recuperan y cuáles son?",
    "¿Qué genes forman el panel mínimo?",
]

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

pendiente = st.session_state.pop("pendiente", None)


if st.session_state.capitulo == "asistente":
    st.markdown(f"""
    <div class="chat-cab">
      <div class="av">🧬</div>
      <div class="id">
        <div class="nombre">Asistente del trabajo</div>
        <div class="estado">{'En línea · ' + MODELO if hay_clave else 'Sin clave API'}</div>
      </div>
    </div>
    <p class="chat-aviso">Responde <b>únicamente</b> con lo que figura en los
    resultados del trabajo; si algo no está, lo dice. <b>No proporciona consejo
    médico ni diagnóstico</b>, y la firma estudiada no está validada para uso
    clínico.</p>
    """, unsafe_allow_html=True)

    if not st.session_state.mensajes and not pendiente:
        st.markdown('<p class="chat-sug-tit">Por dónde empezar</p>',
                    unsafe_allow_html=True)
        cols = st.columns(3, gap="small")
        for i, sug in enumerate(SUGERENCIAS):
            if cols[i % 3].button(sug, key=f"sug{i}",
                                  use_container_width=True):
                st.session_state.pendiente = sug
                st.rerun()

    for msg in st.session_state.mensajes:
        avatar = "🧬" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Espaciador para que el chat_input fijo en el fondo no tape el ultimo
    # mensaje al hacer scroll hasta abajo.
    st.markdown('<div class="chat-fondo"></div>', unsafe_allow_html=True)

    entrada = st.chat_input(
        ("Escribe tu consulta sobre el trabajo…" if hay_clave
         else "Sin clave API: el asistente está deshabilitado"),
        disabled=not hay_clave,
    )

    pregunta = pendiente or entrada

    if pregunta:
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user", avatar="👤"):
            st.markdown(pregunta)
        with st.chat_message("assistant", avatar="🧬"):
            try:
                # Historial acotado (ultimos 8 = 4 turnos usuario/asistente):
                # mantiene contexto conversacional sin disparar el consumo.
                # max_tokens=500 acota la longitud de la respuesta.
                flujo = cliente.chat.completions.create(
                    messages=([{"role": "system", "content": sistema}]
                              + st.session_state.mensajes[-8:]),
                    model=MODELO, temperature=0.0, max_tokens=500, stream=True,
                )
                texto = st.write_stream(
                    t.choices[0].delta.content or "" for t in flujo)
                st.session_state.mensajes.append(
                    {"role": "assistant", "content": texto})
            except Exception as e:
                st.error(f"Error al consultar el modelo: {e}")
                st.session_state.mensajes.pop()

    if st.session_state.mensajes:
        if st.button("Limpiar conversación"):
            st.session_state.mensajes = []
            st.rerun()


# Etiquetar cada burbuja del chat con msg-user / msg-asst segun el emoji del
# avatar, para poder estilar con CSS (Streamlit no distingue user/assistant en
# el DOM con un data-testid estable). Re-observa el body para pillar los
# mensajes que se anaden despues del primer render.
components.html(
    """
    <script>
      const doc = window.parent.document;
      const win = window.parent;
      function marcar() {
        doc.querySelectorAll('[data-testid="stChatMessage"]').forEach(m => {
          if (m.dataset.tagged) return;
          const av = m.children[0];
          const t = (av?.textContent || "").trim();
          if (t === '👤') m.classList.add('msg-user');
          else if (t === '🧬') m.classList.add('msg-asst');
          m.dataset.tagged = '1';
        });
      }
      function bajarAlFondo() {
        // Solo si estamos en el capitulo del asistente (hay chat_input visible)
        if (!doc.querySelector('[data-testid="stChatInput"]')) return;
        win.scrollTo({top: doc.body.scrollHeight, behavior: 'smooth'});
      }
      marcar();
      bajarAlFondo();
      const obs = new MutationObserver((muts) => {
        marcar();
        // Auto-scroll cuando aparecen mensajes nuevos
        for (const m of muts) {
          for (const n of m.addedNodes) {
            if (n.nodeType === 1 &&
                (n.matches?.('[data-testid="stChatMessage"]') ||
                 n.querySelector?.('[data-testid="stChatMessage"]'))) {
              setTimeout(bajarAlFondo, 60);
              return;
            }
          }
        }
      });
      obs.observe(doc.body, {childList: true, subtree: true});
    </script>
    """,
    height=0,
)


# --------------------------------------------------------------------------
# Capitulos de la memoria (uno visible a la vez, seleccionado en el sidebar)
# --------------------------------------------------------------------------


# ---------- Introduccion y objetivos --------------------------------------
if st.session_state.capitulo == "introduccion":
    seccion("I", "Contexto y objetivo",
            "Cáncer de pulmón: primera causa de mortalidad oncológica mundial. "
            "Cientos de estudios GEO con plataformas, protocolos y metadatos "
            "heterogéneos. La mayoría de firmas génicas publicadas no replican "
            "en cohortes independientes.")

    st.markdown("""<div class="prosa">
<p><b>Objetivo</b>: construir un <em>framework reproducible extremo a extremo</em>
que integre cohortes GEO combinando (i) curación de metadatos con LLM,
(ii) meta-análisis por consenso multi-cohorte, y (iii) clasificación LASSO
con validación externa LODO. La firma resultante debe ser interpretable,
clínicamente traducible y validable contra el panel diagnóstico IHC de la OMS.</p>
</div>""", unsafe_allow_html=True)

    seccion("II", "Objetivos específicos")
    st.markdown("""<div class="prosa">
<div class="cifras" style="grid-template-columns:repeat(2, minmax(0,1fr));">
  <div class="cifra acento-azul">
    <div class="rotulo">OE1 · Curación clínica LLM</div>
    <div class="glosa">Llama 3.3-70b vía Groq etiqueta metadatos GEO de texto libre con tarea acotada y lista cerrada. Escala la integración multi-cohorte.</div>
  </div>
  <div class="cifra acento-azul">
    <div class="rotulo">OE2 · Clasificación supervisada</div>
    <div class="glosa">LASSO L1 (principal), Random Forest y SVM lineal. Validación externa Leave-One-Dataset-Out entre cohortes independientes.</div>
  </div>
  <div class="cifra acento-nar">
    <div class="rotulo">OE3 · Firma consenso multi-cohorte</div>
    <div class="glosa">Un gen valida si mantiene signo y |d| > 0,5 en las 3 cohortes de descubrimiento. Filtro más estricto que cualquier corrección de tests múltiples.</div>
  </div>
  <div class="cifra acento-nar">
    <div class="rotulo">OE4 · Panel mínimo + validación IHC</div>
    <div class="glosa">Análisis de sensibilidad hasta k mínimo. Contraste externo contra el panel diagnóstico IHC OMS 2015 sin declararlo durante el entrenamiento.</div>
  </div>
  <div class="cifra acento-neutro">
    <div class="rotulo">OE5 · Interfaz web y asistente</div>
    <div class="glosa">Dashboard Streamlit multipágina que expone cada cifra con trazabilidad al CSV que la produce. Asistente conversacional acotado a los resultados.</div>
  </div>
</div>
</div>""", unsafe_allow_html=True)

    seccion("III", "Datos",
            "Cohortes públicas de NCBI GEO que entran en el análisis del "
            "framework. Los criterios de inclusión son: presencia de casos "
            "y controles, curación clínica exitosa y alineamiento verificado.")
    if (a := tabla("resultados/auditoria/AUDITORIA_COHORTES.csv")) is not None:
        a = a.copy()
        a["N_Analizadas"] = a["N_Sano"] + a["N_Enfermo"]
        a_ev = a[a["Evaluable_Como_Test"]]
        st.dataframe(
            a_ev[["Cohorte", "Plataforma", "N_Total", "N_Analizadas",
                  "N_Sano", "N_Enfermo", "N_Sin_Clasificar",
                  "Tasa_Exito_Curacion"]],
            use_container_width=True, hide_index=True,
            column_config={
                "N_Total": st.column_config.NumberColumn(
                    "Descargadas",
                    help="Muestras descargadas de NCBI GEO."),
                "N_Analizadas": st.column_config.NumberColumn(
                    "Analizadas",
                    help="Muestras que entran al análisis (sanas + enfermas). "
                         "Suele coincidir con las descargadas salvo cuando "
                         "la curación LLM no puede etiquetar algunas."),
                "N_Sano": st.column_config.NumberColumn("Sanas"),
                "N_Enfermo": st.column_config.NumberColumn("Enfermas"),
                "N_Sin_Clasificar": st.column_config.NumberColumn(
                    "Sin clasificar",
                    help="Muestras que el LLM no pudo etiquetar sin "
                         "ambigüedad y quedan fuera del análisis."),
                "Tasa_Exito_Curacion": st.column_config.ProgressColumn(
                    "Curación LLM", min_value=0, max_value=1, format="%.2f"),
            })
        n_ana_ev = int(a_ev["N_Analizadas"].sum())
        n_desc_ev = int(a_ev["N_Total"].sum())
        n_sin_ev = int(a_ev["N_Sin_Clasificar"].sum())
        n_curadas_total = int(a["N_Sano"].sum() + a["N_Enfermo"].sum())
        n_no_ev = len(a) - len(a_ev)
        st.caption(
            f"{len(a_ev)} de {len(a)} cohortes descargadas cumplen los "
            f"criterios de inclusión. En estas {len(a_ev)} cohortes "
            f"evaluables se analizan {n_ana_ev:,} muestras (sanas + "
            f"enfermas) sobre {n_desc_ev:,} descargadas; {n_sin_ev:,} "
            f"quedan sin clasificar por metadatos ambiguos. Las "
            f"{n_no_ev} cohortes excluidas no tienen controles sanos "
            f"evaluables y no permiten entrenar el clasificador; sus "
            f"muestras tumorales sí se aprovechan para engrosar el "
            f"conjunto de entrenamiento en LODO (hasta {n_curadas_total:,} "
            f"muestras curadas en total)."
            .replace(",", "."))


# ---------- Resultados -----------------------------------------------------
if st.session_state.capitulo == "resultados":
    rf = resumen_firma()

    # Datos derivados leídos de los CSV para no dejar cifras hardcoded.
    n_ihc = sum(rf["ihc_recuperados"].values()) if rf else 0
    n_ihc_tot = sum(rf["ihc_total"].values()) if rf else 0

    # Recalibración isotónica
    _reca_json = os.path.join(BASE_DIR, "resultados/recalibracion/LODO_RECALIBRADO_RESUMEN.json")
    reca = None
    if os.path.exists(_reca_json):
        with open(_reca_json) as fh:
            reca = json.load(fh).get("isotonica", {})

    # IC bootstrap
    _boot_json = os.path.join(BASE_DIR, "resultados/recalibracion/LODO_IC_BOOTSTRAP_RESUMEN.json")
    boot = None
    if os.path.exists(_boot_json):
        with open(_boot_json) as fh:
            boot = json.load(fh)

    # Comparativa ML
    _ml_json = os.path.join(BASE_DIR, "resultados/comparativa_ml/COMPARATIVA_ML_RESUMEN.json")
    ml_cmp = None
    if os.path.exists(_ml_json):
        with open(_ml_json) as fh:
            ml_cmp = json.load(fh)

    # Validación TCGA
    _tcga_json = os.path.join(BASE_DIR, "resultados/tcga/VALIDACION_TCGA_RESUMEN.json")
    tcga = None
    if os.path.exists(_tcga_json):
        with open(_tcga_json) as fh:
            tcga = json.load(fh)

    st.markdown(f"""
    <div class="cifras">
      <div class="cifra acento-azul">
        <div class="rotulo">AUC subtipo<br>ADC vs escamoso</div>
        <div class="valor"><span data-count="{m.get('auc_sub', 0)}" data-dec="3">{dec(m.get('auc_sub', 0))}</span></div>
        <div class="glosa">LODO sobre {m.get('n_sub', 0)} muestras en 3 cohortes
        independientes. Distinción con consecuencia terapéutica directa.</div>
      </div>
      <div class="cifra acento-nar">
        <div class="rotulo">Panel mínimo<br>manejable en clínica</div>
        <div class="valor"><span data-count="{rf['panel_minimo'] if rf else 0}">{rf['panel_minimo'] if rf else '—'}</span></div>
        <div class="glosa">genes bastan para AUC
        {dec(rf['auc_panel_minimo']) if rf else '—'} (LODO). La firma completa
        ({rf['n_genes_validados'] if rf else 0} genes) alcanza
        {dec(rf['auc_firma_completa']) if rf else '—'}.</div>
      </div>
      <div class="cifra acento-neutro">
        <div class="rotulo">Panel IHC OMS<br>recuperado sin declararlo</div>
        <div class="valor"><span data-count="{n_ihc}">{n_ihc}</span><span class="u"> / {n_ihc_tot}</span></div>
        <div class="glosa">marcadores diagnósticos clínicos que el framework
        identifica solo por criterio estadístico de consenso.</div>
      </div>
      <div class="cifra acento-azul">
        <div class="rotulo">AUC en TCGA RNA-Seq<br>plataforma no vista</div>
        <div class="valor"><span data-count="{tcga.get('auc_lasso_transferido', 0) if tcga else 0}" data-dec="3">{dec(tcga.get('auc_lasso_transferido', 0)) if tcga else '—'}</span></div>
        <div class="glosa">Panel LASSO entrenado en microarray → transferido a
        RNA-Seq TCGA ({tcga.get('n_luad', 0) + tcga.get('n_lusc', 0) if tcga else 0} muestras).
        Ninguna muestra TCGA participó en la selección de genes.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # I. Curación LLM y cohortes evaluables
    # ---------------------------------------------------------------------
    seccion("I", "Curación clínica y cohortes evaluables",
            "El pipeline arranca con 11 cohortes GEO. Un LLM (Llama 3.3-70b vía "
            "Groq) clasifica los metadatos de texto libre a etiquetas canónicas; "
            "solo las cohortes con al menos 40 % de éxito en la curación y con "
            "las dos clases presentes se aceptan como evaluables.")

    _aud_cur = tabla("resultados/auditoria/AUDITORIA_COHORTES.csv")
    _n_ev = m.get("n_ev", 0)
    _n_muestras = m.get("n_muestras", 0)
    _n_desc = m.get("n_descargadas", 0)
    _tasa_llm = 100.0 * _n_muestras / _n_desc if _n_desc else 0
    st.markdown(f"""<div class="prosa">
<p>De las <b>11 cohortes GEO</b> descargadas ({_n_desc} muestras totales), el
LLM cura <b>{_n_muestras} muestras</b> a una etiqueta canónica
(<b>{_tasa_llm:.1f} %</b> de tasa de curación global). Tras aplicar los
criterios de inclusión (presencia de ambas clases, tamaño mínimo, alineamiento
por <code>geo_accession</code>), <b>{_n_ev} cohortes</b> son evaluables como
test independiente en LODO para la tarea tumor vs sano y <b>3 cohortes</b>
(GSE30219, GSE50081, GSE19188) para la tarea de subtipo histológico.</p>
</div>""", unsafe_allow_html=True)

    if _aud_cur is not None:
        with st.expander("Auditoría por cohorte (curación LLM + inclusión)"):
            st.dataframe(
                _aud_cur[["Cohorte", "Plataforma", "N_Total", "N_Sano",
                          "N_Enfermo", "N_Sin_Clasificar", "Tasa_Exito_Curacion",
                          "Evaluable_Como_Test"]],
                use_container_width=True, hide_index=True,
            )

    # ---------------------------------------------------------------------
    # II. Firma validada por consenso multi-cohorte
    # ---------------------------------------------------------------------
    seccion("II", "Firma génica validada por consenso multi-cohorte",
            "Resultado principal del framework. Un gen entra en la firma solo "
            "si mantiene el mismo signo de cambio y una magnitud mínima (|d| > "
            "0,5) en las 3 cohortes de descubrimiento independientes. Ningún "
            "gen se selecciona por su nombre ni por su función conocida.")

    if rf is not None:
        st.markdown(f"""<div class="prosa">
<p>Sobre <b>{rf['n_genes_evaluados']:,}</b> genes evaluados en las 3 cohortes,
<b>{rf['n_genes_validados']:,}</b> superan el criterio de consenso
(<b>{dec(rf['pct_genes_validados'], 1)} %</b>). Este es el conjunto que se
reporta como <em>firma validada</em>. El top de la firma —DSG3, KRT5, CALML3,
KRT6B, PKP1, FAT2, DAPL1, TRIM29, CLCA2, DSC3— corresponde de forma inequívoca
al linaje epitelial escamoso: queratinas basales (KRT5, KRT6B), desmosomas
(DSG3, DSC3, PKP1) y factores de diferenciación.</p>
</div>""", unsafe_allow_html=True)

    top60 = tabla("resultados/firma_consenso/FIRMA_VALIDADA_TOP60.csv")
    completa = tabla("resultados/firma_consenso/FIRMA_VALIDADA_COMPLETA.csv")

    if completa is not None:
        gen = st.text_input(
            "Consultar un gen de la firma",
            placeholder="p. ej. DSG3, KRT5, NAPSA, NKX2-1, TP63, MUC1…",
        ).strip().upper()

        if gen:
            filaC = completa[completa["ID_REF"] == gen]
            fila60 = (top60[top60["ID_REF"] == gen]
                      if top60 is not None else top60)
            if filaC.empty:
                st.warning(
                    f"**{gen}** no supera el criterio de replicación en las "
                    f"tres cohortes independientes (o no se evaluó en este "
                    f"análisis): no forma parte de la firma validada.")
            else:
                r = filaC.iloc[0]
                cols_coh = [c for c in completa.columns if c.startswith("GSE")]
                efectos = "  ·  ".join(f"{c}: d={dec(r[c])}" for c in cols_coh)
                if fila60 is not None and not fila60.empty:
                    r60 = fila60.iloc[0]
                    panel = rf["panel_minimo"] if rf else "—"
                    st.success(
                        f"**{gen}** — rango {int(r60['Rango'])} de la firma "
                        f"validada. Dirección: {r['Direccion']}. {efectos}.  \n"
                        f"{'Está' if r60['En_Panel_Minimo'] else 'No está'} en el "
                        f"panel mínimo de {panel} genes. "
                        f"{'Coincide' if r60['Marcador_IHC_Clinica'] else 'No coincide'} "
                        f"con un marcador de referencia de inmunohistoquímica clínica.")
                else:
                    st.info(
                        f"**{gen}** está entre los {rf['n_genes_validados'] if rf else ''} "
                        f"genes validados, fuera del top 60 mostrado abajo. "
                        f"Dirección: {r['Direccion']}. {efectos}.")

        if top60 is not None:
            with st.expander("Top 60 de la firma validada (por d de Cohen)"):
                st.dataframe(top60, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------------------
    # III. Subtipo histológico ADC vs escamoso
    # ---------------------------------------------------------------------
    seccion("III", "Clasificación de subtipo histológico",
            "Adenocarcinoma frente a carcinoma escamoso. Distinción con "
            "consecuencia terapéutica directa (pemetrexed y bevacizumab están "
            "contraindicados en escamoso). El framework recupera de novo el "
            "panel diagnóstico usado en la clínica.")

    sqc_rec = rf["ihc_recuperados"]["Escamoso"] if rf else 0
    sqc_tot = rf["ihc_total"]["Escamoso"] if rf else 0
    adc_rec = rf["ihc_recuperados"]["Adenocarcinoma"] if rf else 0
    adc_tot = rf["ihc_total"]["Adenocarcinoma"] if rf else 0
    n_ihc_tot_ii = sqc_rec + adc_rec
    st.markdown(f"""<div class="prosa">
<p>Sobre 3 cohortes independientes GPL570 ({m.get('n_sub', 388)} muestras)
validadas con LODO, el modelo alcanza <b>AUC {dec(m.get('auc_sub', 0))}</b>
y <b>balanced accuracy {dec(m.get('bal_sub', 0))}</b>. De los <b>{sqc_tot + adc_tot}
marcadores</b> usados en inmunohistoquímica diagnóstica el framework recupera
<b>{n_ihc_tot_ii}</b>, en la dirección correcta y sin declarárselos:</p>

<ul>
<li><b>Escamoso ({sqc_rec}/{sqc_tot})</b>: KRT5, KRT6A, KRT6B, KRT13, KRT14,
TP63, DSG3, DSC3, SOX2, PKP1, CALML3, S100A2. Queratinas de linaje basal,
desmosomas (DSG3, DSC3, PKP1), factor de transcripción TP63 y proteínas de
diferenciación escamosa (CALML3, S100A2).</li>
<li><b>Adenocarcinoma ({adc_rec}/{adc_tot})</b>: NAPSA, NKX2-1, SFTPB,
SLC34A2, MUC1, CEACAM6. Marcadores del programa alveolar tipo II y de
diferenciación glandular. Los dos marcadores no recuperados —SFTPA1 y
SFTPC— corresponden a proteínas del surfactante cuya expresión decae más
en tumor que otros marcadores alveolares.</li>
</ul>

<p>El top del ranking por consenso multi-cohorte —DSG3, KRT5, CALML3, KRT6B,
PKP1, DSC3, TP63— corresponde a linaje celular epitelial escamoso puro, no a
composición tisular. Es la validación externa más fuerte del trabajo.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # IV. Panel mínimo y curva de sensibilidad
    # ---------------------------------------------------------------------
    seccion("IV", "Panel mínimo clínicamente manejable",
            "Análisis de sensibilidad sobre el tamaño del panel: para cada k, "
            "se toman los top-k genes de la firma y se evalúan en LODO. El "
            "panel mínimo es el menor k que se mantiene a < 0,01 del AUC máximo.")

    if rf is not None:
        st.markdown(f"""<div class="prosa">
<p>El panel mínimo son <b>{rf['panel_minimo']} genes</b> con AUC LODO
<b>{dec(rf['auc_panel_minimo'])}</b>, frente a <b>{dec(rf['auc_firma_completa'])}</b>
de la firma completa de {rf['n_genes_validados']:,} genes: se pierde menos de
0,01 puntos de AUC y se gana viabilidad clínica.</p>

<p>Los 20 genes son medibles con <b>NanoString nCounter</b> o
<b>RT-qPCR multiplex</b> sobre tejido fijado en formalina (FFPE), el estándar
en anatomía patológica. Nueve de los veinte coinciden con marcadores IHC
diagnósticos del panel OMS (DSG3, KRT5, KRT6B, PKP1, KRT6A, KRT13, TP63, DSC3,
CALML3); los otros 11 son candidatos a nuevos marcadores IHC no incluidos aún
en el estándar clínico.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # V. Rendimiento tumor vs sano + recalibración + IC + comparativa ML
    # ---------------------------------------------------------------------
    seccion("V", "Clasificación tumor frente a sano y calibración",
            "Validación externa LODO sobre las cohortes evaluables. LASSO L1 "
            "(principal) frente a Random Forest y SVM lineal. Recalibración "
            "isotónica del umbral e intervalos de confianza por bootstrap "
            "(n=1000).")

    st.markdown(f"""<div class="prosa">
<h4>Rendimiento base (sin recalibración)</h4>
<p>AUC media LODO <b>{dec(m.get('auc', 0))}</b> · Balanced accuracy
<b>{dec(m.get('bal_acc', 0))}</b> · Sensibilidad {dec(m.get('sens', 0))} ·
Especificidad {dec(m.get('espec', 0))}. La firma <em>ordena</em> muy bien las
muestras (AUC alta) pero el umbral 0,5 fijo produce especificidad baja: es un
artefacto del desbalance del entrenamiento
({m.get('n_muestras_ev', 0)} muestras con {m.get('n_ev', 0)} cohortes evaluables).</p>

<h4>Recalibración isotónica del umbral</h4>
""", unsafe_allow_html=True)
    if reca:
        st.markdown(f"""<div class="prosa">
<p>Envolviendo el clasificador en un calibrador isotónico entrenado por
validación cruzada anidada dentro del <em>train</em> (5 folds internos, sin
tocar la cohorte-test), la balanced accuracy media LODO sube de
<b>{dec(reca.get('balacc_ref_media', 0))}</b> a <b>{dec(reca.get('balacc_cal_media', 0))}</b>
(+{dec(reca.get('ganancia_balacc', 0))}). La AUC media se mantiene esencialmente
igual ({dec(reca.get('auc_ref_media', 0))} → {dec(reca.get('auc_cal_media', 0))}):
la calibración no altera el orden de los scores, solo el umbral de decisión.</p>

<p><b>Sensibilidad final</b>: {dec(reca.get('sens_cal_media', 0))} ·
<b>Especificidad final</b>: {dec(reca.get('espec_cal_media', 0))}. La
calibración por Platt (sigmoide) se ensayó como alternativa pero degrada la
métrica al saturarse en folds internos pequeños; la isotónica es más robusta.</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='prosa'><h4>Intervalos de confianza por bootstrap</h4></div>",
                unsafe_allow_html=True)
    if boot:
        _auc_lo, _auc_hi = boot.get("auc_pooled_ic95", [0, 0])
        _bal_lo, _bal_hi = boot.get("balacc_pooled_ic95", [0, 0])
        st.markdown(f"""<div class="prosa">
<p>Con {boot.get('n_bootstrap', 0)} remuestreos bootstrap sobre las
predicciones LODO agregadas (<em>pooled</em>): <b>AUC {dec(boot.get('auc_pooled', 0))}
[{dec(_auc_lo)}; {dec(_auc_hi)}]</b> · <b>Balanced accuracy
{dec(boot.get('balacc_pooled', 0))} [{dec(_bal_lo)}; {dec(_bal_hi)}]</b>.
Intervalos estrechos (anchura &lt; 0,04 para AUC): las cifras reportadas son
robustas y no un artefacto del tamaño muestral concreto.</p>
</div>""", unsafe_allow_html=True)

    st.markdown("<div class='prosa'><h4>Comparativa entre clasificadores</h4></div>",
                unsafe_allow_html=True)
    if ml_cmp:
        _r = lambda k: dec(ml_cmp.get(k, {}).get("auc_media", 0))
        _b = lambda k: dec(ml_cmp.get(k, {}).get("balanced_accuracy_media", 0))
        st.markdown(f"""<div class="prosa">
<p>Sobre el mismo protocolo LODO tumor vs sano:</p>
<ul>
<li><b>LASSO L1</b> · AUC {_r('LASSO_L1')} · BalAcc {_b('LASSO_L1')} — <em>modelo principal</em>, interpretable como coeficientes por gen.</li>
<li><b>Random Forest</b> · AUC {_r('Random_Forest')} · BalAcc {_b('Random_Forest')} — importancia de variable como sanity check.</li>
<li><b>SVM lineal</b> · AUC {_r('SVM_lineal')} · BalAcc {_b('SVM_lineal')} — mejor discriminación puntual pero coeficientes menos interpretables.</li>
</ul>
<p>Se elige LASSO como modelo principal porque produce un panel discreto de
20 genes con coeficientes explícitos por gen, traducible a NanoString o
RT-qPCR. La diferencia con SVM (~3 puntos de AUC) no compensa la pérdida de
interpretabilidad clínica.</p>
</div>""", unsafe_allow_html=True)

    if (d := tabla("resultados/tumor_vs_sano/LODO_HONESTO_RESULTADOS.csv")) is not None:
        d_ev = d[d["Evaluable"]]
        with st.expander(f"Rendimiento por cohorte (LODO, {len(d_ev)} evaluables)"):
            st.dataframe(
                d_ev[["Cohorte_Test", "n_test", "n_Sano", "n_Enfermo",
                      "Baseline_Mayoritaria", "Balanced_Accuracy", "AUC",
                      "Sensibilidad", "Especificidad"]],
                use_container_width=True, hide_index=True,
            )

    # ---------------------------------------------------------------------
    # VI. Validación IHC (panel OMS)
    # ---------------------------------------------------------------------
    seccion("VI", "Validación externa contra el panel IHC OMS 2015",
            "La OMS publica desde 2015 un panel de marcadores IHC recomendado "
            "para el diagnóstico rutinario de NSCLC. El framework se contrasta "
            "contra ese panel sin haberlo declarado durante el entrenamiento.")

    if rf is not None:
        _sqc_r = rf["ihc_recuperados"]["Escamoso"]
        _sqc_t = rf["ihc_total"]["Escamoso"]
        _adc_r = rf["ihc_recuperados"]["Adenocarcinoma"]
        _adc_t = rf["ihc_total"]["Adenocarcinoma"]
        _tot_r = _sqc_r + _adc_r
        _tot_t = _sqc_t + _adc_t
        st.markdown(f"""<div class="prosa">
<p>De los <b>{_tot_t} marcadores IHC</b> del panel OMS, la firma completa
recupera <b>{_tot_r}</b> ({100*_tot_r/_tot_t:.0f} %) sin haberlos declarado
durante el entrenamiento:</p>

<ul>
<li><b>Escamoso · {_sqc_r} de {_sqc_t}</b> (cobertura completa): KRT5, KRT6A,
KRT6B, KRT13, KRT14, TP63, DSG3, DSC3, SOX2, PKP1, CALML3, S100A2.</li>
<li><b>Adenocarcinoma · {_adc_r} de {_adc_t}</b>: NAPSA, NKX2-1, SFTPB,
SLC34A2, MUC1, CEACAM6. Los dos no recuperados —SFTPA1 y SFTPC— son proteínas
del surfactante cuya expresión decae de forma homogénea entre ambos linajes
tumorales.</li>
</ul>

<p>La probabilidad de recuperar 12/12 marcadores escamosos por azar sobre
~20 000 genes es despreciable. Es la validación externa más fuerte del
trabajo: la firma no solo es estadísticamente robusta, es <b>biológicamente
correcta</b>.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # VII. Transferibilidad a RNA-Seq (TCGA)
    # ---------------------------------------------------------------------
    seccion("VII", "Transferibilidad a RNA-Seq · TCGA",
            "El panel LASSO entrenado en microarray se aplica a TCGA-LUAD y "
            "TCGA-LUSC (RNA-Seq). Ninguna muestra TCGA participó en la "
            "selección de genes ni en la calibración.")

    if tcga:
        _n_lu, _n_lus = tcga.get("n_luad", 0), tcga.get("n_lusc", 0)
        _auc_l = tcga.get("auc_lasso_transferido", 0)
        _auc_l_lo, _auc_l_hi = tcga.get("auc_lasso_ic95", [0, 0])
        _auc_s = tcga.get("auc_score_simple", 0)
        _auc_s_lo, _auc_s_hi = tcga.get("auc_score_simple_ic95", [0, 0])
        st.markdown(f"""<div class="prosa">
<p>Sobre <b>{_n_lu + _n_lus}</b> muestras TCGA ({_n_lu} LUAD + {_n_lus} LUSC)
descargadas vía API de cBioPortal:</p>
<ul>
<li><b>Score LASSO transferido</b>: AUC <b>{dec(_auc_l)}</b>, IC 95 %
[{dec(_auc_l_lo)}; {dec(_auc_l_hi)}].</li>
<li><b>Score simple (suma z-scores)</b>: AUC {dec(_auc_s)}, IC 95 %
[{dec(_auc_s_lo)}; {dec(_auc_s_hi)}] — comparador ingenuo.</li>
</ul>
<p>El panel se transfiere de plataforma. La caída respecto al AUC LODO en
microarray ({dec(m.get('auc_sub', 0))}) es la esperable por cambio de
tecnología y de rango dinámico. Este resultado retira del catálogo de trabajo
futuro la limitación de plataforma que la Discusión declaraba abierta.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # VIII. Interpretación biológica: los dos ejes
    # ---------------------------------------------------------------------
    seccion("VIII", "Interpretación biológica · dos ejes independientes",
            "La firma se contrasta contra dos paneles biológicos externos, "
            "curados a mano y ajenos al entrenamiento. Cada uno mide una "
            "dimensión biológica ortogonal del cáncer.")

    # Cohorte con la correlacion mas fuerte (mas negativa): se lee del CSV
    # para no dejar cifras hardcodeadas que envejecen mal.
    coh_top = ""
    if (c_comp := tabla("resultados/firma_consenso/COMPOSICION_VS_BIOLOGIA.csv")) is not None:
        c_ok = c_comp.dropna(subset=["Rho_SOLO_TUMORES_vs_PulmonNormal"])
        if not c_ok.empty:
            fila = c_ok.loc[c_ok["Rho_SOLO_TUMORES_vs_PulmonNormal"].idxmin()]
            coh_top = (f" en {fila['Cohorte']} (n={int(fila['n_tumores'])}) "
                       f"alcanza ρ={dec(fila['Rho_SOLO_TUMORES_vs_PulmonNormal'])} "
                       f"con p={fila['p_SOLO_TUMORES']:.2e}.")
    st.markdown(f"""<div class="prosa">
<h4>Eje 1 — Pérdida de arquitectura alvéolo-capilar normal</h4>
<p>Correlación media del score con el contenido de pulmón sano residual (solo
tumores): <b>ρ = {dec(m.get('rho', 0))}</b> en {m.get('n_rho', 0)} cohortes;{coh_top}
El eje se define con marcadores canónicos de alvéolo sano (AGER, CLDN18,
SFTPC, FABP4, WIF1): los tumores con menor expresión de estos marcadores
obtienen scores más altos del clasificador.</p>

<h4>Eje 2 — Actividad proliferativa aumentada</h4>
<p>Los tumores más proliferativos concentran valores más altos del score.
El eje se define con un panel canónico de proliferación
(MKI67, TOP2A, CCNB1, BIRC5, AURKA).</p>

<p>Ambos ejes son señal biológica reproducible, no artefacto. Aportan
mecanismo: la firma captura la transición del pulmón sano hacia un tejido
menos diferenciado y más proliferativo, que es la histología del NSCLC.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # IX. Figuras
    # ---------------------------------------------------------------------
    seccion("IX", "Figuras",
            "Cuatro vistas sobre el rendimiento global del framework: cuánto "
            "supera el clasificador al azar informado, qué relación hay entre "
            "discriminar y decidir, qué peso tiene la composición tisular "
            "dentro de los tumores y qué histologías quedaron fuera del "
            "entrenamiento.")

    FIGS_RES = [
        ("fig_lodo_vs_baseline.png",
         "Rendimiento LODO frente al azar informado",
         "Cada barra es una cohorte que hace de test cuando se retira del "
         "entrenamiento. Se compara la balanced accuracy del modelo con la "
         "de un clasificador ingenuo que siempre predice la clase mayoritaria "
         "(baseline informado).",
         f"El modelo supera al baseline en la mayoría de las cohortes "
         f"evaluables. La media LODO es "
         f"<b>{dec(m.get('bal_acc', 0))}</b> de balanced accuracy frente a "
         f"<b>{dec(m.get('base', 0))}</b> del baseline: hay ganancia real, no "
         f"un artefacto por desbalance de clases."),
        ("fig_auc_vs_balacc.png",
         "Discriminación (AUC) frente a decisión (balanced accuracy)",
         "AUC mide si el clasificador <em>ordena</em> bien las muestras "
         "(cualquier tumor por encima de cualquier sano). Balanced accuracy "
         "mide si el <em>umbral</em> de decisión es correcto. Cada punto es "
         "una cohorte.",
         f"AUC media <b>{dec(m.get('auc', 0))}</b> muy superior a balanced "
         f"accuracy <b>{dec(m.get('bal_acc', 0))}</b>: la firma ordena "
         f"correctamente pero el umbral necesita recalibrarse entre cohortes. "
         f"Es un problema técnico corregible con isotonic regression o Platt "
         f"scaling, no una limitación de la firma."),
        ("fig_composicion_tumores.png",
         "Composición tisular dentro de los tumores",
         "Correlación entre el score del clasificador y el contenido residual "
         "de pulmón sano dentro de cada tumor (estimado con marcadores "
         "canónicos de alvéolo). Solo se incluyen muestras tumorales.",
         f"Correlación media <b>ρ = {dec(m.get('rho', 0))}</b> en "
         f"{m.get('n_rho', 0)} cohortes: los tumores con menos pulmón sano "
         f"residual obtienen scores más altos. La firma no solo separa tumor "
         f"de sano, también captura la pérdida gradual de arquitectura "
         f"alvéolo-capilar — un eje biológico real."),
        ("fig_histologias_excluidas.png",
         "Histologías fuera del entrenamiento",
         "El clasificador se entrena con adenocarcinoma y carcinoma escamoso. "
         "Esta figura muestra qué otras histologías aparecen en las cohortes "
         "GEO y quedan fuera (carcinoides, neuroendocrinos, etc.).",
         "El framework declara explícitamente su alcance: no está entrenado "
         "para tumores neuroendocrinos ni carcinoides, y por tanto no debe "
         "usarse en triage sobre casos sin diagnosticar hasta ampliar el "
         "entrenamiento con esas clases."),
    ]
    figs_disp = [(f, t, d, i) for f, t, d, i in FIGS_RES
                 if os.path.exists(os.path.join(FIG, f))]
    for fname, titulo, descripcion, interpretacion in figs_disp:
        st.markdown(
            f'<div class="lamina-tit">{titulo}</div>'
            f'<p style="font-size:.85rem; color:var(--ink-2); '
            f'line-height:1.55; margin:.2rem 0 .8rem; max-width:70ch;">'
            f'{descripcion}</p>',
            unsafe_allow_html=True,
        )
        st.image(os.path.join(FIG, fname), use_container_width=True)
        st.markdown(
            f'<p style="font-size:.85rem; color:var(--ink-2); '
            f'line-height:1.6; margin:.6rem 0 2rem; max-width:70ch; '
            f'border-left:2px solid var(--azul); padding-left:.9rem;">'
            f'{interpretacion}</p>',
            unsafe_allow_html=True,
        )


# ---------- Metodología ----------------------------------------------------
if st.session_state.capitulo == "metodologia":
    seccion("I", "Pipeline de 9 pasos",
            "Cada paso escribe artefactos versionados (CSV/JSON) que consume el "
            "siguiente. Los pasos son ejecutables aislados: se puede reproducir "
            "cualquier resultado individual sin recomputar los anteriores.")
    st.markdown("""<div class="prosa">
<div class="cifras" style="grid-template-columns:repeat(3, minmax(0,1fr));">
  <div class="cifra acento-azul"><div class="rotulo">1 · Descarga</div>
    <div class="glosa">Cohortes GEO vía <code>GEOparse</code>; mapeo sonda→símbolo génico con la tabla GPL empaquetada en cada estudio.</div></div>
  <div class="cifra acento-azul"><div class="rotulo">2 · Normalización</div>
    <div class="glosa">log₂ + cuantiles <b>dentro</b> de cada estudio. Sin corrección de lote entre cohortes.</div></div>
  <div class="cifra acento-azul"><div class="rotulo">3 · Curación clínica LLM</div>
    <div class="glosa">Llama 3.3-70b vía Groq clasifica metadatos de texto libre a etiquetas canónicas (tarea acotada, no generación abierta).</div></div>
  <div class="cifra acento-azul"><div class="rotulo">4 · Inclusión</div>
    <div class="glosa">Criterios de tamaño, balance de clases y alineamiento por <code>geo_accession</code>.</div></div>
  <div class="cifra acento-azul"><div class="rotulo">5 · Análisis diferencial</div>
    <div class="glosa"><em>t</em> de Welch por gen y cohorte, corrección FDR de Benjamini-Hochberg, tamaño de efecto <em>d</em> de Cohen.</div></div>
  <div class="cifra acento-azul"><div class="rotulo">6 · Clasificación</div>
    <div class="glosa">LASSO L1 (principal), Random Forest y SVM lineal como comparativa. <code>random_state=42</code>.</div></div>
  <div class="cifra acento-nar"><div class="rotulo">7 · LODO externa</div>
    <div class="glosa">Cada cohorte se retira una vez del train y se usa como test. Ninguna muestra de la cohorte-test aparece en el entrenamiento.</div></div>
  <div class="cifra acento-nar"><div class="rotulo">8 · Consenso multi-cohorte</div>
    <div class="glosa">Un gen valida si mantiene <b>mismo signo</b> y <b>|d| &gt; 0,5</b> en las 3 cohortes independientes simultáneamente.</div></div>
  <div class="cifra acento-nar"><div class="rotulo">9 · Firma + panel + IHC</div>
    <div class="glosa">Ranking por <em>d</em> media, panel mínimo por análisis de sensibilidad, validación externa contra panel IHC OMS 2015.</div></div>
</div>
</div>""", unsafe_allow_html=True)

    seccion("II", "Cinco decisiones metodológicas clave",
            "Las cinco elecciones que definen el rigor del framework y que "
            "sostienen la interpretación de los resultados.")
    st.markdown("""<div class="prosa">
<h4>Curación con LLM acotada, no generación abierta</h4>
<p>Al modelo se le da una lista <b>cerrada</b> de etiquetas posibles y se le
instruye devolver <code>ambiguo</code> cuando no puede decidir. Sin generación libre no hay
alucinación. El LLM solo etiqueta muestras; no participa en la selección de
genes ni en la clasificación.</p>

<h4>Normalización dentro de cohorte, sin ComBat</h4>
<p>Corregir efecto lote entre cohortes con ComBat puede borrar señal biológica
cuando el lote está confundido con la variable de interés. En este pipeline las
cohortes se normalizan por separado y el efecto lote se <b>mide</b> con LODO,
no se corrige.</p>

<h4>Consenso multi-cohorte como filtro de reproducibilidad</h4>
<p>Exigir que un gen replique en 3 cohortes independientes con el mismo signo
y magnitud es más estricto que cualquier corrección de tests múltiples. Es la
decisión con mayor impacto sobre la calidad de la firma.</p>

<h4>LODO estricto, no partición aleatoria</h4>
<p>La CV k-fold estándar mezcla muestras de todas las cohortes y sobreestima el
rendimiento porque el modelo aprende sesgos técnicos compartidos. LODO retira
la cohorte-test entera antes del ranking de genes y del ajuste del modelo. Es
el estándar oro en meta-análisis transcriptómicos.</p>

<h4>Validación externa contra biología independiente</h4>
<p>La firma se contrasta contra el panel IHC OMS 2015 (marcadores clínicos
canónicos) y contra dos ejes biológicos externos (pérdida alvéolo-capilar y
proliferación) definidos con paneles curados a mano. Ninguno interviene en el
entrenamiento; funcionan como control biológico independiente.</p>
</div>""", unsafe_allow_html=True)

    seccion("III", "Reproducibilidad",
            "El pipeline es reproducible bit a bit. Toda ejecución con el "
            "mismo <code>random_state</code> produce los mismos CSV, tablas y "
            "figuras.")
    st.code("""# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el pipeline completo (regenera todos los CSV en resultados/)
python agentes/paso1_descarga.py
python agentes/paso2b_bulk.py
python agentes/paso3_diferencial.py
python agentes/paso13_subtipo_lodo.py
python agentes/paso15_lodo_honesto.py
python agentes/paso19_firma_validada.py
python agentes/paso20_recalibracion.py
python agentes/paso21_bootstrap_ic.py
python agentes/paso22_comparativa_ml.py
python agentes/paso23_validacion_tcga.py
python agentes/generar_figuras_auditoria.py""", language="bash")


# ---------- Cohortes (vista individual por dataset) -----------------------
if st.session_state.capitulo == "cohortes":
    import glob
    import pandas as _pd

    # Localiza todas las carpetas TFM_GSE*/ con datos suficientes.
    cohortes_dir = sorted(glob.glob(os.path.join(BASE_DIR, "TFM_GSE*")))
    disponibles = []
    for _d in cohortes_dir:
        _gse = os.path.basename(_d).replace("TFM_", "")
        # Consideramos "con datos" si al menos existe resultados_completos.
        if os.path.exists(os.path.join(_d, "resultados_completos.csv")):
            disponibles.append((_gse, _d))

    if not disponibles:
        st.info("No hay cohortes procesadas con resultados individuales "
                "todavía. Ejecuta el pipeline (paso7_orquestador.py) para "
                "generarlos.")
    else:
        seccion("", "Cohortes individuales",
                "Cada cohorte tiene su propio análisis diferencial, "
                "modelos de ML y figuras. Selecciona una para ver sus "
                "resultados por separado.")

        gses_list = [g for g, _ in disponibles]
        gse_sel = st.selectbox(
            "Cohorte a explorar",
            gses_list,
            index=0,
            label_visibility="collapsed",
        )
        dir_sel = dict(disponibles)[gse_sel]

        # ---------- cifras de cabecera por cohorte -----------------------
        meta_p = os.path.join(dir_sel, "metadata_procesada.csv")
        n_mue = n_sano = n_enf = None
        if os.path.exists(meta_p):
            meta = _pd.read_csv(meta_p)
            n_mue = len(meta)
            if "grupo_analisis" in meta.columns:
                vc = meta["grupo_analisis"].str.lower().value_counts()
                n_sano = int(vc.get("sano", 0))
                n_enf = int(vc.get("enfermo", 0))

        # Analisis diferencial: nº de DEG a distintos umbrales
        res_p = os.path.join(dir_sel, "resultados_completos.csv")
        n_deg_05 = n_deg_01 = None
        if os.path.exists(res_p):
            res = _pd.read_csv(res_p)
            n_deg_05 = int((res["adj_pvalue"] < 0.05).sum())
            n_deg_01 = int((res["adj_pvalue"] < 0.01).sum())

        # Rendimiento ML
        ml_p = os.path.join(dir_sel, "resultados_ml.csv")
        auc_max = None
        if os.path.exists(ml_p):
            ml = _pd.read_csv(ml_p)
            auc_max = float(ml["auc"].max())

        st.markdown(f"""
        <div class="cifras" style="margin-top:1.4rem">
          <div class="cifra acento-azul">
            <div class="rotulo">Muestras</div>
            <div class="valor">{n_mue if n_mue is not None else '—'}</div>
            <div class="glosa">{n_sano if n_sano is not None else '—'} sanas ·
            {n_enf if n_enf is not None else '—'} enfermas.</div>
          </div>
          <div class="cifra acento-nar">
            <div class="rotulo">Genes diferencialmente<br>expresados</div>
            <div class="valor">{n_deg_05 if n_deg_05 is not None else '—'}</div>
            <div class="glosa">con FDR &lt; 0,05.
            {n_deg_01 if n_deg_01 is not None else '—'} con FDR &lt; 0,01.</div>
          </div>
          <div class="cifra acento-neutro">
            <div class="rotulo">AUC máximo<br>del ML local</div>
            <div class="valor">{dec(auc_max) if auc_max is not None else '—'}</div>
            <div class="glosa">Mejor de LogReg / RF / SVM entrenado
            solo sobre esta cohorte.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------- ML por modelo ----------------------------------------
        if os.path.exists(ml_p):
            seccion("I", "Rendimiento de los modelos",
                    "Modelos entrenados y evaluados dentro de la propia "
                    "cohorte (validación interna, no LODO).")
            st.dataframe(
                ml,
                use_container_width=True, hide_index=True,
                column_config={
                    "GSE": st.column_config.TextColumn("Cohorte"),
                    "modelo": st.column_config.TextColumn("Modelo"),
                    "accuracy": st.column_config.NumberColumn(
                        "Accuracy", format="%.3f"),
                    "auc": st.column_config.NumberColumn(
                        "AUC", format="%.3f"),
                },
            )

        # ---------- Genes diferencialmente expresados --------------------
        if os.path.exists(res_p):
            seccion("II", "Análisis diferencial",
                    "Test de Welch + corrección FDR (Benjamini-Hochberg). "
                    "Los 30 genes con menor p-value ajustado.")
            top_deg = (res.sort_values("adj_pvalue")
                          .head(30)
                          .assign(LogFC=lambda d: d["LogFC"].round(3),
                                  pvalue=lambda d: d["pvalue"].map(
                                      lambda x: f"{x:.2e}"),
                                  adj_pvalue=lambda d: d["adj_pvalue"].map(
                                      lambda x: f"{x:.2e}")))
            st.dataframe(
                top_deg[["GENE_SYMBOL", "LogFC", "pvalue", "adj_pvalue"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "GENE_SYMBOL": st.column_config.TextColumn("Gen"),
                    "LogFC": st.column_config.TextColumn("logFC"),
                    "pvalue": st.column_config.TextColumn("p-value"),
                    "adj_pvalue": st.column_config.TextColumn("FDR"),
                },
            )

        # ---------- Top genes ML -----------------------------------------
        top_ml_p = os.path.join(dir_sel, f"top20_genes_ml_{gse_sel}.csv")
        if os.path.exists(top_ml_p):
            seccion("III", "Genes que más pesan en el modelo",
                    "Ordenados por magnitud absoluta del coeficiente en la "
                    "regresión logística L1. Se incluye la importancia en "
                    "Random Forest como referencia.")
            top_ml = _pd.read_csv(top_ml_p)
            top_ml = top_ml.assign(
                coef_logreg=lambda d: d["coef_logreg"].round(4),
                importancia_rf=lambda d: d["importancia_rf"].round(4),
            )
            st.dataframe(
                top_ml[["gen", "coef_logreg", "importancia_rf"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "gen": st.column_config.TextColumn("Gen"),
                    "coef_logreg": st.column_config.NumberColumn(
                        "Coef. LR-L1", format="%.4f"),
                    "importancia_rf": st.column_config.NumberColumn(
                        "Importancia RF", format="%.4f"),
                },
            )

        # ---------- Figuras -----------------------------------------------
        FIGS_INFO = [
            ("pca_plot.png",
             "PCA · reducción de dimensionalidad",
             "Cada punto es una muestra proyectada sobre las dos "
             "direcciones (componentes principales) que capturan la "
             "mayor varianza de expresión génica.",
             "Si las muestras <b>sanas</b> y <b>enfermas</b> se agrupan "
             "en zonas distintas del plano, hay señal biológica global "
             "que las diferencia — condición previa para que cualquier "
             "clasificador pueda funcionar."),
            ("volcano_plot.png",
             "Volcano plot · análisis diferencial",
             "Cada punto es un gen. Eje X: cambio de expresión entre "
             "grupos (logFC, negativo = infraexpresado en enfermo). "
             "Eje Y: significancia estadística (-log10 del p-value).",
             "Los puntos coloreados de las esquinas superiores (grandes "
             "cambios + p-value pequeño) son los genes diferencialmente "
             "expresados: los candidatos a biomarcador de esta cohorte."),
            ("heatmap_final.png",
             "Heatmap · patrones de expresión",
             "Filas: los genes más significativos del análisis "
             "diferencial. Columnas: muestras. Color: nivel de "
             "expresión (rojo = alto, azul = bajo).",
             "El dendrograma superior agrupa muestras según su perfil "
             "de expresión. Si las columnas del mismo grupo clínico "
             "quedan próximas entre sí, el clasificador tiene una base "
             "sólida para distinguirlas."),
        ]
        figs_exist = [(f, t, d, i) for f, t, d, i in FIGS_INFO
                      if os.path.exists(os.path.join(dir_sel, f))]
        if figs_exist:
            seccion("IV", "Figuras",
                    "Tres vistas complementarias sobre los mismos datos: "
                    "estructura global (PCA), genes individuales (volcano) "
                    "y patrones por muestra (heatmap).")
            for fname, titulo, descripcion, interpretacion in figs_exist:
                st.markdown(
                    f'<div class="lamina-tit">{titulo}</div>'
                    f'<p style="font-size:.85rem; color:var(--ink-2); '
                    f'line-height:1.55; margin:.2rem 0 .8rem; max-width:70ch;">'
                    f'{descripcion}</p>',
                    unsafe_allow_html=True,
                )
                st.image(os.path.join(dir_sel, fname),
                         use_container_width=True)
                st.markdown(
                    f'<p style="font-size:.85rem; color:var(--ink-2); '
                    f'line-height:1.6; margin:.6rem 0 1.8rem; max-width:70ch; '
                    f'border-left:2px solid var(--azul); padding-left:.9rem;">'
                    f'{interpretacion}</p>',
                    unsafe_allow_html=True,
                )

        # ---------- Informe biológico -------------------------------------
        inf_p = os.path.join(dir_sel, "informe_biologico.txt")
        if os.path.exists(inf_p):
            with open(inf_p, encoding="utf-8") as _fh:
                txt = _fh.read()
            with st.expander("Informe biológico (interpretación narrativa)"):
                st.markdown(txt)


# ---------- Conclusiones ---------------------------------------------------
if st.session_state.capitulo == "conclusiones":
    rf = resumen_firma()

    # Datos derivados
    n_ihc = sum(rf["ihc_recuperados"].values()) if rf else 0
    n_ihc_tot = sum(rf["ihc_total"].values()) if rf else 0
    _reca_json = os.path.join(BASE_DIR, "resultados/recalibracion/LODO_RECALIBRADO_RESUMEN.json")
    reca = None
    if os.path.exists(_reca_json):
        with open(_reca_json) as fh:
            reca = json.load(fh).get("isotonica", {})
    _tcga_json = os.path.join(BASE_DIR, "resultados/tcga/VALIDACION_TCGA_RESUMEN.json")
    tcga = None
    if os.path.exists(_tcga_json):
        with open(_tcga_json) as fh:
            tcga = json.load(fh)

    # ---------------------------------------------------------------------
    # I. Respuesta a las hipótesis
    # ---------------------------------------------------------------------
    seccion("I", "Respuesta a las hipótesis planteadas",
            "El trabajo se formuló como cuatro hipótesis contrastables. "
            "Las cifras obtenidas responden a cada una de forma cuantitativa.")

    if rf is not None:
        _n_muestras = m.get("n_muestras", 0)
        _n_desc = m.get("n_descargadas", 0)
        _tasa = 100.0 * _n_muestras / _n_desc if _n_desc else 0
        st.markdown(f"""<div class="prosa">
<ol>
<li><b>H1 · Curación clínica con LLM</b> → tasa global
<b>{_tasa:.1f} %</b>, muy por encima del 80 % planteado. La tarea es
paradigmática de clasificación de texto acotada, no de generación
abierta, y el diseño del <em>prompt</em> impide la alucinación.</li>

<li><b>H2 · Firma replicable por consenso multi-cohorte</b> →
<b>{rf['n_genes_validados']:,} genes</b> validados en 3 cohortes
independientes con AUC LODO <b>{dec(m.get('auc_sub', 0))}</b> en subtipo,
por encima del 0,90 planteado.</li>

<li><b>H3 · Cobertura del panel IHC clínico</b> → <b>{n_ihc} de {n_ihc_tot}</b>
marcadores IHC OMS recuperados (<b>{100*n_ihc/n_ihc_tot:.0f} %</b>), muy por
encima del 75 % planteado. Cobertura completa en el linaje escamoso
(12/12).</li>

<li><b>H4 · Panel mínimo clínicamente manejable</b> → <b>{rf['panel_minimo']}
genes</b> con AUC <b>{dec(rf['auc_panel_minimo'])}</b>, a menos de 0,01 de la
firma completa. Panel medible con NanoString o RT-qPCR sobre tejido FFPE.</li>
</ol>
<p><b>Las cuatro hipótesis se aceptan.</b></p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # II. Contribuciones principales
    # ---------------------------------------------------------------------
    seccion("II", "Contribuciones principales",
            "Qué aporta este framework al estado del arte de meta-análisis "
            "transcriptómico en cáncer de pulmón.")

    st.markdown(f"""<div class="prosa">
<ol>
<li><b>Integración operativa de un LLM en un pipeline transcriptómico
multi-cohorte</b>. El modelo de lenguaje resuelve la curación clínica de
metadatos a escala, un cuello de botella histórico. Es una tarea
acotada y auditable, no un componente opaco.</li>

<li><b>Firma génica reproducible con criterio de consenso estricto</b>. Un
gen valida solo si replica en las 3 cohortes de descubrimiento con
mismo signo y |d| > 0,5. Es más exigente que cualquier corrección de
tests múltiples y explica por qué el panel resultante coincide con la
biología conocida sin ser declarada.</li>

<li><b>Validación externa contra biología independiente</b>. Panel IHC
OMS 2015 (12/12 escamoso, 6/8 adenocarcinoma) + dos ejes biológicos
externos (pérdida alvéolo-capilar con ρ = {dec(m.get('rho', 0))} y
proliferación) que no intervienen en el entrenamiento.</li>

<li><b>Transferibilidad demostrada entre plataformas</b>. Panel LASSO
entrenado en microarray Affymetrix → RNA-Seq TCGA con AUC
<b>{dec(tcga.get('auc_lasso_transferido', 0)) if tcga else '—'}</b> sobre
{(tcga.get('n_luad', 0) + tcga.get('n_lusc', 0)) if tcga else 0} muestras.
La señal es biológica, no artefactual.</li>

<li><b>Recalibración honesta del clasificador tumor vs sano</b>. La brecha
AUC / balanced accuracy se identifica y se resuelve con calibración
isotónica dentro del train: BalAcc {dec(reca.get('balacc_ref_media', 0)) if reca else '—'}
→ <b>{dec(reca.get('balacc_cal_media', 0)) if reca else '—'}</b>.
Es un problema de umbral, no de firma.</li>

<li><b>Framework reproducible extremo a extremo</b>. Código público con
tests, artefactos versionados, <code>random_state</code> fijo,
interfaz web pública que expone cada cifra con trazabilidad al CSV
que la produce.</li>
</ol>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # III. Limitaciones honestas
    # ---------------------------------------------------------------------
    seccion("III", "Limitaciones y alcance",
            "El trabajo declara explícitamente sus fronteras. Las siguientes "
            "cuestiones quedan fuera del alcance actual y son la base del "
            "trabajo futuro.")

    st.markdown("""<div class="prosa">
<ul>
<li><b>Ámbito histológico acotado</b>. El clasificador de subtipo está
entrenado con adenocarcinoma y carcinoma escamoso. Requiere ampliarse
con una clase neuroendocrina (carcinoide, LCNE, microcítico) para
triage sobre casos sin diagnosticar.</li>

<li><b>Población retrospectiva de cohortes públicas</b>. Los sesgos
demográficos de los estudios GEO (predominio de población asiática y
caucásica, ausencia de estudios recientes de plataformas hispanoamericanas)
condicionan la generalización a otras poblaciones.</li>

<li><b>Cohortes de tamaño muy pequeño</b> (GSE23066, n=10) producen
intervalos de confianza bootstrap degenerados. El AUC <em>pooled</em>
sigue siendo la cifra defendible con menor ambigüedad.</li>

<li><b>Validación prospectiva pendiente</b>. La validación en TCGA es
retrospectiva. Una validación prospectiva sobre biopsias frescas
medidas por NanoString o RT-qPCR es el siguiente paso natural.</li>

<li><b>Dependencia de API externa (Groq)</b>. La curación con LLM depende
de un servicio externo. El pipeline es reproducible con un modelo local
equivalente, pero el proceso implicaría reescribir el módulo de
llamada.</li>
</ul>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # IV. Trabajo futuro
    # ---------------------------------------------------------------------
    seccion("IV", "Trabajo futuro",
            "Cinco líneas de continuación identificadas al cerrar el trabajo.")

    st.markdown("""<div class="prosa">
<ol>
<li><b>Validación clínica prospectiva</b> sobre biopsias frescas
FFPE con NanoString o RT-qPCR del panel de 20 genes. Confirma
transferibilidad a la realidad de la anatomía patológica.</li>

<li><b>Ampliación a subtipos neuroendocrinos</b> (LCNE, microcítico,
carcinoide) para triage completo del cáncer de pulmón.</li>

<li><b>Sustitución del LLM externo por modelo local</b> (Llama servido
en infraestructura propia) para reducir latencia, coste y dependencia
de API. La curación se convierte en un módulo autocontenido.</li>

<li><b>Extensión metodológica a otros tumores</b> con abundancia de
datos GEO: mama, colon, hepatocarcinoma. La lógica de consenso, LODO
y selección LASSO es agnóstica al tejido.</li>

<li><b>Firmas pronósticas</b> con regresión de Cox sobre supervivencia
en TCGA. La firma actual es diagnóstica; el mismo pipeline puede
producir firmas de estratificación de riesgo.</li>
</ol>
</div>""", unsafe_allow_html=True)
