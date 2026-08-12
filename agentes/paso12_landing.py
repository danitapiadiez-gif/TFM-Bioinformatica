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
    padding: 1.4vh 2.5vw;
    font-family: var(--mono); font-size: 10.5px; line-height: 1.55;
    color: #1c8a3f;
    opacity: .32;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
    white-space: pre;
    -webkit-mask-image: linear-gradient(to bottom,
      transparent 0%, black 4%, black 100%);
    mask-image: linear-gradient(to bottom,
      transparent 0%, black 4%, black 100%);
  }
  .portada, div[data-testid="stPageLink"], .pie {
    position: relative; z-index: 2;
  }
  /* Tokens del terminal (coloreados desde el generador de lineas). */
  .terminal-bg .ts   { color: #4a7355; opacity: .70; }
  .terminal-bg .gse  { color: #2d8fb8; }
  .terminal-bg .num  { color: #c78a1e; }
  .terminal-bg .tag  { color: #2fa15c; font-weight: 500; }
  .terminal-bg .ok   { color: #3fbf5f; font-weight: 500; }
  .terminal-bg .dim  { color: #5a7a63; }
  .terminal-bg .cur {
    display: inline-block; width: 7px; height: 12px;
    background: #3fbf5f; vertical-align: -1px;
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
        const gses = ["GSE118370","GSE18842","GSE19188","GSE19804",
          "GSE23066","GSE30219","GSE31210","GSE40791","GSE50081","GSE7670"];
        const genesEsc = ["DSG3","KRT5","KRT6B","CALML3","PKP1","FAT2",
          "DAPL1","TRIM29","CLCA2","DSC3","TP63","KRT14","S100A2","SPRR3"];
        const genesAdeno = ["NAPSA","SFTPC","SFTPB","SFTA2","MUC1","ABCA3",
          "CLDN18","LMO3","FOXA2","NKX2-1"];
        const nSam = {"GSE118370":78,"GSE18842":91,"GSE19188":156,
          "GSE19804":120,"GSE23066":10,"GSE30219":307,"GSE31210":246,
          "GSE40791":194,"GSE50081":181,"GSE7670":66};

        function ts(s) {
          const m = String(Math.floor(s/60)).padStart(2,"0");
          const ss = String(s%60).padStart(2,"0");
          return '<span class="ts">[00:' + m + ':' + ss + ']</span>';
        }
        function rnd(a) { return a[Math.floor(Math.random()*a.length)]; }
        function d() { return (Math.random()*4 + 2).toFixed(2); }
        function auc() { return (0.85 + Math.random()*0.13).toFixed(3); }
        function bal() { return (0.72 + Math.random()*0.15).toFixed(3); }
        function G(x) { return '<span class="gse">' + x + '</span>'; }
        function N(x) { return '<span class="num">' + x + '</span>'; }
        function T(x) { return '<span class="tag">' + x + '</span>'; }
        function OK(x){ return '<span class="ok">'  + x + '</span>'; }

        let t = 0;
        function siguienteLinea() {
          t += Math.floor(Math.random()*3) + 1;
          const c = Math.random();
          if (c < 0.30) {
            const g = rnd(gses);
            return ts(t) + " loading " + G(g.padEnd(9))
              + " · " + N(String(nSam[g]).padStart(3))
              + " samples · GPL570";
          } else if (c < 0.42) {
            const g = rnd(gses);
            return ts(t) + " aligning " + G(g)
              + " by geo_accession · integrity: " + OK("ok");
          } else if (c < 0.52) {
            return ts(t) + " " + T("llama-3.3-70b")
              + " · curating clinical metadata...";
          } else if (c < 0.62) {
            const n = Math.floor(Math.random()*300)+800;
            return ts(t) + " matched " + N(n) + "/"
              + N(n + Math.floor(Math.random()*20))
              + " samples · sano | enfermo";
          } else if (c < 0.72) {
            const g = rnd(gses);
            const n = Math.floor(Math.random()*400)+50;
            return ts(t) + " " + G(g)
              + " · Welch t-test + FDR<0.05 · " + N(n) + " significant";
          } else if (c < 0.85) {
            const fold = Math.floor(Math.random()*8)+1;
            return ts(t) + " " + T("LODO fold " + fold + "/8")
              + ": AUC=" + N(auc()) + " · bal_acc=" + N(bal());
          } else if (c < 0.95) {
            const escamoso = Math.random() < 0.55;
            const g = rnd(escamoso ? genesEsc : genesAdeno);
            const sig = escamoso ? "" : "-";
            return ts(t) + " gene " + T(g.padEnd(7))
              + " replicates · d=" + N(sig + d())
              + " · " + N(sig + d()) + " · " + N(sig + d())
              + " · " + (escamoso ? "escamoso" : "adeno");
          } else {
            const opciones = [
              " " + N("1,174") + " genes validated across 3 independent cohorts",
              " minimum panel: " + N("20") + " genes · AUC=" + N("0.966")
                + " · bal_acc=" + N("0.938"),
              " IHC clinical markers recovered: " + N("18") + "/" + N("20"),
              " writing " + T("FIRMA_VALIDADA_TOP60.csv"),
              " writing " + T("FIRMA_VALIDADA_RESUMEN.json"),
              " " + OK("✓ pipeline done") + " · reset",
              " $ python -m tfm ejecutar " + T("tumor_vs_sano")
            ];
            if (Math.random() < 0.15) t = 0;
            return ts(t) + rnd(opciones);
          }
        }

        // filas maximas segun viewport (line-height ~17px + padding)
        const filasMax = () => Math.max(24,
          Math.floor((window.parent.innerHeight - 40) / 17));

        // Pre-carga instantanea para que la pantalla se vea llena desde
        // el primer instante, en vez de ir goteando durante 20 segundos.
        const cur = '<span class="cur"></span>';
        const inicio = [];
        for (let i = 0; i < filasMax() - 1; i++) inicio.push(siguienteLinea());
        bg.innerHTML = inicio.join("\\n") + " " + cur;

        function agregar() {
          const actual = bg.innerHTML.replace(cur, "");
          bg.innerHTML = actual + "\\n" + siguienteLinea() + " " + cur;
          const partes = bg.innerHTML.split("\\n");
          const max = filasMax();
          if (partes.length > max)
            bg.innerHTML = partes.slice(-max).join("\\n");
          setTimeout(agregar, 350 + Math.random() * 550);
        }
        setTimeout(agregar, 400);
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
