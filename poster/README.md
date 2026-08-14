# Póster TFM — data.lung

Póster A0 vertical (841 × 1189 mm) para la defensa del TFM.

## Estructura

```
poster/
├── poster.tex                       # Fuente LaTeX (tikzposter)
├── poster.pdf                       # PDF compilado
├── fig_panel_minimo.pdf             # Curva AUC vs tamaño de panel
├── fig_composicion_tumores.pdf      # (no usado en el poster actual)
└── fig_lodo_vs_baseline.pdf         # (no usado en el poster actual)
```

## Compilación

```bash
cd poster
pdflatex poster.tex
```

Requiere los paquetes LaTeX: `tikzposter`, `xstring`, `a0poster`,
`extsizes`, `ae`, `ncntrsbk` (todos incluidos en TeX Live estándar).

## Contenido

Cabecera con marca `data.lung` en tipografía mono con acento verde, y
tres columnas debajo:

- **Columna 1**: Contexto y motivación · Objetivo · Método (con diagrama
  TikZ del pipeline).
- **Columna 2**: Cifras principales (grande, tipo dashboard) · Tabla de
  rendimiento LODO por tarea · Curva del panel mínimo.
- **Columna 3**: Validación IHC 18/20 (tabla lado a lado) ·
  Interpretación biológica de los dos ejes · Conclusiones · Trabajo
  futuro.

Pie con URL del repositorio, comando para lanzar la interfaz y licencia
MIT.

## Impresión

- Formato A0 vertical (841 × 1189 mm).
- Márgenes internos ~1,5 cm.
- Todas las figuras son vectoriales (PDF), imprime a cualquier resolución.
- Paleta principal: verde terminal (#1c8a3f) sobre fondo claro
  (#fafaf7). Alto contraste, legible tanto en pared como en pantalla.
