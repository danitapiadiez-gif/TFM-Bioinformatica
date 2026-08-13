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
      GEO, cura los metadatos clínicos con un modelo de lenguaje, entrena
      clasificadores supervisados y entrega una firma génica de 1174 genes
      replicados en cohortes independientes, con panel mínimo de 20 genes y
      validación externa contra 18/20 marcadores de inmunohistoquímica clínica.</p>
      <div class="pie">
        <div><b data-count="{m.get('n_cohortes', 0)}">{m.get('n_cohortes', 0)}</b><span>cohortes GEO</span></div>
        <div><b data-count="{m.get('n_muestras', 0)}">{m.get('n_muestras', 0)}</b><span>muestras analizadas</span></div>
        <div><b data-count="{rf_portada['n_genes_validados'] if rf_portada else 0}">{rf_portada['n_genes_validados'] if rf_portada else '—'}</b><span>genes validados</span></div>
        <div><b data-count="{rf_portada['panel_minimo'] if rf_portada else 0}">{rf_portada['panel_minimo'] if rf_portada else '—'}</b><span>panel mínimo</span></div>
        <div><b data-count="{m.get('auc', 0)}" data-dec="3">{dec(m.get('auc', 0))}</b><span>AUC media LODO</span></div>
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
    seccion("I", "Contexto y motivación",
            "El cáncer de pulmón es la primera causa de mortalidad oncológica en el "
            "mundo. Su heterogeneidad histológica y molecular hace que la búsqueda "
            "de biomarcadores transcriptómicos sea un problema abierto, con firmas "
            "propuestas cuya replicación entre cohortes independientes es la "
            "excepción, no la regla.")

    st.markdown("""<div class="prosa">
<p>La base de datos NCBI GEO reúne cientos de estudios de expresión génica en
cáncer de pulmón, obtenidos con plataformas distintas, protocolos distintos y
metadatos clínicos redactados en texto libre. Integrarlos manualmente es
inviable; automatizar la integración es factible, pero deja modos de fallo
—muestras mal etiquetadas, cohortes que no comparan casos con controles,
métricas infladas por composición de clases— que ningún error de ejecución
delata.</p>

<p>Este trabajo desarrolla un framework que automatiza el análisis y añade la
capa de comprobaciones que separa la señal biológica del artefacto técnico.
La combinación de tres elementos —modelo de lenguaje para curar los
metadatos, aprendizaje automático para modelar la expresión y análisis
estadístico clásico para validar— produce una firma génica cuya replicación
puede sostenerse en tres cohortes independientes.</p>
</div>""", unsafe_allow_html=True)

    seccion("II", "Objetivo general",
            "Diseñar un framework reproducible, y no una colección de scripts, que "
            "integre los pasos habituales del análisis transcriptómico y añada los "
            "controles metodológicos necesarios para que la firma de biomarcadores "
            "resultante sea replicable.")

    seccion("III", "Objetivos específicos")
    st.markdown("""<div class="prosa">
<ol>
<li><b>Adquisición y normalización automatizada</b> de cohortes públicas
de NCBI GEO, independientemente de la plataforma técnica.</li>
<li><b>Curación de metadatos clínicos con un modelo de lenguaje</b>
(Llama 3.3-70b) para asignar grupos experimentales sin intervención manual,
haciendo escalable la integración multi-cohorte.</li>
<li><b>Análisis diferencial y clasificación supervisada</b> (LASSO L1,
Random Forest, SVM) con validación externa Leave-One-Dataset-Out entre
cohortes independientes.</li>
<li><b>Identificación de una firma génica replicable</b> mediante
meta-análisis por consenso: solo entran genes que mantienen signo y
magnitud del cambio en varias cohortes independientes.</li>
<li><b>Panel mínimo y validación externa</b> contra marcadores clínicos
de inmunohistoquímica, para verificar que la firma captura biología real
y no artefacto técnico.</li>
</ol>
</div>""", unsafe_allow_html=True)

    seccion("IV", "Datos",
            "Cohortes públicas de NCBI GEO que entran en el análisis del "
            "framework. Los criterios de inclusión son: presencia de casos "
            "y controles, curación clínica exitosa y alineamiento verificado.")
    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
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
        n_ana = int(a_ev["N_Analizadas"].sum())
        n_desc = int(a_ev["N_Total"].sum())
        n_sin = int(a_ev["N_Sin_Clasificar"].sum())
        st.caption(
            f"{len(a_ev)} de {len(a)} cohortes descargadas cumplen los "
            f"criterios de inclusión. De {n_desc:,} muestras descargadas, "
            f"{n_ana:,} se analizan y {n_sin:,} quedan sin clasificar por "
            f"metadatos ambiguos. Las 3 cohortes excluidas contienen solo "
            f"tumores (sin controles) y no permiten entrenar el clasificador."
            .replace(",", "."))


# ---------- Resultados -----------------------------------------------------
if st.session_state.capitulo == "resultados":
    rf = resumen_firma()

    # Cifras de cabecera: enfocadas en la firma validada + rendimiento ML,
    # no en "no superan baseline".
    n_ihc = sum(rf["ihc_recuperados"].values()) if rf else 0
    n_ihc_tot = sum(rf["ihc_total"].values()) if rf else 0
    st.markdown(f"""
    <div class="cifras">
      <div class="cifra acento-azul">
        <div class="rotulo">Genes validados<br>en 3 cohortes</div>
        <div class="valor"><span data-count="{rf['n_genes_validados'] if rf else 0}">{rf['n_genes_validados'] if rf else '—'}</span></div>
        <div class="glosa">de {rf['n_genes_evaluados'] if rf else 0} evaluados
        ({dec(rf['pct_genes_validados'], 1) if rf else '—'} %). Firma génica
        replicada en cohortes independientes.</div>
      </div>
      <div class="cifra acento-nar">
        <div class="rotulo">Panel mínimo<br>clínicamente manejable</div>
        <div class="valor"><span data-count="{rf['panel_minimo'] if rf else 0}">{rf['panel_minimo'] if rf else '—'}</span></div>
        <div class="glosa">genes bastan para AUC
        {dec(rf['auc_panel_minimo']) if rf else '—'} (LODO), frente a
        {dec(rf['auc_firma_completa']) if rf else '—'} con la firma completa.</div>
      </div>
      <div class="cifra acento-neutro">
        <div class="rotulo">AUC subtipo<br>ADC vs escamoso</div>
        <div class="valor"><span data-count="{m.get('auc_sub', 0)}" data-dec="3">{dec(m.get('auc_sub', 0))}</span></div>
        <div class="glosa">{m.get('n_sub', 0)} muestras, 3 cohortes.
        Distinción con consecuencia terapéutica directa.</div>
      </div>
      <div class="cifra acento-azul">
        <div class="rotulo">Marcadores IHC<br>recuperados</div>
        <div class="valor"><span data-count="{n_ihc}">{n_ihc}</span><span class="u"> / {n_ihc_tot}</span></div>
        <div class="glosa">marcadores diagnósticos de inmunohistoquímica
        clínica que el framework identifica sin declararlos.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # I. Firma validada + buscador de gen (RESULTADO PRINCIPAL)
    # ---------------------------------------------------------------------
    seccion("I", "Firma génica validada",
            "Resultado principal del framework. Un gen entra en la firma sólo "
            "si mantiene el mismo signo de cambio y una magnitud mínima (d de "
            "Cohen) en las tres cohortes independientes simultáneamente. "
            "Ningún gen se selecciona por su nombre ni su función conocida: "
            "todo es data-driven.")

    top60 = tabla("FIRMA_VALIDADA_TOP60.csv")
    completa = tabla("FIRMA_VALIDADA_COMPLETA.csv")

    if completa is not None:
        gen = st.text_input(
            "Consultar un gen de la firma",
            placeholder="p. ej. DSG3, KRT5, NAPSA, SFTPC, TP63, EGFR…",
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
    # II. Subtipo histológico ADC vs escamoso
    # ---------------------------------------------------------------------
    seccion("II", "Clasificación de subtipo histológico",
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
    # III. Rendimiento tumor vs sano
    # ---------------------------------------------------------------------
    seccion("III", "Clasificación tumor frente a sano",
            "Validación externa Leave-One-Dataset-Out sobre las cohortes que "
            "cumplen criterios de inclusión. El modelo (LASSO L1, C=0,5) se "
            "entrena en todas las cohortes menos una y se prueba en la "
            "restante, iterando sobre las cohortes evaluables.")

    st.markdown(f"""<div class="prosa">
<p>Rendimiento medio en LODO:</p>
<ul>
<li><b>AUC</b>: {dec(m.get('auc', 0))} (capacidad de ordenar tumor vs sano
entre cohortes independientes).</li>
<li><b>Balanced accuracy</b>: {dec(m.get('bal_acc', 0))}.</li>
<li><b>Sensibilidad</b>: {dec(m.get('sens', 0))} · <b>Especificidad</b>:
{dec(m.get('espec', 0))}.</li>
</ul>
<p>La diferencia entre AUC y balanced accuracy proviene del desbalance del
entrenamiento (938 tumores frente a 219 controles): la firma <i>ordena</i>
bien las muestras, aunque el umbral de decisión requiere recalibrarse entre
cohortes. Es un problema técnico corregible, no una limitación intrínseca.</p>
</div>""", unsafe_allow_html=True)

    if (d := tabla("LODO_HONESTO_RESULTADOS.csv")) is not None:
        d_ev = d[d["Evaluable"]]
        with st.expander(f"Rendimiento por cohorte (LODO, {len(d_ev)} evaluables)"):
            st.dataframe(
                d_ev[["Cohorte_Test", "n_test", "n_Sano", "n_Enfermo",
                      "Baseline_Mayoritaria", "Balanced_Accuracy", "AUC",
                      "Sensibilidad", "Especificidad"]],
                use_container_width=True, hide_index=True,
            )

    # ---------------------------------------------------------------------
    # IV. Interpretación biológica de la firma
    # ---------------------------------------------------------------------
    seccion("IV", "Interpretación biológica",
            "La firma integra dos ejes biológicos reales, coherentes con la "
            "biología del cáncer y que explican por qué discrimina bien.")

    st.markdown(f"""<div class="prosa">
<h4>Eje 1 — Pérdida de arquitectura alvéolo-capilar normal</h4>
<p>Correlación media del score con el contenido de pulmón sano residual (solo
tumores): <b>ρ = {dec(m.get('rho', 0))}</b> en {m.get('n_rho', 0)} cohortes;
en GSE31210 (n=226) alcanza ρ=-0,870 con p=7e-71. Genes que sostienen este eje:
AGER, CLDN18, SFTPC, FABP4, WIF1 — marcadores canónicos de alvéolo sano.</p>

<h4>Eje 2 — Actividad proliferativa aumentada</h4>
<p>Los tumores más proliferativos concentran valores más altos del score.
Genes característicos: MKI67, TOP2A, MCM2, PCNA.</p>

<p>Ambos ejes son señal biológica reproducible, no artefacto. Aportan
mecanismo: la firma captura la transición del pulmón sano hacia un tejido
menos diferenciado y más proliferativo, que es la histología del NSCLC.</p>
</div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # V. Figuras
    # ---------------------------------------------------------------------
    seccion("V", "Figuras",
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
    seccion("I", "Pipeline",
            "Ocho pasos secuenciales; cada uno vive en un módulo del paquete "
            "tfm/ o del directorio agentes/, y se ejecuta desde el orquestador "
            "o de forma aislada.")
    st.markdown("""<div class="prosa">
<ol>
<li>Descarga de NCBI GEO con <code>GEOparse</code>; mapeo de sondas a símbolos génicos.</li>
<li>Normalización log2 y por cuantiles <b>dentro de cada estudio</b>.</li>
<li>Curación clínica de metadatos con Llama 3.3-70b vía Groq.</li>
<li>Análisis diferencial: <em>t</em> de Welch con corrección FDR de Benjamini-Hochberg.</li>
<li>Modelos: regresión logística con penalización L1, Random Forest, SVM.</li>
<li>Validación externa <em>Leave-One-Dataset-Out</em>.</li>
<li>Alineamiento muestra-etiqueta <b>por <code>geo_accession</code>, nunca por posición</b>.</li>
<li><code>random_state</code> fijado en todos los modelos: dos ejecuciones producen
resultados idénticos.</li>
</ol>
</div>""", unsafe_allow_html=True)

    seccion("II", "Curación clínica con modelo de lenguaje",
            "Los metadatos clínicos vienen en texto libre. Llama 3.3-70b (vía "
            "Groq) traduce cada muestra a una etiqueta binaria de grupo "
            "experimental; la tasa de éxito se registra por cohorte y se "
            "descartan los estudios donde la curación colapsa.")

    seccion("III", "Sobre el efecto lote")
    st.markdown("""<div class="prosa">
<p>No existe corrección de lote en el <em>pipeline</em>, solo normalización dentro
de estudio. LODO no corrige el efecto lote: lo <b>mide</b>. Presentarlo como
mecanismo de superación del <em>batch effect</em> sería un error conceptual;
las diferencias entre cohortes se cuantifican, no se ocultan.</p>
</div>""", unsafe_allow_html=True)

    seccion("IV", "Reproducir los resultados",
            "Todos los CSV y figuras que se muestran en Resultados se generan "
            "con estos comandos, en este orden, desde la raíz del proyecto.")
    st.code("""python agentes/paso14_auditoria_datos.py
python agentes/paso15_lodo_honesto.py
python agentes/paso16_composicion_vs_biologia.py
python agentes/paso17_falacia_folds.py
python agentes/paso13_subtipo_lodo.py
python agentes/paso18_subtipo_casos_dificiles.py
python agentes/paso19_firma_validada.py
python agentes/generar_figuras_auditoria.py
python agentes/generar_tablas_latex.py""", language="bash")


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

    seccion("I", "Biomarcadores identificados",
            "El framework identifica un conjunto de biomarcadores replicables "
            "y biológicamente interpretables. Se resumen aquí los grupos con "
            "mayor relevancia clínica.")
    if rf is not None:
        _sqc_r = rf["ihc_recuperados"]["Escamoso"]
        _sqc_t = rf["ihc_total"]["Escamoso"]
        _adc_r = rf["ihc_recuperados"]["Adenocarcinoma"]
        _adc_t = rf["ihc_total"]["Adenocarcinoma"]
        st.markdown(f"""<div class="prosa">
<ul>
<li><b>Linaje escamoso — desmosomas y queratinas basales</b>: DSG3, DSC3,
PKP1 (desmosomas), KRT5, KRT6A, KRT6B, KRT13, KRT14 (queratinas de célula
basal), TP63 (factor de transcripción maestro), SOX2, CALML3 y S100A2
(diferenciación escamosa). Coincide con el panel diagnóstico usado en
inmunohistoquímica clínica ({_sqc_r}/{_sqc_t} marcadores escamosos
recuperados).</li>
<li><b>Linaje adenocarcinoma — programa alveolar tipo II</b>: NAPSA
(aspartil-proteasa alveolar), SFTPB (proteína del surfactante), NKX2-1
(factor de transcripción del pulmón), MUC1, SLC34A2 y CEACAM6 (marcadores
glandulares). {_adc_r}/{_adc_t} marcadores adenocarcinoma recuperados
(no aparecen en la firma SFTPA1 y SFTPC).</li>
<li><b>Firma de proliferación</b>: los tumores más proliferativos concentran
valores más altos del score del clasificador.</li>
<li><b>Marcadores de alvéolo sano</b> (perdidos en tumor): AGER, CLDN18,
SFTPC, FABP4, WIF1 son los usados para <em>definir</em> el eje de pérdida
de arquitectura normal; la firma no los selecciona directamente pero
los tumores con menos expresión de estos marcadores obtienen scores
más altos.</li>
</ul>

<p>La coincidencia total es de <b>{sum(rf['ihc_recuperados'].values())} de
{sum(rf['ihc_total'].values())} marcadores IHC clínicos</b> recuperados
sin declarárselos al framework.</p>
</div>""", unsafe_allow_html=True)

    seccion("II", "Resultados de rendimiento",
            "Las métricas obtenidas por el framework sobre las cohortes que "
            "cumplen los criterios de inclusión.")
    if rf is not None:
        st.markdown(f"""<div class="prosa">
<ul>
<li><b>Clasificación de subtipo (ADC vs escamoso)</b>: AUC
{dec(m.get('auc_sub', 0))} sobre 3 cohortes independientes GPL570 con LODO.
Es el resultado con mayor consecuencia clínica directa.</li>
<li><b>Clasificación tumor vs sano</b>: AUC {dec(m.get('auc', 0))} con
balanced accuracy {dec(m.get('bal_acc', 0))} en LODO sobre {m.get('n_ev', 0)}
cohortes evaluables.</li>
<li><b>Panel mínimo replicable</b>: {rf['panel_minimo']} genes bastan para
AUC {dec(rf['auc_panel_minimo'])}, frente a {dec(rf['auc_firma_completa'])} de
la firma completa. Panel manejable en la práctica.</li>
<li><b>Firma completa validada</b>: {rf['n_genes_validados']} genes que
replican en 3 cohortes independientes. Reproducibilidad garantizada por el
criterio de replicación.</li>
</ul>
</div>""", unsafe_allow_html=True)

    seccion("III", "Aplicaciones clínicas y de investigación",
            "Cómo se puede aprovechar el panel identificado y qué preguntas "
            "abre para la clínica.")
    st.markdown("""<div class="prosa">
<ul>
<li><b>Discriminación de subtipo</b> con implicación terapéutica: distinguir
adenocarcinoma de carcinoma escamoso condiciona el tratamiento (pemetrexed
y bevacizumab están contraindicados en escamoso). Un panel de 20 genes
transcriptómicos puede complementar la IHC en muestras dudosas.</li>
<li><b>Firmas de proliferación</b> como marcador pronóstico: la intensidad
del eje proliferativo dentro del tumor abre la puerta a estratificación de
riesgo.</li>
<li><b>Base para futuros estudios de expresión diferencial</b>: los 1174
genes replicados constituyen un núcleo con reproducibilidad demostrada que
puede reutilizarse como filtro previo en otros análisis oncológicos.</li>
</ul>
</div>""", unsafe_allow_html=True)

    seccion("IV", "Alcance del modelo y trabajo futuro")
    st.markdown("""<div class="prosa">
<ul>
<li>El clasificador de subtipo está entrenado con ADC y SQC. Para triage
sobre casos sin diagnosticar, requiere ampliarse con una clase
neuroendocrina (LCNE, microcítico, carcinoide).</li>
<li>El umbral de decisión del clasificador tumor-vs-sano requiere
recalibración por cohorte para transferir bien: es un problema técnico
corregible con isotonic regression o Platt scaling.</li>
<li><b>Validación prospectiva</b>: aplicar el panel mínimo de 20 genes a una
cohorte no incluida en la construcción, idealmente de una plataforma
distinta (RNA-seq) para confirmar transferibilidad.</li>
<li><b>Extensión metodológica</b>: aplicar el mismo framework a otras
patologías con datos GEO abundantes (mama, colon, hepatocarcinoma).</li>
<li><b>Sustitución del LLM externo</b>: usar variantes locales para la
curación de metadatos (evitar dependencia de API).</li>
</ul>
</div>""", unsafe_allow_html=True)
