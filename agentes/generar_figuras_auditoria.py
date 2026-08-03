"""
Genera las figuras de los capitulos de Resultados y Discusion (pasos 14-18).

Todas las figuras se construyen desde los CSV producidos por los pasos 14-18; no
se codifica ningun valor a mano, de modo que si un analisis se reejecuta las
figuras cambian con el.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, "figuras_auditoria")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 300,
    "savefig.bbox": "tight",
})

AZUL, ROJO, GRIS, VERDE = "#2c5f8a", "#b5453b", "#9aa0a6", "#3d7a5a"


def guardar(fig, nombre):
    """Guarda en PDF (para LaTeX) y en PNG (para la interfaz web)."""
    ruta = os.path.join(FIG_DIR, nombre)
    fig.savefig(ruta)
    png = ruta.replace(".pdf", ".png")
    fig.savefig(png, dpi=170, transparent=True)
    plt.close(fig)
    print(f"  {nombre} + {os.path.basename(png)}")


def fig_curacion_llm():
    """Tasa de exito de la curacion clinica automatizada por cohorte."""
    aud = pd.read_csv(os.path.join(BASE_DIR, "AUDITORIA_COHORTES.csv"))
    aud = aud.sort_values("Tasa_Exito_Curacion")
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    col = [ROJO if t < 0.5 else (GRIS if t < 1 else AZUL)
           for t in aud["Tasa_Exito_Curacion"]]
    ax.barh(aud["Cohorte"], aud["Tasa_Exito_Curacion"] * 100, color=col)
    for i, (_, r) in enumerate(aud.iterrows()):
        ax.text(r["Tasa_Exito_Curacion"] * 100 + 1.5, i,
                f"{r['N_Sin_Clasificar']:.0f}/{r['N_Total']:.0f} perdidas"
                if r["N_Sin_Clasificar"] else "completa",
                va="center", fontsize=7.5, color="#333")
    ax.set_xlim(0, 128)
    ax.set_xlabel("Muestras clasificadas por el LLM (\\%)")
    ax.axvline(100, color="k", lw=0.6, ls=":")
    ax.set_title("Tasa de exito de la curacion clinica automatizada",
                 loc="left", fontsize=10)
    guardar(fig, "fig_curacion_llm.pdf")


def fig_lodo_vs_baseline():
    """Accuracy frente al baseline de clase mayoritaria, por cohorte."""
    r = pd.read_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"))
    r = r.sort_values(["Evaluable", "Ganancia_vs_Baseline"], ascending=[False, False])
    x = np.arange(len(r))
    fig, ax = plt.subplots(figsize=(7, 3.6))

    col = [AZUL if (e and g > 0) else (ROJO if e else GRIS)
           for e, g in zip(r["Evaluable"], r["Ganancia_vs_Baseline"])]
    ax.bar(x, r["Accuracy"], color=col, width=0.62, label="Accuracy obtenida")
    ax.scatter(x, r["Baseline_Mayoritaria"], marker="_", s=420, color="k",
               linewidths=1.8, zorder=5, label="Baseline de clase mayoritaria")

    for i, (_, row) in enumerate(r.iterrows()):
        if not row["Evaluable"]:
            ax.text(i, 0.04, "no\nevaluable", ha="center", fontsize=6.5,
                    color="white", weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(r["Cohorte_Test"], rotation=45, ha="right", fontsize=7.5)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Proporcion")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left", ncol=2)
    ax.set_title("Validacion LODO: accuracy frente al azar informado",
                 loc="left", fontsize=10)
    guardar(fig, "fig_lodo_vs_baseline.pdf")


def fig_auc_vs_balacc():
    """Discriminacion (AUC) frente a decision (balanced accuracy)."""
    r = pd.read_csv(os.path.join(BASE_DIR, "LODO_HONESTO_RESULTADOS.csv"))
    r = r[r["Evaluable"]].copy()
    fig, ax = plt.subplots(figsize=(4.6, 4.3))
    ax.plot([0.4, 1.02], [0.4, 1.02], ls="--", color=GRIS, lw=0.8)
    ax.scatter(r["Balanced_Accuracy"], r["AUC"],
               s=18 + r["n_test"] * 0.55, color=AZUL, alpha=0.75,
               edgecolor="white", linewidth=0.8, zorder=3)
    for _, row in r.iterrows():
        ax.annotate(row["Cohorte_Test"],
                    (row["Balanced_Accuracy"], row["AUC"]),
                    xytext=(4, -7), textcoords="offset points", fontsize=6.8)
    ax.set_xlabel("Balanced accuracy (decision con umbral 0,5)")
    ax.set_ylabel("AUC (capacidad de ordenacion)")
    ax.set_xlim(0.4, 1.03)
    ax.set_ylim(0.4, 1.03)
    ax.text(0.44, 0.98, "ordena bien,\ndecide mal", fontsize=7.5,
            color=ROJO, style="italic")
    ax.set_title("La firma discrimina, pero el umbral\nno transfiere entre cohortes",
                 loc="left", fontsize=9.5)
    guardar(fig, "fig_auc_vs_balacc.pdf")


def fig_concordancia_folds():
    """Concordancia de signo: folds solapados frente a mitades disjuntas."""
    c = pd.read_csv(os.path.join(BASE_DIR, "FALACIA_FOLDS_COMPARACION.csv"))
    vals = c["concordancia_pareja_media"].values * 100
    fig, ax = plt.subplots(figsize=(4.4, 3.5))
    barras = ax.bar(["Parejas de folds LODO\n(98\\% de muestras\ncompartidas)",
                     "Mitades disjuntas\n(0\\% compartido,\n$n$ comparable)"],
                    vals, color=[ROJO, AZUL], width=0.55)
    for b, v in zip(barras, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}\\%",
                ha="center", fontsize=10, weight="bold")
    ax.annotate("", xy=(1, vals[1]), xytext=(1, vals[0]),
                arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax.text(1.08, (vals[0] + vals[1]) / 2, f"$-${vals[0] - vals[1]:.0f} puntos",
            fontsize=8.5, va="center")
    ax.set_ylim(0, 118)
    ax.set_ylabel("Concordancia de signo entre modelos (\\%)")
    ax.set_title("El acuerdo de signo lo produce el\nsolapamiento, no la biologia",
                 loc="left", fontsize=9.5)
    guardar(fig, "fig_concordancia_folds.pdf")


def fig_composicion():
    """Score del clasificador frente a contenido de pulmon normal, en tumores."""
    d = pd.read_csv(os.path.join(BASE_DIR, "COMPOSICION_SCORES_POR_MUESTRA.csv"))
    res = pd.read_csv(os.path.join(BASE_DIR, "COMPOSICION_VS_BIOLOGIA.csv"))
    evaluables = res.dropna(subset=["Rho_SOLO_TUMORES_vs_PulmonNormal"])
    evaluables = evaluables.sort_values("n_tumores", ascending=False).head(4)

    fig, axes = plt.subplots(1, len(evaluables),
                             figsize=(2.6 * len(evaluables), 2.9), sharey=False)
    axes = np.atleast_1d(axes)
    for ax, (_, r) in zip(axes, evaluables.iterrows()):
        sub = d[(d["Cohorte"] == r["Cohorte"]) & (d["Es_Tumor"])]
        ax.scatter(sub["Score_PulmonNormal"], sub["Score_Clasificador"],
                   s=11, color=AZUL, alpha=0.6, edgecolor="none")
        if len(sub) > 2:
            z = np.polyfit(sub["Score_PulmonNormal"], sub["Score_Clasificador"], 1)
            xs = np.linspace(sub["Score_PulmonNormal"].min(),
                             sub["Score_PulmonNormal"].max(), 20)
            ax.plot(xs, np.polyval(z, xs), color=ROJO, lw=1.3)
        rho = r["Rho_SOLO_TUMORES_vs_PulmonNormal"]
        ax.set_title(f"{r['Cohorte']}\n$\\rho={rho:.2f}$  ($n={int(r['n_tumores'])}$)",
                     fontsize=8.5)
        ax.set_xlabel("Pulmon normal", fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].set_ylabel("Score del clasificador", fontsize=8)
    fig.suptitle("Solo muestras tumorales: el score sigue al tejido normal residual",
                 fontsize=9.5, x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    guardar(fig, "fig_composicion_tumores.pdf")


def fig_neuroendocrinos():
    """Probabilidad asignada a histologias no vistas por el clasificador."""
    p = pd.read_csv(os.path.join(BASE_DIR, "SUBTIPO_PROBS_AMBIGUAS.csv"))
    orden = (p.groupby("Histologia")["P_Escamoso"]
             .agg(["median", "count"]).query("count >= 3")
             .sort_values("median"))
    grupos = [p.loc[p["Histologia"] == h, "P_Escamoso"].values for h in orden.index]
    etiquetas = [f"{h}\n($n={int(n)}$)"
                 for h, n in zip(orden.index, orden["count"])]

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    bp = ax.boxplot(grupos, vert=True, patch_artist=True, widths=0.55,
                    medianprops=dict(color="k", lw=1.3),
                    flierprops=dict(marker="o", markersize=2.5, alpha=0.5))
    for caja, h in zip(bp["boxes"], orden.index):
        neuro = any(k in h for k in ("neuroendocrino", "microcitico", "carcinoide"))
        caja.set_facecolor(ROJO if neuro else AZUL)
        caja.set_alpha(0.65)
    ax.axhline(0.5, color="k", ls="--", lw=0.8)
    ax.axhspan(0.9, 1.0, color=GRIS, alpha=0.18)
    ax.axhspan(0.0, 0.1, color=GRIS, alpha=0.18)
    ax.text(len(grupos) + 0.35, 0.5, "umbral", fontsize=7, va="center", rotation=90)
    ax.set_xticklabels(etiquetas, fontsize=7)
    ax.set_ylabel("$P$(escamoso) asignada")
    ax.set_ylim(-0.03, 1.03)
    ax.set_title("Histologias excluidas del entrenamiento: en rojo, "
                 "tumores neuroendocrinos", loc="left", fontsize=9.5)
    guardar(fig, "fig_histologias_excluidas.pdf")


if __name__ == "__main__":
    print("Generando figuras en figuras_auditoria/")
    fig_curacion_llm()
    fig_lodo_vs_baseline()
    fig_auc_vs_balacc()
    fig_concordancia_folds()
    fig_composicion()
    fig_neuroendocrinos()
    print("Listo.")
