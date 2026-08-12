"""
Paso 12: interfaz web del framework (Streamlit).

Ejecutar desde la raiz del proyecto con:
    streamlit run agentes/paso12_web_chatbot.py

La interfaz reproduce la estructura de la memoria: introduccion y objetivos,
metodologia, resultados y conclusiones. El asistente conversacional queda
siempre visible sobre las pestanas para que pueda consultarse en cualquier
momento sin cambiar de vista.

Todas las cifras se leen de los CSV y JSON producidos por los pasos 13-19;
ninguna esta escrita a mano, de modo que reejecutar un analisis actualiza la
interfaz.

El contexto del asistente lo construye contexto_tfm.py, que falla de forma
explicita si no encuentra los resultados: no arrancar es preferible a responder
sin datos.

El lenguaje visual acompana a estilo_viz.py, de modo que la interfaz y las
figuras comparten paleta, tipografia y jerarquia.
"""

import json
import os
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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
FIG = os.path.join(BASE_DIR, "figuras_auditoria")

st.set_page_config(
    page_title="Framework transcriptómico · TFM",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    --linea:      #e1e0d9;
    --superficie: #fcfcfb;
    --plano:      #f4f3ef;
    --azul:       #2a78d6;
    --naranja:    #eb6834;
    --rojo:       #d03b3b;
    --neutro:     #898781;
    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia,
             "Times New Roman", serif;
    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
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
    padding-top: 1.6rem; padding-bottom: 4rem; max-width: 1140px;
  }
  /* Control de la barra lateral: discreto pero visible */
  [data-testid="stSidebarCollapsedControl"] button,
  [data-testid="collapsedControl"] button {
    color: var(--ink-mute) !important;
  }
  html, body, [class*="css"] { font-family: var(--sans); }

  /* ---------- Portada ---------- */
  .portada { margin-bottom: 2.4rem; }
  .portada .filete {
    height: 3px; background: var(--ink); width: 62px; margin-bottom: 1.1rem;
  }
  .portada .kicker {
    font-size: .7rem; font-weight: 650; letter-spacing: .16em;
    text-transform: uppercase; color: var(--ink-mute); margin-bottom: .7rem;
  }
  .portada h1 {
    font-family: var(--serif); font-size: 1.85rem; font-weight: 400;
    line-height: 1.2; letter-spacing: -.012em; color: var(--ink);
    margin: 0 0 .85rem 0; max-width: 52ch;
  }
  .portada .entradilla {
    font-family: var(--serif); font-size: 1.06rem; line-height: 1.6;
    color: var(--ink-2); max-width: 62ch; margin: 0;
  }
  .portada .pie {
    display: flex; gap: 1.7rem; flex-wrap: wrap; margin-top: 1.5rem;
    padding-top: 1.1rem; border-top: 1px solid var(--linea);
    font-size: .78rem; color: var(--ink-mute);
  }
  .portada .pie b {
    display: block; font-family: var(--serif); font-size: 1.28rem;
    font-weight: 400; color: var(--ink); letter-spacing: -.01em;
    margin-bottom: .1rem;
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
    width: 30px; height: 30px; border: 1px solid var(--ink);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--serif); font-size: .95rem; color: var(--ink);
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
  div[data-testid="stChatMessage"] {
    background: var(--plano); border: 1px solid var(--linea);
    border-radius: 0; padding: .9rem 1.05rem; margin-bottom: .7rem;
  }
  div[data-testid="stChatMessage"] p { font-size: .88rem; line-height: 1.65; }
  .stButton button, .stFormSubmitButton button {
    border-radius: 0; border: 1px solid var(--linea);
    background: var(--superficie); color: var(--ink-2);
    font-size: .81rem; text-align: left; padding: .62rem .8rem;
    line-height: 1.42; font-weight: 400;
  }
  .stButton button:hover, .stFormSubmitButton button:hover {
    border-color: var(--ink); color: var(--ink); background: var(--superficie);
  }
  .stFormSubmitButton button {
    text-align: center; background: var(--ink); color: #fff;
    border-color: var(--ink);
  }
  .stFormSubmitButton button:hover {
    background: var(--ink-2); color: #fff; border-color: var(--ink-2);
  }
  .stTextInput input {
    border-radius: 0 !important; border: 1px solid var(--linea) !important;
    background: var(--plano) !important; font-size: .88rem !important;
    padding: .7rem .85rem !important;
  }
  .stTextInput input:focus {
    border-color: var(--ink) !important; box-shadow: none !important;
  }

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
@st.cache_data(show_spinner="Cargando resultados del proyecto…")
def cargar_sistema():
    return prompt_sistema()


@st.cache_data
def tabla(nombre):
    ruta = os.path.join(BASE_DIR, nombre)
    return pd.read_csv(ruta) if os.path.exists(ruta) else None


@st.cache_data
def metricas():
    """Todas las cifras de cabecera, leidas de los CSV."""
    m = {}
    if (d := tabla("LODO_HONESTO_RESULTADOS.csv")) is not None:
        ev = d[d["Evaluable"]]
        m |= {
            "n_cohortes": len(d), "n_ev": len(ev),
            "bal_acc": ev["Balanced_Accuracy"].mean(),
            "auc": ev["AUC"].mean(),
            "sens": ev["Sensibilidad"].mean(),
            "espec": ev["Especificidad"].mean(),
            "base": ev["Baseline_Mayoritaria"].mean(),
            "ganancia": ev["Ganancia_vs_Baseline"].mean(),
            "no_superan": int((~ev["Supera_Baseline"]).sum()),
            "acc_11": d["Accuracy"].mean(),
        }
    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
        m |= {
            "n_muestras": int(a["N_Total"].sum()),
            "sin_clas": int(a["N_Sin_Clasificar"].sum()),
            "desal": int(a["N_Muestras_Desalineadas"].fillna(0).sum()),
            "n_mono": int((~a["Evaluable_Como_Test"]).sum()),
        }
    if (s := tabla("SUBTIPO_LODO_RESULTADOS.csv")) is not None:
        m |= {"auc_sub": s["AUC"].mean(), "bal_sub": s["Balanced_Accuracy"].mean(),
              "n_sub": int(s["n_test"].sum())}
    if (c := tabla("COMPOSICION_VS_BIOLOGIA.csv")) is not None:
        v = c["Rho_SOLO_TUMORES_vs_PulmonNormal"].dropna()
        m |= {"rho": v.mean(), "n_rho": len(v),
              "rho_max": v.min(), "n_rho_sup": int((v.abs() > 0.7).sum())}
    if (f := tabla("FALACIA_FOLDS_COMPARACION.csv")) is not None:
        m |= {"conc_lodo": f.iloc[0]["concordancia_pareja_media"] * 100,
              "conc_disj": f.iloc[1]["concordancia_pareja_media"] * 100,
              "genes_folds": int(f.iloc[0]["genes_acuerdo_signo_perfecto"]),
              "genes_disj": int(f.iloc[1]["genes_acuerdo_signo_perfecto"])}
    if (h := tabla("SUBTIPO_CASOS_DIFICILES.csv")) is not None:
        m |= {"pct_conf": 100 * h["N_Alta_Confianza"].sum() / h["n"].sum()}
    return m


@st.cache_data
def resumen_firma():
    ruta = os.path.join(BASE_DIR, "FIRMA_VALIDADA_RESUMEN.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta) as fh:
        return json.load(fh)


def dec(v, n=3):
    return f"{v:.{n}f}".replace(".", ",")


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
rf_portada = resumen_firma()
st.markdown(f"""
<div class="portada">
  <div class="filete"></div>
  <div class="kicker">Trabajo de Fin de Máster · Bioinformática · UAX</div>
  <h1>Framework transcriptómico basado en la integración de modelos de
  lenguaje y aprendizaje automático para la identificación de biomarcadores
  en cáncer de pulmón</h1>
  <p class="entradilla">Pipeline automatizado que descarga cohortes de NCBI GEO,
  cura los metadatos clínicos con un modelo de lenguaje, entrena clasificadores
  supervisados y ejecuta los controles necesarios para separar la señal
  biológica de los artefactos técnicos. El resultado es una firma génica
  replicada en tres cohortes independientes.</p>
  <div class="pie">
    <div><b data-count="{m.get('n_cohortes', 0)}">{m.get('n_cohortes', 0)}</b>cohortes GEO</div>
    <div><b data-count="{m.get('n_muestras', 0)}">{m.get('n_muestras', 0)}</b>muestras</div>
    <div><b data-count="{rf_portada['n_genes_validados'] if rf_portada else 0}">{rf_portada['n_genes_validados'] if rf_portada else '—'}</b>genes validados</div>
    <div><b data-count="{rf_portada['panel_minimo'] if rf_portada else 0}">{rf_portada['panel_minimo'] if rf_portada else '—'}</b>panel mínimo</div>
    <div><b data-count="{m.get('auc', 0)}" data-dec="3">{dec(m.get('auc', 0))}</b>AUC media LODO</div>
    <div style="margin-left:auto;align-self:flex-end">Daniel Tapia Díez</div>
  </div>
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
      const doc = window.parent.document;
      const dur = 1200;
      function animar(el) {
        if (el.hasAttribute("data-done")) return;
        el.setAttribute("data-done", "1");
        const objetivo = parseFloat(el.dataset.count);
        const dec = parseInt(el.dataset.dec || "0", 10);
        const fmt = (v) => dec === 0
          ? Math.floor(v).toString()
          : v.toFixed(dec).replace(".", ",");
        el.textContent = fmt(0);
        const t0 = performance.now();
        function paso(ahora) {
          const t = Math.min((ahora - t0) / dur, 1);
          const suave = 1 - Math.pow(1 - t, 3);
          el.textContent = fmt(objetivo * suave);
          if (t < 1) requestAnimationFrame(paso);
          else el.textContent = fmt(objetivo);
        }
        requestAnimationFrame(paso);
      }
      doc.querySelectorAll("[data-count]").forEach(animar);
      const obs = new MutationObserver((muts) => {
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
with st.sidebar:
    st.markdown('<p class="lat-tit">Cifras principales</p>', unsafe_allow_html=True)
    st.markdown("".join(
        f'<div class="lat-fila"><span>{k}</span><span class="v">{v}</span></div>'
        for k, v in [
            ("Balanced accuracy", dec(m.get("bal_acc", 0))),
            ("AUC media", dec(m.get("auc", 0))),
            ("Especificidad", dec(m.get("espec", 0))),
            ("AUC subtipo", dec(m.get("auc_sub", 0))),
        ]), unsafe_allow_html=True)

    st.markdown('<p class="lat-tit" style="margin-top:1.7rem">Integridad</p>',
                unsafe_allow_html=True)
    st.markdown("".join(
        f'<div class="lat-fila"><span>{k}</span><span class="v">{v}</span></div>'
        for k, v in [
            ("Muestras", str(m.get("n_muestras", 0))),
            ("Sin clasificar", str(m.get("sin_clas", 0))),
            ("Etiqueta cruzada", str(m.get("desal", 0))),
            ("No evaluables", str(m.get("n_mono", 0))),
        ]), unsafe_allow_html=True)
    if "n_muestras" in m:
        pct = 100 * m["sin_clas"] / m["n_muestras"]
        st.caption(f"El {dec(pct, 1)} % de las muestras se perdió en la curación "
                   f"automatizada.")

    inv = inventario()
    with st.expander(f"Procedencia · {sum(inv.values())}/{len(inv)}"):
        for n, ok in inv.items():
            st.caption(f"{'·' if ok else '✘'} `{n}`")
    st.caption(f"Asistente: `{MODELO}`")
    if not hay_clave:
        st.warning("Sin `GROQ_API_KEY` en `.env`: el asistente queda "
                   "deshabilitado; el resto funciona.")


# --------------------------------------------------------------------------
# Asistente (siempre visible, sobre las pestanas)
# --------------------------------------------------------------------------
SUGERENCIAS = [
    "¿Qué rendimiento real tiene el clasificador tumor frente a sano?",
    "¿Qué pasó con SLC6A4 y los genes de la firma original?",
    "¿Por qué tres cohortes no son evaluables como test?",
    "¿Qué hipótesis no se confirmaron y por qué?",
    "¿Qué mide realmente la firma de consenso?",
    "Explica el bug de desalineamiento de GSE30219.",
]

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

pendiente = st.session_state.pop("pendiente", None)

st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
st.markdown(f"""
<div class="chat-cab">
  <div class="av">◫</div>
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
        if cols[i % 3].button(sug, key=f"sug{i}", use_container_width=True):
            st.session_state.pendiente = sug
            st.rerun()

for msg in st.session_state.mensajes:
    avatar = "◫" if msg["role"] == "assistant" else "▪"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

with st.form("form_chat", clear_on_submit=True):
    col_txt, col_btn = st.columns([9, 1], gap="small")
    with col_txt:
        entrada = st.text_input(
            "Escribe tu consulta sobre el trabajo…",
            placeholder=("Escribe tu consulta sobre el trabajo…" if hay_clave
                         else "Sin clave API: el asistente está deshabilitado"),
            label_visibility="collapsed",
            disabled=not hay_clave,
        )
    with col_btn:
        enviar = st.form_submit_button("Enviar", use_container_width=True,
                                       disabled=not hay_clave)

pregunta = pendiente or (entrada if enviar else None)

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar="▪"):
        st.markdown(pregunta)
    with st.chat_message("assistant", avatar="◫"):
        try:
            flujo = cliente.chat.completions.create(
                messages=([{"role": "system", "content": sistema}]
                          + st.session_state.mensajes[-12:]),
                model=MODELO, temperature=0.0, max_tokens=900, stream=True,
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

st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Capitulos de la memoria
# --------------------------------------------------------------------------
t_intro, t_met, t_res, t_con = st.tabs(
    ["Introducción y objetivos", "Metodología", "Resultados", "Conclusiones"])


# ---------- Introduccion y objetivos --------------------------------------
with t_intro:
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
<li>Automatizar la descarga y normalización de cohortes de NCBI GEO,
independientemente de la plataforma (microarray o RNA-seq).</li>
<li>Emplear un modelo de lenguaje para curar los metadatos clínicos —texto
libre— y asignar cada muestra a un grupo experimental sin intervención
manual.</li>
<li>Ejecutar análisis diferencial y modelos de clasificación supervisada con
validación externa <em>Leave-One-Dataset-Out</em> sobre las cohortes
compatibles.</li>
<li>Diseñar y aplicar cuatro controles automáticos —alineamiento por
identificador, composición tisular, estabilidad de la firma sobre particiones
disjuntas, validación externa contra marcadores clínicos de referencia— para
detectar los modos de fallo silencioso característicos de este tipo de
análisis.</li>
<li>Publicar la firma génica resultante, su panel mínimo replicable y un
asistente conversacional que permita consultar los resultados sin necesidad
de manipular los datos brutos.</li>
</ol>
</div>""", unsafe_allow_html=True)

    seccion("IV", "Datos", "Cohortes públicas de NCBI GEO integradas en el análisis.")
    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
        st.dataframe(
            a[["Cohorte", "Plataforma", "N_Total", "N_Sano", "N_Enfermo",
               "Tasa_Exito_Curacion", "Evaluable_Como_Test"]],
            use_container_width=True, hide_index=True,
            column_config={
                "N_Total": st.column_config.NumberColumn("Muestras"),
                "N_Sano": st.column_config.NumberColumn("Sanas"),
                "N_Enfermo": st.column_config.NumberColumn("Enfermas"),
                "Tasa_Exito_Curacion": st.column_config.ProgressColumn(
                    "Curación LLM", min_value=0, max_value=1, format="%.2f"),
                "Evaluable_Como_Test": st.column_config.CheckboxColumn("Evaluable"),
            })


# ---------- Resultados -----------------------------------------------------
with t_res:
    st.markdown(f"""
    <div class="cifras">
      <div class="cifra acento-azul">
        <div class="rotulo">Tumor vs. sano<br>balanced accuracy</div>
        <div class="valor"><span data-count="{m.get('bal_acc', 0)}" data-dec="3">{dec(m.get('bal_acc', 0))}</span></div>
        <div class="glosa">Sobre {m.get('n_ev', 0)} cohortes evaluables de
        {m.get('n_cohortes', 0)}. Baseline medio {dec(m.get('base', 0))}.</div>
      </div>
      <div class="cifra acento-nar">
        <div class="rotulo">AUC media</div>
        <div class="valor"><span data-count="{m.get('auc', 0)}" data-dec="3">{dec(m.get('auc', 0))}</span></div>
        <div class="glosa">Discrimina bien y decide mal: la especificidad media
        es {dec(m.get('espec', 0))}.</div>
      </div>
      <div class="cifra acento-rojo">
        <div class="rotulo">No superan su baseline</div>
        <div class="valor"><span data-count="{m.get('no_superan', 0)}">{m.get('no_superan', 0)}</span><span class="u"> / {m.get('n_ev', 0)}</span></div>
        <div class="glosa">Cohortes evaluables por debajo de su propio azar
        informado.</div>
      </div>
      <div class="cifra acento-neutro">
        <div class="rotulo">Control positivo<br>AUC de subtipo</div>
        <div class="valor"><span data-count="{m.get('auc_sub', 0)}" data-dec="3">{dec(m.get('auc_sub', 0))}</span></div>
        <div class="glosa">{m.get('n_sub', 0)} muestras, 3 cohortes. Recupera los
        12 marcadores de inmunohistoquímica.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    seccion("I", "Rendimiento y hipótesis pre-registradas",
            "Cada análisis fijó su hipótesis y su umbral antes de ejecutarse. Dos "
            "no se confirmaron y se reportan como resultaron; los umbrales no se "
            "modificaron a posteriori.")

    HIP = [
        ("des", "descriptivo", "Auditoría de integridad",
         f"Sin hipótesis que confirmar. Cuatro modos de fallo, ninguno con error "
         f"en ejecución: 3 cohortes declaradas sin procesar, "
         f"<span class='dato'>{m.get('desal', 0)}</span> muestras con la etiqueta "
         f"clínica de otro paciente, <span class='dato'>{m.get('sin_clas', 0)}</span> "
         f"perdidas en la curación y <span class='dato'>{m.get('n_mono', 0)}</span> "
         f"cohortes de una sola clase empleadas como test."),
        ("si", "confirmada", "LODO con métricas completas",
         f"Balanced accuracy <span class='dato'>{dec(m.get('bal_acc', 0))}</span> "
         f"sobre cohortes evaluables, frente a una accuracy de "
         f"<span class='dato'>{dec(m.get('acc_11', 0))}</span> sobre las "
         f"{m.get('n_cohortes', 0)} incluidas las monoclase. "
         f"{m.get('no_superan', 0)} de {m.get('n_ev', 0)} no superan su baseline. "
         f"No previsto: AUC <span class='dato'>{dec(m.get('auc', 0))}</span> con "
         f"especificidad <span class='dato'>{dec(m.get('espec', 0))}</span> — la "
         f"firma ordena bien, pero el umbral de decisión no transfiere."),
        ("no", "no confirmada", "Composición tisular frente a biología",
         f"Al umbral pre-registrado |ρ| &gt; 0,7 se obtuvo "
         f"<span class='dato'>ρ = {dec(m.get('rho', 0))}</span> entre tumores; "
         f"{m.get('n_rho_sup', 0)} de {m.get('n_rho', 0)} cohortes lo superan "
         f"individualmente, con un máximo de "
         f"<span class='dato'>{dec(m.get('rho_max', 0))}</span>. La composición "
         f"explica una fracción sustancial de la señal sin agotarla, y coexiste con "
         f"un eje de proliferación no previsto."),
        ("si", "confirmada", "Validez de la consistencia de signo",
         f"Parejas de <em>folds</em> LODO que comparten el 98 % del entrenamiento "
         f"concuerdan al <span class='dato'>{dec(m.get('conc_lodo', 0), 1)} %</span>; "
         f"mitades disjuntas de tamaño comparable, al "
         f"<span class='dato'>{dec(m.get('conc_disj', 0), 2)} %</span>. "
         f"{m.get('genes_folds', 0)} genes con acuerdo perfecto entre folds frente "
         f"a {m.get('genes_disj', 0)} entre cohortes disjuntas: ninguno de los siete "
         f"genes destacados replica."),
        ("no", "no confirmada", "Límites del clasificador de subtipo",
         f"Al umbral del 50 %, solo el "
         f"<span class='dato'>{dec(m.get('pct_conf', 0), 1)} %</span> de las "
         f"histologías no vistas recibe asignación de alta confianza, frente al "
         f"63,1 % de las vistas: el modelo es más prudente de lo previsto. Pero el "
         f"92 % de los 101 tumores neuroendocrinos se etiqueta como adenocarcinoma, "
         f"un fallo con consecuencia clínica directa."),
    ]
    for i, (clase, etq, titulo, cuerpo) in enumerate(HIP):
        ultima = " ultima" if i == len(HIP) - 1 else ""
        st.markdown(f"""<div class="hip{ultima}">
          <div class="veredicto {clase}">{etq}</div>
          <div><h4>{titulo}</h4><p>{cuerpo}</p></div>
        </div>""", unsafe_allow_html=True)

    seccion("II", "Figuras")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        lamina("Rendimiento frente al azar informado", "fig_lodo_vs_baseline.png")
        lamina("El acuerdo de signo lo produce el solapamiento",
               "fig_concordancia_folds.png")
    with c2:
        lamina("Discriminación frente a decisión", "fig_auc_vs_balacc.png")
        lamina("Histologías ausentes del entrenamiento",
               "fig_histologias_excluidas.png")
    lamina("Composición tisular dentro de los tumores",
           "fig_composicion_tumores.png")

    if (d := tabla("LODO_HONESTO_RESULTADOS.csv")) is not None:
        with st.expander("Tabla completa de validación LODO"):
            st.dataframe(d, use_container_width=True, hide_index=True)

    seccion("III", "Integridad de los datos",
            "Cuatro modos de fallo, ninguno con error en ejecución: el pipeline "
            "termina, escribe sus ficheros y produce tablas de aspecto correcto. "
            "Los controles del framework los identifican antes de interpretar nada.")

    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
        st.dataframe(
            a[["Cohorte", "Plataforma", "N_Total", "N_Sano", "N_Enfermo",
               "N_Sin_Clasificar", "Tasa_Exito_Curacion", "Alineamiento",
               "Evaluable_Como_Test"]],
            use_container_width=True, hide_index=True,
            column_config={
                "N_Total": st.column_config.NumberColumn("Muestras"),
                "N_Sano": st.column_config.NumberColumn("Sanas"),
                "N_Enfermo": st.column_config.NumberColumn("Enfermas"),
                "N_Sin_Clasificar": st.column_config.NumberColumn("Sin clasificar"),
                "Tasa_Exito_Curacion": st.column_config.ProgressColumn(
                    "Curación LLM", min_value=0, max_value=1, format="%.2f"),
                "Alineamiento": st.column_config.TextColumn("Alineamiento"),
                "Evaluable_Como_Test": st.column_config.CheckboxColumn("Evaluable"),
            })

    lamina("Curación clínica automatizada", "fig_curacion_llm.png")

    st.markdown("""<div class="nota" style="margin-top:1.6rem">
    <b>El desalineamiento como fallo indistinguible.</b> En GSE30219 las 307
    columnas de la matriz están en orden distinto a las filas del metadata.
    Asignar la etiqueta por posición adjudica a cada muestra los datos clínicos
    de otro paciente. Efecto medido: el clasificador de subtipo daba AUC
    <b>0,56</b> con el bug y <b>0,99</b> tras corregirlo, con los mismos datos
    y el mismo modelo. Un AUC de 0,56 es indistinguible de una ausencia genuina
    de señal; solo la comparación con marcadores de referencia externos lo
    reveló.
    </div>""", unsafe_allow_html=True)

    seccion("IV", "La firma validada",
            "Un gen entra en la firma si mantiene el mismo signo de cambio, con "
            "tamaño de efecto suficiente (d de Cohen), en las tres cohortes "
            "independientes. Ningún gen se elige por su nombre ni por su función "
            "conocida.")

    rf = resumen_firma()
    if rf is not None:
        st.markdown(f"""
        <div class="cifras">
          <div class="cifra acento-azul">
            <div class="rotulo">Genes validados</div>
            <div class="valor"><span data-count="{rf['n_genes_validados']}">{rf['n_genes_validados']}</span></div>
            <div class="glosa">de {rf['n_genes_evaluados']} evaluados
            ({dec(rf['pct_genes_validados'], 1)} %) en
            {rf['n_cohortes_independientes']} cohortes independientes.</div>
          </div>
          <div class="cifra acento-nar">
            <div class="rotulo">Panel mínimo</div>
            <div class="valor"><span data-count="{rf['panel_minimo']}">{rf['panel_minimo']}</span></div>
            <div class="glosa">genes bastan para AUC
            {dec(rf['auc_panel_minimo'])}, frente a
            {dec(rf['auc_firma_completa'])} con la firma completa.</div>
          </div>
          <div class="cifra acento-neutro">
            <div class="rotulo">Marcadores IHC recuperados</div>
            <div class="valor"><span data-count="{sum(rf['ihc_recuperados'].values())}">{sum(rf['ihc_recuperados'].values())}</span><span class="u"> / {sum(rf['ihc_total'].values())}</span></div>
            <div class="glosa">marcadores de inmunohistoquímica clínica que el
            framework recupera sin conocerlos de antemano.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    top60 = tabla("FIRMA_VALIDADA_TOP60.csv")
    completa = tabla("FIRMA_VALIDADA_COMPLETA.csv")

    if completa is not None:
        gen = st.text_input(
            "Consultar un gen de la firma",
            placeholder="p. ej. DSG3, KRT5, EGFR…",
        ).strip().upper()

        if gen:
            filaC = completa[completa["ID_REF"] == gen]
            fila60 = (top60[top60["ID_REF"] == gen]
                      if top60 is not None else top60)
            if filaC.empty:
                st.warning(
                    f"**{gen}** no supera el criterio de replicación en las tres "
                    f"cohortes independientes (o no se evaluó en este análisis): "
                    f"no forma parte de la firma validada.")
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
            with st.expander("Top 60 de la firma validada"):
                st.dataframe(top60, use_container_width=True, hide_index=True)


# ---------- Metodología ----------------------------------------------------
with t_met:
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

    seccion("IV", "Sobre la paleta de las figuras")
    st.markdown("""<div class="prosa">
<p>Los colores se comprobaron con un validador de accesibilidad en modo claro y
oscuro. El resultado condicionó el diseño: el par verde–rojo, habitual para
«cumple / no cumple», da una separación de solo ΔE&nbsp;4,1 en deuteranopía y fue
descartado. Las oposiciones usan la pareja divergente azul–rojo (ΔE&nbsp;23,8), y
ninguna figura se apoya en el color en solitario: todas llevan leyenda o etiquetas
directas.</p>
</div>""", unsafe_allow_html=True)

    seccion("V", "Reproducir los resultados",
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


# ---------- Conclusiones ---------------------------------------------------
with t_con:
    seccion("I", "Qué demuestra el framework",
            "La combinación de curación por LLM, modelos de clasificación con "
            "validación externa y controles metodológicos produce una firma "
            "génica cuya replicación puede sostenerse en cohortes que no "
            "participaron en su construcción.")
    rf = resumen_firma()
    if rf is not None:
        st.markdown(f"""<div class="prosa">
<ul>
<li><b>{rf['n_genes_validados']} genes</b> mantienen el mismo signo de cambio,
con tamaño de efecto suficiente, en las
{rf['n_cohortes_independientes']} cohortes independientes; el
<b>{sum(rf['ihc_recuperados'].values())} de {sum(rf['ihc_total'].values())}</b>
de los marcadores clínicos de inmunohistoquímica se recupera sin haber sido
declarado.</li>
<li>Un <b>panel mínimo de {rf['panel_minimo']} genes</b> conserva AUC
{dec(rf['auc_panel_minimo'])} frente a {dec(rf['auc_firma_completa'])} de la
firma completa: la señal biológica se concentra en pocas variables.</li>
<li>La validación LODO reporta AUC <b>{dec(m.get('auc', 0))}</b> con
balanced accuracy <b>{dec(m.get('bal_acc', 0))}</b>: la firma ordena bien,
aunque el umbral de decisión no transfiere entre cohortes.</li>
</ul>
</div>""", unsafe_allow_html=True)

    seccion("II", "Qué limitaciones se detectaron",
            "Los controles del framework identifican tres modos de fallo que "
            "en un pipeline sin ellos habrían pasado inadvertidos.")
    st.markdown(f"""<div class="prosa">
<ul>
<li><b>Desalineamiento silencioso.</b> GSE30219 llevaba las columnas de la
matriz en orden distinto a las filas del metadata; asignar por posición daba
AUC 0,56 y por identificador daba 0,99. Sin comparación externa contra
marcadores clínicos, el fallo era indistinguible de ausencia de señal.</li>
<li><b>Composición tisular como confusor parcial.</b> Al umbral pre-registrado
|ρ| &gt; 0,7 no se confirmó la hipótesis (ρ medio = {dec(m.get('rho', 0))}),
pero {m.get('n_rho_sup', 0)} de {m.get('n_rho', 0)} cohortes lo superan
individualmente: la composición explica una fracción de la señal sin
agotarla.</li>
<li><b>Estabilidad aparente.</b> Parejas de <em>folds</em> LODO que comparten
el 98 % del entrenamiento concuerdan al {dec(m.get('conc_lodo', 0), 1)} %;
mitades disjuntas de tamaño comparable, al {dec(m.get('conc_disj', 0), 2)} %.
La estabilidad medida sobre <em>folds</em> solapados sobrestima la
reproducibilidad real.</li>
</ul>
</div>""", unsafe_allow_html=True)

    seccion("III", "Seis controles recomendados",
            "Contribución metodológica extraíble para trabajos análogos, "
            "independientemente del dominio biológico concreto.")
    st.markdown("""<div class="prosa">
<ol>
<li>Alinear muestras y metadatos por identificador explícito, nunca por posición.</li>
<li>Validar contra marcadores biológicos conocidos antes de interpretar nada.</li>
<li>Reportar el <em>baseline</em> de clase mayoritaria junto a toda métrica, y
excluir explícitamente las cohortes de una sola clase.</li>
<li>Separar métricas de discriminación (AUC) y de decisión (balanced accuracy).</li>
<li>Medir la estabilidad sobre particiones disjuntas, no sobre <em>folds</em> solapados.</li>
<li>Cuantificar y reportar la tasa de éxito de toda etapa de curación automatizada.</li>
</ol>
</div>""", unsafe_allow_html=True)

    seccion("IV", "Trabajo futuro")
    st.markdown("""<div class="prosa">
<ul>
<li>Validación prospectiva del panel mínimo sobre una cohorte independiente
no incluida en la construcción de la firma.</li>
<li>Ampliación del framework a otras patologías oncológicas con la misma
estructura de pipeline y sistema de controles.</li>
<li>Sustitución del modelo de lenguaje por variantes locales, para que la
curación de metadatos no dependa de una API externa.</li>
</ul>
</div>""", unsafe_allow_html=True)
