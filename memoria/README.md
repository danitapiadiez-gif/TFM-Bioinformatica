# Memoria TFM — LaTeX

Fuente LaTeX de la memoria del Trabajo Fin de Máster
*«Framework transcriptómico basado en la integración de modelos de
lenguaje y aprendizaje automático para la identificación de
biomarcadores en cáncer de pulmón»* (Daniel Tapia Díez, UAX 2026).

## Estructura

```
memoria/
├── main.tex                 # Documento maestro
├── preambulo.tex            # Paquetes, geometría, tipografía
├── portada.tex              # Portada UAX + firmas
├── resumen.tex              # Resumen (es) + Abstract (en)
├── bibliografia.bib         # Referencias BibTeX
├── main.pdf                 # PDF compilado (96 páginas)
├── README.md                # Este fichero
│
├── capitulos/
│   ├── 01_introduccion.tex
│   ├── 02_estado_arte.tex
│   ├── 03_objetivos.tex     # (front matter, tras resumen)
│   ├── 04_metodos.tex
│   ├── 05_resultados.tex
│   ├── 06_discusion.tex
│   ├── 07_conclusiones.tex
│   ├── A_repositorio.tex        # Anexo A
│   ├── B_ficheros_resultados.tex # Anexo B
│   ├── C_interfaz.tex           # Anexo C
│   ├── D_paneles.tex            # Anexo D
│   ├── E_prompts_llm.tex        # Anexo E
│   ├── F_despliegue.tex         # Anexo F
│   └── G_glosario.tex           # Anexo G
│
└── figuras/
    ├── fig_lodo_vs_baseline.pdf
    ├── fig_auc_vs_balacc.pdf
    ├── fig_composicion_tumores.pdf
    ├── fig_histologias_excluidas.pdf
    ├── fig_panel_minimo.pdf
    ├── fig_curacion_llm.pdf
    ├── fig_concordancia_folds.pdf
    ├── pca_gse31210.png
    ├── volcano_gse31210.png
    ├── heatmap_gse31210.png
    └── interfaz/
        └── 01_landing.png … 08_conclusiones.png
```

## Compilación

**Opción rápida (recomendada)**:

```bash
cd memoria
latexmk -pdf main.tex
```

**Manual**:

```bash
cd memoria
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Salida: `main.pdf` (96 páginas, ~3 MB).

## Requisitos

- **Distribución LaTeX**: TeX Live 2023+ / MacTeX / MiKTeX / TinyTeX.
- **Motor**: `pdflatex` (no necesita XeLaTeX ni LuaLaTeX).
- **Herramienta de bibliografía**: `bibtex` (viene con cualquier
  distribución LaTeX).

### Paquetes requeridos

Todos incluidos en el instalador *full* de TeX Live y MacTeX. Si usas
TinyTeX o una instalación mínima, instálalos con:

```bash
# Bloque de instalación completa
tlmgr install \
  babel-spanish lmodern setspace \
  fancyhdr geometry titlesec appendix \
  graphicx float booktabs longtable multirow subcaption \
  caption xcolor listings \
  amsmath amssymb mathtools \
  hyperref natbib \
  pgf tikz \
  xstring extsizes a0poster ncntrsbk ae
```

Los últimos cinco (`xstring extsizes a0poster ncntrsbk ae`) sólo son
necesarios si además compilas el póster A0 que vive en `../poster/`;
para la memoria en sí pueden omitirse.

### Lista mínima (sólo para la memoria)

```bash
tlmgr install \
  babel-spanish lmodern setspace \
  fancyhdr geometry titlesec appendix \
  graphicx float booktabs longtable multirow subcaption caption \
  xcolor listings amsmath amssymb mathtools \
  hyperref natbib pgf tikz
```

## Antes de entregar

- Rellenar el campo **`NP:`** en `portada.tex` con el número de
  preinscripción (línea con `\rule{4cm}{0.4pt}`).
- Revisar la **fecha de presentación** en `portada.tex` (por defecto
  14 de agosto de 2026).
- Si dispones del **PNG oficial del logo UAX**, copiarlo a
  `figuras/logo_uax.png` y sustituir en `portada.tex` el bloque:

  ```latex
  {\fontsize{72}{72}\selectfont \textbf{U\textcolor{blue!70!black}{A}X}}
  ```

  por:

  ```latex
  \includegraphics[width=6cm]{figuras/logo_uax.png}
  ```

## Ajustes rápidos

- **Interlineado**: `\onehalfspacing` en `preambulo.tex` puede
  cambiarse por `\singlespacing` para acortar la memoria.
- **Añadir un capítulo**: crear el `.tex` bajo `capitulos/`, incluirlo
  con `\input{capitulos/NN_nombre}` en `main.tex`, y usar
  `\label{cap:etiqueta}` para referencias cruzadas.
- **Añadir un anexo**: mismo patrón, colocarlo dentro del bloque
  `\begin{appendices}…\end{appendices}` de `main.tex`.

## Contenido

- **Resumen y abstract** en español e inglés (~2 páginas cada uno).
- **Objetivos** en front matter, tras el resumen (5 objetivos
  específicos + 4 hipótesis).
- **7 capítulos** de cuerpo (Introducción, Estado del arte, Métodos,
  Resultados, Discusión, Conclusiones).
- **7 anexos** (repositorio, ficheros de resultados, interfaz web,
  paneles biológicos, prompts LLM, guía de despliegue, glosario).
- **Bibliografía** con 20 referencias.
- Diagramas TikZ (pipeline, LODO, arquitectura de la interfaz, prompt
  del asistente, meta-análisis por consenso).
- Tablas y figuras con referencias cruzadas.
- Enlaces internos y externos en azul (`hyperref colorlinks`).
