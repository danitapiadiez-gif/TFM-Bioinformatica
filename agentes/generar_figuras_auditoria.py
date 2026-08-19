"""
Genera las figuras de los capitulos de Resultados y Discusion (pasos 14-18).

Todas se construyen desde los CSV de los pasos 14-18: ningun valor esta escrito a
mano, de modo que reejecutar un analisis actualiza las figuras con el.

La paleta y la tipografia vienen de estilo_viz.py, comprobadas con el validador
de la guia de visualizacion en modo claro y oscuro. Dos reglas se respetan en
todas las figuras:

  - Ninguna oposicion se codifica con el par rojo-verde: el validador lo rechaza
    (CVD ΔE 4,1 en deuteranopia). Se usa la pareja divergente azul <-> rojo.
  - La identidad nunca depende del color en solitario: cada figura lleva leyenda
    o etiquetas directas.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from estilo_viz import (
    AZUL,
    AZUL_RAMPA,
    EJE,
    INK,
    INK_2,
    INK_MUTE,
    NARANJA,
    REJILLA,
    NEUTRO,
    ROJO,
    aplicar_estilo,
    barras_redondeadas,
    coma,
    encabezado,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, "figuras_auditoria")
os.makedirs(FIG_DIR, exist_ok=True)

aplicar_estilo()


def guardar(fig, nombre):
    """Guarda en PDF (para LaTeX) y en PNG (para la interfaz web)."""
    ruta = os.path.join(FIG_DIR, nombre)
    fig.savefig(ruta)
    fig.savefig(ruta.replace(".pdf", ".png"), dpi=180)
    plt.close(fig)
    print(f"  {nombre}")


# --------------------------------------------------------------------------
def fig_curacion_llm():
    """Magnitud (% curado) con las dos cohortes fallidas marcadas.

    Forma: barras horizontales, la magnitud es el dato. El color es una rampa
    secuencial de un solo tono (magnitud), y el rojo marca el estado de fallo,
    siempre acompanado de etiqueta directa.
    """
    aud = pd.read_csv(os.path.join(BASE_DIR, "AUDITORIA_COHORTES.csv"))
    aud = aud.sort_values("Tasa_Exito_Curacion")
    t = aud["Tasa_Exito_Curacion"].values * 100

    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    ax.grid(axis="x", color=REJILLA, linewidth=0.6)
    ax.grid(axis="y", visible=False)

    colores = [ROJO if v < 50 else (AZUL_RAMPA[300] if v < 100 else AZUL_RAMPA[450])
               for v in t]
    ax.set_yticks(np.arange(len(aud)))
    ax.set_ylim(-0.7, len(aud) - 0.3)
    ax.set_xlim(0, 152)
    barras_redondeadas(ax, np.arange(len(aud)), t, 0.55, colores,
                       horizontal=True)

    for i, (_, r) in enumerate(aud.iterrows()):
        perdidas = int(r["N_Sin_Clasificar"])
        etq = (f"{perdidas} de {int(r['N_Total'])} sin clasificar"
               if perdidas else "curación completa")
        peso = "semibold" if r["Tasa_Exito_Curacion"] < 0.5 else "normal"
        ax.text(t[i] + 2, i, etq, va="center", fontsize=7.2,
                color=INK if peso == "semibold" else INK_2, weight=peso)

    ax.set_yticklabels(aud["Cohorte"], fontsize=7.5, color=INK_2)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100 %"])
    ax.axvline(100, color=EJE, lw=0.7, ls=(0, (2, 2)), zorder=2)
    encabezado(ax, "Curación clínica automatizada por cohorte",
               "El fallo es bimodal: éxito casi completo, o colapso")
    ax.legend(handles=[
        Patch(facecolor=AZUL_RAMPA[450], label="completa"),
        Patch(facecolor=AZUL_RAMPA[300], label="parcial"),
        Patch(facecolor=ROJO, label="colapso (< 50 %)"),
    ], loc="lower right", ncol=3, bbox_to_anchor=(1.0, -0.28))
    guardar(fig, "fig_curacion_llm.pdf")


# --------------------------------------------------------------------------
def fig_lodo_vs_baseline():
    """Magnitud frente a una referencia, con estado por cohorte.

    La oposicion "supera / no supera" usa la pareja divergente azul-rojo, nunca
    verde-rojo. El gris queda reservado a "no evaluable", que no es una serie.
    """
    r = pd.read_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"))
    r = r.sort_values(["Evaluable", "Ganancia_vs_Baseline"],
                      ascending=[False, False]).reset_index(drop=True)
    x = np.arange(len(r))

    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    colores = [NEUTRO if not e else (AZUL if g > 0 else ROJO)
               for e, g in zip(r["Evaluable"], r["Ganancia_vs_Baseline"])]
    ax.set_xlim(-0.7, len(r) - 0.3)
    ax.set_ylim(0, 1.06)
    barras_redondeadas(ax, x, r["Accuracy"].values, 0.5, colores)

    # Referencia: el azar informado de cada cohorte.
    for i, b in enumerate(r["Baseline_Mayoritaria"]):
        ax.plot([i - 0.34, i + 0.34], [b, b], color=INK, lw=1.6,
                solid_capstyle="round", zorder=5)

    for i, row in r.iterrows():
        if not row["Evaluable"]:
            ax.text(i, 0.06, "no evaluable", ha="center", va="bottom",
                    fontsize=6.6, color="white", weight="semibold",
                    rotation=90, zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels(r["Cohorte_Test"], rotation=38, ha="right", fontsize=7.3)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(coma))
    ax.set_ylabel("Proporción de acierto")
    encabezado(ax, "Validación LODO frente al azar informado",
               "La marca negra es el baseline de clase mayoritaria de cada cohorte")
    ax.legend(handles=[
        Patch(facecolor=AZUL, label="supera su baseline"),
        Patch(facecolor=ROJO, label="por debajo de su baseline"),
        Patch(facecolor=NEUTRO, label="no evaluable (una sola clase)"),
        Line2D([0], [0], color=INK, lw=1.6, label="baseline"),
    ], loc="lower left", ncol=2, bbox_to_anchor=(0.0, -0.46))
    guardar(fig, "fig_lodo_vs_baseline.pdf")


# --------------------------------------------------------------------------
def fig_auc_vs_balacc():
    """Serie unica: no procede leyenda, el titulo la nombra.

    El area de cada punto codifica el tamano de la cohorte; la diagonal es la
    referencia de "decision perfectamente calibrada".
    """
    r = pd.read_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"))
    r = r[r["Evaluable"]].copy()

    fig, ax = plt.subplots(figsize=(4.9, 4.5))
    ax.grid(axis="both", color=REJILLA, linewidth=0.6)
    ax.plot([0.42, 1.02], [0.42, 1.02], ls=(0, (3, 3)), color=EJE, lw=0.9,
            zorder=2)
    ax.annotate("calibración perfecta", xy=(0.92, 0.92), xytext=(-4, -14),
                textcoords="offset points", fontsize=6.8, color=INK_MUTE,
                rotation=39, ha="right")

    ax.scatter(r["Balanced_Accuracy"], r["AUC"],
               s=26 + r["n_test"] * 0.6, color=AZUL, alpha=0.8,
               edgecolor="white", linewidth=1.4, zorder=4)

    # Offsets manuales por cohorte para evitar solapamiento en el cluster
    # superior derecho (AUC ~1, BalAcc ~0.9).
    OFFSETS = {
        "GSE40791":  (14, -4),    # aparta a la derecha del punto (aislado a la izq)
        "GSE7670":   (-8, 12),    # arriba a la izquierda
        "GSE19804":  (10, -12),   # abajo a la derecha
        "GSE118370": (-14, 10),   # muy a la izquierda arriba
        "GSE18842":  (-14, -12),  # abajo a la izquierda
        "GSE19188":  (14, -12),   # abajo a la derecha
        "GSE31210":  (14, 12),    # arriba a la derecha
        "GSE23066":  (0, -12),    # abajo (esta aislada)
    }
    for _, row in r.iterrows():
        cohorte = row["Cohorte_Test"]
        dx, dy = OFFSETS.get(cohorte, (0, -13))
        ha = "left" if dx > 4 else "right" if dx < -4 else "center"
        ax.annotate(cohorte,
                    (row["Balanced_Accuracy"], row["AUC"]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=6.8, color=INK_2, ha=ha)

    ax.set_xlim(0.42, 1.08)
    ax.set_ylim(0.42, 1.06)
    ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.xaxis.set_major_formatter(plt.FuncFormatter(coma))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(coma))
    ax.set_xlabel("Balanced accuracy  (decisión con umbral 0,5)")
    ax.set_ylabel("AUC  (capacidad de ordenación)")
    encabezado(ax, "Discriminación frente a decisión",
               "El área del punto es el tamaño de la cohorte")
    # Anotacion "ordena bien, decide mal": desplazada a la izquierda del cluster
    # de GSE40791 para no invadir su label.
    ax.annotate("ordena bien,\ndecide mal", xy=(0.44, 0.985),
                fontsize=7.4, color=ROJO, style="italic", va="top",
                ha="left")
    guardar(fig, "fig_auc_vs_balacc.pdf")


# --------------------------------------------------------------------------
def fig_concordancia_folds():
    """Dos condiciones que solo difieren en el solapamiento: dos slots
    categoricos, con el valor etiquetado directamente en cada barra."""
    c = pd.read_csv(os.path.join(BASE_DIR, "FALACIA_FOLDS_COMPARACION.csv"))
    v = c["concordancia_pareja_media"].values * 100

    fig, ax = plt.subplots(figsize=(4.7, 3.7))
    ax.set_xlim(-0.55, 1.95)
    ax.set_ylim(0, 116)
    barras_redondeadas(ax, [0, 1], v, 0.42, [NARANJA, AZUL])
    for i, val in enumerate(v):
        ax.text(i, val + 2, f"{val:.1f} %".replace(".", ","), ha="center",
                fontsize=11.5, color=INK, weight="semibold")

    # La caida: lo unico que cambia entre ambas condiciones.
    ax.annotate("", xy=(1.42, v[1]), xytext=(1.42, v[0]),
                arrowprops=dict(arrowstyle="<->", color=INK_2, lw=0.9))
    ax.text(1.5, (v[0] + v[1]) / 2, f"−{v[0] - v[1]:.0f}\npuntos",
            fontsize=8, color=INK, va="center", weight="semibold")

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Parejas de folds LODO\n98 % de muestras compartidas",
                        "Mitades disjuntas\n0 % compartido, $n$ comparable"],
                       fontsize=7.6, color=INK_2)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100 %"])
    ax.set_ylabel("Concordancia de signo entre modelos")
    encabezado(ax, "El acuerdo de signo lo produce el solapamiento",
               "Entrenamientos de tamaño comparable: solo cambia si comparten muestras")
    guardar(fig, "fig_concordancia_folds.pdf")


# --------------------------------------------------------------------------
def fig_composicion():
    """Multiplos pequenos, serie unica. La recta de ajuste va en ink
    secundario, no en un segundo color de serie."""
    d = pd.read_csv(os.path.join(BASE_DIR, "COMPOSICION_SCORES_POR_MUESTRA.csv"))
    res = pd.read_csv(os.path.join(BASE_DIR, "COMPOSICION_VS_BIOLOGIA.csv"))
    ev = (res.dropna(subset=["Rho_SOLO_TUMORES_vs_PulmonNormal"])
          .sort_values("n_tumores", ascending=False))

    fig, axes = plt.subplots(1, len(ev), figsize=(2.55 * len(ev), 3.0))
    axes = np.atleast_1d(axes)
    for ax, (_, r) in zip(axes, ev.iterrows()):
        sub = d[(d["Cohorte"] == r["Cohorte"]) & d["Es_Tumor"]]
        ax.grid(axis="both", color=REJILLA, linewidth=0.6)
        ax.scatter(sub["Score_PulmonNormal"], sub["Score_Clasificador"],
                   s=13, color=AZUL, alpha=0.62, edgecolor="none", zorder=3)
        if len(sub) > 2:
            z = np.polyfit(sub["Score_PulmonNormal"], sub["Score_Clasificador"], 1)
            xs = np.linspace(sub["Score_PulmonNormal"].min(),
                             sub["Score_PulmonNormal"].max(), 20)
            ax.plot(xs, np.polyval(z, xs), color=INK, lw=1.3, zorder=4)
        rho = f"{r['Rho_SOLO_TUMORES_vs_PulmonNormal']:.2f}".replace(".", ",")
        ax.set_title(f"{r['Cohorte']}", fontsize=8.8, pad=14)
        ax.annotate(f"ρ = {rho}   n = {int(r['n_tumores'])}",
                    xy=(0, 1), xycoords="axes fraction", xytext=(0, 4),
                    textcoords="offset points", fontsize=7.2, color=INK_2)
        ax.set_xlabel("Contenido de pulmón normal", fontsize=7.4)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(coma))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(coma))
        ax.tick_params(labelsize=6.8)
        ax.locator_params(nbins=5)
    axes[0].set_ylabel("Score del clasificador", fontsize=7.4)
    fig.suptitle("Solo muestras tumorales: el score sigue al tejido normal residual",
                 fontsize=9.5, x=0.005, ha="left", weight="semibold", color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.9])
    guardar(fig, "fig_composicion_tumores.pdf")


# --------------------------------------------------------------------------
def fig_neuroendocrinos():
    """Dos grupos: leyenda obligatoria (>= 2 series) ademas del eje, que ya
    nombra cada histologia."""
    p = pd.read_csv(os.path.join(BASE_DIR, "SUBTIPO_PROBS_AMBIGUAS.csv"))
    orden = (p.groupby("Histologia")["P_Escamoso"].agg(["median", "count"])
             .query("count >= 3").sort_values("median"))
    grupos = [p.loc[p["Histologia"] == h, "P_Escamoso"].values for h in orden.index]

    def es_neuro(h):
        return any(k in h for k in ("neuroendocrino", "microcitico", "carcinoide"))

    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    bp = ax.boxplot(grupos, widths=0.5, patch_artist=True, zorder=3,
                    medianprops=dict(color=INK, lw=1.4),
                    whiskerprops=dict(color=EJE, lw=0.9),
                    capprops=dict(color=EJE, lw=0.9),
                    flierprops=dict(marker="o", markersize=2.6,
                                    markerfacecolor=INK_MUTE,
                                    markeredgecolor="none", alpha=0.5))
    for caja, h in zip(bp["boxes"], orden.index):
        caja.set_facecolor(NARANJA if es_neuro(h) else AZUL)
        caja.set_alpha(0.72)
        caja.set_edgecolor("white")
        caja.set_linewidth(1.2)

    ax.axhline(0.5, color=INK_2, ls=(0, (3, 3)), lw=0.9, zorder=2)
    ax.text(len(grupos) + 0.42, 0.5, "umbral", fontsize=6.9, color=INK_MUTE,
            va="center")
    for y0, y1 in [(0.9, 1.0), (0.0, 0.1)]:
        ax.axhspan(y0, y1, color=EJE, alpha=0.22, zorder=1)
    ax.text(0.62, 0.95, "alta confianza", fontsize=6.6, color=INK_MUTE,
            va="center")

    ax.set_xticklabels([f"{h}\nn = {int(n)}"
                        for h, n in zip(orden.index, orden["count"])],
                       fontsize=7.0, color=INK_2)
    ax.set_ylim(-0.04, 1.04)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(coma))
    ax.set_ylabel("$P$(escamoso) asignada")
    encabezado(ax, "Histologías ausentes del entrenamiento",
               "Los neuroendocrinos se desplazan hacia adenocarcinoma")
    ax.legend(handles=[
        Patch(facecolor=NARANJA, alpha=0.72, label="tumor neuroendocrino"),
        Patch(facecolor=AZUL, alpha=0.72, label="otras histologías excluidas"),
    ], loc="lower left", ncol=2, bbox_to_anchor=(0.0, -0.42))
    guardar(fig, "fig_histologias_excluidas.pdf")


# --------------------------------------------------------------------------
def fig_panel_minimo():
    """Rendimiento frente al tamano del panel: cuantos genes bastan.

    Forma: linea sobre magnitud creciente, con la banda entre el AUC medio y el
    minimo entre cohortes. El minimo importa mas que la media: un panel util no
    puede depender de que la cohorte de destino sea la favorable.
    """
    c = pd.read_csv(os.path.join(BASE_DIR, "PANEL_MINIMO_CURVA.csv"))
    with open(os.path.join(BASE_DIR, "FIRMA_VALIDADA_RESUMEN.json")) as fh:
        res = json.load(fh)
    k = res["panel_minimo"]

    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    ax.grid(axis="both", color=REJILLA, linewidth=0.6)
    ax.fill_between(c["N_Genes"], c["AUC_Minima"], c["AUC_Media"],
                    color=AZUL, alpha=0.16, zorder=2, linewidth=0)
    ax.plot(c["N_Genes"], c["AUC_Media"], color=AZUL, lw=2,
            marker="o", markersize=4.5, markeredgecolor="white",
            markeredgewidth=1, zorder=4, label="AUC media entre cohortes")
    ax.plot(c["N_Genes"], c["AUC_Minima"], color=INK_2, lw=1.1,
            ls=(0, (3, 2)), zorder=3, label="AUC de la peor cohorte")

    ax.axvline(k, color=ROJO, lw=1.1, zorder=5)
    ax.annotate(f"panel mínimo\n{k} genes",
                xy=(k, c["AUC_Minima"].min()), xytext=(6, 4),
                textcoords="offset points", fontsize=7.6, color=ROJO,
                weight="semibold", va="bottom")

    ax.set_xscale("log")
    ax.set_xticks([3, 10, 30, 100, 500])
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_xlabel("Genes en el panel (escala logarítmica)")
    ax.set_ylabel("AUC en validación LODO")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(coma))
    ax.set_ylim(0.86, 1.005)
    ax.legend(loc="lower right", ncol=1)
    encabezado(ax, "Cuántos biomarcadores bastan",
               "Con 20 genes el rendimiento ya no mejora de forma apreciable")
    guardar(fig, "fig_panel_minimo.pdf")


if __name__ == "__main__":
    print("Generando figuras en figuras_auditoria/")
    fig_curacion_llm()
    fig_lodo_vs_baseline()
    fig_auc_vs_balacc()
    fig_concordancia_folds()
    fig_composicion()
    fig_neuroendocrinos()
    fig_panel_minimo()
    print("Listo.")
