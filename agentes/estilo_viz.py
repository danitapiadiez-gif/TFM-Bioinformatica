"""
Sistema visual compartido: paleta validada y tipografia de las figuras.

La paleta se comprobo con el validador de la guia de visualizacion en modo claro
y oscuro. Dos resultados condicionaron las decisiones:

  - verde #0ca30c frente a rojo #d03b3b da CVD ΔE 4,1 en deuteranopia (FALLA):
    la codificacion "supera / no supera" NO puede apoyarse en el par rojo-verde,
    que es la trampa clasica de daltonismo.
  - la pareja divergente azul #2a78d6 <-> rojo #d03b3b pasa todas las
    comprobaciones en ambos modos (ΔE 23,8 protanopia, 31,6 vision normal),
    de modo que es la que se emplea para las oposiciones.

Ademas, ninguna figura se apoya en el color por si solo: todas llevan leyenda o
etiquetas directas.
"""

import matplotlib as mpl

# --- Paleta -------------------------------------------------------------
AZUL = "#2a78d6"       # serie 1 / polo "cumple"
NARANJA = "#eb6834"    # serie 2
ROJO = "#d03b3b"       # polo "no cumple" (validado frente a AZUL)
NEUTRO = "#898781"     # sin dato / no evaluable (nunca una serie)

# Rampa secuencial de azul, para magnitud continua.
AZUL_RAMPA = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
}

# --- Cromo e ink --------------------------------------------------------
SUPERFICIE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"


def aplicar_estilo():
    """Fija la tipografia y el cromo recesivo comunes a todas las figuras."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial",
                            "DejaVu Sans"],
        "font.size": 8.5,
        "figure.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.06,

        # Superficie
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,

        # Ejes recesivos: sin marco, solo la linea base
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": True,
        "axes.edgecolor": EJE,
        "axes.linewidth": 0.7,
        "axes.labelcolor": INK_2,
        "axes.labelsize": 8,
        "axes.labelpad": 6,
        "axes.titlesize": 9.5,
        "axes.titlecolor": INK,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 10,

        # Rejilla hairline, por debajo de los datos
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": REJILLA,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,

        # Marcas de eje discretas
        "xtick.color": INK_MUTE,
        "ytick.color": INK_MUTE,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 5,
        "ytick.major.pad": 4,

        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "legend.labelcolor": INK_2,
        "legend.handlelength": 1.1,
        "legend.handleheight": 0.9,
        "legend.columnspacing": 1.4,
    })


def coma(x, pos=None):
    """Formateador de eje con coma decimal."""
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if s else "0"


def subtitulo(ax, texto):
    """Anota bajo el titulo la lectura que la figura pretende sostener."""
    ax.annotate(texto, xy=(0, 1), xycoords="axes fraction",
                xytext=(0, 16), textcoords="offset points",
                fontsize=7.6, color=INK_2, va="bottom", ha="left")


def encabezado(ax, titulo, subtitulo=None):
    """Titulo y subtitulo apilados correctamente sobre el area de datos.

    matplotlib no tiene subtitulo por eje: usar set_title mas una anotacion con
    desplazamiento positivo coloca el subtitulo POR ENCIMA del titulo. Aqui el
    titulo se dibuja con margen suficiente y el subtitulo debajo de el.
    """
    pad = 24 if subtitulo else 10
    ax.set_title(titulo, pad=pad)
    if subtitulo:
        ax.annotate(subtitulo, xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 7), textcoords="offset points",
                    fontsize=7.6, color=INK_2, va="bottom", ha="left")


def barras_redondeadas(ax, posiciones, valores, ancho, colores,
                       horizontal=False, radio_px=3.0):
    """Barras con el extremo de dato redondeado, ancladas a la linea base.

    El radio se expresa en pixeles y se traduce a unidades de datos;
    mutation_aspect corrige la distorsion entre ejes para que el redondeo se vea
    circular y no ovalado. Requiere que los limites del eje esten ya fijados.
    """
    from matplotlib.patches import FancyBboxPatch

    ax.figure.canvas.draw()
    bbox = ax.get_window_extent()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dx = (x1 - x0) / max(bbox.width, 1)     # unidades de x por pixel
    dy = (y1 - y0) / max(bbox.height, 1)    # unidades de y por pixel

    # Solo el extremo de dato va redondeado: la barra se extiende por debajo de
    # la linea base una distancia igual al radio, de modo que las esquinas
    # inferiores caen fuera de los limites del eje y quedan recortadas. La
    # longitud visible sigue siendo exactamente el valor.
    for p, v, c in zip(posiciones, valores, colores):
        if horizontal:
            radio = min(radio_px * dy, abs(v) / 2 if v else radio_px * dy)
            rect = ((-radio_px * dx, p - ancho / 2), v + radio_px * dx, ancho)
            aspecto = dy / dx
        else:
            radio = min(radio_px * dx, abs(v) / 2 if v else radio_px * dx)
            rect = ((p - ancho / 2, -radio_px * dy), ancho, v + radio_px * dy)
            aspecto = dx / dy
        caja = FancyBboxPatch(
            rect[0], rect[1], rect[2],
            boxstyle=f"round,pad=0,rounding_size={radio}",
            mutation_aspect=aspecto,
            facecolor=c, edgecolor="none", zorder=3, clip_on=True,
        )
        ax.add_patch(caja)
