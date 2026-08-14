# Memoria TFM — LaTeX

Fuente LaTeX de la memoria del Trabajo Fin de Máster.

## Estructura

```
memoria/
├── main.tex                 # Documento maestro
├── preambulo.tex            # Paquetes, geometría, tipografía
├── portada.tex              # Portada institucional UAX + firmas
├── resumen.tex              # Resumen + Abstract
├── bibliografia.bib         # Referencias BibLaTeX
├── capitulos/
│   ├── 01_introduccion.tex
│   ├── 02_estado_arte.tex
│   ├── 03_objetivos.tex
│   ├── 04_metodos.tex
│   ├── 05_resultados.tex
│   ├── 06_discusion.tex
│   └── 07_conclusiones.tex
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
    └── heatmap_gse31210.png
```

## Compilación

Requisitos: TeX Live / MacTeX / TinyTeX con `pdflatex` y `bibtex`
disponibles.

```bash
cd memoria
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Alternativa con `latexmk` (más simple, resuelve las tres pasadas
automáticamente):

```bash
cd memoria
latexmk -pdf main.tex
```

Salida: `main.pdf`.

## Antes de entregar

- Rellenar el campo `NP:` en `portada.tex` con el número de preinscripción.
- Revisar la fecha de presentación en `portada.tex` (por defecto 14 de
  agosto de 2026).
- Revisar la firma del director cuando esté disponible.
- Ajustar las referencias BibLaTeX marcadas como ilustrativas
  (`wang2024geoparser`) si aplica.
- Verificar los años entre paréntesis de las referencias antes de imprimir
  (algunas están puestas del año conocido de publicación; contrastar con
  la referencia definitiva si el tribunal exige DOI).

## Ajustes rápidos

- **Extensión**: la memoria en su forma actual es de aproximadamente
  60-75 páginas dependiendo de las opciones tipográficas locales. Para
  reducir, `\onehalfspacing` en `preambulo.tex` puede cambiarse por
  `\singlespacing`.
- **Cambio de tutor / autor / título**: en `main.tex` (comentario de
  cabecera), `portada.tex` (todas las apariciones) y `resumen.tex`.
- **Añadir un capítulo**: crear el fichero bajo `capitulos/`, incluirlo
  con `\input{capitulos/NN_nombre}` en `main.tex`, y añadir la referencia
  a `\ref{cap:etiqueta}` donde corresponda.
