"""
Landing (portada) de data.lung.

Se registra como pagina "/" del sitio multipage en paso12_web_chatbot.py y
no se ejecuta directamente. Portada minimalista: nombre gigante, tagline, y
un boton para entrar al framework. Todo el detalle vive en la pagina siguiente.
"""

import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contexto_tfm import FaltanResultados, prompt_sistema  # noqa: E402


# Falla pronto y con mensaje claro si faltan datos, en vez de mostrar la
# portada como si todo fuera bien.
try:
    prompt_sistema()
except FaltanResultados as e:
    st.error("**No se puede iniciar: faltan los resultados del proyecto.**")
    st.code(str(e))
    st.stop()


st.markdown(
    """
<style>
  :root {
    --ink:      #0b0b0b;
    --ink-2:    #4a4a48;
    --ink-mute: #8a8880;
    --linea:    #e2e0d8;
    --plano:    #fafaf7;
    --verde:    #1c8a3f;
    --verde-2:  #146a2f;
    --mono: ui-monospace, "SF Mono", "Menlo", "Consolas", monospace;
    --sans: system-ui, -apple-system, "Segoe UI", sans-serif;
    --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  }
  #MainMenu, footer, .stAppDeployButton,
  [data-testid="stMainMenuButton"] { display: none !important; }
  header[data-testid="stHeader"] {
    background: transparent !important; height: 2rem;
  }
  .stApp { background: var(--plano); }
  .block-container {
    padding-top: 1rem !important; padding-bottom: 2rem !important;
  }
  html, body, [class*="css"] { font-family: var(--sans); }

  /* Fondo de terminal en vivo. Posicion fija a pantalla completa, opacidad
     muy baja, degradado en los extremos para que se funda con el fondo.
     Usa div (no pre) porque Streamlit sanea <pre>. */
  .terminal-bg {
    position: fixed; inset: 0;
    padding: 6vh 4vw;
    font-family: var(--mono); font-size: 11px; line-height: 1.55;
    color: var(--verde);
    opacity: .11;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
    white-space: pre;
    -webkit-mask-image: linear-gradient(to bottom,
      transparent 0%, black 18%, black 82%, transparent 100%);
    mask-image: linear-gradient(to bottom,
      transparent 0%, black 18%, black 82%, transparent 100%);
  }
  .portada, div[data-testid="stPageLink"], .pie {
    position: relative; z-index: 2;
  }
  .terminal-bg .cur {
    display: inline-block; width: 7px; height: 12px;
    background: var(--verde); vertical-align: -1px;
    animation: parpadeo 1s steps(2) infinite;
  }
  @keyframes parpadeo { 50% { opacity: 0; } }

  .portada {
    min-height: 82vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center;
    padding: 3rem 1.5rem;
  }
  .portada .marca {
    font-family: var(--mono); font-size: .82rem; font-weight: 500;
    color: var(--ink-mute); letter-spacing: .04em;
    margin-bottom: 3.5rem;
  }
  .portada .marca::before {
    content: "❯ "; color: var(--verde);
  }
  .portada .brand {
    font-family: var(--mono);
    font-size: clamp(4rem, 15vw, 10rem);
    font-weight: 500; line-height: .95; letter-spacing: -.05em;
    color: var(--ink); margin: 0 0 2rem;
  }
  .portada .brand .punto {
    color: var(--verde);
    display: inline-block;
    transform: translateY(-.02em);
  }
  .portada .tagline {
    font-family: var(--serif); font-weight: 400;
    font-size: clamp(1.05rem, 2.2vw, 1.45rem);
    color: var(--ink-2); line-height: 1.5; letter-spacing: -.005em;
    max-width: 34ch; margin: 0 auto 3.5rem;
  }
  .portada .filete {
    width: 44px; height: 2px; background: var(--verde);
    margin: 0 auto 2.5rem;
  }

  /* Boton CTA: verde terminal, presencia clara. Streamlit page_link vive en
     data-testid="stPageLink"; sobreescribimos con !important porque su CSS
     por defecto pisa lo demas. */
  div[data-testid="stPageLink"] { display: flex; justify-content: center; }
  div[data-testid="stPageLink"] a {
    background: var(--verde) !important; color: #fff !important;
    border: 1px solid var(--verde) !important; border-radius: 0 !important;
    font-family: var(--mono) !important;
    font-size: .95rem !important; font-weight: 500 !important;
    letter-spacing: .02em !important;
    padding: 1rem 2.4rem !important;
    text-decoration: none !important;
    transition: all .18s ease !important;
  }
  div[data-testid="stPageLink"] a:hover {
    background: var(--verde-2) !important;
    border-color: var(--verde-2) !important;
    transform: translateY(-1px);
  }
  div[data-testid="stPageLink"] a p {
    margin: 0 !important; padding: 0 !important;
    color: #fff !important; font-family: var(--mono) !important;
  }
  div[data-testid="stPageLink"] a::before {
    content: "❯ "; color: #fff; margin-right: .35rem;
  }
  div[data-testid="stPageLink"] a svg { display: none !important; }

  .pie {
    text-align: center;
    font-family: var(--mono); font-size: .68rem; color: var(--ink-mute);
    letter-spacing: .1em; text-transform: uppercase;
    padding-top: 1.6rem; border-top: 1px solid var(--linea);
    max-width: 720px; margin: 0 auto;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --ink: #f5f5f2; --ink-2: #c3c2b7; --ink-mute: #7a7873;
      --linea: #2c2c2a; --plano: #0d0d0d;
      --verde: #3fbf5f; --verde-2: #5cd47b;
    }
  }
</style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
<div class="terminal-bg" id="terminal-bg"></div>

<div class="portada">
  <div class="marca">data.lung</div>
  <div class="brand">data<span class="punto">.</span>lung</div>
  <div class="filete"></div>
  <p class="tagline">Biomarcadores pulmonares que replican en cohortes
  independientes.</p>
</div>
    """,
    unsafe_allow_html=True,
)

# Fondo terminal en vivo: script que simula la ejecucion del pipeline con
# lineas reales del proyecto (cohortes, tests, genes replicados, LODO).
# Ejecutado en iframe con acceso a window.parent.document.
components.html(
    """
    <script>
      const doc = window.parent.document;
      const bg = doc.getElementById("terminal-bg");
      if (bg && !bg.dataset.started) {
        bg.dataset.started = "1";
        const lineas = [
          "$ python -m tfm ejecutar tumor_vs_sano",
          "[00:00:01] loading GSE118370  · 78 samples · GPL570",
          "[00:00:02] loading GSE18842   · 91 samples · GPL570",
          "[00:00:04] loading GSE19188   · 156 samples · GPL570",
          "[00:00:06] loading GSE19804   · 120 samples · GPL570",
          "[00:00:08] loading GSE23066   · 10 samples · GPL570",
          "[00:00:10] loading GSE30219   · 307 samples · GPL570",
          "[00:00:12] loading GSE31210   · 246 samples · GPL570",
          "[00:00:15] loading GSE40791   · 194 samples · GPL570",
          "[00:00:16] loading GSE50081   · 181 samples · GPL570",
          "[00:00:18] aligning by geo_accession · integrity: ok",
          "[00:00:20] mapping probes  → gene symbols · 22,883 probes",
          "[00:00:23] llama-3.3-70b · curating clinical metadata...",
          "[00:00:26] matched 1,397/1,637 samples · sano | enfermo",
          "[00:00:29] differential expression · Welch t-test · FDR<0.05",
          "[00:00:31] selected 217 significant genes per cohort",
          "[00:00:33] training LogisticL1 · RandomForest · SVM",
          "[00:00:38] LODO fold 1/8: AUC=0.943 · bal_acc=0.821",
          "[00:00:41] LODO fold 2/8: AUC=0.887 · bal_acc=0.762",
          "[00:00:44] LODO fold 3/8: AUC=0.951 · bal_acc=0.808",
          "[00:00:47] LODO fold 4/8: AUC=0.929 · bal_acc=0.774",
          "[00:00:50] LODO fold 5/8: AUC=0.910 · bal_acc=0.751",
          "[00:00:53] LODO fold 6/8: AUC=0.968 · bal_acc=0.792",
          "[00:00:56] gene DSG3   replicates · d=4.88 · 2.57 · 5.08 · escamoso",
          "[00:00:58] gene KRT5   replicates · d=6.06 · 2.46 · 3.38 · escamoso",
          "[00:00:59] gene CALML3 replicates · d=3.73 · 2.37 · 2.84 · escamoso",
          "[00:01:01] gene NAPSA  replicates · d=-3.28 · -2.94 · -3.61 · adeno",
          "[00:01:03] gene TP63   replicates · d=5.14 · 3.02 · 3.87 · escamoso",
          "[00:01:05] gene SFTPC  replicates · d=-4.11 · -3.66 · -4.02 · adeno",
          "[00:01:07] 1,174 genes validated across 3 independent cohorts",
          "[00:01:09] minimum panel: 20 genes · AUC=0.966 · bal_acc=0.938",
          "[00:01:11] IHC clinical markers recovered: 18/20",
          "[00:01:12] writing FIRMA_VALIDADA_TOP60.csv",
          "[00:01:13] writing FIRMA_VALIDADA_COMPLETA.csv",
          "[00:01:14] writing FIRMA_VALIDADA_RESUMEN.json",
          "[00:01:15] ✓ done",
          ""
        ];
        let idx = 0, maxLineas = 32;
        function agregar() {
          if (idx >= lineas.length) {
            setTimeout(() => {
              bg.innerHTML = "";
              idx = 0;
              agregar();
            }, 4500);
            return;
          }
          const linea = lineas[idx++];
          const cur = '<span class="cur"></span>';
          const actual = bg.innerHTML.replace(cur, "");
          bg.innerHTML = actual + linea + " " + cur + "\\n";
          const partes = bg.innerHTML.split("\\n");
          if (partes.length > maxLineas)
            bg.innerHTML = partes.slice(-maxLineas).join("\\n");
          setTimeout(agregar, 300 + Math.random() * 500);
        }
        agregar();
      }
    </script>
    """,
    height=0,
)

st.page_link("paso12_dashboard.py", label="Entrar al framework")

st.markdown(
    """
<div class="pie" style="margin-top: 4rem;">
  Daniel Tapia Díez · TFM · Bioinformática · UAX
</div>
    """,
    unsafe_allow_html=True,
)
