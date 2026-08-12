"""
Landing (portada) de data.lung.

Se registra como pagina "/" del sitio multipage en paso12_web_chatbot.py y
no se ejecuta directamente. Portada minimalista: nombre gigante, tagline, y
un boton para entrar al framework. Todo el detalle vive en la pagina siguiente.
"""

import os
import sys
from urllib.parse import quote

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


# --------------------------------------------------------------------------
# SVG decorativo: pulmones, doble helice, bases A-T-G-C y adenina.
# Se inyecta como background-image data-URI porque Streamlit sanea las
# etiquetas <line>, <polygon> y <text> dentro de un <svg> inline; el data-URI
# se sirve tal cual, sin sanitizacion.
# --------------------------------------------------------------------------
_svg_bio = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 720" '
    'stroke="#1c8a3f" fill="none" stroke-width="1.4" '
    'stroke-linecap="round" stroke-linejoin="round">'
    # Pulmones
    '<g transform="translate(100, 90)">'
    '<line x1="0" y1="-40" x2="0" y2="-8" stroke-width="2"/>'
    '<line x1="-10" y1="-8" x2="10" y2="-8" stroke-width="2"/>'
    '<path d="M -8 -6 Q -45 15 -48 55 Q -50 78 -30 78 Q -12 78 -8 60 Z" stroke-width="1.6"/>'
    '<path d="M 8 -6 Q 45 15 48 55 Q 50 78 30 78 Q 12 78 8 60 Z" stroke-width="1.6"/>'
    '<path d="M -12 5 Q -25 15 -30 30 M -30 30 Q -35 40 -38 55 M -30 30 Q -25 45 -18 55"/>'
    '<path d="M 12 5 Q 25 15 30 30 M 30 30 Q 35 40 38 55 M 30 30 Q 25 45 18 55"/>'
    '</g>'
    # Doble helice
    '<g transform="translate(100, 260)">'
    '<path d="M -35 0 Q 0 25 35 50 Q 0 75 -35 100 Q 0 125 35 150 Q 0 175 -35 200" stroke-width="1.6"/>'
    '<path d="M 35 0 Q 0 25 -35 50 Q 0 75 35 100 Q 0 125 -35 150 Q 0 175 35 200" stroke-width="1.6"/>'
    '<line x1="-28" y1="10" x2="28" y2="10"/>'
    '<line x1="-16" y1="30" x2="16" y2="30"/>'
    '<line x1="-3" y1="50" x2="3" y2="50"/>'
    '<line x1="16" y1="70" x2="-16" y2="70"/>'
    '<line x1="28" y1="90" x2="-28" y2="90"/>'
    '<line x1="16" y1="110" x2="-16" y2="110"/>'
    '<line x1="3" y1="130" x2="-3" y2="130"/>'
    '<line x1="-16" y1="150" x2="16" y2="150"/>'
    '<line x1="-28" y1="170" x2="28" y2="170"/>'
    '<line x1="-16" y1="190" x2="16" y2="190"/>'
    '</g>'
    # Letras A-T, G-C, C-G, T-A (emparejamiento de bases)
    '<g transform="translate(100, 510)" font-family="ui-monospace,Menlo,monospace" '
    'font-size="22" font-weight="500" fill="#1c8a3f" stroke="none" text-anchor="middle">'
    '<text x="-45" y="0">A</text>'
    '<line x1="-32" y1="-6" x2="-13" y2="-6" stroke="#1c8a3f" stroke-dasharray="2 2"/>'
    '<text x="0" y="0">T</text>'
    '<text x="-45" y="35">G</text>'
    '<line x1="-32" y1="29" x2="-13" y2="29" stroke="#1c8a3f" stroke-dasharray="2 2"/>'
    '<text x="0" y="35">C</text>'
    '<text x="-45" y="70">C</text>'
    '<line x1="-32" y1="64" x2="-13" y2="64" stroke="#1c8a3f" stroke-dasharray="2 2"/>'
    '<text x="0" y="70">G</text>'
    '<text x="-45" y="105">T</text>'
    '<line x1="-32" y1="99" x2="-13" y2="99" stroke="#1c8a3f" stroke-dasharray="2 2"/>'
    '<text x="0" y="105">A</text>'
    '</g>'
    # Adenina esquematica (dos anillos fusionados)
    '<g transform="translate(100, 660)">'
    '<polygon points="-30,-15 -15,-25 5,-15 5,5 -15,15 -30,5" stroke-width="1.4"/>'
    '<polygon points="5,-15 22,-18 32,-5 22,10 5,5" stroke-width="1.4"/>'
    '<circle cx="-33" cy="10" r="1.8" fill="#1c8a3f"/>'
    '<circle cx="8" cy="-22" r="1.8" fill="#1c8a3f"/>'
    '<text x="60" y="3" font-family="ui-monospace,Menlo,monospace" '
    'font-size="10" fill="#1c8a3f" stroke="none" text-anchor="middle">adenina</text>'
    '</g>'
    '</svg>'
)
_svg_bio_url = quote(_svg_bio, safe="")

st.markdown(
    f"""
<style>
  .bio-bg {{
    background-image: url("data:image/svg+xml,{_svg_bio_url}");
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
  }}
</style>
    """,
    unsafe_allow_html=True,
)

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
    position: fixed; top: 0; bottom: 0; left: 0; right: 32%;
    padding: 1.4vh 2vw;
    font-family: var(--mono); font-size: 10.5px; line-height: 1.55;
    color: #1c8a3f;
    opacity: .32;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
    white-space: pre;
    -webkit-mask-image: linear-gradient(to bottom,
      transparent 0%, black 4%, black 96%, transparent 100%);
    mask-image: linear-gradient(to bottom,
      transparent 0%, black 4%, black 96%, transparent 100%);
  }

  /* Panel decorativo derecho: iconografia bio (pulmon, ADN, bases). Opacidad
     baja, mismo tono verde que el terminal. */
  .bio-bg {
    position: fixed; top: 0; bottom: 0; right: 0; width: 30%;
    display: flex; align-items: center; justify-content: center;
    pointer-events: none; z-index: 0;
    opacity: .14;
    padding: 2rem 1.5rem;
  }
  .bio-bg svg { width: 100%; height: 100%; max-width: 360px; }
  @media (max-width: 900px) {
    .bio-bg { display: none; }
    .terminal-bg { right: 0; }
  }
  .portada, .stButton, .pie {
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
    min-height: 68vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center;
    padding: 2rem 1.5rem 1rem;
  }
  .portada .marca {
    font-family: var(--mono); font-size: .82rem; font-weight: 500;
    color: var(--ink-mute); letter-spacing: .04em;
    margin-bottom: 3.5rem;
    display: flex; justify-content: space-between; align-items: center;
    width: 100%; max-width: 720px;
  }
  .portada .marca .izq::before {
    content: "❯ "; color: var(--verde);
  }
  .portada .marca .der {
    font-size: .72rem; color: var(--ink-mute);
    letter-spacing: .06em; text-transform: uppercase;
  }
  .portada .marca .der .autor { color: var(--ink); font-weight: 500; }
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

  /* Boton CTA: verde terminal, presencia clara. Aplica al st.button que
     dispara st.switch_page en la landing. */
  .stButton button, [data-testid="stBaseButton-secondary"] {
    background: var(--verde) !important; color: #fff !important;
    border: 1px solid var(--verde) !important; border-radius: 0 !important;
    font-family: var(--mono) !important;
    font-size: .95rem !important; font-weight: 500 !important;
    letter-spacing: .02em !important;
    padding: 1rem 1.8rem !important;
    transition: all .18s ease !important;
  }
  .stButton button:hover,
  [data-testid="stBaseButton-secondary"]:hover {
    background: var(--verde-2) !important;
    border-color: var(--verde-2) !important;
    color: #fff !important;
    transform: translateY(-1px);
  }
  .stButton button p, [data-testid="stBaseButton-secondary"] p {
    color: #fff !important; font-family: var(--mono) !important;
    margin: 0 !important;
  }

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
<div class="bio-bg"></div>

<div class="portada">
  <div class="marca">
    <div class="izq">data.lung</div>
    <div class="der">
      <span class="autor">Daniel Tapia Díez</span> · TFM · Bioinformática · UAX
    </div>
  </div>
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
      function arrancar() {
        const bg = doc.getElementById("terminal-bg");
        if (!bg) { return setTimeout(arrancar, 150); }
        if (bg.dataset.started) return;
        inicializar(bg);
      }
      arrancar();
      function inicializar(bg) {
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

c_izq, c_btn, c_der = st.columns([1, 2, 1])
with c_btn:
    if st.button("❯ Entrar al framework", use_container_width=True,
                 key="btn_entrar"):
        st.switch_page("paso12_dashboard.py")

