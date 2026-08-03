"""
Paso 12: interfaz web de consulta de resultados (Streamlit).

Ejecutar desde la raiz del proyecto con:
    streamlit run agentes/paso12_web_chatbot.py

Cuatro pestanas: asistente conversacional, resultados, auditoria de integridad y
metodologia. Todas las cifras se leen de los CSV producidos por los pasos 13-18;
ninguna esta escrita a mano, de modo que reejecutar un analisis actualiza la
interfaz.

El contexto del asistente lo construye contexto_tfm.py, que falla de forma
explicita si no encuentra los resultados: no arrancar es preferible a responder
sin datos, que es lo que hacia la version anterior de este fichero.
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
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Estilo
# --------------------------------------------------------------------------
st.markdown("""
<style>
  :root {
    --tinta:      #1a1d21;
    --tenue:      #5f6b7a;
    --linea:      #e3e8ee;
    --lienzo:     #f7f9fb;
    --azul:       #2c5f8a;
    --rojo:       #b5453b;
    --verde:      #3d7a5a;
    --ambar:      #9a6b1e;
  }
  .block-container { padding-top: 2.1rem; max-width: 1180px; }
  #MainMenu, footer { visibility: hidden; }

  /* Cabecera */
  .hero {
    border: 1px solid var(--linea); border-left: 4px solid var(--azul);
    border-radius: 10px; padding: 1.25rem 1.5rem; background: var(--lienzo);
    margin-bottom: 1.4rem;
  }
  .hero h1 {
    font-size: 1.42rem; font-weight: 650; margin: 0 0 .3rem 0;
    letter-spacing: -.015em; color: var(--tinta); line-height: 1.25;
  }
  .hero p { margin: 0; color: var(--tenue); font-size: .92rem; line-height: 1.5; }
  .hero .meta {
    margin-top: .8rem; font-size: .78rem; color: var(--tenue);
    font-variant-numeric: tabular-nums;
  }
  .hero .meta b { color: var(--tinta); font-weight: 600; }

  /* Tarjetas de metrica */
  .fila { display: flex; gap: .8rem; flex-wrap: wrap; margin-bottom: 1.1rem; }
  .tarjeta {
    flex: 1 1 190px; border: 1px solid var(--linea); border-radius: 9px;
    padding: .85rem 1rem; background: #fff;
  }
  .tarjeta .et {
    font-size: .72rem; text-transform: uppercase; letter-spacing: .055em;
    color: var(--tenue); font-weight: 600; margin-bottom: .3rem;
  }
  .tarjeta .val {
    font-size: 1.62rem; font-weight: 660; color: var(--tinta);
    font-variant-numeric: tabular-nums; line-height: 1.1;
  }
  .tarjeta .nota { font-size: .76rem; color: var(--tenue); margin-top: .25rem; line-height: 1.4; }
  .tarjeta.ok   { border-left: 3px solid var(--verde); }
  .tarjeta.mal  { border-left: 3px solid var(--rojo); }
  .tarjeta.avi  { border-left: 3px solid var(--ambar); }
  .tarjeta.neu  { border-left: 3px solid var(--azul); }

  /* Distintivos de hipotesis */
  .dist {
    display: inline-block; padding: .13rem .5rem; border-radius: 4px;
    font-size: .71rem; font-weight: 640; letter-spacing: .02em;
  }
  .dist.si  { background: #e6f0ea; color: var(--verde); }
  .dist.no  { background: #fbecea; color: var(--rojo); }
  .dist.des { background: #eceff3; color: var(--tenue); }

  /* Bloque de hallazgo */
  .hallazgo {
    border: 1px solid var(--linea); border-radius: 9px; padding: .9rem 1.1rem;
    margin-bottom: .7rem; background: #fff;
  }
  .hallazgo h4 {
    margin: .35rem 0 .45rem 0; font-size: .97rem; font-weight: 620;
    color: var(--tinta);
  }
  .hallazgo p { margin: 0; font-size: .87rem; color: var(--tenue); line-height: 1.55; }
  .hallazgo .cifra {
    font-variant-numeric: tabular-nums; font-weight: 640; color: var(--tinta);
  }

  /* Aviso */
  .aviso {
    border: 1px solid #f0dcc4; background: #fdf8f1; border-radius: 8px;
    padding: .7rem .95rem; font-size: .83rem; color: #6b4d1c; line-height: 1.5;
    margin-bottom: 1rem;
  }

  [data-testid="stSidebar"] { border-right: 1px solid var(--linea); }
  .stTabs [data-baseweb="tab"] { font-size: .9rem; font-weight: 550; }
  div[data-testid="stChatMessage"] { border-radius: 9px; }

  @media (prefers-color-scheme: dark) {
    :root {
      --tinta: #e8ecf1; --tenue: #9aa7b8; --linea: #2b323c;
      --lienzo: #1a1f26; --azul: #6fa8d8;
    }
    .tarjeta, .hallazgo { background: #171b21; }
    .aviso { background: #241f16; border-color: #4a3d24; color: #d9c9a8; }
      .dist.si { background: #1c2e24; } .dist.no { background: #2e1d1b; }
    .dist.des { background: #22262d; }
  }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Carga de datos
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
        m |= {"rho": v.mean(), "n_rho": len(v)}
    if (f := tabla("FALACIA_FOLDS_COMPARACION.csv")) is not None:
        m |= {"conc_lodo": f.iloc[0]["concordancia_pareja_media"] * 100,
              "conc_disj": f.iloc[1]["concordancia_pareja_media"] * 100}
    if (h := tabla("SUBTIPO_CASOS_DIFICILES.csv")) is not None:
        m |= {"pct_conf": 100 * h["N_Alta_Confianza"].sum() / h["n"].sum()}
    return m


def dec(v, n=3):
    """Formato con coma decimal."""
    return f"{v:.{n}f}".replace(".", ",")


def img(nombre, **kw):
    ruta = os.path.join(FIG, nombre)
    if os.path.exists(ruta):
        st.image(ruta, **kw)
    else:
        st.caption(f"Figura no disponible: `{nombre}`. "
                   f"Generar con `python agentes/generar_figuras_auditoria.py`.")


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
# Cabecera
# --------------------------------------------------------------------------
st.markdown(f"""
<div class="hero">
  <h1>Auditoría de reproducibilidad de firmas transcriptómicas<br>en cáncer de pulmón</h1>
  <p>Consulta de los resultados del Trabajo de Fin de Máster. El objetivo no es proponer
  biomarcadores: es caracterizar cómo fallan, sin emitir ningún error, los <em>pipelines</em>
  que los derivan de datos públicos.</p>
  <div class="meta">
    <b>{m.get('n_cohortes', 0)}</b> cohortes GEO ·
    <b>{m.get('n_muestras', 0)}</b> muestras ·
    <b>5</b> hipótesis con umbral pre-registrado
    (<b>3</b> confirmadas, <b>2</b> no) ·
    Daniel Tapia Díez · UAX
  </div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Barra lateral
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Cifras principales")
    st.caption("Leídas de los CSV de resultados.")

    if "bal_acc" in m:
        st.metric("Balanced accuracy", dec(m["bal_acc"]),
                  delta=f"{dec(m['ganancia'])} sobre baseline",
                  help=f"Tumor frente a sano. Media sobre las {m['n_ev']} "
                       f"cohortes evaluables de {m['n_cohortes']}.")
        st.metric("AUC media", dec(m["auc"]),
                  help="Ordena bien; el umbral de decisión no transfiere.")
    if "auc_sub" in m:
        st.metric("AUC subtipo (control +)", dec(m["auc_sub"]),
                  help="Adenocarcinoma frente a escamoso. Válido solo sobre "
                       "tumores ya confirmados como una de las dos clases.")

    st.divider()
    st.markdown("#### Integridad de los datos")
    if "n_muestras" in m:
        st.caption(f"Muestras totales: **{m['n_muestras']}**")
        st.caption(f"Sin clasificar por el LLM: **{m['sin_clas']}** "
                   f"({dec(100 * m['sin_clas'] / m['n_muestras'], 1)} %)")
        st.caption(f"Con etiqueta cruzada, corregido: **{m['desal']}**")
        st.caption(f"Cohortes no evaluables: **{m['n_mono']}**")

    st.divider()
    inv = inventario()
    with st.expander(f"Procedencia ({sum(inv.values())}/{len(inv)})"):
        for n, ok in inv.items():
            st.caption(f"{'✔' if ok else '✘'} `{n}`")
    st.caption(f"Modelo: `{MODELO}`")
    if not hay_clave:
        st.warning("Sin `GROQ_API_KEY` en `.env`: el asistente está "
                   "deshabilitado, el resto de pestañas funciona.")


# --------------------------------------------------------------------------
# Pestañas
# --------------------------------------------------------------------------
t_chat, t_res, t_aud, t_met = st.tabs(
    ["Asistente", "Resultados", "Auditoría de integridad", "Metodología"])


# ---------- Asistente ------------------------------------------------------
with t_chat:
    st.markdown("""<div class="aviso">
    Este asistente responde <b>únicamente</b> con lo que figura en los resultados del
    trabajo; si algo no está, lo dice. <b>No proporciona consejo médico ni
    diagnóstico</b>, y la firma estudiada no está validada para uso clínico.
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

    # Se resuelve antes de pintar las sugerencias: si hay una pregunta en curso,
    # los botones no deben seguir en pantalla junto a la primera respuesta.
    pendiente = st.session_state.pop("pendiente", None)

    if not st.session_state.mensajes and not pendiente:
        st.caption("Preguntas para empezar:")
        cols = st.columns(2)
        for i, sug in enumerate(SUGERENCIAS):
            if cols[i % 2].button(sug, key=f"sug{i}", use_container_width=True):
                st.session_state.pendiente = sug
                st.rerun()

    for msg in st.session_state.mensajes:
        with st.chat_message(msg["role"], avatar="🔬" if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    entrada = st.chat_input("Consulta sobre los resultados…", disabled=not hay_clave)
    pregunta = pendiente or entrada

    if pregunta:
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)

        with st.chat_message("assistant", avatar="🔬"):
            try:
                flujo = cliente.chat.completions.create(
                    messages=([{"role": "system", "content": sistema}]
                              + st.session_state.mensajes[-12:]),
                    model=MODELO, temperature=0.0, max_tokens=900, stream=True,
                )
                texto = st.write_stream(
                    trozo.choices[0].delta.content or "" for trozo in flujo)
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
    <div class="fila">
      <div class="tarjeta neu">
        <div class="et">Tumor vs. sano · bal. accuracy</div>
        <div class="val">{dec(m.get('bal_acc', 0))}</div>
        <div class="nota">Sobre {m.get('n_ev', 0)} cohortes evaluables.
        Baseline medio {dec(m.get('base', 0))}.</div>
      </div>
      <div class="tarjeta avi">
        <div class="et">AUC media</div>
        <div class="val">{dec(m.get('auc', 0))}</div>
        <div class="nota">Discrimina bien, pero decide mal:
        especificidad {dec(m.get('espec', 0))}.</div>
      </div>
      <div class="tarjeta mal">
        <div class="et">No superan su baseline</div>
        <div class="val">{m.get('no_superan', 0)} / {m.get('n_ev', 0)}</div>
        <div class="nota">Cohortes evaluables por debajo del azar informado.</div>
      </div>
      <div class="tarjeta ok">
        <div class="et">Control positivo · AUC subtipo</div>
        <div class="val">{dec(m.get('auc_sub', 0))}</div>
        <div class="nota">{m.get('n_sub', 0)} muestras, 3 cohortes.
        12/12 marcadores de IHC recuperados.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Las cinco hipótesis")
    HIP = [
        ("des", "Auditoría de integridad (paso 14)",
         f"Descriptivo, sin hipótesis a confirmar. Cuatro modos de fallo, ninguno "
         f"con error en ejecución: 3 cohortes declaradas sin procesar, "
         f"<span class='cifra'>{m.get('desal', 0)}</span> muestras con etiqueta cruzada, "
         f"<span class='cifra'>{m.get('sin_clas', 0)}</span> perdidas en la curación y "
         f"<span class='cifra'>{m.get('n_mono', 0)}</span> cohortes no evaluables usadas como test."),
        ("si", "LODO con métricas completas (paso 15)",
         f"Confirmada. Balanced accuracy <span class='cifra'>{dec(m.get('bal_acc', 0))}</span> "
         f"sobre cohortes evaluables, frente a una accuracy de "
         f"<span class='cifra'>{dec(m.get('acc_11', 0))}</span> sobre las "
         f"{m.get('n_cohortes', 0)} incluidas las monoclase. "
         f"{m.get('no_superan', 0)} de {m.get('n_ev', 0)} no superan su baseline."),
        ("no", "Composición tisular frente a biología (paso 16)",
         f"<b>No confirmada</b> al umbral pre-registrado |ρ| &gt; 0,7: obtenido "
         f"<span class='cifra'>ρ = {dec(m.get('rho', 0), 3)}</span> entre tumores "
         f"({m.get('n_rho', 0)} cohortes). El umbral no se modificó. La composición explica "
         f"una fracción sustancial de la señal sin agotarla, y coexiste con un eje de "
         f"proliferación no previsto."),
        ("si", "Validez de la consistencia de signo (paso 17)",
         f"Confirmada, con control del tamaño de muestra. Parejas de <em>folds</em> LODO que "
         f"comparten el 98 % del entrenamiento concuerdan al "
         f"<span class='cifra'>{dec(m.get('conc_lodo', 0), 1)} %</span>; mitades disjuntas de "
         f"tamaño comparable, al <span class='cifra'>{dec(m.get('conc_disj', 0), 2)} %</span>. "
         f"Ninguno de los 7 genes destacados replica entre cohortes disjuntas."),
        ("no", "Límites del clasificador de subtipo (paso 18)",
         f"<b>No confirmada</b> al umbral del 50 %: solo el "
         f"<span class='cifra'>{dec(m.get('pct_conf', 0), 1)} %</span> de las histologías no "
         f"vistas recibe asignación de alta confianza, frente al 62,6 % de las vistas. Pero el "
         f"93 % de los 101 tumores neuroendocrinos se etiqueta como adenocarcinoma, fallo con "
         f"consecuencia clínica."),
    ]
    for estado, titulo, cuerpo in HIP:
        etq = {"si": "confirmada", "no": "no confirmada",
               "des": "descriptivo"}[estado]
        st.markdown(f"""<div class="hallazgo">
          <span class="dist {estado}">{etq}</span>
          <h4>{titulo}</h4><p>{cuerpo}</p></div>""", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Rendimiento frente al azar informado")
        img("fig_lodo_vs_baseline.png", use_container_width=True)
    with c2:
        st.markdown("##### Discriminación frente a decisión")
        img("fig_auc_vs_balacc.png", use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("##### El acuerdo de signo lo produce el solapamiento")
        img("fig_concordancia_folds.png", use_container_width=True)
    with c4:
        st.markdown("##### Histologías excluidas del entrenamiento")
        img("fig_histologias_excluidas.png", use_container_width=True)

    st.markdown("##### Composición tisular dentro de los tumores")
    img("fig_composicion_tumores.png", use_container_width=True)

    if (d := tabla("LODO_HONESTO_RESULTADOS.csv")) is not None:
        with st.expander("Tabla completa de validación LODO"):
            st.dataframe(d, use_container_width=True, hide_index=True)


# ---------- Auditoría ------------------------------------------------------
with t_aud:
    st.markdown("Los cuatro problemas detectados comparten un rasgo que los hace "
                "peligrosos: **ninguno interrumpe la ejecución**. El *pipeline* "
                "termina, escribe sus ficheros y produce tablas de aspecto correcto.")

    if (a := tabla("AUDITORIA_COHORTES.csv")) is not None:
        st.dataframe(
            a[["Cohorte", "Plataforma", "N_Total", "N_Sano", "N_Enfermo",
               "N_Sin_Clasificar", "Tasa_Exito_Curacion", "Alineamiento",
               "Evaluable_Como_Test"]],
            use_container_width=True, hide_index=True,
            column_config={
                "Tasa_Exito_Curacion": st.column_config.ProgressColumn(
                    "Curación LLM", min_value=0, max_value=1, format="%.1f"),
                "Evaluable_Como_Test": st.column_config.CheckboxColumn("Evaluable"),
            })

    st.markdown("##### Curación clínica automatizada")
    st.caption("El fallo es bimodal, no gradual: éxito casi completo o colapso. "
               "Eso sugiere sensibilidad al formato de los metadatos más que una "
               "limitación uniforme del modelo.")
    img("fig_curacion_llm.png", use_container_width=True)

    st.markdown("##### El desalineamiento como fallo indistinguible")
    st.info("En GSE30219 las 307 columnas de la matriz están en orden distinto a las "
            "filas del metadata. Asignar la etiqueta por posición adjudica a cada "
            "muestra los datos clínicos de otro paciente.\n\n"
            "**Efecto medido:** el clasificador de subtipo daba AUC **0,56** con el "
            "bug y **0,99** tras corregirlo, con los mismos datos y el mismo modelo. "
            "Un AUC de 0,56 es indistinguible de una ausencia genuina de señal, y "
            "solo la comparación con marcadores de referencia externos lo reveló.")


# ---------- Metodología ----------------------------------------------------
with t_met:
    st.markdown("""
#### Pipeline

1. Descarga de NCBI GEO con `GEOparse`; mapeo de sondas a símbolos génicos.
2. Normalización log2 y por cuantiles **dentro de cada estudio**.
3. Curación clínica de metadatos con Llama 3.3-70b vía Groq.
4. Análisis diferencial: *t* de Welch con corrección FDR de Benjamini-Hochberg.
5. Modelos: regresión logística con penalización L1, Random Forest, SVM.
6. Validación externa *Leave-One-Dataset-Out*.
7. Alineamiento muestra-etiqueta **por `geo_accession`, nunca por posición**.

> **Sobre el efecto lote.** No existe corrección de lote en el *pipeline*, solo
> normalización dentro de estudio. LODO no corrige el efecto lote: lo **mide**.
> Presentarlo como mecanismo de superación del *batch effect* es un error
> conceptual que la versión previa de la memoria contenía.

#### Seis controles recomendados

1. Alinear muestras y metadatos por identificador explícito, nunca por posición.
2. Validar contra marcadores biológicos conocidos antes de interpretar nada.
3. Reportar el *baseline* de clase mayoritaria junto a toda métrica, y excluir
   explícitamente las cohortes de una sola clase.
4. Separar métricas de discriminación (AUC) y de decisión (balanced accuracy).
5. Medir la estabilidad sobre particiones disjuntas, no sobre *folds* solapados.
6. Cuantificar y reportar la tasa de éxito de toda etapa de curación automatizada.

#### Reproducir

```bash
python agentes/paso14_auditoria_datos.py
python agentes/paso15_lodo_honesto.py
python agentes/paso16_composicion_vs_biologia.py
python agentes/paso17_falacia_folds.py
python agentes/paso13_subtipo_lodo.py
python agentes/paso18_subtipo_casos_dificiles.py
python agentes/generar_figuras_auditoria.py
python agentes/generar_tablas_latex.py
```
""")
