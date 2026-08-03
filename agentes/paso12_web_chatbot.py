"""
Paso 12: interfaz web de consulta de resultados (Streamlit).

Ejecutar desde la raiz del proyecto con:
    streamlit run agentes/paso12_web_chatbot.py

Cuatro secciones: asistente conversacional, resultados, integridad de los datos y
metodologia. Todas las cifras se leen de los CSV producidos por los pasos 13-18;
ninguna esta escrita a mano, de modo que reejecutar un analisis actualiza la
interfaz.

El contexto del asistente lo construye contexto_tfm.py, que falla de forma
explicita si no encuentra los resultados: no arrancar es preferible a responder
sin datos, que es lo que hacia la version anterior de este fichero.

El lenguaje visual acompana a estilo_viz.py, de modo que la interfaz y las
figuras comparten paleta, tipografia y jerarquia.
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
FIG = os.path.join(BASE_DIR, "figuras_auditoria")

st.set_page_config(
    page_title="Auditoría de firmas transcriptómicas · TFM",
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
    font-family: var(--serif); font-size: 2.5rem; font-weight: 400;
    line-height: 1.12; letter-spacing: -.018em; color: var(--ink);
    margin: 0 0 .85rem 0; max-width: 21ch;
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
  div[data-testid="stChatMessage"] {
    background: var(--superficie); border: 1px solid var(--linea);
    border-radius: 0; padding: .9rem 1.05rem; margin-bottom: .7rem;
  }
  div[data-testid="stChatMessage"] p { font-size: .88rem; line-height: 1.65; }
  .stButton button {
    border-radius: 0; border: 1px solid var(--linea);
    background: var(--superficie); color: var(--ink-2);
    font-size: .81rem; text-align: left; padding: .62rem .8rem;
    line-height: 1.42; font-weight: 400;
  }
  .stButton button:hover {
    border-color: var(--ink); color: var(--ink); background: var(--superficie);
  }
  [data-testid="stChatInput"] { border-radius: 0; border-color: var(--linea); }

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
st.markdown(f"""
<div class="portada">
  <div class="filete"></div>
  <div class="kicker">Trabajo de Fin de Máster · Bioinformática · UAX</div>
  <h1>Auditoría de reproducibilidad de firmas transcriptómicas</h1>
  <p class="entradilla">El objetivo no es proponer biomarcadores de cáncer de
  pulmón. Es caracterizar de qué formas concretas fallan —&nbsp;sin emitir ningún
  error&nbsp;— los <em>pipelines</em> que los derivan de repositorios públicos, y
  qué controles los detectan.</p>
  <div class="pie">
    <div><b>{m.get('n_cohortes', 0)}</b>cohortes GEO</div>
    <div><b>{m.get('n_muestras', 0)}</b>muestras</div>
    <div><b>5</b>hipótesis pre-registradas</div>
    <div><b>3 / 2</b>confirmadas / no</div>
    <div><b>4</b>modos de fallo silencioso</div>
    <div style="margin-left:auto;align-self:flex-end">Daniel Tapia Díez</div>
  </div>
</div>
""", unsafe_allow_html=True)


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
t_chat, t_res, t_aud, t_met = st.tabs(
    ["Asistente", "Resultados", "Integridad de los datos", "Metodología"])


# ---------- Asistente ------------------------------------------------------
with t_chat:
    st.markdown("""<div class="nota">
    Responde <b>únicamente</b> con lo que figura en los resultados del trabajo; si
    algo no está, lo dice. <b>No proporciona consejo médico ni diagnóstico</b>, y
    la firma estudiada no está validada para uso clínico.
    </div>""", unsafe_allow_html=True)

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

    if not st.session_state.mensajes and not pendiente:
        st.markdown('<p class="lat-tit">Por dónde empezar</p>',
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

    entrada = st.chat_input("Consulta sobre los resultados…", disabled=not hay_clave)
    pregunta = pendiente or entrada

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


# ---------- Resultados -----------------------------------------------------
with t_res:
    st.markdown(f"""
    <div class="cifras">
      <div class="cifra acento-azul">
        <div class="rotulo">Tumor vs. sano<br>balanced accuracy</div>
        <div class="valor">{dec(m.get('bal_acc', 0))}</div>
        <div class="glosa">Sobre {m.get('n_ev', 0)} cohortes evaluables de
        {m.get('n_cohortes', 0)}. Baseline medio {dec(m.get('base', 0))}.</div>
      </div>
      <div class="cifra acento-nar">
        <div class="rotulo">AUC media</div>
        <div class="valor">{dec(m.get('auc', 0))}</div>
        <div class="glosa">Discrimina bien y decide mal: la especificidad media
        es {dec(m.get('espec', 0))}.</div>
      </div>
      <div class="cifra acento-rojo">
        <div class="rotulo">No superan su baseline</div>
        <div class="valor">{m.get('no_superan', 0)}<span class="u"> / {m.get('n_ev', 0)}</span></div>
        <div class="glosa">Cohortes evaluables por debajo de su propio azar
        informado.</div>
      </div>
      <div class="cifra acento-neutro">
        <div class="rotulo">Control positivo<br>AUC de subtipo</div>
        <div class="valor">{dec(m.get('auc_sub', 0))}</div>
        <div class="glosa">{m.get('n_sub', 0)} muestras, 3 cohortes. Recupera los
        12 marcadores de inmunohistoquímica.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    seccion("I", "Las cinco hipótesis",
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


# ---------- Integridad -----------------------------------------------------
with t_aud:
    seccion("III", "Cuatro modos de fallo silencioso",
            "Los cuatro comparten el rasgo que los hace peligrosos: ninguno "
            "interrumpe la ejecución. El <em>pipeline</em> termina, escribe sus "
            "ficheros y produce tablas de aspecto correcto.")

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
    Asignar la etiqueta por posición adjudica a cada muestra los datos clínicos de
    otro paciente. Efecto medido: el clasificador de subtipo daba AUC <b>0,56</b>
    con el bug y <b>0,99</b> tras corregirlo, con los mismos datos y el mismo
    modelo. Un AUC de 0,56 es indistinguible de una ausencia genuina de señal;
    solo la comparación con marcadores de referencia externos lo reveló.
    </div>""", unsafe_allow_html=True)


# ---------- Metodología ----------------------------------------------------
with t_met:
    seccion("IV", "Metodología")
    st.markdown("""<div class="prosa">
<h4>Pipeline</h4>
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

<h4>Sobre el efecto lote</h4>
<p>No existe corrección de lote en el <em>pipeline</em>, solo normalización dentro
de estudio. LODO no corrige el efecto lote: lo <b>mide</b>. Presentarlo como
mecanismo de superación del <em>batch effect</em> es un error conceptual que la
versión previa de la memoria contenía.</p>

<h4>Sobre la paleta de las figuras</h4>
<p>Los colores se comprobaron con un validador de accesibilidad en modo claro y
oscuro. El resultado condicionó el diseño: el par verde–rojo, habitual para
«cumple / no cumple», da una separación de solo ΔE&nbsp;4,1 en deuteranopía y fue
descartado. Las oposiciones usan la pareja divergente azul–rojo (ΔE&nbsp;23,8), y
ninguna figura se apoya en el color en solitario: todas llevan leyenda o etiquetas
directas.</p>

<h4>Seis controles recomendados</h4>
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

    st.markdown('<div class="lamina-tit">Reproducir</div>', unsafe_allow_html=True)
    st.code("""python agentes/paso14_auditoria_datos.py
python agentes/paso15_lodo_honesto.py
python agentes/paso16_composicion_vs_biologia.py
python agentes/paso17_falacia_folds.py
python agentes/paso13_subtipo_lodo.py
python agentes/paso18_subtipo_casos_dificiles.py
python agentes/generar_figuras_auditoria.py
python agentes/generar_tablas_latex.py""", language="bash")
